"""Golden-set fingerprint (hash)."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from recfair.config import golden_cases_path


def load_cases(path: Path | None = None) -> list[dict[str, Any]]:
    """Load frozen golden-set cases."""
    target = path or golden_cases_path()
    return json.loads(target.read_text(encoding="utf-8"))


def golden_revision(cases: list[dict[str, Any]] | None = None) -> str:
    """SHA-256 short hash of the canonical JSON blob."""
    items = cases if cases is not None else load_cases()
    blob = json.dumps(items, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()[:16]
