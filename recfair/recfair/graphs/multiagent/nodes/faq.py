"""FAQ specialist — retrieve then ground-only synthesize."""

from __future__ import annotations

import logging
import time
from typing import Any, Literal

from pydantic import BaseModel

from recfair.graphs.multiagent.llm import make_structured_llm, unpack_structured
from recfair.graphs.multiagent.skills import load_skill
from recfair.graphs.multiagent.state import MultiAgentState
from recfair.observability.agent_trace import AgentTrace, append_trace
from recfair.prompts.multiagent_v3 import build_faq_prompt
from recfair.rag.faq_index import FAQ_K, retrieve_faq
from recfair.schemas.output import RecFairOutput
from recfair.schemas.routing import AgentMetrics, AgentResult, RoutingDecision

_LOG = logging.getLogger(__name__)
_STRUCTURED: Any = None


class FaqSynthesis(BaseModel):
    """Grounded FAQ answer; ``no_evidence`` triggers a single replan."""

    status: Literal["ok", "no_evidence"]
    answer_text: str = ""


def _structured() -> Any:
    global _STRUCTURED
    if _STRUCTURED is None:
        _STRUCTURED = make_structured_llm(FaqSynthesis)
    return _STRUCTURED


def _route(state: MultiAgentState, extra: str) -> list[str]:
    prior = [row["agent_id"] for row in (state.get("agent_traces") or [])]
    return prior + [extra]


def _replan(routing: RoutingDecision | None, suffix: str) -> RoutingDecision:
    base = routing or RoutingDecision(
        domain="faq",
        skill="skill_faq",
        plan=["skill_faq"],
        routing_reason="faq",
    )
    return base.model_copy(
        update={
            "replanned": True,
            "plan": ["skill_faq", "handoff"],
            "routing_reason": f"{base.routing_reason} → {suffix}",
        }
    )


def _fail(
    state: MultiAgentState,
    *,
    status: Literal["no_evidence", "error"],
    latency: float,
    hits: list[dict[str, Any]],
    suffix: str,
    tokens_in: int = 0,
    tokens_out: int = 0,
    used_llm: bool = False,
    extra_payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    skill = load_skill("skill_faq")
    new_routing = _replan(state.get("routing"), suffix)
    trace = AgentTrace(
        agent_id="faq",
        routing_reason=new_routing.routing_reason,
        plan=list(new_routing.plan),
        replanned=True,
        chamadas_llm=1 if used_llm else 0,
        tool_calls=1,
        latencia_s=latency,
        tokens_entrada=tokens_in,
        tokens_saida=tokens_out,
    )
    last_result = AgentResult(
        agent_id="faq",
        status=status,
        payload={
            "skill": skill["index"],
            "instruction": skill["instruction"],
            **(extra_payload or {}),
        },
        evidence=hits,
        metrics=AgentMetrics(
            latencia_s=latency,
            chamadas_llm=1 if used_llm else 0,
            tool_calls=1,
            tokens_entrada=tokens_in,
            tokens_saida=tokens_out,
        ),
    )
    update: dict[str, Any] = {
        "routing": new_routing,
        "faq_status": status,
        "faq_evidence": hits,
        "last_result": last_result,
        "agent_traces": append_trace(state, trace),
        "tool_calls": state.get("tool_calls", 0) + 1,
        "step": state.get("step", 0) + 1,
    }
    if used_llm:
        update["chamadas_llm"] = state.get("chamadas_llm", 0) + 1
        update["tokens_entrada"] = state.get("tokens_entrada", 0) + tokens_in
        update["tokens_saida"] = state.get("tokens_saida", 0) + tokens_out
    return update


def faq_node(state: MultiAgentState) -> dict[str, Any]:
    """Retrieve top-k FAQ chunks and synthesize, or mark ``no_evidence``."""
    start = time.perf_counter()
    skill = load_skill("skill_faq")
    query = state.get("query_sanitized") or state["query"]
    routing = state.get("routing")

    try:
        hits = retrieve_faq(query, k=FAQ_K)
    except Exception as exc:
        latency = round(time.perf_counter() - start, 4)
        error = f"{type(exc).__name__}: {exc}"
        _LOG.warning("retrieve_faq failed: %s", error)
        return _fail(
            state,
            status="error",
            latency=latency,
            hits=[],
            suffix=f"replanejado para handoff (erro retrieve_faq: {type(exc).__name__})",
            extra_payload={"error": error},
        )

    if not hits:
        latency = round(time.perf_counter() - start, 4)
        return _fail(
            state,
            status="no_evidence",
            latency=latency,
            hits=[],
            suffix="replanejado para handoff (sem evidência)",
        )

    context = "\n\n".join(
        f"[{hit.get('source', '?')} | score={hit.get('score', 0):.2f}]\n{hit.get('excerpt', '')}"
        for hit in hits
    )
    try:
        packed = _structured().invoke(
            build_faq_prompt(query, context, instruction=str(skill["instruction"]))
        )
        parsed, tokens_in, tokens_out = unpack_structured(packed)
    except Exception as exc:
        latency = round(time.perf_counter() - start, 4)
        error = f"{type(exc).__name__}: {exc}"
        _LOG.warning("faq synthesize failed: %s", error)
        return _fail(
            state,
            status="error",
            latency=latency,
            hits=hits,
            suffix=f"replanejado para handoff (erro síntese: {type(exc).__name__})",
            extra_payload={"error": error},
        )

    latency = round(time.perf_counter() - start, 4)
    tokens_in = tokens_in or 0
    tokens_out = tokens_out or 0

    if parsed is None or parsed.status != "ok" or not parsed.answer_text.strip():
        return _fail(
            state,
            status="no_evidence",
            latency=latency,
            hits=hits,
            suffix="replanejado para handoff (síntese sem evidência)",
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            used_llm=True,
        )

    route = _route(state, "faq")
    output = RecFairOutput(
        status="faq",
        halt_reason="completed",
        answer_text=parsed.answer_text.strip(),
        agents_route=route,
    )
    trace = AgentTrace(
        agent_id="faq",
        routing_reason=routing.routing_reason if routing else skill["index"],
        plan=list(routing.plan) if routing else ["skill_faq"],
        replanned=False,
        chamadas_llm=1,
        tool_calls=1,
        latencia_s=latency,
        tokens_entrada=tokens_in,
        tokens_saida=tokens_out,
    )
    last_result = AgentResult(
        agent_id="faq",
        status="ok",
        payload={
            "skill": skill["index"],
            "instruction": skill["instruction"],
            "answer_text": parsed.answer_text.strip(),
        },
        evidence=hits,
        metrics=AgentMetrics(
            latencia_s=latency,
            chamadas_llm=1,
            tool_calls=1,
            tokens_entrada=tokens_in,
            tokens_saida=tokens_out,
        ),
    )
    return {
        "faq_status": "ok",
        "faq_evidence": hits,
        "output": output,
        "last_result": last_result,
        "agents_route": route,
        "agent_traces": append_trace(state, trace),
        "chamadas_llm": state.get("chamadas_llm", 0) + 1,
        "tokens_entrada": state.get("tokens_entrada", 0) + tokens_in,
        "tokens_saida": state.get("tokens_saida", 0) + tokens_out,
        "tool_calls": state.get("tool_calls", 0) + 1,
        "step": state.get("step", 0) + 1,
    }


def route_after_faq(state: MultiAgentState) -> str:
    """Send no-evidence or tool-error FAQ to the handoff node; otherwise end."""
    result = state.get("last_result")
    if result is not None and result.status in {"no_evidence", "error"}:
        return "handoff"
    if state.get("faq_status") in {"no_evidence", "error"}:
        return "handoff"
    return "end"
