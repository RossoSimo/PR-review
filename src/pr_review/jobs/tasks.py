"""
The actual work a worker process does for each job: fetch the diff,
analyze it, post the resulting comments back on the PR.
"""

from __future__ import annotations

import logging

from pr_review.github.client import get_installation_client
from pr_review.github.fetch_diff import fetch_pr_diff
from pr_review.github.post_review import post_review_comments
from pr_review.review.analyze import analyze_pr

logger = logging.getLogger("pr_review.jobs.tasks")


def process_pr_review(
    repo_full_name: str,
    pr_number: int,
    head_sha: str,
    installation_id: int,
) -> None:
    logger.info(
        "Processing review job: repo=%s pr=#%s sha=%s",
        repo_full_name,
        pr_number,
        head_sha,
    )

    client = get_installation_client(installation_id)
    diffs = fetch_pr_diff(client, repo_full_name, pr_number)

    comments = analyze_pr(diffs)
    logger.info("Generated %d comments for PR #%s", len(comments), pr_number)

    post_review_comments(client, repo_full_name, pr_number, head_sha, comments)