"""
Shared data shape for review comments, validated wherever the LLM output
crosses a module boundary.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel


class ReviewComment(BaseModel):
    line: int
    file: str
    severity: Literal["blocking", "suggestion", "nitpick"]
    comment: str