"""
Stub for now - see AGENTS.md. Returns empty context until indexing/ is
built. The interface is intentionally already shaped like what
indexing-backed retrieval will return (a string of relevant snippets), so
wiring in the real implementation later won't require changes to
analyze.py or anything upstream of it.
"""

from __future__ import annotations


def build_context(filename: str, patch: str) -> str:
    # TODO (post-MVP): query indexing/ for callers, related tests, and
    # docstrings relevant to the symbols touched in `patch`.
    return ""