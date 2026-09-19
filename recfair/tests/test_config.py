"""Tests for env loading and Hugging Face token export."""

from __future__ import annotations

import os

from recfair.config import (
    export_hf_token,
    hf_token,
    huggingface_token_kwargs,
    parse_dotenv,
)


def test_parse_dotenv_strips_quotes_and_skips_comments() -> None:
    parsed = parse_dotenv(
        """
# comment
HF_TOKEN="hf_example"
GOOGLE_API_KEY='abc'
RECFAIR_MODEL_VERSION=gemini-3.5-flash-lite
EMPTY=
"""
    )
    assert parsed["HF_TOKEN"] == "hf_example"
    assert parsed["GOOGLE_API_KEY"] == "abc"
    assert parsed["RECFAIR_MODEL_VERSION"] == "gemini-3.5-flash-lite"
    assert parsed["EMPTY"] == ""


def test_export_hf_token_aliases_hub_token(monkeypatch) -> None:
    monkeypatch.setenv("HF_TOKEN", "hf_test_not_real")
    monkeypatch.delenv("HUGGING_FACE_HUB_TOKEN", raising=False)
    source = export_hf_token()
    assert source == "HF_TOKEN"
    assert os.environ["HUGGING_FACE_HUB_TOKEN"] == "hf_test_not_real"
    assert hf_token() == "hf_test_not_real"
    assert huggingface_token_kwargs() == {"token": "hf_test_not_real"}


def test_export_hf_token_missing_when_blank(monkeypatch) -> None:
    monkeypatch.setenv("HF_TOKEN", "")
    monkeypatch.setenv("HUGGING_FACE_HUB_TOKEN", "")
    assert export_hf_token() is None
    assert hf_token() is None
    assert huggingface_token_kwargs() == {}
