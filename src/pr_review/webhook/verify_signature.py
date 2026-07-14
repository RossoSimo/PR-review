"""
Validates that an incoming webhook request really comes from GitHub.

GitHub signs every webhook payload with the secret you set when creating
the GitHub App, using HMAC-SHA256. It sends the signature in the
`X-Hub-Signature-256` header as `sha256=<hex digest>`.

We recompute the same HMAC over the raw request body and compare it to
the header using a constant-time comparison (hmac.compare_digest), to
avoid leaking timing information that could help an attacker guess a
valid signature byte by byte.

Usage in the FastAPI webhook endpoint:

    from fastapi import Request, HTTPException
    from pr_review.webhook.verify_signature import verify_github_signature

    @app.post("/webhooks/github")
    async def github_webhook(request: Request):
        raw_body = await request.body()
        signature = request.headers.get("X-Hub-Signature-256")

        if not verify_github_signature(raw_body, signature, settings.github_webhook_secret):
            raise HTTPException(status_code=401, detail="Invalid signature")

        # ... only past this point do we trust the payload and enqueue a job
"""

from __future__ import annotations

import hashlib
import hmac


def verify_github_signature(
    payload_body: bytes,
    signature_header: str | None,
    webhook_secret: str,
) -> bool:
    """
    Verify that `payload_body` was signed by GitHub with `webhook_secret`.

    Args:
        payload_body: the raw, unparsed request body (bytes). Must be the
            exact bytes GitHub sent — do NOT re-serialize JSON before
            checking, or the signature will never match.
        signature_header: the value of the `X-Hub-Signature-256` header,
            expected in the form "sha256=<hex digest>". None if the header
            is missing.
        webhook_secret: the secret configured both in the GitHub App
            settings and in your environment (`GITHUB_WEBHOOK_SECRET`).

    Returns:
        True if the signature is valid, False otherwise (missing header,
        malformed header, or mismatch).
    """
    if not signature_header:
        return False

    if not signature_header.startswith("sha256="):
        return False

    expected_digest = signature_header.removeprefix("sha256=")

    computed_hmac = hmac.new(
        key=webhook_secret.encode("utf-8"),
        msg=payload_body,
        digestmod=hashlib.sha256,
    )
    computed_digest = computed_hmac.hexdigest()

    return hmac.compare_digest(computed_digest, expected_digest)