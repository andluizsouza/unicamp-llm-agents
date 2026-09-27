"""Resilient runner: E3 graph + harness (retry, timeout, degrade, silent checks)."""

from __future__ import annotations

import time
import uuid
from typing import Any

from recfair.graphs.multiagent.graph import build_graph, recursion_limit
from recfair.graphs.multiagent.runner import CaseMetrics
from recfair.graphs.multiagent.state import MultiAgentState
from recfair.harness.citations import fill_citations
from recfair.harness.context import harness_scope, settings_from_env
from recfair.harness.degrade import label_degraded, timeout_output, tool_error_output
from recfair.harness.retry import TransientError
from recfair.harness.timeout import TimeoutExpired
from recfair.harness.unstable import FonteIndisponivel
from recfair.harness.verify_output import apply_silent_failure_checks
from recfair.observability.agent_trace import traces_to_dicts
from recfair.prompts.multiagent_v4 import PROMPT_VERSION
from recfair.schemas.output import RecFairOutput

_ARCHITECTURE_ID = "resilient"
_ARCHITECTURE_DATE = "2026-09-27"


def architecture_id() -> str:
    """Stable id for the E4 resilient architecture."""
    return _ARCHITECTURE_ID


def architecture_date() -> str:
    """ISO date this architecture was introduced."""
    return _ARCHITECTURE_DATE


def prompt_version() -> str:
    """Prompt set used when the harness is enabled (v4)."""
    return PROMPT_VERSION


def _metrics_from_state(
    final: dict[str, Any],
    *,
    latency: float,
    output: RecFairOutput,
    erro: str | None = None,
) -> CaseMetrics:
    tokens_in = final.get("tokens_entrada", 0)
    tokens_out = final.get("tokens_saida", 0)
    traces = traces_to_dicts(list(final.get("agent_traces") or []))
    routing = final.get("routing")
    return CaseMetrics(
        latencia_s=round(latency, 2),
        tokens_entrada=tokens_in if tokens_in else None,
        tokens_saida=tokens_out if tokens_out else None,
        chamadas_llm=final.get("chamadas_llm", 0),
        tool_calls=final.get("tool_calls", 0),
        scoring_trace=final.get("scoring_trace") or [],
        agent_traces=traces,
        agents_route=list(output.agents_route or final.get("agents_route") or []),
        routing_plan=list(routing.plan) if routing else [],
        replanned=bool(routing.replanned) if routing else False,
        erro=erro,
    )


def _post_process(final: dict[str, Any], output: RecFairOutput) -> RecFairOutput:
    """Fill citations, convert silent failures, label FAQ/tool handoff as degraded."""
    filled = fill_citations(output, faq_evidence=final.get("faq_evidence") or [])
    checked = apply_silent_failure_checks(
        filled,
        routing=final.get("routing"),
        last_result=final.get("last_result"),
        faq_evidence=final.get("faq_evidence") or [],
    )
    routing = final.get("routing")
    last = final.get("last_result")
    if (
        checked.status == "handoff"
        and not checked.degraded
        and routing is not None
        and routing.replanned
        and last is not None
        and last.status in {"error", "no_evidence"}
    ):
        return label_degraded(checked, reason=f"faq_{last.status}")
    return checked


def run(query: str, thread_id: str | None = None) -> tuple[RecFairOutput, CaseMetrics]:
    """Execute the E3 graph under the E4 harness and verify the result."""
    compiled = build_graph()
    tid = thread_id or str(uuid.uuid4())
    config = {"configurable": {"thread_id": tid}, "recursion_limit": recursion_limit()}
    initial: MultiAgentState = {
        "query": query,
        "thread_id": tid,
        "chamadas_llm": 0,
        "tokens_entrada": 0,
        "tokens_saida": 0,
        "tool_calls": 0,
        "step": 0,
        "agent_traces": [],
        "errors": [],
        "agents_route": [],
        "scoring_trace": [],
    }
    start = time.perf_counter()
    settings = settings_from_env(enabled=True)
    with harness_scope(settings):
        try:
            final = compiled.invoke(initial, config=config)
            latency = time.perf_counter() - start
            output = final.get("output")
            if output is None:
                output = RecFairOutput(
                    status="abstention",
                    reason=None,
                    halt_reason="schema_invalid",
                    agents_route=list(final.get("agents_route") or []),
                    degraded=True,
                    degraded_reason="missing_output",
                )
            output = _post_process(final, output)
            return output, _metrics_from_state(final, latency=latency, output=output)
        except TimeoutExpired as exc:
            latency = time.perf_counter() - start
            output = timeout_output(agents_route=["security", "supervisor", "verify"])
            return output, CaseMetrics(
                latencia_s=round(latency, 2),
                tokens_entrada=None,
                tokens_saida=None,
                chamadas_llm=1,
                tool_calls=0,
                erro=f"{type(exc).__name__}: {exc}",
                agents_route=output.agents_route,
            )
        except (FonteIndisponivel, TransientError) as exc:
            latency = time.perf_counter() - start
            output = tool_error_output(
                reason=type(exc).__name__,
                agents_route=["security", "supervisor", "faq", "verify"],
            )
            return output, CaseMetrics(
                latencia_s=round(latency, 2),
                tokens_entrada=None,
                tokens_saida=None,
                chamadas_llm=1,
                tool_calls=1,
                erro=f"{type(exc).__name__}: {exc}",
                agents_route=output.agents_route,
            )
        except Exception as exc:
            latency = time.perf_counter() - start
            halt = "recursion_limit" if "recursion" in str(exc).lower() else "schema_invalid"
            if "timeout" in str(exc).lower():
                output = timeout_output(agents_route=["verify"])
                return output, CaseMetrics(
                    latencia_s=round(latency, 2),
                    tokens_entrada=None,
                    tokens_saida=None,
                    chamadas_llm=1,
                    tool_calls=0,
                    erro=f"{type(exc).__name__}: {exc}",
                    agents_route=output.agents_route,
                )
            fallback = RecFairOutput(
                status="abstention",
                reason=None,
                halt_reason=halt,
                agents_route=["security", "supervisor"],
                degraded=halt != "recursion_limit",
                degraded_reason=halt if halt != "recursion_limit" else None,
            )
            return fallback, CaseMetrics(
                latencia_s=round(latency, 2),
                tokens_entrada=None,
                tokens_saida=None,
                chamadas_llm=1,
                tool_calls=0,
                erro=f"{type(exc).__name__}: {exc}",
                agents_route=fallback.agents_route,
            )


def reset_checkpoint(thread_id: str) -> None:
    """Clear in-memory checkpoint for a thread (CLI /reset)."""
    build_graph().checkpointer.delete_thread(thread_id)
