"""
Fetch the file-level diff for a pull request.
"""

from __future__ import annotations
from dataclasses import dataclass
from github import Github


@dataclass
class FileDiff:
    filename: str
    status: str  # "added" | "modified" | "removed" | "renamed"
    patch: str | None  # unified diff text for this file; None for binary/too-large files


def fetch_pr_diff(client: Github, repo_full_name: str, pr_number: int) -> list[FileDiff]:
    repo = client.get_repo(repo_full_name)
    pr = repo.get_pull(pr_number)

    return [
        FileDiff(filename=f.filename, status=f.status, patch=f.patch)
        for f in pr.get_files()
    ]