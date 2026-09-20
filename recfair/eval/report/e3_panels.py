"""E3 evaluation panels, instrumentation and context sections."""

from __future__ import annotations

from typing import Any

import pandas as pd

from eval.contexts import (
    CONTEXT_ARCHITECTURES,
    CONTEXT_LABELS,
    EvalContext,
    filter_records_by_context,
    routing_destination,
)
from eval.glossary import ARCHITECTURE_LABELS, CONTEXT_SECTIONS, METRIC_GLOSSARY
from eval.metrics import FAQ_SEMANTIC_THRESHOLD
from eval.report.html import render_comparison_report
from eval.verify import (
    final_status,
    format_baseline_col,
    format_gabarito_col,
    is_restrict_scope,
    recommendation_final_status,
)


def build_agent_cost_table(records: list[dict[str, Any]]) -> pd.DataFrame:
    """Per-agent averages over cases where the node was actually invoked."""
    from recfair.observability.tokens import estimate_llm_cost_usd

    rows: dict[str, dict[str, float]] = {}
    for record in records:
        for step in record.get("metrics", {}).get("agent_traces") or []:
            agent_id = step.get("agent_id") or "?"
            bucket = rows.setdefault(
                agent_id,
                {
                    "latencia_s": 0.0,
                    "chamadas_llm": 0.0,
                    "tool_calls": 0.0,
                    "tokens_entrada": 0.0,
                    "tokens_saida": 0.0,
                    "custo_usd": 0.0,
                    "n": 0.0,
                },
            )
            bucket["latencia_s"] += float(step.get("latencia_s") or 0)
            bucket["chamadas_llm"] += float(step.get("chamadas_llm") or 0)
            bucket["tool_calls"] += float(step.get("tool_calls") or 0)
            bucket["tokens_entrada"] += float(step.get("tokens_entrada") or 0)
            bucket["tokens_saida"] += float(step.get("tokens_saida") or 0)
            if step.get("custo_usd") is not None:
                bucket["custo_usd"] += float(step["custo_usd"])
            else:
                bucket["custo_usd"] += estimate_llm_cost_usd(
                    step.get("tokens_entrada") or 0,
                    step.get("tokens_saida") or 0,
                )
            bucket["n"] += 1
    data = []
    for agent_id, bucket in sorted(rows.items()):
        n = bucket["n"]
        if n <= 0:
            continue
        data.append(
            {
                "agente": agent_id,
                "casos": int(n),
                "latencia_s": round(bucket["latencia_s"] / n, 2),
                "chamadas_llm": round(bucket["chamadas_llm"] / n, 2),
                "tool_calls": round(bucket["tool_calls"] / n, 2),
                "tokens_entrada": round(bucket["tokens_entrada"] / n),
                "tokens_saida": round(bucket["tokens_saida"] / n),
                "custo_usd": round(bucket["custo_usd"] / n, 6),
            }
        )
    return pd.DataFrame(data)


def render_agent_cost_table(
    records: list[dict[str, Any]],
    *,
    title: str = "Custo e latência por agente",
) -> str:
    """HTML table of per-agent instrumentation."""
    df = build_agent_cost_table(records)
    if df.empty:
        df = pd.DataFrame([{"agente": "—", "casos": 0, "latencia_s": 0, "chamadas_llm": 0}])
    return render_comparison_report(
        df,
        status_col="agente",
        title=title,
        subtitle="Média por run · somente casos em que o nó foi chamado · security e handoff são determinísticos (0 LLM).",
        code_columns=frozenset({"agente"}),
    )


def _fmt_rate(value: float | None) -> str:
    if value is None:
        return "—"
    return f"{value:.1%}"


def _fmt_score(value: float | None) -> str:
    if value is None:
        return "—"
    return f"{value:.4f}"


def _mean_case_instrumentation(records: list[dict[str, Any]]) -> dict[str, float | int | None]:
    """Per-case averages for latency, tokens, calls and cost."""
    from recfair.observability.tokens import estimate_llm_cost_usd

    if not records:
        return {
            "latencia_media_s": None,
            "tokens_entrada": None,
            "tokens_saida": None,
            "tokens_total": None,
            "chamadas_llm": None,
            "tool_calls": None,
            "custo_usd": None,
        }

    latencies: list[float] = []
    tokens_in: list[float] = []
    tokens_out: list[float] = []
    llm_calls: list[float] = []
    tool_calls: list[float] = []
    costs: list[float] = []
    for record in records:
        metrics = record.get("metrics") or {}
        latencies.append(float(metrics.get("latencia_s") or 0))
        tok_in = float(metrics.get("tokens_entrada") or 0)
        tok_out = float(metrics.get("tokens_saida") or 0)
        tokens_in.append(tok_in)
        tokens_out.append(tok_out)
        llm_calls.append(float(metrics.get("chamadas_llm") or 0))
        tool_calls.append(float(metrics.get("tool_calls") or 0))
        costs.append(estimate_llm_cost_usd(tok_in, tok_out))

    n = len(records)
    mean_in = sum(tokens_in) / n
    mean_out = sum(tokens_out) / n
    return {
        "latencia_media_s": round(sum(latencies) / n, 2),
        "tokens_entrada": round(mean_in),
        "tokens_saida": round(mean_out),
        "tokens_total": round(mean_in + mean_out),
        "chamadas_llm": round(sum(llm_calls) / n, 2),
        "tool_calls": round(sum(tool_calls) / n, 2),
        "custo_usd": round(sum(costs) / n, 6),
    }


def build_arch_instrumentation_table(
    manifests: dict[str, dict[str, Any]],
    context: EvalContext = "recomendacao",
) -> pd.DataFrame:
    """Compare per-case instrumentation averages across architectures."""
    rows: list[dict[str, str]] = []
    for arch in ("baseline", "workflow", "multiagent"):
        manifest = manifests.get(arch)
        if not manifest:
            continue
        records = filter_records_by_context(manifest.get("records") or [], context)
        if not records:
            continue
        stats = _mean_case_instrumentation(records)
        rows.append(
            {
                "versão": ARCHITECTURE_LABELS.get(arch, arch),
                "casos": str(len(records)),
                "latência média (s)": str(stats.get("latencia_media_s") or "—"),
                "tokens entrada": f"{int(stats['tokens_entrada']):,}"
                if stats.get("tokens_entrada") is not None
                else "—",
                "tokens saída": f"{int(stats['tokens_saida']):,}"
                if stats.get("tokens_saida") is not None
                else "—",
                "tokens total": f"{int(stats['tokens_total']):,}"
                if stats.get("tokens_total") is not None
                else "—",
                "chamadas ao modelo": str(stats.get("chamadas_llm") or "—"),
                "chamadas de ferramentas": str(stats.get("tool_calls") or "—"),
                "custo estimado (USD)": f"${float(stats.get('custo_usd') or 0):.4f}",
            }
        )
    if not rows:
        rows.append({"versão": "—", "casos": "0"})
    return pd.DataFrame(rows)


def render_arch_instrumentation_panel(
    manifests: dict[str, dict[str, Any]],
    context: EvalContext = "recomendacao",
    *,
    title: str = "Instrumentação — E1 × E2 × E3",
) -> str:
    """HTML panel comparing operational metadata across architectures."""
    section = CONTEXT_SECTIONS.get(context, {})
    subtitle = (
        f"{section.get('comparacao', '')} · média por caso em "
        f"{CONTEXT_LABELS.get(context, context).lower()}"
    )
    df = build_arch_instrumentation_table(manifests, context)
    return render_comparison_report(
        df,
        status_col="versão",
        title=title,
        subtitle=subtitle,
        code_columns=frozenset(),
        show_legend=False,
    )


def build_context_summary_table(
    manifests: dict[str, dict[str, Any]],
    context: EvalContext,
) -> pd.DataFrame:
    """Human-readable summary table for one evaluation context."""
    rows: list[dict[str, str]] = []
    arches = [arch for arch in CONTEXT_ARCHITECTURES[context] if arch in manifests]

    for arch in arches:
        block = (manifests[arch].get("resumo_v3") or {}).get("e3_by_context", {}).get(
            context, {}
        )
        row: dict[str, str] = {
            "versão": ARCHITECTURE_LABELS.get(arch, arch),
            "casos avaliados": str(block.get("n") or "—"),
        }
        if context == "recomendacao":
            row["qualidade do ranking"] = _fmt_score(block.get("mean_ndcg_at_5"))
            row["taxa de lista exata"] = _fmt_rate(block.get("aprovado_exact_rate"))
            row["taxa de erro grave"] = _fmt_rate(block.get("grave_error_rate"))
        elif context == "seguranca":
            row["taxa de aprovação"] = _fmt_rate(block.get("pass_rate"))
            row["taxa de vazamento"] = _fmt_rate(block.get("guardrail_hit_rate"))
        elif context == "faq":
            row["similaridade semântica média"] = _fmt_score(
                block.get("mean_semantic_similarity")
            )
            row["limiar de aprovação"] = str(block.get("semantic_threshold") or FAQ_SEMANTIC_THRESHOLD)
            row["taxa de aprovação"] = _fmt_rate(block.get("pass_rate"))
        else:
            row["taxa de roteamento correto"] = _fmt_rate(block.get("routing_pass_rate"))
            by_dest = block.get("by_destination") or {}
            for dest, label in (
                ("recomendação", "acerto em recomendação"),
                ("perguntas frequentes", "acerto em FAQ"),
                ("transbordo", "acerto em transbordo"),
                ("fora de contexto", "acerto em fora de contexto"),
            ):
                dest_block = by_dest.get(dest) or {}
                row[label] = _fmt_rate(dest_block.get("pass_rate"))
        rows.append(row)

    if not rows:
        rows.append({"versão": "—", "casos avaliados": "0"})
    return pd.DataFrame(rows)


def build_context_case_table(
    records: list[dict[str, Any]],
    context: EvalContext,
    *,
    output_column: str = "resposta do sistema",
) -> pd.DataFrame:
    """Per-case detail table with context-specific columns in Portuguese."""
    subset = filter_records_by_context(records, context)
    rows: list[dict[str, Any]] = []
    for record in subset:
        case = record["case"]
        check = record["check"]
        restrict = is_restrict_scope(case["familia"])
        if context == "recomendacao":
            status = recommendation_final_status(check, restrict)
        else:
            status = final_status(check["aprovado"], restrict)
        row: dict[str, Any] = {
            "caso": case["id"],
            "status_final": status,
            "pergunta": case.get("entrada") or " / ".join(case.get("turns") or []),
            output_column: format_baseline_col(check),
        }
        if context == "recomendacao":
            row["qualidade do ranking"] = check.get("ndcg_at_5")
            row["gravidade do erro"] = check.get("severity")
            row["gabarito"] = format_gabarito_col(case, check)
        elif context == "seguranca":
            row["vazamento detectado"] = bool(
                check.get("pii_hits") or check.get("injection_hits") or check.get("jailbreak_hits")
            )
            row["gabarito"] = format_gabarito_col(case, check)
        elif context == "faq":
            row["similaridade semântica"] = check.get("faq_semantic_similarity")
            row["texto gerado"] = (check.get("answer_text") or "")[:160]
            row["referência"] = (case.get("expected_answer") or "")[:160]
        else:
            row["destino esperado"] = routing_destination(case)
            row["rota executada"] = " > ".join(check.get("agents_route") or [])
            row["status final"] = check.get("status")
        rows.append(row)
    return pd.DataFrame(rows)


def render_context_evaluation_section(
    manifests: dict[str, dict[str, Any]],
    records: list[dict[str, Any]],
    context: EvalContext,
    *,
    output_column: str = "resposta do sistema",
) -> str:
    """Full HTML section: intro, summary table and per-case table for one context."""
    section = CONTEXT_SECTIONS[context]
    summary_df = build_context_summary_table(manifests, context)
    cases_df = build_context_case_table(records, context, output_column=output_column)

    intro = (
        f'<p style="margin:0 0 10px;font-size:14px;line-height:1.55;color:#1f2937;">'
        f'<strong>Pergunta avaliada:</strong> {section["pergunta"]}<br>'
        f'<strong>Comparação:</strong> {section["comparacao"]}<br>'
        f'<strong>Métrica principal:</strong> {section["metrica_principal"]}<br>'
        f'<strong>Casos:</strong> {section["casos"]}'
        f"</p>"
    )
    summary_html = render_comparison_report(
        summary_df,
        status_col="versão",
        title=section["titulo"],
        subtitle=section["comparacao"],
        code_columns=frozenset(),
        show_legend=False,
    )
    instrumentation_html = ""
    if context == "recomendacao" and len(manifests) > 1:
        instrumentation_html = render_arch_instrumentation_panel(
            manifests,
            context,
            title="H.1 — Instrumentação (custo, latência e chamadas)",
        )
    cases_html = render_comparison_report(
        cases_df,
        status_col="status_final",
        title=f"Detalhe por caso — {CONTEXT_LABELS[context]}",
        subtitle=f"{len(cases_df)} casos · resultado individual",
        code_columns=frozenset({"pergunta", "texto gerado", "referência", "rota executada", "gabarito"}),
        show_legend=True,
    )
    return intro + summary_html + instrumentation_html + cases_html


def render_arch_comparison_v3(
    manifests: list[dict[str, Any]],
    *,
    title: str = "Comparação E3 — baseline × workflow × multiagent (recomendação)",
) -> str:
    """Three-column comparison using ``resumo_v3`` scopes."""
    labels = [m.get("architecture_id", f"arch{i}") for i, m in enumerate(manifests)]
    metric_rows = [
        ("e3_overall.mean_ndcg_at_5", "overall mean nDCG@5"),
        ("e3_overall.aprovado_exact_rate", "overall aprovado_exact"),
        ("e3_overall.grave_error_rate", "overall grave_error_rate"),
        ("e3_restrict_core.mean_ndcg_at_5", "restrict_core nDCG@5"),
        ("e3_gap.gap_intentional_pass_rate", "gap_intentional_pass"),
        ("e3_memory.aprovado_exact_rate", "memory aprovado_exact"),
        ("e3_scoring.aprovado_exact_rate", "scoring aprovado_exact"),
        ("e1_rate_overall", "legado e1_rate_overall"),
        ("latencia_mediana_s", "latência mediana (s)"),
        ("chamadas_llm", "chamadas LLM"),
        ("custo_estimado_usd", "custo est. (USD)"),
    ]

    def _dig(resumo: dict[str, Any], dotted: str) -> Any:
        current: Any = resumo
        for part in dotted.split("."):
            if not isinstance(current, dict):
                return None
            current = current.get(part)
        return current

    rows = []
    for dotted, label in metric_rows:
        row: dict[str, Any] = {"métrica": label}
        for label_arch, manifest in zip(labels, manifests, strict=True):
            resumo = manifest.get("resumo_v3") or manifest.get("resumo") or {}
            row[label_arch] = _dig(resumo, dotted)
        rows.append(row)
    df = pd.DataFrame(rows)
    revision = manifests[0].get("golden_revision", "—") if manifests else "—"
    return render_comparison_report(
        df,
        status_col="métrica",
        title=title,
        subtitle=f"golden_revision={revision} · mesmo modelo · mesma sessão",
        code_columns=frozenset(),
    )


def render_metric_glossary() -> str:
    """HTML glossary table for notebook insertion."""
    df = pd.DataFrame(METRIC_GLOSSARY)
    return render_comparison_report(
        df,
        status_col="contexto",
        title="Glossário das métricas de avaliação",
        subtitle="Consulta rápida — cada contexto tem uma métrica principal e métricas de apoio.",
        code_columns=frozenset(),
        show_legend=False,
    )
