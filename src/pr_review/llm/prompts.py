"""
Centralized prompt templates. Nothing outside llm/ builds prompts by hand
(see AGENTS.md).
"""

from __future__ import annotations

SYSTEM_PROMPT = """You are a precise code reviewer. You receive a code \
change (a diff) and optional context about the codebase. Respond ONLY \
with a JSON array of objects, no prose, no markdown fences:

[{"line": <int>, "file": "<path>", "severity": "blocking"|"suggestion"|"nitpick", "comment": "<short, specific comment>"}]

Only flag concrete issues: missing error handling, breaking changes to \
callers, missing tests for new logic. Do not comment on style or \
formatting. If there are no issues, return an empty array: []
"""


def build_user_prompt(filename: str, patch: str, context: str) -> str:
    context_block = (
        f"\n\nRelevant context from the rest of the repo:\n{context}"
        if context
        else ""
    )
    return f"File: {filename}\n\nDiff:\n{patch}{context_block}"