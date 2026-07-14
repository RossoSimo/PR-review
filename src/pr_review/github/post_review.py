"""
Post inline review comments back on a pull request.
"""

from __future__ import annotations
from github import Github
from pr_review.llm.models import ReviewComment


def post_review_comments(
    client: Github,
    repo_full_name: str,
    pr_number: int,
    commit_sha: str,
    comments: list[ReviewComment],
) -> None:
    if not comments:
        return  # nothing to say is a valid outcome, not an error

    repo = client.get_repo(repo_full_name)
    pr = repo.get_pull(pr_number)
    commit = repo.get_commit(commit_sha)

    review_comments = [
        {
            "path": c.file,
            "line": c.line,
            "body": f"**[{c.severity}]** {c.comment}",
        }
        for c in comments
    ]

    pr.create_review(
        commit=commit,
        body="Automated review",
        event="COMMENT",
        comments=review_comments,
    )