"""
GitHub App authentication and client factory.

Every other github/ module gets an authenticated PyGithub client from
here. Nothing outside github/ should import PyGithub directly - this is
the boundary AGENTS.md talks about.
"""

from __future__ import annotations
from github import Github, GithubIntegration
from pr_review.config import settings


def _read_private_key() -> str:
    with open(settings.github_private_key_path, "r", encoding="utf-8") as f:
        return f.read()


def get_installation_client(installation_id: int) -> Github:
    """
    Returns a PyGithub client authenticated as a specific installation of
    the GitHub App - the token used to act on the repos the user
    authorized. It's short-lived (~1h) and scoped only to those repos, so
    we mint a fresh one per job rather than caching it long-term.
    """
    integration = GithubIntegration(
        integration_id=int(settings.github_app_id),
        private_key=_read_private_key(),
    )
    access_token = integration.get_access_token(installation_id).token
    return Github(access_token)