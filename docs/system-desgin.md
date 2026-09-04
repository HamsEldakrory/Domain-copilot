# System Design Document — Domain Copilot (D2 + T7)

## Part A — Ideal Enterprise Architecture (The Big Picture)

If we were building this for a massive insurance company with unlimited budget, we would use cloud services to make it scale infinitely:

- **API Gateway:** A front door that protects the app from hackers and handles huge amounts of web traffic.
- **Secrets Manager:** A secure vault to store passwords and API keys instead of keeping them in files.
- **Managed Queues:** Cloud services (like AWS SQS) to handle thousands of background tasks at once without crashing.
- **Autoscaling Workers:** Systems that automatically add more computers to process claims when it gets busy, and remove them when it's quiet.
- **Dedicated Vector Database:** A specialized database just for AI search, hosted by a cloud provider for maximum speed.
- **Monitoring Dashboards:** Tools to track exactly how long every AI task takes and how much it costs in real-time.
- **Automated Deployments:** Systems that automatically test and deploy new code safely to production.
- **Disaster Recovery:** Automatic backups of all databases so no data is ever lost if a server dies.

```text
        ┌──────────────┐
        │  API Gateway │  (Security & Traffic)
        └──────┬───────┘
      ┌────────┴─────────┐
      │   Web Server      │──── Secrets Manager
      │ (Django Backend)  │──── Cache (Redis)
      └────────┬─────────┘
      ┌────────┴─────────┐
      │ Background Queue  │
      └────────┬─────────┘
      ┌────────┴─────────┐
      │ Scalable AI       │──── Cloud Vector DB
      │ Workers           │──── Cloud Relational DB 
      │ (Celery)          │──── Monitoring Dashboards
      └───────────────────┘
```

---

## Part B — Implemented Project

A single-service Django application, one co-located Postgres+pgvector instance, and a
self-hosted Celery/Redis queue — sufficient to demonstrate every functional requirement
without paying for managed infrastructure.

**What's built:**
- Clean Architecture / Ports & Adapters — `domain` and `application` have zero
  framework/SDK imports; swapping `EMBEDDING_PROVIDER` between OpenAI and Ollama required
  only a config change.
- PostgreSQL + pgvector (co-located, ADR-003), 13 core entities, migrations.
- LLM provider abstraction — 2 working implementations (OpenAI, Ollama), decoupled
  provider selection for completions vs. embeddings (ADR-004).
- Ingestion pipeline: PDF/DOCX extraction, section-heading chunking, embedding, indexing,
  idempotent re-ingestion (content-hash based).
- Hybrid retrieval: dense + keyword, RRF fusion, metadata filtering by policy version,
  refusal gated on raw dense similarity (ADR-005).
- 3 specialized agents (Coverage Matcher, Exclusion Analyst, Adjudication Drafter) +
  pipeline orchestrator (ADR-002); deterministic `calculate_payout`, never LLM-computed.
- Per-agent tool allow-lists (`ToolGateway`), max-iteration breaker, per-step timeout,
  retry with backoff, graceful degradation to plain RAG.
- Approval gate — approve / reject / edit-and-approve, with a validation guard preventing
  a silent "edit" that carries no actual edited values.
- Full audit trail — `AuditLog`, `Approval`, `Decision` all scoped by Job ID, so a trace
  for one run never leaks data from a different run of the same claim.
- T7: Celery + Redis, real job lifecycle (QUEUED→RUNNING→WAITING_APPROVAL→
  RUNNING→COMPLETED/FAILED/CANCELLED), atomic step claiming (unique DB constraint +
  `select_for_update`, verified under real concurrent load), cooperative cancellation
  checked between steps and mid-token-stream, restart/resume via `JobStep`.
- Real-time: SSE with Redis Streams, true token-level streaming from both providers, event
  replay for late connections, `Last-Event-ID` reconnect support.
- Auth: JWT (Djoser + SimpleJWT), 2 roles (Adjuster, Manager) enforced server-side via a
  domain-level access policy; Manager-only endpoints for creating Adjusters and uploading
  new policy documents (with limit/deductible captured directly at upload time).
- Observability: correlation ID threaded explicitly through Celery task args (not
  thread-local, which doesn't cross process boundaries), real per-agent token counts
  (from the provider's actual usage data, not an estimate), health/readiness endpoints.
- OpenAPI documentation (drf-spectacular), Swagger UI.
- Frontend: React, Redux Toolkit, React Query, React Hook Form, React Router,
  React-Bootstrap — login, claims list/detail, ask, run with live progress, approval,
  trace, policy upload, history.
- Evaluation harness: 25+ Q/A golden set incl. adversarial cases, real recorded hit-rate
  and refusal-correctness numbers with honest interpretation (`docs/EVALUATION.md`).
- Security: rate limiting, CORS/security headers, prompt injection eval cases (incl.
  indirect), secret scanning, dependency scanning.

### Gap Table

| Target Component | Implemented? | Why Not Built | What We Did Instead |
|---|---|---|---|
| Cloud API Gateway | No | No cloud infrastructure for this project | Basic request limits are handled directly inside Django |
| Secrets Manager | No | Out of scope for a local project | API keys stored in a `.env` file that is never committed to Git |
| Managed Cloud Queue | No | Self-hosted Redis is enough to prove the concept | A local Redis instance running in Docker |
| Autoscaling Workers | No | No cloud budget or deployment environment | A single Celery worker running locally in Docker |
| Dedicated Vector Database | Partial | Needs a paid cloud service at scale | PostgreSQL + pgvector in the same database handles AI search for now |
| Full Monitoring Dashboards | No | No hosting budget | Every agent step and error is logged to the database |
| Automated Backups | No | No production data to protect | Data lives locally; can be backed up manually with a database dump |
| Live Production Deployment | No | Not required — local is sufficient | The entire stack runs with a single `docker compose up` command |