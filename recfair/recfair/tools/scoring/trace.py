"""Structured trace for scoring workflow steps."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

TraceAction = Literal["removed", "bonus", "skipped", "ranked", "pool"]


@dataclass
class TraceEntry:
    """One observability event in the scoring pipeline."""

    step: str
    sku: str
    action: TraceAction
    reason: str
    points_delta: int = 0
    points_total: int = 0


@dataclass
class ScoreTrace:
    """Append-only log of scoring decisions."""

    entries: list[TraceEntry] = field(default_factory=list)

    def log(
        self,
        step: str,
        sku: str,
        action: TraceAction,
        reason: str,
        *,
        points_delta: int = 0,
        points_total: int = 0,
    ) -> None:
        """Append a trace entry."""
        self.entries.append(
            TraceEntry(
                step=step,
                sku=sku,
                action=action,
                reason=reason,
                points_delta=points_delta,
                points_total=points_total,
            )
        )

    def to_dicts(self) -> list[dict[str, Any]]:
        """Serialize for run manifests and CLI."""
        return [asdict(entry) for entry in self.entries]
