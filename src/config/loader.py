"""Load application configuration from config/config.json."""

from __future__ import annotations

import json
import logging
from pathlib import Path

from src.config.schema import AppConfig, config_from_dict

logger = logging.getLogger(__name__)

__all__ = ["load_config"]


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def default_config_path() -> Path:
    return _repo_root() / "config" / "config.json"


def load_config(path: Path | str | None = None) -> AppConfig:
    """Load config from JSON file; fall back to example defaults when missing or invalid."""
    config_path = Path(path) if path is not None else default_config_path()

    if not config_path.exists():
        logger.info("Config file %s not found — using defaults", config_path)
        return config_from_dict(None)

    try:
        raw = config_path.read_text(encoding="utf-8")
        data = json.loads(raw)
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("Failed to read config %s (%s) — using defaults", config_path, exc)
        return config_from_dict(None)

    if not isinstance(data, dict):
        logger.warning("Config %s is not a JSON object — using defaults", config_path)
        return config_from_dict(None)

    # Strip JSON Schema metadata keys if present (config.example.json includes $schema).
    data = {k: v for k, v in data.items() if not k.startswith("$") and k != "description"}

    try:
        return config_from_dict(data)
    except ValueError as exc:
        logger.warning("Invalid config in %s (%s) — using defaults", config_path, exc)
        return config_from_dict(None)
