"""Short-lived on-screen alert popup for temperature warnings."""

from __future__ import annotations

import logging
import sys
import threading

logger = logging.getLogger(__name__)

DEFAULT_TOAST_SECONDS = 5.0

# Severity ramp: amber (warning) → orange (high) → deep red (critical)
_COLOR_WARNING = "#D97706"
_COLOR_HIGH = "#EA580C"
_COLOR_CRITICAL = "#B42318"

__all__ = [
    "DEFAULT_TOAST_SECONDS",
    "alert_toast_background_color",
    "format_alert_toast_text",
    "show_temperature_alert_toast",
]


def alert_toast_background_color(
    peak_temp: float,
    threshold: int,
    critical_tiers: tuple[int, ...] | list[int] = (),
) -> str:
    """Return toast background color based on peak temperature severity."""
    tiers = sorted({threshold, *critical_tiers})
    if peak_temp < tiers[0]:
        return _COLOR_WARNING

    active_tier = max(t for t in tiers if peak_temp >= t)
    tier_index = tiers.index(active_tier)
    if tier_index == 0:
        return _COLOR_WARNING
    if tier_index == len(tiers) - 1:
        return _COLOR_CRITICAL
    return _COLOR_HIGH


def format_alert_toast_text(peak_temp: float, threshold: int) -> tuple[str, str]:
    """Return (title, body) for the alert popup."""
    title = "CPU/GPU Temperature Alert"
    body = f"Peak temperature {peak_temp:.1f}°C exceeds threshold {threshold}°C."
    return title, body


def show_temperature_alert_toast(
    peak_temp: float,
    threshold: int,
    *,
    critical_tiers: tuple[int, ...] | list[int] = (),
    duration_seconds: float = DEFAULT_TOAST_SECONDS,
) -> None:
    """Show a topmost popup that closes automatically after a few seconds."""
    if sys.platform != "win32":
        return

    title, body = format_alert_toast_text(peak_temp, threshold)
    bg_color = alert_toast_background_color(peak_temp, threshold, critical_tiers)
    thread = threading.Thread(
        target=_run_toast,
        args=(title, body, bg_color, duration_seconds),
        daemon=True,
        name="alert-toast",
    )
    thread.start()


def _run_toast(title: str, body: str, bg_color: str, duration_seconds: float) -> None:
    try:
        import tkinter as tk
        from tkinter import ttk
    except ImportError:
        logger.warning("tkinter unavailable — alert popup skipped")
        return

    root = tk.Tk()
    root.withdraw()

    toast = tk.Toplevel(root)
    toast.overrideredirect(True)
    toast.attributes("-topmost", True)
    toast.configure(bg=bg_color, padx=16, pady=12)

    title_label = tk.Label(
        toast,
        text=title,
        fg="white",
        bg=bg_color,
        font=("Segoe UI", 11, "bold"),
        anchor="w",
        justify="left",
    )
    title_label.pack(fill="x")

    body_label = tk.Label(
        toast,
        text=body,
        fg="white",
        bg=bg_color,
        font=("Segoe UI", 10),
        anchor="w",
        justify="left",
        wraplength=320,
    )
    body_label.pack(fill="x", pady=(6, 0))

    toast.update_idletasks()
    width = max(toast.winfo_reqwidth(), 280)
    height = toast.winfo_reqheight()
    screen_w = toast.winfo_screenwidth()
    screen_h = toast.winfo_screenheight()
    x = screen_w - width - 24
    y = screen_h - height - 64
    toast.geometry(f"{width}x{height}+{x}+{y}")

    def close() -> None:
        try:
            toast.destroy()
        finally:
            root.quit()

    toast.after(int(duration_seconds * 1000), close)
    try:
        root.mainloop()
    finally:
        try:
            root.destroy()
        except tk.TclError:
            pass
