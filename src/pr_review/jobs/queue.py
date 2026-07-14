"""
Redis connection and job enqueueing.

This module owns the Redis connection and the RQ Queue object. Nothing
outside `jobs/` should talk to Redis or RQ directly - the webhook handler
just calls `enqueue_review_job(...)` and doesn't know or care how the job
is actually executed.
"""

from __future__ import annotations

from redis import Redis
from rq import Queue

from pr_review.config import settings

redis_conn = Redis.from_url(settings.redis_url)

# TODO: consider separate queues (e.g. "reviews", "default") if you later
# want different priorities/concurrency for different job types.
review_queue = Queue("reviews", connection=redis_conn)


def enqueue_review_job(
    repo_full_name: str, pr_number: int, head_sha: str, installation_id: int
) -> str:
    """
    Enqueue a PR review job. Returns the RQ job id (useful for logging /
    later lookup, e.g. from a dashboard).

    This function must stay fast and side-effect-free besides enqueueing -
    no LLM calls, no GitHub API calls here. Those belong in the worker task.
    """
    job = review_queue.enqueue(
        "pr_review.jobs.tasks.process_pr_review",
        repo_full_name,
        pr_number,
        head_sha,
        installation_id,
        job_timeout="10m",  # TODO: tune once you know real review latency
    )
    return job.id