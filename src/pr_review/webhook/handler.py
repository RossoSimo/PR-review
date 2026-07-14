"""
Webhook entry point: receives GitHub events, validates them, and (for now)
just logs what arrived.

Per AGENTS.md, this module contains NO review logic and NEVER calls the
LLM — its only job is: validate the request is really from GitHub, extract
the relevant fields, and hand off. The "hand off" step is a job enqueue,
which we'll add in the next iteration; right now it only logs, so we can
verify the GitHub -> ngrok -> our server chain actually works end to end
before adding any more moving parts.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Header, HTTPException, Request

from pr_review.config import settings
from pr_review.webhook.verify_signature import verify_github_signature

logger = logging.getLogger("pr_review.webhook")

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post("/github")
async def github_webhook(
        request: Request,
        x_hub_signature_256: str | None = Header(default=None),
        x_github_event: str | None = Header(default=None),
) -> dict[str, str]:
    raw_body = await request.body()

    if not verify_github_signature(
            payload_body=raw_body,
            signature_header=x_hub_signature_256,
            webhook_secret=settings.github_webhook_secret,
    ):
        logger.warning("Rejected webhook: invalid or missing signature")
        raise HTTPException(status_code=401, detail="Invalid signature")

    # We only care about pull_request events for now. GitHub sends many
    # other event types (ping, installation, etc.) to the same endpoint.
    if x_github_event == "ping":
        logger.info("Received GitHub ping event (App just installed/configured)")
        return {"status": "pong"}

    if x_github_event != "pull_request":
        logger.info("Ignoring event type: %s", x_github_event)
        return {"status": "ignored"}

    payload = await request.json()
    action = payload.get("action")

    # We only care about PRs being opened or updated with new commits —
    # not closed, labeled, assigned, etc.
    if action not in ("opened", "synchronize", "reopened"):
        logger.info("Ignoring pull_request action: %s", action)
        return {"status": "ignored"}

    pr = payload["pull_request"]
    repo_full_name = payload["repository"]["full_name"]
    pr_number = pr["number"]
    pr_author = pr["user"]["login"]
    head_sha = pr["head"]["sha"]

    logger.info(
        "PR event accepted: repo=%s pr=#%s action=%s author=%s sha=%s",
        repo_full_name,
        pr_number,
        action,
        pr_author,
        head_sha,
    )

    # NEXT STEP (not yet implemented): enqueue a job here instead of just
    # logging, e.g.:
    #   enqueue_review_job(repo=repo_full_name, pr_number=pr_number, sha=head_sha)

    return {"status": "accepted"}
