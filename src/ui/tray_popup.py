"""Non-modal tray popup menu — avoids Win32 TrackPopupMenu keyboard capture."""

from __future__ import annotations

import logging
import sys
import threading
from typing import Any, Callable

logger = logging.getLogger(__name__)

__all__ = ["show_tray_popup_menu"]

_active_popup_close: Callable[[], None] | None = None
_popup_lock = threading.Lock()


def show_tray_popup_menu(
    items: list[Any],
    *,
    x: int,
    y: int,
    icon: Any = None,
) -> None:
    """Show a lightweight popup at (x, y). Does not use grab_set or modal menu loop."""
    if sys.platform != "win32":
        return

    if not items:
        logger.warning("Tray popup skipped — menu items not ready yet")
        return

    global _active_popup_close

    with _popup_lock:
        if _active_popup_close is not None:
            try:
                _active_popup_close()
            except Exception:
                pass
            _active_popup_close = None

    def runner() -> None:
        global _active_popup_close
        try:
            closer = _run_popup(items, x=x, y=y, icon=icon)
            with _popup_lock:
                _active_popup_close = closer
        except Exception:
            logger.exception("Tray popup failed")
            with _popup_lock:
                _active_popup_close = None

    threading.Thread(target=runner, daemon=True, name="tray-popup").start()


def _run_popup(items: list[Any], *, x: int, y: int, icon: Any) -> Callable[[], None]:
    import tkinter as tk

    root = tk.Tk()
    root.withdraw()

    popup = tk.Toplevel(root)
    popup.overrideredirect(True)
    popup.attributes("-topmost", True)
    popup.configure(bg="#2b2b2b", highlightthickness=1, highlightbackground="#555555")

    frame = tk.Frame(popup, bg="#2b2b2b", padx=0, pady=0)
    frame.pack(fill="both", expand=True)

    closed = {"value": False}

    def close() -> None:
        if closed["value"]:
            return
        closed["value"] = True
        try:
            popup.destroy()
        except tk.TclError:
            pass
        try:
            root.quit()
        except tk.TclError:
            pass

    def run_action(action: Callable[..., None] | None) -> None:
        close()
        if action is None:
            return
        try:
            action(icon, None)
        except TypeError:
            action()

    for spec in items:
        if spec.separator:
            sep = tk.Frame(frame, bg="#555555", height=1)
            sep.pack(fill="x", padx=6, pady=2)
            continue

        if spec.enabled and spec.action is not None:
            btn = tk.Button(
                frame,
                text=spec.label,
                anchor="w",
                relief="flat",
                bg="#2b2b2b",
                fg="#f0f0f0",
                activebackground="#3d3d3d",
                activeforeground="#ffffff",
                font=("Segoe UI", 9),
                padx=12,
                pady=4,
                command=lambda action=spec.action: run_action(action),
            )
            btn.pack(fill="x")
            btn.bind("<Enter>", lambda _e, b=btn: b.configure(bg="#3d3d3d"))
            btn.bind("<Leave>", lambda _e, b=btn: b.configure(bg="#2b2b2b"))
        else:
            lbl = tk.Label(
                frame,
                text=spec.label,
                anchor="w",
                bg="#2b2b2b",
                fg="#aaaaaa",
                font=("Segoe UI", 9),
                padx=12,
                pady=4,
            )
            lbl.pack(fill="x")

    popup.update_idletasks()
    width = max(popup.winfo_reqwidth(), 220)
    height = popup.winfo_reqheight()
    screen_w = popup.winfo_screenwidth()
    screen_h = popup.winfo_screenheight()
    # Align like a taskbar context menu: above and right-aligned to the cursor.
    pos_x = max(0, min(x - width, screen_w - width))
    pos_y = max(0, min(y - height, screen_h - height))
    popup.geometry(f"{width}x{height}+{pos_x}+{pos_y}")

    popup.bind("<Escape>", lambda _e: close())
    logger.info("Tray popup opened at (%d, %d)", pos_x, pos_y)

    def on_done() -> None:
        global _active_popup_close
        with _popup_lock:
            if _active_popup_close is close:
                _active_popup_close = None

    try:
        root.protocol("WM_DELETE_WINDOW", close)
        root.mainloop()
    finally:
        on_done()
        try:
            root.destroy()
        except tk.TclError:
            pass

    return close
