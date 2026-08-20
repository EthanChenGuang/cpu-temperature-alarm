"""Settings dialog — Tkinter modal for phone, API key, and threshold."""

from __future__ import annotations

import sys
import threading
from dataclasses import replace
from typing import Any, Callable

from src.config.loader import save_config
from src.config.schema import AppConfig, config_from_dict, validate_config

__all__ = ["show_settings_dialog"]


def show_settings_dialog(
    config: AppConfig,
    *,
    tk_module: Any | None = None,
    on_save: Callable[[AppConfig], None] | None = None,
    config_path: Any | None = None,
    autostart_is_enabled: Callable[[], bool] | None = None,
    autostart_set_enabled: Callable[[bool], tuple[bool, str]] | None = None,
) -> AppConfig | None:
    """Show modal settings dialog. Returns updated config on save, None on cancel."""
    if tk_module is None:
        import tkinter as tk_module

    if autostart_is_enabled is None or autostart_set_enabled is None:
        if sys.platform == "win32":
            from src.platform.autostart import is_autostart_enabled, set_autostart

            autostart_is_enabled = is_autostart_enabled
            autostart_set_enabled = set_autostart
        else:
            autostart_is_enabled = lambda: False
            autostart_set_enabled = lambda _enabled: (False, "Autostart is only supported on Windows.")

    root = tk_module.Tk()
    root.title("CPU Temperature Alert — Settings")
    root.resizable(False, False)

    phone_var = tk_module.StringVar(value=config.whatsapp_phone)
    threshold_var = tk_module.StringVar(value=str(config.threshold_celsius))
    api_key_var = tk_module.StringVar(value=config.callmebot_api_key)
    error_var = tk_module.StringVar(value="")
    sound_alerts_var = tk_module.BooleanVar(value=config.sound_alerts_enabled)
    whatsapp_alerts_var = tk_module.BooleanVar(value=config.whatsapp_alerts_enabled)
    autostart_var = tk_module.BooleanVar(value=autostart_is_enabled())
    autostart_status_var = tk_module.StringVar(
        value="Enabled" if autostart_var.get() else "Disabled"
    )

    frame = tk_module.Frame(root, padx=12, pady=12)
    frame.grid(row=0, column=0, sticky="nsew")

    row = 0

    whatsapp_toggle_frame = tk_module.Frame(frame)
    whatsapp_toggle_frame.grid(row=row, column=0, columnspan=2, sticky="ew", pady=(0, 8))
    row += 1

    tk_module.Checkbutton(
        whatsapp_toggle_frame,
        text="WhatsApp message",
        variable=whatsapp_alerts_var,
        command=lambda: _sync_whatsapp_fields(),
    ).pack(side="left")
    tk_module.Label(
        whatsapp_toggle_frame,
        text="(off = idle; credentials kept)",
        fg="gray",
    ).pack(side="left", padx=(8, 0))

    whatsapp_fields_frame = tk_module.Frame(frame)
    whatsapp_fields_frame.grid(row=row, column=0, columnspan=2, sticky="ew")
    row += 1

    def _sync_whatsapp_fields() -> None:
        if whatsapp_alerts_var.get():
            whatsapp_fields_frame.grid()
        else:
            whatsapp_fields_frame.grid_remove()

    tk_module.Label(whatsapp_fields_frame, text="WhatsApp phone (E.164):").grid(
        row=0, column=0, sticky="w"
    )
    tk_module.Entry(whatsapp_fields_frame, textvariable=phone_var, width=32).grid(
        row=1, column=0, columnspan=2, sticky="ew", pady=(0, 8)
    )

    tk_module.Label(whatsapp_fields_frame, text="CallMeBot API key:").grid(
        row=2, column=0, sticky="w"
    )
    api_row = tk_module.Frame(whatsapp_fields_frame)
    api_row.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(0, 8))

    api_key_visible = {"value": False}

    api_entry = tk_module.Entry(api_row, textvariable=api_key_var, width=28, show="*")
    api_entry.pack(side="left", fill="x", expand=True)

    def _toggle_api_key_visibility() -> None:
        api_key_visible["value"] = not api_key_visible["value"]
        api_entry.config(show="" if api_key_visible["value"] else "*")
        eye_button.config(text="Hide" if api_key_visible["value"] else "\U0001f441")

    eye_button = tk_module.Button(
        api_row,
        text="\U0001f441",
        width=3,
        command=_toggle_api_key_visibility,
    )
    eye_button.pack(side="left", padx=(4, 0))

    tk_module.Label(frame, text="Alarm threshold (°C):").grid(row=row, column=0, sticky="w")
    tk_module.Entry(frame, textvariable=threshold_var, width=8).grid(
        row=row, column=1, sticky="w", padx=(8, 0), pady=(0, 8)
    )
    row += 1

    sound_frame = tk_module.Frame(frame)
    sound_frame.grid(row=row, column=0, columnspan=2, sticky="w", pady=(0, 8))
    row += 1

    tk_module.Checkbutton(
        sound_frame,
        text="Sound alerts",
        variable=sound_alerts_var,
    ).pack(side="left")
    tk_module.Label(
        sound_frame,
        text="(off = mute beeps; independent of WhatsApp)",
        fg="gray",
    ).pack(side="left", padx=(8, 0))

    if sys.platform == "win32":
        autostart_frame = tk_module.Frame(frame)
        autostart_frame.grid(row=row, column=0, columnspan=2, sticky="w", pady=(0, 8))
        row += 1

        def _on_autostart_toggle() -> None:
            desired = autostart_var.get()
            autostart_status_var.set("Enabled" if desired else "Disabled")
            error_var.set("")
            root.update_idletasks()

            def _apply() -> None:
                ok, message = autostart_set_enabled(desired)

                def _finish() -> None:
                    if ok:
                        autostart_status_var.set("Enabled" if desired else "Disabled")
                        error_var.set("")
                    else:
                        autostart_var.set(not desired)
                        autostart_status_var.set("Enabled" if not desired else "Disabled")
                        error_var.set(message)

                root.after(0, _finish)

            root.after(0, lambda: threading.Thread(target=_apply, daemon=True).start())

        tk_module.Checkbutton(
            autostart_frame,
            text="Start with Windows",
            variable=autostart_var,
            command=_on_autostart_toggle,
        ).pack(side="left")
        tk_module.Label(
            autostart_frame,
            textvariable=autostart_status_var,
            fg="gray",
        ).pack(side="left", padx=(8, 0))

    tk_module.Label(frame, textvariable=error_var, fg="red", wraplength=360).grid(
        row=row, column=0, columnspan=2, sticky="w"
    )
    row += 1

    result: dict[str, AppConfig | None] = {"config": None}

    def _attempt_save() -> None:
        error_var.set("")
        try:
            threshold = int(threshold_var.get().strip())
        except ValueError:
            error_var.set("Threshold must be a whole number.")
            return

        api_key = api_key_var.get().strip() or config.callmebot_api_key

        candidate = replace(
            config,
            whatsapp_phone=phone_var.get().strip(),
            callmebot_api_key=api_key,
            threshold_celsius=threshold,
            sound_alerts_enabled=bool(sound_alerts_var.get()),
            whatsapp_alerts_enabled=bool(whatsapp_alerts_var.get()),
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
            "beep_burst_count": candidate.beep_burst_count,
            "beep_burst_gap_ms": candidate.beep_burst_gap_ms,
            "beep_interval_seconds": candidate.beep_interval_seconds,
            "critical_beep_burst_count": candidate.critical_beep_burst_count,
            "critical_beep_interval_seconds": candidate.critical_beep_interval_seconds,
            "mute_duration_seconds": candidate.mute_duration_seconds,
            "sound_alerts_enabled": candidate.sound_alerts_enabled,
            "whatsapp_alerts_enabled": candidate.whatsapp_alerts_enabled,
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
    button_frame.grid(row=row, column=0, columnspan=2, pady=(8, 0))

    tk_module.Button(button_frame, text="Save", command=_attempt_save, width=10).pack(
        side="left", padx=(0, 8)
    )
    tk_module.Button(button_frame, text="Cancel", command=_cancel, width=10).pack(side="left")

    _sync_whatsapp_fields()

    root.protocol("WM_DELETE_WINDOW", _cancel)
    root.mainloop()
    return result["config"]
