"""Routing contract tests (no LLM)."""

from __future__ import annotations

from recfair.graphs.multiagent.nodes.faq import faq_node, route_after_faq
from recfair.graphs.multiagent.nodes.handoff import HANDOFF_PHONE, handoff_node
from recfair.graphs.multiagent.nodes.recommend import route_after_recommend
from recfair.graphs.multiagent.nodes.security import security_node
from recfair.graphs.multiagent.nodes.supervisor import _coerce
from recfair.graphs.multiagent.skills import SKILLS, load_skill, skills_index
from recfair.observability.agent_trace import AgentTrace
from recfair.schemas.routing import AgentResult, RoutingDecision


def test_skills_index_has_two_capabilities() -> None:
    index = skills_index()
    assert "skill_recommend" in index
    assert "skill_faq" in index
    assert set(SKILLS) == {"skill_recommend", "skill_faq"}


def test_load_skill_faq_exists() -> None:
    spec = load_skill("skill_faq")
    assert "retrieve_faq" in spec["tools"]
    assert spec["instruction"]
    rec = load_skill("skill_recommend")
    assert "score_recommendation" in rec["tools"]


def test_coerce_low_confidence_becomes_handoff() -> None:
    decision = RoutingDecision(
        domain="faq",
        skill="skill_faq",
        plan=["skill_faq"],
        routing_reason="incerto",
        confidence=0.2,
    )
    coerced = _coerce(decision)
    assert coerced.domain == "handoff"
    assert coerced.skill is None
    assert coerced.plan == ["handoff"]


def test_handoff_node_sets_phone_and_agent_result() -> None:
    result = handoff_node({"query": "imposto de renda", "step": 1})
    output = result["output"]
    assert output.status == "handoff"
    assert output.handoff_phone == HANDOFF_PHONE
    assert HANDOFF_PHONE in (output.answer_text or "")
    assert "handoff" in output.agents_route
    last = result["last_result"]
    assert isinstance(last, AgentResult)
    assert last.agent_id == "handoff"
    assert last.status == "ok"
    assert last.payload["phone"] == HANDOFF_PHONE


def test_security_preserves_original_query() -> None:
    original = "Meu CPF é 529.982.247-25 — quais shampoos?"
    update = security_node({"query": original, "step": 0, "tool_calls": 0})
    assert "query" not in update
    assert "[CPF]" in update["query_sanitized"]
    assert "529.982.247-25" not in update["query_sanitized"]
    assert update["agent_traces"][0]["custo_usd"] == 0.0


def test_faq_no_evidence_emits_agent_result(monkeypatch) -> None:
    monkeypatch.setattr(
        "recfair.graphs.multiagent.nodes.faq.retrieve_faq",
        lambda query, k=3: [],
    )
    update = faq_node(
        {
            "query": "política de garantia estendida lunar",
            "query_sanitized": "política de garantia estendida lunar",
            "step": 1,
            "tool_calls": 0,
            "routing": RoutingDecision(
                domain="faq",
                skill="skill_faq",
                plan=["skill_faq"],
                routing_reason="parece FAQ",
            ),
        }
    )
    last = update["last_result"]
    assert last.agent_id == "faq"
    assert last.status == "no_evidence"
    assert update["faq_status"] == "no_evidence"
    assert update["routing"].replanned is True
    assert update["routing"].plan == ["skill_faq", "handoff"]
    assert route_after_faq(update) == "handoff"


def test_faq_retrieve_error_is_not_silent(monkeypatch) -> None:
    def _boom(query: str, k: int = 3):
        raise RuntimeError("faiss missing")

    monkeypatch.setattr("recfair.graphs.multiagent.nodes.faq.retrieve_faq", _boom)
    update = faq_node(
        {
            "query": "bandeiras",
            "query_sanitized": "bandeiras",
            "step": 1,
            "tool_calls": 0,
        }
    )
    assert update["last_result"].status == "error"
    assert "RuntimeError" in update["last_result"].payload["error"]
    assert route_after_faq({"last_result": update["last_result"]}) == "handoff"


def test_route_after_recommend_error() -> None:
    ok = route_after_recommend({"last_result": AgentResult(agent_id="recommendation", status="ok")})
    err = route_after_recommend(
        {"last_result": AgentResult(agent_id="recommendation", status="error")}
    )
    assert ok == "end"
    assert err == "handoff"


def test_agent_trace_includes_cost_and_plan() -> None:
    trace = AgentTrace(
        agent_id="supervisor",
        routing_reason="faq",
        plan=["skill_faq"],
        tokens_entrada=1000,
        tokens_saida=100,
        chamadas_llm=1,
    )
    dumped = trace.to_dict()
    assert dumped["plan"] == ["skill_faq"]
    assert dumped["custo_usd"] > 0
    assert "custo_usd" not in trace.model_dump()


def test_append_trace_concatenates_this_turn() -> None:
    from recfair.observability.agent_trace import append_trace

    first = AgentTrace(agent_id="security", routing_reason="clean")
    second = AgentTrace(agent_id="supervisor", routing_reason="faq", plan=["skill_faq"])
    after_sec = append_trace({}, first)
    after_sup = append_trace({"agent_traces": after_sec}, second)
    assert [row["agent_id"] for row in after_sup] == ["security", "supervisor"]
    assert after_sup[1]["plan"] == ["skill_faq"]
