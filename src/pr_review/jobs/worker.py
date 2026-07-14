"""
Worker process entrypoint. Run with:

    uv run python -m pr_review.jobs.worker

Keep this running in a separate terminal from uvicorn - it's a different
process that pulls jobs off the "reviews" queue and executes them.
"""

from __future__ import annotations

from rq import Worker

from pr_review.jobs.queue import redis_conn, review_queue

if __name__ == "__main__":
    worker = Worker([review_queue], connection=redis_conn)
    worker.work()