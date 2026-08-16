"""LibreHardwareMonitor bridge via pythonnet."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from src.telemetry.exceptions import LhmDllNotFoundError, LhmRuntimeError


@dataclass(frozen=True)
class SensorReading:
    name: str
    value_celsius: float


class LhmBackend(Protocol):
    def read_temperatures(self) -> list[SensorReading]: ...


def default_vendor_dir() -> Path:
    return Path(__file__).resolve().parents[2] / "vendor" / "LibreHardwareMonitor"


class LhmBridge(LhmBackend):
    def __init__(self, vendor_dir: Path | None = None) -> None:
        self._vendor_dir = vendor_dir or default_vendor_dir()
        self._computer = None
        self._hardware_type = None
        self._sensor_type = None

    def open(self) -> None:
        dll_path = self._vendor_dir / "LibreHardwareMonitorLib.dll"
        if not dll_path.exists():
            raise LhmDllNotFoundError(
                f"LibreHardwareMonitorLib.dll not found at {dll_path}. "
                "Run: pwsh scripts/fetch-lhm.ps1"
            )

        try:
            import sys

            import clr  # noqa: PLC0415 — lazy import per D-15

            vendor_str = str(self._vendor_dir)
            if vendor_str not in sys.path:
                sys.path.append(vendor_str)

            clr.AddReference(str(self._vendor_dir / "LibreHardwareMonitorLib"))
            clr.AddReference(str(self._vendor_dir / "HidSharp"))

            from LibreHardwareMonitor.Hardware import Computer, HardwareType, SensorType

            self._hardware_type = HardwareType
            self._sensor_type = SensorType

            computer = Computer()
            computer.IsCpuEnabled = True
            computer.IsGpuEnabled = True
            computer.IsMemoryEnabled = False
            computer.IsMotherboardEnabled = False
            computer.IsControllerEnabled = False
            computer.IsNetworkEnabled = False
            computer.IsStorageEnabled = False
            computer.Open()
            self._computer = computer
        except LhmDllNotFoundError:
            raise
        except Exception as exc:
            raise LhmRuntimeError(
                "Failed to load LibreHardwareMonitor. "
                "Ensure .NET Framework 4.7.2 or later is installed."
            ) from exc

    def _update_hardware(self, hardware) -> None:
        hardware.Update()
        for sub in hardware.SubHardware:
            self._update_hardware(sub)

    def _iter_cpu_gpu_hardware(self):
        cpu_gpu = {
            self._hardware_type.Cpu,
            self._hardware_type.GpuNvidia,
            self._hardware_type.GpuAmd,
            self._hardware_type.GpuIntel,
        }

        def walk(hardware):
            if hardware.HardwareType in cpu_gpu:
                yield hardware
            for sub in hardware.SubHardware:
                yield from walk(sub)

        for hw in self._computer.Hardware:
            yield from walk(hw)

    @staticmethod
    def _hardware_prefix(hardware_type) -> str:
        from LibreHardwareMonitor.Hardware import HardwareType

        if hardware_type == HardwareType.Cpu:
            return "CPU"
        return "GPU"

    def read_temperatures(self) -> list[SensorReading]:
        if self._computer is None:
            raise LhmRuntimeError("LhmBridge not opened. Call open() first.")

        for hw in self._computer.Hardware:
            self._update_hardware(hw)

        readings: list[SensorReading] = []
        for hardware in self._iter_cpu_gpu_hardware():
            prefix = self._hardware_prefix(hardware.HardwareType)
            for sensor in hardware.Sensors:
                if sensor.SensorType != self._sensor_type.Temperature:
                    continue
                value = sensor.Value
                if value is None:
                    continue
                readings.append(
                    SensorReading(name=f"{prefix} / {sensor.Name}", value_celsius=float(value))
                )
        return readings
