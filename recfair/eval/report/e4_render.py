"""HTML panels and manifest loaders for the E4 notebook."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from eval.cases import is_frozen_ruler_case
from eval.contexts import CONTEXT_ARCHITECTURES, CONTEXT_LABELS, EVAL_CONTEXTS, EvalContext, filter_records_by_context
from eval.ethics import pair_verdicts
from eval.glossary import ARCHITECTURE_LABELS, CONTEXT_SECTIONS
from eval.report.e3_panels import build_context_summary_table, render_arch_instrumentation_panel
from eval.report.e4_panels import case_changes_table, consequence_matrix_table, prepare_consolidation_table
from eval.report.html import _PANEL, _PANEL_HDR, render_comparison_report
from eval.verify import final_status, format_baseline_col, is_restrict_scope, recommendation_final_status
from recfair.config import eval_runs_dir

E4_CANONICAL_RUN_IDS: dict[str, str] = {
    "baseline": "c6d86c0d894f",
    "workflow": "6d5cb78a9e25",
    "multiagent": "ae3f3348d3e4",
}

_MIN_PAIRS_FIXTURE = Path(__file__).resolve().parent.parent / "fixtures" / "e4_min_pairs_resilient.json"

_ARCH_EVOLUTION_ROWS = [
    {
        "entrega": "E1 — Baseline",
        "arch": "baseline",
        "adr": "0001",
        "desenho": "Stuffing CSV + 1× Gemini structured output",
        "peça nova": "Contrato Pydantic `RecFairOutput`",
        "limite medido": "Ranking no LLM; alto custo/token; sem tools nem guardrail dedicado",
    },
    {
        "entrega": "E2 — Workflow",
        "arch": "workflow",
        "adr": "0002",
        "desenho": "LangGraph ReAct + tools (engine 7 passos, claims, estoque)",
        "peça nova": "Ranking determinístico auditável",
        "limite medido": "Domínio único (sem FAQ/supervisor); claims por substring",
    },
    {
        "entrega": "E3 — Multi-agentes",
        "arch": "multiagent",
        "adr": "0003",
        "desenho": "Supervisor + especialistas + RAG FAQ + security determinístico",
        "peça nova": "T39–T60; métricas por contexto (H.1–H.4)",
        "limite medido": "Sem retry/degrade/verify pós-grafo; variância entre runs",
    },
    {
        "entrega": "E4 — Resiliente",
        "arch": "resilient",
        "adr": "0004",
        "desenho": "Grafo E3 + harness (retry, timeout, citations, verify v4)",
        "peça nova": "`recfair/harness/`; pares mínimos P01–P05; Wilson + dano ponderado",
        "limite medido": "Latência no pior caso; handoff degradado; HITL",
    },
]

_TRACEABILITY_ROWS = [
    {
        "check": "Manifest persiste após a sessão",
        "mecanismo": "`eval.runner.run_eval(persist=True)` → `save_run` → `eval/runs/<run_id>.json`",
        "evidência": "Campos `run_id`, `git_sha`, `golden_revision`, `architecture_id` no JSON",
    },
    {
        "check": "Componente identificado no trace",
        "mecanismo": "`AgentTrace.agent_id` em cada passo do grafo (security, supervisor, faq, …)",
        "evidência": "Lista `agent_traces` dentro de `metrics` em cada record do manifest",
    },
    {
        "check": "Roteamento explicado",
        "mecanismo": "`RoutingDecision.routing_reason` + `agents_route` agregada no output",
        "evidência": "Colunas de roteamento no painel H.4 e campo `agents_route` no manifest",
    },
    {
        "check": "Citações ao usuário (v4)",
        "mecanismo": "`harness.citations.fill_citations` após nós FAQ/recommendation",
        "evidência": "`RecFairOutput.citations` na CLI (`/trace`) e serializado no manifest",
    },
    {
        "check": "Degradação visível",
        "mecanismo": "`label_degraded` prefixa `[Resposta parcial]` e seta `degraded=True`",
        "evidência": "CLI mostra `halt_reason` + `degraded_reason`; eval marca peso harm=1",
    },
    {
        "check": "Falha silenciosa → handoff ruidoso",
        "mecanismo": "`apply_silent_failure_checks` após FAQ/recommendation no runner `resilient`",
        "evidência": "`halt_reason=degraded`; códigos `invented_sku:*` / `high_confidence_without_evidence`",
    },
    {
        "check": "Régua T01–T60 imutável",
        "mecanismo": "`eval.verify.verify_case` + hash `golden_revision` no manifest",
        "evidência": "Mesma função de verify desde E1; campos E4 são aditivos no output",
    },
    {
        "check": "Memória LangGraph",
        "mecanismo": "Checkpointer in-memory na sessão CLI",
        "evidência": "Não é fonte de accountability — decisão ADR 0004; auditoria via manifest",
    },
]


def _load_run_json(run_id: str) -> dict[str, Any]:
    path = eval_runs_dir() / f"{run_id}.json"
    if not path.is_file():
        raise FileNotFoundError(f"Manifest não encontrado: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def _latest_resilient_run_id() -> str | None:
    best: tuple[float, str] | None = None
    for path in eval_runs_dir().glob("*.json"):
        try:
            manifest = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        if manifest.get("architecture_id") != "resilient":
            continue
        frozen = sum(
            1
            for row in manifest.get("records") or []
            if is_frozen_ruler_case(row.get("case") or {})
        )
        if frozen < 60:
            continue
        mtime = path.stat().st_mtime
        if best is None or mtime > best[0]:
            best = (mtime, manifest.get("run_id") or path.stem)
    return best[1] if best else None


def load_e4_manifests(
    *,
    resilient_run_id: str | None = None,
    include_resilient: bool = True,
) -> dict[str, dict[str, Any]]:
    """Load canonical E1–E3 manifests plus optional resilient run (60× T01–T60)."""
    out: dict[str, dict[str, Any]] = {}
    for arch, run_id in E4_CANONICAL_RUN_IDS.items():
        out[arch] = _load_run_json(run_id)
    if not include_resilient:
        return out
    rid = resilient_run_id or _latest_resilient_run_id()
    if rid:
        out["resilient"] = _load_run_json(rid)
    return out


def load_min_pairs_snapshot() -> list[dict[str, Any]]:
    """Frozen min-pair run (no LLM in notebook)."""
    if not _MIN_PAIRS_FIXTURE.is_file():
        return []
    payload = json.loads(_MIN_PAIRS_FIXTURE.read_text(encoding="utf-8"))
    if isinstance(payload, list):
        return payload
    return list(payload.get("pairs") or [])


def save_min_pairs_snapshot(pair_runs: list[dict[str, Any]]) -> Path:
    """Persist min-pair results for offline notebook rendering."""
    _MIN_PAIRS_FIXTURE.parent.mkdir(parents=True, exist_ok=True)
    _MIN_PAIRS_FIXTURE.write_text(
        json.dumps(pair_runs, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return _MIN_PAIRS_FIXTURE


def _status_label(record: dict[str, Any], context: EvalContext) -> str:
    case = record["case"]
    check = record["check"]
    restrict = is_restrict_scope(case.get("familia") or "")
    if context == "recomendacao":
        return recommendation_final_status(check, restrict)
    return final_status(check["aprovado"], restrict)


def build_e4_context_case_table(
    manifests: dict[str, dict[str, Any]],
    context: EvalContext,
) -> pd.DataFrame:
    """Per-case table with one result column per architecture (E4 consolidation)."""
    arches = [arch for arch in CONTEXT_ARCHITECTURES[context] if arch in manifests]
    by_id: dict[str, dict[str, Any]] = {}
    for arch in arches:
        label = ARCHITECTURE_LABELS.get(arch, arch)
        records = filter_records_by_context(list(manifests[arch].get("records") or []), context)
        for record in records:
            case = record["case"]
            case_id = case["id"]
            row = by_id.setdefault(
                case_id,
                {
                    "caso": case_id,
                    "pergunta": (case.get("entrada") or " / ".join(case.get("turns") or []))[:120],
                },
            )
            row[label] = _status_label(record, context)
            if context == "recomendacao" and "qualidade do ranking" not in row:
                row["qualidade do ranking"] = record["check"].get("ndcg_at_5")
                row["gravidade"] = record["check"].get("severity")
    if not by_id:
        return pd.DataFrame([{"caso": "—", "pergunta": "sem dados"}])
    frame = pd.DataFrame(list(by_id.values())).sort_values("caso")
    arch_labels = [ARCHITECTURE_LABELS.get(a, a) for a in arches]
    cols = ["caso", "pergunta"] + arch_labels
    if context == "recomendacao":
        cols.extend(["qualidade do ranking", "gravidade"])
    return frame[[c for c in cols if c in frame.columns]]


def render_all_e4_context_sections(manifests: dict[str, dict[str, Any]]) -> str:
    """H.1–H.4 style sections comparing all architectures present in ``manifests``."""
    parts: list[str] = []
    for context in EVAL_CONTEXTS:
        section = CONTEXT_SECTIONS[context]
        summary_df = build_context_summary_table(manifests, context)
        cases_df = build_e4_context_case_table(manifests, context)
        intro = (
            f'<p style="margin:16px 0 10px;font-size:14px;line-height:1.55;color:#1f2937;">'
            f"<strong>{section['titulo']}</strong><br>"
            f"<strong>Pergunta:</strong> {section['pergunta']}<br>"
            f"<strong>Métrica principal:</strong> {section['metrica_principal']}<br>"
            f"<strong>Escopo:</strong> {CONTEXT_LABELS[context]} · {section['casos']}"
            f"</p>"
        )
        parts.append(intro)
        parts.append(
            render_comparison_report(
                summary_df,
                status_col="versão",
                title=f"Agregado — {CONTEXT_LABELS[context]}",
                subtitle="Uma linha por entrega · mesma régua T01–T60",
                show_legend=False,
            )
        )
        if context == "recomendacao" and len(manifests) > 1:
            parts.append(
                render_arch_instrumentation_panel(
                    manifests,
                    context,
                    title="Instrumentação (custo e latência por arquitetura)",
                )
            )
        parts.append(
            render_comparison_report(
                cases_df,
                status_col="caso",
                title=f"Detalhe por caso — {CONTEXT_LABELS[context]}",
                subtitle="Colunas por entrega · verde/vermelho segue legenda sucesso/erro",
                code_columns=frozenset({"pergunta", "caso"}),
                show_legend=True,
            )
        )
    return "".join(parts)


def render_architecture_evolution_table() -> str:
    """ADR-aligned architecture map E1–E4."""
    df = pd.DataFrame(_ARCH_EVOLUTION_ROWS)
    return render_comparison_report(
        df,
        status_col="entrega",
        title="Evolução E1 → E4 (mapa de arquitetura)",
        subtitle="Resumo dos ADRs 0001–0004 · mesmo modelo nas comparações reportadas",
        code_columns=frozenset({"arch", "adr"}),
        show_legend=False,
    )


def render_case_changes_panel(manifests: dict[str, dict[str, Any]]) -> str:
    """Per-case pass/fail across architectures with status badges."""
    df = case_changes_table(manifests).copy()
    for col in df.columns:
        if col == "caso":
            continue
        if df[col].dtype == bool:
            df[col] = df[col].map({True: "sucesso", False: "erro"})
    return render_comparison_report(
        df,
        status_col="caso",
        title="Flips por caso (T01–T60)",
        subtitle="Verde = aprovado na régua herdada · vermelho = reprovado",
        show_legend=True,
    )


def render_consolidation_panel(df: pd.DataFrame) -> str:
    """Full consolidation + Wilson columns (operational metrics omitted)."""
    slim = prepare_consolidation_table(df)
    return render_comparison_report(
        slim,
        status_col="versao",
        title="Consolidação T01–T60 (taxa simples + Wilson 95%)",
        subtitle="Colunas operacionais (LLM, tools, latência, custo) omitidas — ver instrumentação H.1",
        show_legend=False,
    )


def render_containment_panel(stats: dict[str, Any]) -> str:
    """Demo AP7 containment metrics."""
    rows = [
        ("Probabilidade de falha injetada", stats.get("failure_prob")),
        ("Chamadas simuladas", stats.get("n_calls")),
        ("Sucesso após retry", stats.get("ok")),
        ("Degradadas (handoff)", stats.get("degraded")),
        ("Recuperadas por retry", stats.get("recovered")),
        ("halt_reason na degradação", stats.get("halt_on_degrade")),
        ("Usuário vê [Resposta parcial]", "sim" if stats.get("degraded_identifies_as_partial") else "não"),
    ]
    df = pd.DataFrame(rows, columns=["métrica", "valor"])
    return render_comparison_report(
        df,
        status_col="métrica",
        title="Demo de contenção (sem LLM)",
        subtitle="`recfair.harness.demo_containment` · `call_with_retry` + `tool_error_output`",
        show_legend=False,
    )


def render_silent_checks_panel(result: dict[str, Any]) -> str:
    """Anti silent-failure verifier demo."""
    df = pd.DataFrame(
        [
            ("Evidência na fonte", ", ".join(result.get("evidence_issues") or []) or "—"),
            ("Confiança × evidência", ", ".join(result.get("confidence_issues") or []) or "—"),
            ("status após conversão", result.get("converted_status")),
            ("degraded", result.get("converted_degraded")),
            ("halt_reason", result.get("converted_halt")),
            ("prefixo visível ao usuário", "sim" if result.get("user_sees_partial") else "não"),
        ],
        columns=["verificador", "códigos"],
    )
    return render_comparison_report(
        df,
        status_col="verificador",
        title="Verificadores anti-falha silenciosa",
        subtitle="`verify_evidence` + `verify_confidence` → `apply_silent_failure_checks`",
        code_columns=frozenset({"códigos"}),
        show_legend=False,
    )


def render_reliability_chart(resumo: dict[str, Any]) -> str:
    """Bar chart of pass rates per repeated run + unstable case list."""
    por_rodada = resumo.get("por_rodada") or []
    arch = resumo.get("architecture_id") or "?"
    n = resumo.get("n_rodadas") or len(por_rodada)
    taxa_min = resumo.get("taxa_min")
    taxa_max = resumo.get("taxa_max")
    band = ""
    if taxa_min is not None and taxa_max is not None:
        band = f"Faixa min–max: {taxa_min:.1%} – {taxa_max:.1%}"
    bars: list[str] = []
    max_h = 120
    for row in por_rodada:
        taxa = float(row.get("taxa") or 0)
        h = max(4, taxa * max_h)
        run_id = row.get("run_id") or "?"
        bars.append(
            f'<div style="text-align:center;flex:1;">'
            f'<div style="height:{max_h}px;display:flex;align-items:flex-end;justify-content:center;">'
            f'<div style="width:48px;height:{h:.1f}px;background:#059669;border-radius:6px 6px 0 0;" '
            f'title="{taxa:.1%}"></div></div>'
            f'<div style="font-size:11px;margin-top:6px;">Rodada {row.get("rodada")}</div>'
            f'<div style="font-size:12px;font-weight:600;">{taxa:.1%}</div>'
            f'<div style="font-size:10px;color:#6b7280;">{run_id}</div></div>'
        )
    instaveis = resumo.get("instaveis") or []
    flip_note = ""
    if instaveis:
        flip_note = (
            f"<p style='font-size:12px;color:#b45309;margin-top:10px;'>"
            f"Casos instáveis (flip entre rodadas): {', '.join(instaveis)}.</p>"
        )
    return (
        f'<div style="border:1px solid #d1d5db;border-radius:12px;padding:14px 16px;background:#fff;">'
        f'<div style="font-weight:700;">Confiabilidade — {arch} ({n} rodadas)</div>'
        f'<div style="font-size:12px;color:#6b7280;margin:6px 0 12px;">{band}</div>'
        f'<div style="display:flex;gap:12px;align-items:flex-end;">{"".join(bars)}</div>'
        f"{flip_note}</div>"
    )


def render_wilson_interval_chart(df: pd.DataFrame) -> str:
    """Horizontal Wilson intervals per architecture."""
    if df.empty:
        return "<p>Sem dados para Wilson.</p>"
    rows_html: list[str] = []
    for _, row in df.iterrows():
        lo = float(row.get("lower_limit") or 0)
        hi = float(row.get("upper_limit") or 0)
        mid = float(row.get("taxa") or (lo + hi) / 2)
        label = row.get("versao") or row.get("arch")
        rows_html.append(
            f'<div style="margin:10px 0;">'
            f'<div style="font-size:12px;font-weight:600;margin-bottom:4px;">{label} '
            f'<span style="color:#6b7280;font-weight:400;">({mid:.1%} · [{lo:.1%}, {hi:.1%}])</span></div>'
            f'<div style="position:relative;height:14px;background:#f3f4f6;border-radius:8px;">'
            f'<div style="position:absolute;left:{lo*100:.1f}%;width:{(hi-lo)*100:.1f}%;'
            f'height:14px;background:#3b82f6;border-radius:8px;opacity:0.85;"></div>'
            f'<div style="position:absolute;left:{mid*100:.1f}%;width:4px;height:14px;'
            f'background:#1e3a8a;margin-left:-2px;border-radius:2px;"></div>'
            f"</div></div>"
        )
    body = "".join(rows_html)
    return (
        f'<div style="{_PANEL}">'
        f'<div style="{_PANEL_HDR}">'
        f'<div style="font-size:1.08rem;font-weight:700;color:#ffffff;">Intervalos de Wilson (95%)</div>'
        f'<div style="font-size:12px;color:#e2e8f0;margin-top:5px;">Barra azul = faixa plausível · traço = taxa observada</div>'
        f"</div>"
        f'<div style="padding:14px 18px;background:#fff;">{body}</div></div>'
    )


def render_overlap_panel(overlap_df: pd.DataFrame) -> str:
    """Pairwise Wilson overlap table."""
    if overlap_df.empty:
        return "<p>Sem pares para comparar.</p>"
    display = overlap_df.copy()
    display["sobrepoe"] = display["sobrepoe"].map({True: "sim", False: "não"})
    return render_comparison_report(
        display,
        status_col="par",
        title="Sobreposição de intervalos (pares de arquiteturas)",
        subtitle="`sim` → empate técnico possível na taxa agregada T01–T60",
        show_legend=False,
    )


def render_consequence_matrix_panel() -> str:
    """Static ethics consequence matrix."""
    df = consequence_matrix_table()
    return render_comparison_report(
        df,
        status_col="modo",
        title="Matriz de consequências (modo × gravidade)",
        subtitle="Pesos alinhados a `eval.ethics.GRAVIDADE` · não altera `verify_case`",
        show_legend=False,
    )


def render_weighted_ranking_panel(df: pd.DataFrame) -> str:
    """Simple vs harm-weighted ranking."""
    if df.empty:
        return "<p>Sem manifests para ranking ético.</p>"
    display = df.copy()
    for col in ("taxa_simples", "score_ponderado", "mean_harm"):
        if col in display.columns:
            display[col] = display[col].map(lambda v: f"{float(v):.4f}" if v is not None else "—")
    return render_comparison_report(
        display,
        status_col="versao",
        title="Taxa simples × score ponderado por dano",
        subtitle="Compare `rank_simples` vs `rank_ponderado` — divergência indica erros graves desbalanceados",
        show_legend=False,
    )


def _fmt_dim(value: Any) -> str:
    if value is None:
        return "—"
    if isinstance(value, float):
        return f"{value:.3f}"
    return str(value)


def render_min_pairs_panel(
    pair_runs: list[dict[str, Any]],
    *,
    pairs_meta: list[dict[str, Any]] | None = None,
) -> str:
    """Side-by-side min-pair comparison (P01–P05)."""
    parts: list[str] = []
    meta_by_id = {p["pair_id"]: p for p in (pairs_meta or [])}
    if not pair_runs and pairs_meta:
        catalog_rows = []
        for pair in pairs_meta:
            variants = " · ".join(
                f"{v.get('label')}: «{(v.get('entrada') or '')[:50]}…»"
                for v in (pair.get("variants") or [])[:2]
            )
            catalog_rows.append(
                {
                    "par": pair["pair_id"],
                    "eixo": pair.get("axis"),
                    "camada": pair.get("layer"),
                    "exemplo": variants,
                    "nota": (pair.get("note") or "")[:100],
                }
            )
        parts.append(
            render_comparison_report(
                pd.DataFrame(catalog_rows),
                status_col="par",
                title="Catálogo de pares mínimos (exemplos de entrada)",
                subtitle="Execute `RUN_E4` com `persist=True` e grave snapshot em "
                "`eval/fixtures/e4_min_pairs_resilient.json` para métricas lado a lado",
                code_columns=frozenset({"exemplo"}),
                show_legend=False,
            )
        )
        return "".join(parts)

    for pair in pair_runs:
        pair_id = pair.get("pair_id")
        meta = meta_by_id.get(pair_id) or {}
        subtitle = meta.get("note") or pair.get("note") or ""
        rows: list[dict[str, Any]] = []
        for variant in pair.get("variants") or []:
            media = variant.get("media") or {}
            rows.append(
                {
                    "variante": variant.get("label"),
                    "reformulação": variant.get("reformulation"),
                    "entrada": (variant.get("entrada") or "")[:90],
                    "acerto": _fmt_dim(media.get("acerto")),
                    "confiança": _fmt_dim(media.get("confianca")),
                    "evidência": _fmt_dim(media.get("evidencia")),
                    "ressalvas": _fmt_dim(media.get("ressalvas")),
                    "nDCG@5": _fmt_dim(media.get("ndcg_at_5")),
                }
            )
        parts.append(
            render_comparison_report(
                pd.DataFrame(rows),
                status_col="variante",
                title=f"Par {pair_id} — eixo {pair.get('axis')} ({pair.get('layer')})",
                subtitle=subtitle,
                code_columns=frozenset({"entrada"}),
                show_legend=False,
            )
        )
        for verdict in pair_verdicts(pair):
            if not verdict.get("relevante"):
                continue
            parts.append(
                f'<p style="font-size:12px;color:#b45309;margin:4px 0 12px 18px;">'
                f"⚠ Diferença relevante (reformulação {verdict.get('reformulation')}): "
                f"{verdict.get('left')} vs {verdict.get('right')} · deltas {verdict.get('deltas')}"
                f"</p>"
            )
    title = "Pares mínimos P01–P05 (resilient)"
    if not parts:
        return render_comparison_report(
            pd.DataFrame([{"par": "—", "status": "sem snapshot"}]),
            status_col="par",
            title=title,
            subtitle="Nenhum dado em `eval/fixtures/e4_min_pairs_resilient.json`",
            show_legend=False,
        )
    header = (
        f'<div style="font-size:13px;color:#374151;margin:8px 0 14px;">'
        f"{title} — comparação lado a lado · diferença só conta acima da faixa de ruído (§D)"
        f"</div>"
    )
    return header + "".join(parts)


def render_traceability_panel() -> str:
    """§I checklist mapped to package modules."""
    df = pd.DataFrame(_TRACEABILITY_ROWS)
    return render_comparison_report(
        df,
        status_col="check",
        title="Rastreabilidade — onde cada garantia é aplicada",
        subtitle="Checklist §I mapeado para módulos do pacote (sem lógica no notebook)",
        code_columns=frozenset({"mecanismo", "evidência"}),
        show_legend=False,
    )
