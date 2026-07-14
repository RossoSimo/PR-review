"""
Selects which of the PR's changed files are worth sending to the LLM.

For the MVP we treat each file's patch as a single unit rather than
splitting it further into individual hunks - simpler, and still respects
the "cap context per call" rule since we skip huge/binary patches.
Splitting into finer-grained hunks is a reasonable next improvement once
this works end to end.
"""

from __future__ import annotations

from pr_review.github.fetch_diff import FileDiff

# Keep prompts small and cheap; tune once you've measured real latency/cost
# on your hardware.
MAX_PATCH_CHARS = 6000


def select_reviewable_files(diffs: list[FileDiff]) -> list[FileDiff]:
    """
    Filters out files we shouldn't send to the LLM: no patch (binary/huge
    files GitHub didn't diff), or patches so large they'd blow the context
    budget.
    """
    return [d for d in diffs if d.patch and len(d.patch) <= MAX_PATCH_CHARS]