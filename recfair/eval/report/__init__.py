"""Notebook report tables and HTML panels."""

from eval.report.e3_panels import (
    build_agent_cost_table,
    build_arch_instrumentation_table,
    build_context_case_table,
    build_context_summary_table,
    render_agent_cost_table,
    render_arch_instrumentation_panel,
    render_context_evaluation_section,
    render_metric_glossary,
)
from eval.report.html import render_comparison_report
from eval.report.legacy import (
    build_arch_comparison_table,
    build_results_table,
    render_arch_comparison,
    render_metrics_panel,
    summarize_records,
)
from eval.report.scopes import (
    e3_scope_of,
    render_rf_breakdown_table,
    summarize_by_context,
    summarize_records_v3,
)

__all__ = [
    "build_agent_cost_table",
    "build_arch_comparison_table",
    "build_arch_instrumentation_table",
    "build_context_case_table",
    "build_context_summary_table",
    "build_results_table",
    "e3_scope_of",
    "render_agent_cost_table",
    "render_arch_comparison",
    "render_arch_instrumentation_panel",
    "render_comparison_report",
    "render_context_evaluation_section",
    "render_metric_glossary",
    "render_metrics_panel",
    "render_rf_breakdown_table",
    "summarize_by_context",
    "summarize_records",
    "summarize_records_v3",
]
