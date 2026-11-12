"""Where the assistant keeps its data."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

HOME_ENV = "PERSONAL_ASSISTANT_HOME"
DEFAULT_DIR_NAME = ".personal_assistant"


def resolve_data_dir(env: Mapping[str, str]) -> Path:
    """Data directory from $PERSONAL_ASSISTANT_HOME or ~/.personal_assistant; created if missing."""
    configured = env.get(HOME_ENV, "").strip()
    data_dir = Path(configured).expanduser() if configured else Path.home() / DEFAULT_DIR_NAME
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir
