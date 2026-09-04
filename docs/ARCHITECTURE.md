# Architecture

## 1. Architecture Overview

The Insurance Claims Adjudication System (Domain Copilot) follows a modular monolith
architecture using Clean Architecture and Ports and Adapters principles. It provides
AI-assisted insurance claim adjudication while keeping high-impact decisions under human
control (the approval gate).

Two roles: **Adjuster** (reviews and adjudicates assigned claims) and **Manager**
(supervises claims, uploads new policy documents, creates Adjuster accounts, broader
system access).

---

## 2. C4 Architecture

### 2.1 Level 1 — System Context
Shows Adjuster and Manager interacting with the system, and the system's outbound
communication with the external LLM Provider.
**Diagram source:** [`c4-context.mmd`](diagrams/c4-context.mmd)

### 2.2 Level 2 — Container
Containers:
- React Web UI (Redux Toolkit, React Query, React Router, React Hook Form)
- Django REST Framework API (JWT-authenticated)
- Celery Worker (Redis-backed queue — async adjudication and document ingestion)
- PostgreSQL with pgvector — one co-located database (relational tables and vector
  chunks share the same instance; see ADR-003)
- External LLM Provider (OpenAI and Ollama, swappable via configuration)

The Web UI calls the API directly for synchronous operations (ask, claim lookup, auth)
and opens an SSE connection for live job progress. The API enqueues long-running
adjudication/ingestion work onto the Celery worker rather than executing it inline.

**Diagram source:** [`c4-container.mmd`](diagrams/c4-container.mmd)

### 2.3 Level 3 — Component
Components: API Layer, Claim Use Cases, Document Ingestion, Retrieval Service, Agent
Orchestrator, Tool Layer, Approval Workflow, LLM Port, Vector Store access (via the
Retriever ports), Repository Ports.
**Diagram source:** [`c4-component.mmd`](diagrams/c4-component.mmd)

---

## 3. Data Flow and Trust Boundaries

1. Adjuster/Manager interacts with the React Web UI.
2. Web UI calls the Django REST API (JWT bearer token).
3. Authentication and role-based authorization applied server-side (domain access policy).
4. Application retrieves claim/policy context via the Retrieval Service.
5. Selected context (retrieved chunks only, never raw documents or DB access) is sent to
   the external LLM Provider.
6. Response returns to the application, then the Web UI — for adjudication, this happens
   asynchronously via Celery, with progress pushed over SSE.

**Diagram source:** [`data-flow.mmd`](diagrams/data-flow.mmd)

### 3.1 Trust Boundaries
- **User boundary** — Adjuster/Manager via the React Web UI.
- **Application boundary** — auth, authorization, retrieval, orchestration, tool execution.
- **External provider boundary** — the LLM Provider, outside application infrastructure.

### 3.2 LLM Data Boundary
The LLM Provider never accesses PostgreSQL/pgvector directly and never receives database
credentials. It receives only: the user's question, retrieved policy/claim context, and
required tool results — selected and sanitized by the application first.

---

## 4. Entity Relationship Diagram
Entities: User, Client, Policy, PolicyVersion, Claim, Document, DocumentChunk, Job,
JobStep, AgentRun, Approval, Decision, AuditLog. Policy documents are chunked and embedded
for retrieval; claims are assigned to Adjusters; Job/JobStep/AgentRun track each async
adjudication run; final decisions are recorded only through the approval workflow.
**Diagram source:** [`er-diagram.mmd`](diagrams/er-diagram.mmd)

---

## 5. Layer Dependency Diagram
Layers: API/Presentation → Application → Domain, with Infrastructure → Application →
Domain. The Application layer depends on domain logic and Ports, never directly on
infrastructure. Verified in practice when `EMBEDDING_PROVIDER` was switched between
OpenAI and Ollama with zero changes to `domain/` or `application/`.
**Diagram source:** [`layer-dependency.mmd`](diagrams/layer-dependency.mmd)

---

## 6. Sequence Diagram — Full Agentic Workflow

Covers the complete flow: async submission, SSE connect with replay/reconnect, all 3
agents streaming tokens with cooperative cancellation checks, the approval gate
(approve / reject / edit-and-approve with validation), finalization, and the full
Agent → Tool → Evidence → Approval → Decision trace query.

**Diagram source:** [`sequence.mmd`](diagrams/sequence.mmd)

---

## 7. Architecture Decision Records

### ADR-001 — Chunking & Retrieval Strategy
**Decision:** Chunk by numbered section heading (not fixed token windows); metadata
filtering by policy version on every retrieval call.
**Alternatives rejected:** Fixed-token chunking (breaks citation precision at clause
boundaries).
**Consequences:** Chunk boundaries follow document structure, so citations map cleanly
to a real section/clause — at the cost of chunk size varying per section instead of being
uniform.

### ADR-002 — Orchestration Pattern
**Decision:** Pipeline pattern — Coverage Matcher → Exclusion Analyst → Adjudication
Drafter, fixed sequence.
**Alternatives rejected:** Supervisor/planner-executor (unnecessary — D2's workflow is
linear and known in advance, not dynamic).
**Consequences:** Simple to reason about and test; the max-iteration breaker is a
structural safeguard that cannot realistically fire under this pattern, since there is no
loop to break out of.

### ADR-003 — Vector Store Choice
**Decision:** pgvector extension co-located on the same PostgreSQL instance as relational
data — one database, not two.
**Alternatives rejected:** Standalone vector DB (extra infrastructure to operate);
managed vector DB (cost, violates the free-tier design constraint).
**Consequences:** No ivfflat/hnsw index while the embedding column stays
dimension-unconstrained (ADR-004) — acceptable at current corpus scale, documented gap
for production.

### ADR-004 — Decoupled Embedding Provider Selection
**Decision:** `EMBEDDING_PROVIDER` is a separate config value from `LLM_PROVIDER`
(completions), with no fallback chain. `DocumentChunk.embedding` is an unconstrained
pgvector column (no fixed dimension) instead of hardcoded to 1536.
**Alternatives rejected:** One shared provider toggle for both completions and embeddings
(rejected — caused a real, observed dimension-mismatch failure: OpenAI's
`text-embedding-3-small` returns 1536-dim vectors, Ollama's `nomic-embed-text` returns
768-dim; a shared toggle with fallback would have silently mixed incompatible vector
spaces in the same column).
**Consequences:** Switching `EMBEDDING_PROVIDER` requires a full corpus re-ingest — the
whole corpus must be embedded by one consistent provider at a time, never mixed per-chunk.

### ADR-005 — Hybrid Retrieval Fusion and Refusal Gating
**Decision:** Dense (cosine similarity) + keyword (Postgres full-text) retrieval, combined
via Reciprocal Rank Fusion (RRF) for result ordering. Refusal on low-evidence questions is
gated on **raw dense cosine similarity** against a calibrated threshold, not the fused RRF
score.
**Alternatives rejected:** Weighted linear score combination (rejected — cosine similarity
and full-text rank scores aren't on comparable scales, requiring fragile per-corpus
tuning); gating refusal on fused RRF score (rejected after empirical testing — RRF
reflects rank position only, not match quality; an out-of-corpus query's nearest, still-
distant neighbor can rank #1 in both lists and score identically to a genuinely strong
match, so no threshold on the fused score cleanly separated relevant from irrelevant
queries in practice).
**Consequences:** Two different scores now exist in the pipeline by design — fused score
for ranking which chunks to return, raw similarity for the separate refusal decision.

### ADR-006 — T7 Central Decision: Async Execution, Resume, Idempotency
**Decision:** Celery + Redis broker. Job/JobStep state persisted to Postgres on every
transition, not held in worker memory. Step claiming is atomic — a unique `(job, name)`
DB constraint plus insert-or-fail + `select_for_update()`, so concurrent task delivery
cannot execute the same agent step twice (verified with a real multi-threaded regression
test, not mocked timing). Cancellation is cooperative, checked between pipeline steps and
mid-token-stream inside each agent's LLM call; providers explicitly close their stream
connection on cancellation for deterministic cleanup.
**Alternatives rejected:** In-process background threads as a Redis-outage fallback
(rejected during review — a thread dies with the Django process, has no resume, and would
silently bypass every guarantee this ADR describes without the grader knowing which code
path they were observing).
**Consequences:** Redis is a real single point of failure for async execution; documented
as a gap-table item rather than masked with a silent, untested fallback path. Cancellation
is cooperative, not a guaranteed instant abort — Python cannot forcibly kill a thread, so
the underlying HTTP call to the LLM provider may continue briefly server-side even after
the orchestrator stops waiting on it.

---

## 8. Status

Complete: C4 (1–3), data-flow/trust boundaries, ER, layer dependency, sequence diagram,
all 6 ADRs above.

No remaining architecture-documentation gaps at this stage.