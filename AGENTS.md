# PR Review Bot with Semantic Repo Context

## What this project is

A bot that receives GitHub pull request webhooks, enriches the diff with
repo context (callers, related tests, docstrings), calls an LLM to spot
concrete issues (missing error handling, breaking changes, untested paths),
and posts inline comments on the PR, line by line.

**It is not** a style linter. **It is not** a code generator. It's a
reviewer that reasons about context, not just the isolated diff.

## Non-negotiable architectural principle

The code is split into modules with hard boundaries. A module never calls
an external service belonging to another domain directly — it always goes
through a dedicated interface. This is because the project is designed to
grow toward other modules in the future (bug-triage, changelog, code tutor)
that will reuse `indexing` and `review.build_context` without modifying
them.

**Before writing any code, figure out which package it belongs to:**

```
src/pr_review/
  webhook/      → receives GitHub events, validates HMAC signature, enqueues jobs
                 (contains NO review logic, NEVER calls the LLM)
  jobs/         → async job handling (RQ + Redis)
                 (contains NO business logic, only orchestration)
  github/       → every GitHub API call goes through here (PyGithub)
                 (no other module imports PyGithub directly)
  review/       → core business logic: parse_diff, build_context, analyze
                 (the only module that orchestrates webhook→github→llm→github)
  indexing/     → building and querying the repo's semantic index
                 (tree-sitter + pgvector)
                 (in the MVP phase, build_context() can return empty context:
                  the interface stays identical, the implementation comes later)
  llm/          → every model call goes through here, prompts are centralized
                 (no other module builds prompts "by hand")
  db/           → SQLAlchemy models, session management, Alembic migrations
  config.py     → environment variables, centralized (pydantic-settings)
```

If you're about to write a direct call to `PyGithub` or the Ollama client
outside of `github/` or `llm/`, stop: that's a signal the boundary is wrong.

### LLM provider: local-first, provider-agnostic

The project runs against a **local Ollama instance by default** (zero API
cost). `llm/client.py` must expose a small abstract interface (e.g.
`generate_review(context: str) -> list[ReviewComment]`) so the underlying
provider can be swapped later (a hosted API, a different local model)
without touching `review/` or any other module. Never hardcode "Ollama" or
a specific model name outside of `llm/` and `config.py`.

## Implementation rules

- **Python 3.12+, full type hints.** No untyped function signatures in
  `src/`. Run `mypy` (or `pyright`) before considering a change complete.
- **All I/O is async.** FastAPI endpoints, DB access (`asyncpg` via
  SQLAlchemy async engine), and the Anthropic client calls should all be
  async — don't mix blocking calls into the request path.
- **LLM output is always structured JSON**, validated with a Pydantic
  model, never free text parsed with regex. Expected shape for each
  comment:
  ```python
  class ReviewComment(BaseModel):
      line: int
      file: str
      severity: Literal["blocking", "suggestion", "nitpick"]
      comment: str
  ```
  If the model returns malformed JSON or a field that fails validation,
  treat it as a retryable error — don't silently drop or guess values.
- **Never process a webhook synchronously.** The FastAPI endpoint only
  validates the signature and enqueues a job (RQ); a worker process
  handles diff parsing, context building, and the LLM call in the
  background. GitHub expects a response to the webhook within a few
  seconds, not a full review cycle.
- **Always cap the context sent to the LLM.** Never send the entire repo.
  The context bundle per hunk should stay in the range of a few hundred
  lines: this is the product's main cost constraint, not an optimization
  detail to defer.
- **One targeted call per hunk, not one giant prompt.** Prefer several
  focused, cheaper LLM calls over concatenating context from too many
  sources into a single monolithic prompt for the whole PR.
- **Justify every new dependency in `pyproject.toml`** in the PR/commit
  message. Prefer solutions already present in the stack (see below) over
  adding new libraries.

## Reference stack (don't deviate without an explicit reason)

| Layer | Choice |
|---|---|
| Language | Python 3.12+ |
| Web framework | FastAPI |
| Data validation | Pydantic v2 |
| Job queue | RQ + Redis (not Celery — lower setup overhead for a solo MVP) |
| DB | PostgreSQL + pgvector extension |
| ORM | SQLAlchemy (async) + Alembic for migrations |
| Code parsing | tree-sitter (via `tree-sitter-languages`) |
| GitHub API | PyGithub, GitHub App auth (JWT + installation token) |
| LLM | Anthropic Python SDK, structured JSON output |
| Testing | pytest + pytest-asyncio |
| Hosting | Localhost or Railway |

## Project tooling

- Dependency management: `uv` or `poetry` (pick one, don't mix).
- Formatting/linting: `ruff` (format + lint in one tool).
- Pre-commit hooks for `ruff` and `mypy` before every commit.

## User configuration (stable contract, don't break without reason)

The `.pr-review.yml` file in the user's repo is the only configuration
interface. Don't add new keys without documenting them here:

```yaml
severity_threshold: suggestion   # blocking | suggestion | nitpick
ignore_paths:
  - "tests/fixtures/**"
focus:
  - error_handling
  - breaking_changes
  - missing_tests
```

## What to never do

- Never introduce blocking/synchronous LLM calls in the webhook request
  path.
- Never have the LLM comment on style/formatting — that's out of scope for
  this product (linters already cover that).
- Never build the web dashboard before the core loop
  webhook → jobs → review → post comments works end-to-end on a real PR.
  That is priority zero; everything else comes after.
- Never prematurely optimize indexing (e.g. sophisticated incremental
  embeddings) before the simplest version (re-index changed files on every
  push) is tested and working.
- Never commit `.env` files, real API keys, or a real `.pr-review.yml`
  containing project-specific data — only `.env.example` with placeholder
  values.

## Definition of "done" for the MVP

The minimum success criterion, before adding any further feature: a real PR
opened on a test repo receives at least one relevant inline comment,
correctly positioned on the right line, generated by the full chain
webhook → jobs → review (even with an empty build_context()) → LLM →
post comment on GitHub.
