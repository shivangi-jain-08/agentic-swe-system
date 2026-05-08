from __future__ import annotations

import os
from pathlib import Path

from .schema import SOPConfig


def load_sop(path: str | None = None) -> SOPConfig:
    """Load the SOP config from a path or `SOP_PATH` env var."""

    sop_path = path or os.getenv("SOP_PATH")
    if not sop_path:
        raise ValueError("SOP path not provided and SOP_PATH env var is not set")
    return SOPConfig.from_yaml(Path(sop_path))
