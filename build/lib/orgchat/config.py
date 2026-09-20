from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Any


class ConfigError(ValueError):
    """Raised when orgchat.toml cannot be loaded."""


def load_config(root: Path, config_path: Path | None = None) -> tuple[dict[str, Any], Path | None, bool]:
    path = config_path or (root / "orgchat.toml")
    if not path.is_absolute():
        path = (root / path).resolve()

    if not path.exists():
        return {}, None, False

    try:
        with path.open("rb") as handle:
            data = tomllib.load(handle)
    except tomllib.TOMLDecodeError as exc:
        raise ConfigError(f"Invalid TOML in {path}: {exc}") from exc
    except OSError as exc:
        raise ConfigError(f"Cannot read {path}: {exc}") from exc

    if not isinstance(data, dict):
        raise ConfigError(f"The configuration root must be a TOML table: {path}")
    return data, path, True


def section(config: dict[str, Any], name: str) -> dict[str, Any]:
    value = config.get(name, {})
    return value if isinstance(value, dict) else {}


def resolve_project_path(root: Path, value: Any) -> Path | None:
    if not isinstance(value, str) or not value.strip():
        return None
    text = value.strip()
    if text.startswith(("http://", "https://", "cmd:", "/health", "health://")):
        return None
    candidate = Path(text)
    if not candidate.is_absolute():
        candidate = root / candidate
    return candidate.resolve()
