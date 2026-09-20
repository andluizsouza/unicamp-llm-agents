"""E1 baseline: single LLM call with stuffed catalog + sales tables."""

from __future__ import annotations

import re
import time
from dataclasses import dataclass
from typing import Any

import pandas as pd
from langchain_google_genai import ChatGoogleGenerativeAI

from recfair.config import (
    TEMPERATURE,
    THINKING_LEVEL,
    model_version,
    sampling_fixed_by_model,
)
from recfair.data.catalog import (
    TODAY,
    WINDOW_END,
    WINDOW_START,
    ensure_csv_files,
)
from recfair.observability.tokens import usage_from_response
from recfair.prompts.baseline_v1 import PROMPT_VERSION, build_prompt
from recfair.schemas.output import RecFairOutput

_ARCHITECTURE_ID = "baseline"
_ARCHITECTURE_DATE = "2026-09-07"

_PROMPT_CACHE: dict[str, str] | None = None
_LLM: ChatGoogleGenerativeAI | None = None
_STRUCTURED: Any = None


@dataclass
class CaseMetrics:
    """Per-invocation instrumentation."""

    latencia_s: float
    tokens_entrada: int | None
    tokens_saida: int | None
    chamadas_llm: int
    tool_calls: int
    scoring_trace: list[dict[str, Any]] | None = None
    erro: str | None = None


def architecture_id() -> str:
    return _ARCHITECTURE_ID


def architecture_date() -> str:
    return _ARCHITECTURE_DATE


def prompt_version() -> str:
    return PROMPT_VERSION


def _load_prompt_tables() -> dict[str, str]:
    global _PROMPT_CACHE
    if _PROMPT_CACHE is None:
        paths = ensure_csv_files()
        df_catalogo = pd.read_csv(paths["tb_catalogo"])
        df_vendas = pd.read_csv(paths["tb_vendas"])
        cat_cols = ["cod_sku", "name_sku", "brand", "category"]
        sales_cols = ["date", "cod_sku", "qt_sold"]
        _PROMPT_CACHE = {
            "catalog": df_catalogo[cat_cols].to_csv(index=False),
            "sales": df_vendas[sales_cols].to_csv(index=False),
        }
    return _PROMPT_CACHE


def _get_structured_llm() -> Any:
    global _LLM, _STRUCTURED
    if _STRUCTURED is None:
        mv = model_version()
        kwargs: dict[str, Any] = {"model": mv, "thinking_level": THINKING_LEVEL}
        if not sampling_fixed_by_model(mv):
            kwargs["temperature"] = TEMPERATURE
        _LLM = ChatGoogleGenerativeAI(**kwargs)
        _STRUCTURED = _LLM.with_structured_output(
            RecFairOutput,
            include_raw=True,
            method="json_schema",
        )
    return _STRUCTURED


def _message_text(raw: Any) -> str:
    content = getattr(raw, "content", raw)
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for block in content:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict) and block.get("type") == "text":
                parts.append(str(block.get("text") or ""))
        return "".join(parts)
    return str(content or "")


def _parse_output(packed: Any) -> tuple[RecFairOutput | None, Any]:
    raw = None
    parsed = None
    if isinstance(packed, dict) and "parsed" in packed:
        raw = packed.get("raw")
        parsed = packed.get("parsed")
    elif isinstance(packed, RecFairOutput):
        parsed = packed
    if parsed is None and raw is not None:
        text = _message_text(raw)
        match = re.search(r"\{.*\}", text, flags=re.DOTALL)
        if match:
            try:
                parsed = RecFairOutput.model_validate_json(match.group(0))
            except Exception:
                parsed = None
    return parsed, raw


def run(query: str) -> tuple[RecFairOutput, CaseMetrics]:
    """One Gemini call: stuffed tables + structured JSON output."""
    tables = _load_prompt_tables()
    prompt = build_prompt(
        query,
        today=TODAY.isoformat(),
        window_start=WINDOW_START.isoformat(),
        window_end=WINDOW_END.isoformat(),
        tb_catalogo=tables["catalog"],
        tb_vendas=tables["sales"],
    )
    structured = _get_structured_llm()
    start = time.perf_counter()
    try:
        packed = structured.invoke(prompt)
        latency = time.perf_counter() - start
        parsed, raw = _parse_output(packed)
        tokens_in, tokens_out = usage_from_response(raw)
        if parsed is None:
            parsed = RecFairOutput(
                status="abstention",
                reason=None,
                halt_reason="schema_invalid",
            )
        metrics = CaseMetrics(
            latencia_s=round(latency, 2),
            tokens_entrada=tokens_in,
            tokens_saida=tokens_out,
            chamadas_llm=1,
            tool_calls=0,
        )
        return parsed, metrics
    except Exception as exc:
        latency = time.perf_counter() - start
        fallback = RecFairOutput(
            status="abstention",
            reason=None,
            halt_reason="schema_invalid",
        )
        return fallback, CaseMetrics(
            latencia_s=round(latency, 2),
            tokens_entrada=None,
            tokens_saida=None,
            chamadas_llm=1,
            tool_calls=0,
            erro=f"{type(exc).__name__}: {exc}",
        )
