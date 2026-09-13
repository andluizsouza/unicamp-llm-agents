"""Golden-set evaluation runner (invoked from notebooks)."""

from __future__ import annotations

import platform
from dataclasses import asdict
from datetime import datetime
from typing import Any

from eval.fingerprint import golden_revision, load_cases
from eval.report import summarize_records
from eval.verify import (
    diagnose_failure,
    final_status,
    is_restrict_scope,
    motivo_sucesso,
    verify_case,
)
from recfair.config import (
    ARCHITECTURE_DATES,
    TEMPERATURE,
    apply_dotenv,
    ensure_google_api_key,
    model_version,
)
from recfair.graphs import baseline, workflow
from recfair.graphs.registry import get_runner
from recfair.observability.run_record import git_sha, new_run_id, run_started_at, save_run


def _architecture_date(arch_id: str) -> str:
    if arch_id == baseline.architecture_id():
        return baseline.architecture_date()
    if arch_id == workflow.architecture_id():
        return workflow.architecture_date()
    return ARCHITECTURE_DATES.get(arch_id, datetime.now().date().isoformat())


def _prompt_version(arch_id: str) -> str:
    if arch_id == baseline.architecture_id():
        return baseline.prompt_version()
    if arch_id == workflow.architecture_id():
        return workflow.prompt_version()
    return baseline.prompt_version()


def _sum_optional_tokens(left: int | None, right: int | None) -> int | None:
    if left is None and right is None:
        return None
    return (left or 0) + (right or 0)


def _merge_metrics(acc: Any, new: Any) -> Any:
    """Accumulate metrics across multi-turn invocations."""
    if acc is None:
        return new
    acc.latencia_s = round(acc.latencia_s + new.latencia_s, 2)
    acc.chamadas_llm += new.chamadas_llm
    acc.tool_calls += new.tool_calls
    acc.tokens_entrada = _sum_optional_tokens(acc.tokens_entrada, new.tokens_entrada)
    acc.tokens_saida = _sum_optional_tokens(acc.tokens_saida, new.tokens_saida)
    trace_a = getattr(acc, "scoring_trace", None) or []
    trace_b = getattr(new, "scoring_trace", None) or []
    if trace_b:
        acc.scoring_trace = trace_a + trace_b
    return acc


def _run_case(runner: Any, case: dict[str, Any], arch_id: str) -> tuple[Any, Any]:
    """Run single-shot or multi-turn case."""
    turns = case.get("turns")
    if turns:
        tid = case["id"] if arch_id == workflow.architecture_id() else None
        output = None
        metrics = None
        for turn in turns:
            if tid:
                output, step_metrics = runner(turn, thread_id=tid)
            else:
                output, step_metrics = runner(turn)
            metrics = _merge_metrics(metrics, step_metrics)
        return output, metrics
    return runner(case["entrada"])


def run_eval(arch: str | None = "baseline", *, persist: bool = True) -> dict[str, Any]:
    """Execute all golden cases and return run manifest."""
    apply_dotenv()
    ensure_google_api_key()
    arch_id, runner = get_runner(arch)
    cases = load_cases()
    revision = golden_revision(cases)
    run_id = new_run_id()
    records: list[dict[str, Any]] = []

    for case in cases:
        output, metrics = _run_case(runner, case, arch_id)
        check = verify_case(case, output)
        restrict = is_restrict_scope(case["familia"])
        records.append(
            {
                "case": case,
                "output": output.model_dump(),
                "metrics": asdict(metrics),
                "check": check,
                "status": final_status(check["aprovado"], restrict),
                "motivo": motivo_sucesso(case, check) or diagnose_failure(case, check),
            }
        )

    resumo = summarize_records(records)
    manifest: dict[str, Any] = {
        "run_id": run_id,
        "architecture_id": arch_id,
        "architecture_date": _architecture_date(arch_id),
        "git_sha": git_sha(),
        "model": model_version(),
        "model_version": model_version(),
        "temperature": TEMPERATURE,
        "prompt_version": _prompt_version(arch_id),
        "golden_revision": revision,
        "started_at": run_started_at(),
        "python": platform.python_version(),
        "resumo": resumo,
        "records": records,
    }
    if persist:
        path = save_run(None, manifest)
        manifest["run_path"] = str(path)
    return manifest
