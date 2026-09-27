"""Prompt dispatcher: v3 by default, v4 when the E4 harness is on."""

from __future__ import annotations

from recfair.harness.context import is_harness_enabled
from recfair.prompts import multiagent_v3, multiagent_v4


def build_supervisor_prompt(query: str, skills_index: str) -> str:
    """Format the supervisor routing prompt for the active architecture."""
    if is_harness_enabled():
        return multiagent_v4.build_supervisor_prompt(query, skills_index)
    return multiagent_v3.build_supervisor_prompt(query, skills_index)


def build_faq_prompt(query: str, context: str, instruction: str = "") -> str:
    """Format the grounded FAQ synthesis prompt for the active architecture."""
    if is_harness_enabled():
        return multiagent_v4.build_faq_prompt(query, context, instruction=instruction)
    return multiagent_v3.build_faq_prompt(query, context, instruction=instruction)
