"""Deterministic golden-set verification."""

from eval.verify.case import verify_case
from eval.verify.diagnosis import diagnose_failure, motivo_sucesso
from eval.verify.presentation import (
    escopo_label,
    final_status,
    format_baseline_col,
    format_gabarito_col,
    gold_diff_label,
    is_restrict_scope,
    recommendation_final_status,
)

__all__ = [
    "diagnose_failure",
    "escopo_label",
    "final_status",
    "format_baseline_col",
    "format_gabarito_col",
    "gold_diff_label",
    "is_restrict_scope",
    "motivo_sucesso",
    "recommendation_final_status",
    "verify_case",
]
