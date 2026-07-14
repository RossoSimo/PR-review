"""
LLM client - local-first via Ollama (see AGENTS.md). This is the only
module that knows we're talking to Ollama specifically; everything else
calls generate_review_comments() without knowing the provider, so
swapping to a hosted API later means changing only this file.
"""

from __future__ import annotations

import json
import logging

import ollama

from pr_review.config import settings
from pr_review.llm.models import ReviewComment
from pr_review.llm.prompts import SYSTEM_PROMPT, build_user_prompt

logger = logging.getLogger("pr_review.llm.client")


def generate_review_comments(
    filename: str, patch: str, context: str = ""
) -> list[ReviewComment]:
    """
    Calls the local Ollama model for a single file's diff and returns
    validated ReviewComment objects. Returns an empty list on any
    parsing/validation failure rather than raising - a bad response for
    one file shouldn't kill the whole PR review.
    """
    client = ollama.Client(host=settings.ollama_base_url)

    response = client.chat(
        model=settings.ollama_model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": build_user_prompt(filename, patch, context)},
        ],
        format="json",  # constrains Ollama to emit syntactically valid JSON
    )

    raw = response["message"]["content"]

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        logger.warning("Model returned invalid JSON for %s: %r", filename, raw[:200])
        return []

    # format="json" guarantees valid JSON syntax but not our schema, so we
    # still validate each item defensively.
    items = data if isinstance(data, list) else data.get("comments", [])

    comments: list[ReviewComment] = []
    for item in items:
        try:
            comments.append(ReviewComment(**item))
        except Exception:
            logger.warning("Skipping malformed comment from model: %r", item)

    return comments