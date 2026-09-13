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
    PROMPT_VERSION,
    TEMPERATURE,
    apply_dotenv,
    ensure_google_api_key,
    model_version,
)
from recfair.graphs import baseline
from recfair.graphs.registry import get_runner
from recfair.observability.run_record import git_sha, new_run_id, run_started_at, save_run


def _architecture_date(arch_id: str) -> str:
    if arch_id == baseline.architecture_id():
        return baseline.architecture_date()
    return ARCHITECTURE_DATES.get(arch_id, datetime.now().date().isoformat())


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
        output, metrics = runner(case["entrada"])
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
        "prompt_version": PROMPT_VERSION,
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
