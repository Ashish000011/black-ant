"""Loads config.yaml from the project root."""

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent


def _numbers(value):
    """PyYAML reads 4.8675e24 (no sign after the e) as text; turn any number-like text into a float."""
    if isinstance(value, dict):
        return {k: _numbers(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_numbers(v) for v in value]
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            return value
    return value


def load_config(path: Path | str | None = None) -> dict:
    with open(path or ROOT / "config.yaml", encoding="utf-8") as f:
        return _numbers(yaml.safe_load(f))
