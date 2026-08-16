"""Settings dialog — Tkinter modal for phone, API key, and threshold."""

from __future__ import annotations

from dataclasses import replace
from typing import Any, Callable

from src.config.loader import save_config
from src.config.schema import AppConfig, config_from_dict, validate_config

__all__ = ["show_settings_dialog"]


def _mask_hint(api_key: str) -> str:
    if len(api_key) <= 4:
        return "Enter API key"
    return f"Current key ends with …{api_key[-4:]}"


def show_settings_dialog(
    config: AppConfig,
    *,
    tk_module: Any | None = None,
    on_save: Callable[[AppConfig], None] | None = None,
    config_path: Any | None = None,
) -> AppConfig | None:
    """Show modal settings dialog. Returns updated config on save, None on cancel."""
    if tk_module is None:
        import tkinter as tk_module

    root = tk_module.Tk()
    root.title("CPU Temperature Alert — Settings")
    root.resizable(False, False)

    phone_var = tk_module.StringVar(value=config.whatsapp_phone)
    threshold_var = tk_module.StringVar(value=str(config.threshold_celsius))
    api_key_var = tk_module.StringVar(value="")
    error_var = tk_module.StringVar(value="")

    frame = tk_module.Frame(root, padx=12, pady=12)
    frame.grid(row=0, column=0, sticky="nsew")

    tk_module.Label(frame, text="WhatsApp phone (E.164):").grid(row=0, column=0, sticky="w")
    phone_entry = tk_module.Entry(frame, textvariable=phone_var, width=32)
    phone_entry.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 8))

    tk_module.Label(frame, text="CallMeBot API key:").grid(row=2, column=0, sticky="w")
    tk_module.Label(frame, text=_mask_hint(config.callmebot_api_key), fg="gray").grid(
        row=2, column=1, sticky="e"
    )
    api_entry = tk_module.Entry(frame, textvariable=api_key_var, width=32, show="*")
    api_entry.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(0, 8))

    tk_module.Label(frame, text="Alarm threshold (°C):").grid(row=4, column=0, sticky="w")
    threshold_entry = tk_module.Entry(frame, textvariable=threshold_var, width=8)
    threshold_entry.grid(row=5, column=0, sticky="w", pady=(0, 8))

    error_label = tk_module.Label(frame, textvariable=error_var, fg="red")
    error_label.grid(row=6, column=0, columnspan=2, sticky="w")

    result: dict[str, AppConfig | None] = {"config": None}

    def _attempt_save() -> None:
        error_var.set("")
        try:
            threshold = int(threshold_var.get().strip())
        except ValueError:
            error_var.set("Threshold must be a whole number.")
            return

        new_key = api_key_var.get().strip()
        api_key = new_key if new_key else config.callmebot_api_key

        candidate = replace(
            config,
            whatsapp_phone=phone_var.get().strip(),
            callmebot_api_key=api_key,
            threshold_celsius=threshold,
        )
        data = {
            "threshold_celsius": candidate.threshold_celsius,
            "critical_tiers_celsius": list(candidate.critical_tiers_celsius),
            "cooldown_seconds": candidate.cooldown_seconds,
            "poll_interval_seconds": candidate.poll_interval_seconds,
            "whatsapp_phone": candidate.whatsapp_phone,
            "callmebot_api_key": candidate.callmebot_api_key,
            "beep_frequency_hz": candidate.beep_frequency_hz,
            "beep_duration_ms": candidate.beep_duration_ms,
            "alert_message_template": candidate.alert_message_template,
        }
        try:
            validate_config(data)
            saved = config_from_dict(data)
        except ValueError as exc:
            error_var.set(str(exc))
            return

        save_config(saved, config_path)
        if on_save is not None:
            on_save(saved)
        result["config"] = saved
        root.destroy()

    def _cancel() -> None:
        root.destroy()

    button_frame = tk_module.Frame(frame)
    button_frame.grid(row=7, column=0, columnspan=2, pady=(8, 0))

    tk_module.Button(button_frame, text="Save", command=_attempt_save, width=10).pack(
        side="left", padx=(0, 8)
    )
    tk_module.Button(button_frame, text="Cancel", command=_cancel, width=10).pack(side="left")

    root.protocol("WM_DELETE_WINDOW", _cancel)
    root.mainloop()
    return result["config"]
