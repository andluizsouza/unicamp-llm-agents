"""Persist eval run manifests to eval/runs/."""

from __future__ import annotations

import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from recfair.config import eval_runs_dir


def git_sha() -> str | None:
    """Best-effort current git commit."""
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            stderr=subprocess.DEVNULL,
            text=True,
        )
        return out.strip()[:12]
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def new_run_id() -> str:
    """Short unique run id."""
    return uuid4().hex[:12]


def save_run(path: Path | None, payload: dict[str, Any]) -> Path:
    """Write run JSON under eval/runs/."""
    target_dir = eval_runs_dir()
    target_dir.mkdir(parents=True, exist_ok=True)
    out = path or target_dir / f"{payload.get('run_id', new_run_id())}.json"
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    return out


def run_started_at() -> str:
    """ISO timestamp for run manifest."""
    return datetime.now(UTC).astimezone().isoformat(timespec="seconds")
