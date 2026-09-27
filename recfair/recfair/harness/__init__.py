"""Runtime harness: constrain, verify, correct (E4 resilient architecture)."""

from recfair.harness.citations import fill_citations
from recfair.harness.context import (
    HarnessSettings,
    harness_scope,
    inject_failure_prob,
    is_harness_enabled,
)
from recfair.harness.degrade import (
    DEGRADED_PREFIX,
    label_degraded,
    timeout_output,
    tool_error_output,
)
from recfair.harness.demo import demo_containment, demo_silent_checks
from recfair.harness.retry import TransientError, call_with_retry, is_transient
from recfair.harness.timeout import TimeoutExpired, run_with_timeout
from recfair.harness.unstable import FonteIndisponivel, maybe_fail
from recfair.harness.verify_output import (
    apply_silent_failure_checks,
    verify_confidence,
    verify_evidence,
)

__all__ = [
    "DEGRADED_PREFIX",
    "FonteIndisponivel",
    "HarnessSettings",
    "TimeoutExpired",
    "TransientError",
    "apply_silent_failure_checks",
    "call_with_retry",
    "demo_containment",
    "demo_silent_checks",
    "fill_citations",
    "harness_scope",
    "inject_failure_prob",
    "is_harness_enabled",
    "is_transient",
    "label_degraded",
    "maybe_fail",
    "run_with_timeout",
    "timeout_output",
    "tool_error_output",
    "verify_confidence",
    "verify_evidence",
]
