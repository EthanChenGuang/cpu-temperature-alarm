"""Windows logon autostart via Startup folder shortcut (visible in Settings > Startup)."""

from __future__ import annotations

import logging
import subprocess
import sys
from pathlib import Path

from src.paths import app_root
from src.platform.windows import hidden_subprocess_kwargs

logger = logging.getLogger(__name__)

DEFAULT_TASK_NAME = "CpuTempAlert"
STARTUP_SHORTCUT_NAME = "CPU Temp Alert.lnk"
TASK_DESCRIPTION = "CPU High Temperature Alert — silent tray monitor at logon"
_POWERSHELL = ["powershell.exe", "-NoProfile", "-WindowStyle", "Hidden", "-ExecutionPolicy", "Bypass"]

__all__ = [
    "DEFAULT_TASK_NAME",
    "STARTUP_SHORTCUT_NAME",
    "disable_autostart",
    "enable_autostart",
    "is_autostart_enabled",
    "set_autostart",
    "startup_shortcut_path",
]


def _ps_quote(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def _run_powershell(script: str, *, timeout: int = 30) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [*_POWERSHELL, "-Command", script],
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
        **hidden_subprocess_kwargs(),
    )


def _set_shortcut_run_as_admin_powershell(shortcut_path_expr: str = "$ShortcutPath") -> str:
    """PowerShell snippet to mark a .lnk as Run as administrator."""
    return f"""
$bytes = [System.IO.File]::ReadAllBytes({shortcut_path_expr})
$bytes[0x15] = $bytes[0x15] -bor 0x20
[System.IO.File]::WriteAllBytes({shortcut_path_expr}, $bytes)
"""


def autostart_launch_spec() -> tuple[str, str, Path]:
    """Return executable, arguments, and working directory for autostart."""
    if getattr(sys, "frozen", False):
        exe = Path(sys.executable).resolve()
        return str(exe), "--logon-delay 30", exe.parent

    root = app_root()
    executable = Path(sys.executable)
    pythonw = executable.with_name("pythonw.exe")
    if not pythonw.exists():
        pythonw = executable
    return str(pythonw.resolve()), "-m src.main --logon-delay 30", root


def startup_shortcut_path() -> Path:
    """Return the Startup-folder shortcut path for the current user."""
    if sys.platform != "win32":
        return Path(STARTUP_SHORTCUT_NAME)
    import os

    appdata = os.environ.get("APPDATA", "")
    return Path(appdata) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup" / STARTUP_SHORTCUT_NAME


def _remove_legacy_scheduled_task(task_name: str = DEFAULT_TASK_NAME) -> None:
    """Remove old Task Scheduler entry so we do not launch twice."""
    script = (
        f"Unregister-ScheduledTask -TaskName {_ps_quote(task_name)} "
        "-Confirm:$false -ErrorAction SilentlyContinue"
    )
    _run_powershell(script, timeout=15)


def is_autostart_enabled(task_name: str = DEFAULT_TASK_NAME) -> bool:
    if sys.platform != "win32":
        return False

    shortcut = startup_shortcut_path()
    if shortcut.is_file():
        return True

    script = (
        f"$task = Get-ScheduledTask -TaskName {_ps_quote(task_name)} "
        "-ErrorAction SilentlyContinue; "
        "if ($null -eq $task) { exit 1 }; "
        "exit 0"
    )
    result = _run_powershell(script, timeout=15)
    return result.returncode == 0


def enable_autostart(task_name: str = DEFAULT_TASK_NAME) -> tuple[bool, str]:
    if sys.platform != "win32":
        return False, "Autostart is only supported on Windows."

    target, arguments, working_dir = autostart_launch_spec()
    if not Path(target).exists():
        return False, f"Executable not found: {target}"

    shortcut = startup_shortcut_path()
    arg_line = f"$Link.Arguments = {_ps_quote(arguments)}" if arguments else ""
    script = f"""
$ErrorActionPreference = 'Stop'
$StartupDir = [Environment]::GetFolderPath('Startup')
$ShortcutPath = Join-Path $StartupDir {_ps_quote(STARTUP_SHORTCUT_NAME)}
$Target = {_ps_quote(target)}
$WorkingDir = {_ps_quote(str(working_dir))}
$Shell = New-Object -ComObject WScript.Shell
$Link = $Shell.CreateShortcut($ShortcutPath)
$Link.TargetPath = $Target
{arg_line}
$Link.WorkingDirectory = $WorkingDir
$Link.Description = {_ps_quote(TASK_DESCRIPTION)}
$Link.Save()
{_set_shortcut_run_as_admin_powershell()}
"""
    result = _run_powershell(script)
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "unknown error").strip()
        logger.warning("Failed to enable autostart: %s", detail)
        return False, f"Could not create startup shortcut: {detail[:160]}"

    _remove_legacy_scheduled_task(task_name)
    logger.info("Autostart enabled via startup shortcut %s", shortcut)
    return True, "Start with Windows enabled."


def disable_autostart(task_name: str = DEFAULT_TASK_NAME) -> tuple[bool, str]:
    if sys.platform != "win32":
        return False, "Autostart is only supported on Windows."

    shortcut = startup_shortcut_path()
    removed_shortcut = False
    if shortcut.is_file():
        try:
            shortcut.unlink()
            removed_shortcut = True
        except OSError as exc:
            logger.warning("Failed to remove startup shortcut: %s", exc)
            return False, f"Could not remove startup shortcut: {exc}"

    _remove_legacy_scheduled_task(task_name)

    if removed_shortcut:
        logger.info("Autostart disabled — removed startup shortcut")
        return True, "Start with Windows disabled."

    script = (
        f"$task = Get-ScheduledTask -TaskName {_ps_quote(task_name)} "
        "-ErrorAction SilentlyContinue; "
        "if ($null -eq $task) { exit 0 }; "
        f"Unregister-ScheduledTask -TaskName {_ps_quote(task_name)} -Confirm:$false -ErrorAction Stop"
    )
    result = _run_powershell(script, timeout=15)
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "unknown error").strip()
        logger.warning("Failed to disable autostart: %s", detail)
        return False, f"Could not remove autostart entry: {detail[:160]}"

    logger.info("Autostart disabled — removed legacy scheduled task")
    return True, "Start with Windows disabled."


def set_autostart(enabled: bool, task_name: str = DEFAULT_TASK_NAME) -> tuple[bool, str]:
    if enabled:
        return enable_autostart(task_name)
    return disable_autostart(task_name)
