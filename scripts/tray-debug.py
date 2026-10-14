"""Diagnose pystray visibility on Windows — writes to %TEMP%\\tray-debug.log"""
import sys
import traceback
from pathlib import Path

LOG = Path(__file__).resolve().parent / "tray-debug.log"

def log(msg):
    line = str(msg)
    print(line, flush=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")

try:
    log("=== tray debug start ===")
    log(f"python: {sys.executable}")
    log(f"frozen: {getattr(sys, 'frozen', False)}")
    log(f"cwd: {Path.cwd()}")

    log("import pystray/PIL...")
    import pystray
    from PIL import Image, ImageDraw

    log("render icon...")
    img = Image.new("RGB", (64, 64), color=(30, 30, 30))
    d = ImageDraw.Draw(img)
    d.text((4, 20), "63", fill=(255, 255, 255))

    log("create Icon...")
    icon = pystray.Icon("cpu-temp-debug", img, "CPU Temp Debug: 63C")

    def on_quit(icon, item):
        log("quit clicked")
        icon.stop()

    icon.menu = pystray.Menu(
        pystray.MenuItem("Quit", on_quit),
    )

    log("calling icon.run() — icon should appear in system tray for 30s")
    log("NOTE: if run as Admin, check HIDDEN ICONS (^) in taskbar overflow")

    import threading
    import time
    def auto_stop():
        time.sleep(30)
        log("auto-stop after 30s")
        icon.stop()
    threading.Thread(target=auto_stop, daemon=True).start()

    icon.run()
    log("icon.run() returned — OK")
except Exception:
    log("ERROR:\n" + traceback.format_exc())
    sys.exit(1)
