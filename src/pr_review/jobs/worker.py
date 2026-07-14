"""
Worker process entrypoint. Run with:

    uv run python -m pr_review.jobs.worker

Keep this running in a separate terminal from uvicorn - it's a different
process that pulls jobs off the "reviews" queue and executes them.

Uses SimpleWorker instead of the default Worker: the default Worker calls
os.fork() to isolate each job in a child process, which doesn't exist on
Windows. SimpleWorker runs jobs in-process instead - less isolation
between jobs, but that's an acceptable tradeoff for local development.
If you deploy on Linux later, you can switch back to Worker for proper
process isolation.
"""

from __future__ import annotations

import logging

from rq.worker import SimpleWorker

from pr_review.jobs.queue import redis_conn, review_queue

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)

if __name__ == "__main__":
    worker = SimpleWorker([review_queue], connection=redis_conn)
    worker.work()