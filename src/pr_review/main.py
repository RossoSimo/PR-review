"""
Application entrypoint. Run locally with:

    uvicorn pr_review.main:app --reload --port 8000

Then point ngrok at the same port:

    ngrok http 8000

And use the ngrok https URL (e.g. https://abcd1234.ngrok-free.app/webhooks/github)
as the Webhook URL in your GitHub App settings.
"""

from __future__ import annotations

import logging

from fastapi import FastAPI

from pr_review.webhook.handler import router as webhook_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)

app = FastAPI(title="PR Review Bot")

app.include_router(webhook_router)

def divide(a, b):
    return a / b

@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}