"""
Orchestrates a full PR review: for each reviewable file, build context and
call the LLM, then collect all comments. This is the only module that
ties together review/, llm/, and the data coming from github/.
"""

from __future__ import annotations

import logging

from pr_review.github.fetch_diff import FileDiff
from pr_review.llm.client import generate_review_comments
from pr_review.llm.models import ReviewComment
from pr_review.review.build_context import build_context
from pr_review.review.parse_diff import select_reviewable_files

logger = logging.getLogger("pr_review.review.analyze")


def analyze_pr(diffs: list[FileDiff]) -> list[ReviewComment]:
    reviewable = select_reviewable_files(diffs)
    logger.info("Reviewing %d/%d changed files", len(reviewable), len(diffs))

    all_comments: list[ReviewComment] = []
    for file_diff in reviewable:
        context = build_context(file_diff.filename, file_diff.patch or "")
        comments = generate_review_comments(
            filename=file_diff.filename,
            patch=file_diff.patch or "",
            context=context,
        )
        all_comments.extend(comments)

    return all_comments