"""Standalone settings dialog — launched in a subprocess from the tray menu."""

from __future__ import annotations

from src.config.loader import load_config
from src.ui.settings import show_settings_dialog


def main() -> int:
    show_settings_dialog(load_config())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
