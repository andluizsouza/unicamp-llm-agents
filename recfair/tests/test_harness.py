"""Harness unit tests (no LLM)."""

from __future__ import annotations

import time

import pytest

from recfair.harness.context import HarnessSettings, harness_scope, is_harness_enabled
from recfair.harness.degrade import DEGRADED_PREFIX, timeout_output, tool_error_output
from recfair.harness.demo import demo_containment, demo_silent_checks
from recfair.harness.retry import TransientError, call_with_retry, is_transient
from recfair.harness.timeout import TimeoutExpired, run_with_timeout
from recfair.harness.unstable import FonteIndisponivel
from recfair.harness.verify_output import (
    apply_silent_failure_checks,
    verify_confidence,
    verify_evidence,
)
from recfair.schemas.output import RecFairOutput, RecommendationItem
from recfair.schemas.routing import AgentResult, RoutingDecision


def test_harness_disabled_by_default() -> None:
    assert is_harness_enabled() is False


def test_harness_scope_restores() -> None:
    with harness_scope(HarnessSettings(enabled=True, inject_failure_prob=0.4)):
        assert is_harness_enabled() is True
    assert is_harness_enabled() is False


def test_retry_recovers_from_transient() -> None:
    calls = {"n": 0}

    def flaky() -> str:
        calls["n"] += 1
        if calls["n"] < 3:
            raise FonteIndisponivel("fonte FAQ instável")
        return "ok"

    assert call_with_retry(flaky, attempts=4, sleep=lambda _s: None, jitter=False) == "ok"
    assert calls["n"] == 3


def test_retry_does_not_retry_value_error() -> None:
    def boom() -> None:
        raise ValueError("bad arg")

    with pytest.raises(ValueError):
        call_with_retry(boom, attempts=3, sleep=lambda _s: None, jitter=False)


def test_retry_exhausted_raises_transient() -> None:
    def always() -> None:
        raise FonteIndisponivel("fonte FAQ instável")

    with pytest.raises(TransientError):
        call_with_retry(always, attempts=2, sleep=lambda _s: None, jitter=False)


def test_timeout_expires() -> None:
    def slow() -> None:
        time.sleep(2)

    start = time.perf_counter()
    with pytest.raises(TimeoutExpired):
        run_with_timeout(slow, 0.05)
    assert time.perf_counter() - start < 0.5


def test_retry_exhausted_timeout_reraises() -> None:
    def always() -> None:
        raise TimeoutExpired("operation exceeded 0.1s")

    with pytest.raises(TimeoutExpired):
        call_with_retry(always, attempts=2, sleep=lambda _s: None, jitter=False)


def test_fonte_indisponivel_is_transient() -> None:
    assert is_transient(FonteIndisponivel("fonte FAQ instável"))


def test_degraded_output_identifies_itself() -> None:
    out = tool_error_output(reason="FonteIndisponivel")
    assert out.degraded is True
    assert out.answer_text is not None
    assert out.answer_text.startswith(DEGRADED_PREFIX)
    timed = timeout_output()
    assert timed.halt_reason == "timeout"
    assert timed.degraded is True


def test_verify_evidence_catches_invented_sku() -> None:
    items = [
        RecommendationItem(
            sku="ZZZZZZ",
            name="x",
            brand="x",
            category="cabelos",
            units_7d=1,
        )
        for _ in range(5)
    ]
    output = RecFairOutput(status="recommendation", items=items, halt_reason="completed")
    issues = verify_evidence(output, catalog={})
    assert any(item.startswith("invented_sku") for item in issues)


def test_verify_confidence_high_without_evidence() -> None:
    output = RecFairOutput(status="faq", halt_reason="completed", answer_text="prazo 3 dias")
    routing = RoutingDecision(
        domain="faq",
        skill="skill_faq",
        plan=["skill_faq"],
        routing_reason="faq",
        confidence=0.99,
    )
    issues = verify_confidence(
        output,
        routing=routing,
        last_result=AgentResult(agent_id="faq", status="ok"),
    )
    assert "high_confidence_without_evidence" in issues


def test_apply_silent_failure_converts_to_handoff() -> None:
    output = RecFairOutput(status="faq", halt_reason="completed", answer_text="prazo 3 dias")
    routing = RoutingDecision(
        domain="faq",
        skill="skill_faq",
        plan=["skill_faq"],
        routing_reason="faq",
        confidence=0.99,
    )
    converted = apply_silent_failure_checks(
        output,
        routing=routing,
        last_result=AgentResult(agent_id="faq", status="ok"),
    )
    assert converted.status == "handoff"
    assert converted.degraded is True
    assert converted.answer_text is not None
    assert converted.answer_text.startswith(DEGRADED_PREFIX)


def test_demo_containment_and_silent_checks() -> None:
    containment = demo_containment(failure_prob=1.0, n_calls=3, seed=1)
    assert containment["degraded"] == 3
    assert containment["ok"] == 0
    assert containment["recovered"] == 0
    healthy = demo_containment(failure_prob=0.0, n_calls=3, seed=1)
    assert healthy["ok"] == 3
    assert healthy["recovered"] == 0
    mixed = demo_containment(failure_prob=0.4, n_calls=10, seed=7)
    assert mixed["ok"] == 10
    assert mixed["recovered"] == 7
    silent = demo_silent_checks()
    assert silent["converted_degraded"] is True
    assert silent["user_sees_partial"] is True
