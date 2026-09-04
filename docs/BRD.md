# Business Requirements Document (BRD)

## Insurance Claims Adjudication Copilot

**Domain:** D02 — Insurance Claims Adjudication
**Mandatory Twist:** T07 — Async Long-Running Jobs
**Status:** Implementation Update
**Version:** 0.2

---

## 1. Context

Insurance claims require an Adjuster to review a claim, identify the
applicable insurance policy version, check coverage, exclusions and
limits, detect anomalies, and determine an appropriate outcome.

The Insurance Claims Adjudication Copilot will assist the Adjuster by
retrieving relevant insurance policy information and coordinating
specialised AI agents to analyse the claim.
The system will provide a recommendation supported by evidence.
The final consequential decision remains under human approval.
The system must also support long-running adjudication workflows
through asynchronous jobs.

---

## 2. Personas

### 2.1 Adjuster

The Adjuster is the primary user responsible for reviewing and
adjudicating assigned insurance claims.

The Adjuster should be able to:

- View assigned claims.
- Review relevant policy information.
- Run the adjudication workflow.
- Review evidence and recommendations.
- Approve, reject, or edit and approve the proposed decision.

An Adjuster must not access claims assigned outside their permitted
scope.

---

### 2.2 Manager

The Manager supervises Adjusters and has broader visibility over the
claims within their management scope.

The Manager should be able to:

- View Adjusters within their scope.
- View claims within their scope.
- Monitor adjudication activity.
- Review workflow results and job status.
- Ingest and manage insurance policy documents.
- Manage system/user settings within the Manager's permitted scope.

The Manager is not automatically the final decision maker for an
Adjuster's claim.

---

## 3. Objectives

### OBJ-01 — Improve Claim Review

Help Adjusters review insurance claims more efficiently by providing
relevant policy information and structured analysis.

**Measurable Criteria:**

- At least 90% of golden evaluation cases requiring policy retrieval
  return relevant supporting evidence.

---

### OBJ-02 — Use the Correct Policy Version

Ensure that adjudication uses the policy version applicable to the
claim date.

**Measurable Criteria:**

- At least 1 evaluation test case explicitly verifies that the correct
  policy version is selected for a given claim date.
- All policy-version test cases must select the version whose effective
  dates contain the claim date.

---

### OBJ-03 — Provide Grounded Recommendations

Provide recommendations based on retrieved policy evidence with
traceable citations.

**Measurable Criteria:**

- Achieve at least 90% retrieval hit-rate on the golden evaluation set.
- Retrieved recommendations must include traceable supporting
  citations.

---

### OBJ-04 — Keep Decisions Human-Controlled

Ensure that consequential claim decisions require human approval.

**Measurable Criteria:**

- 100% of finalized consequential decisions have a corresponding
  Approval record.
- Zero consequential decisions may be finalized without an approval
  record.

---

### OBJ-05 — Support Long-Running Workflows

Execute long-running adjudication workflows asynchronously while
allowing users to monitor their progress.

**Measurable Criteria:**

- A job identifier and initial status are returned immediately after
  submission.
- Job status is queryable within 1 second under normal operating
  conditions.
- A job interrupted by a worker/service restart can resume from its
  persisted state.
- Restart/retry scenarios produce zero duplicate consequential side
  effects.

---

## 4. Requirements

### BR-01 — Document Ingestion

The system shall support ingestion of at least two document formats.

**Acceptance Criteria:**

- Two document formats can be ingested.
- Documents can be processed into searchable content.
- Relevant document metadata is preserved.

**Status:** Implemented

**Evidence:** `infrastructure/ingestion/` (`PdfExtractor`, `DocxExtractor`,
`NumberedHeadingChunker`), `application/use_cases/ingest_document.py`
(`IngestDocumentUseCase`), `manage.py ingest_corpus`. Metadata (source,
section, page, clause, policy version) preserved per chunk. Idempotent
re-ingestion via `Document.content_hash`, verified with a duplicate-run test.

---

### BR-02 — Hybrid Retrieval

The system shall provide hybrid retrieval combining semantic and
keyword retrieval.

**Acceptance Criteria:**

- Semantic retrieval is supported.
- Keyword retrieval is supported.
- Results from both approaches are combined.

**Status:** Implemented

**Evidence:** `infrastructure/retrieval/dense_retriever.py` (pgvector cosine
distance), `infrastructure/retrieval/keyword_retriever.py` (Postgres
full-text search), combined via Reciprocal Rank Fusion in
`application/use_cases/retrieve_chunks.py`. See ADR-005.

---

### BR-03 — Policy Version Selection

The system shall use the policy version applicable to the claim date.

**Acceptance Criteria:**

- Policy versions can be identified.
- The claim date is considered.
- The selected policy version is recorded.

**Status:** Implemented

**Evidence:** `infrastructure/tools/get_policy_version.py` resolves the
correct `PolicyVersion` by `claim_date` and flags
`version_mismatch_detected` when the claim's pre-assigned version differs.
Covered by the `adversarial_conflicting_version` evaluation case.

---

### BR-04 — Grounded Answers and Citations

The system shall provide evidence supporting retrieved answers.

**Acceptance Criteria:**

- Answers contain citations.
- Citations identify the supporting source/chunk.
- Unsupported questions are handled without inventing information.

**Status:** Implemented

**Evidence:** `application/use_cases/format_citation.py` returns document,
policy version, section, clause, page, and excerpt per result. Refusal on
low-evidence questions gated on raw dense similarity (ADR-005), verified
against 6 adversarial cases in `docs/EVALUATION.md`.

---

### BR-05 — Multi-Agent Workflow

The system shall contain at least three specialised agents and an
orchestrator.

The planned agents are:

- Coverage Matcher.
- Exclusion Analyst.
- Adjudication Drafter.

**Acceptance Criteria:**

- Three specialised agents are provided.
- An orchestrator coordinates the workflow.
- Each agent has a defined responsibility.

**Status:** Implemented

**Evidence:** `application/agents/coverage_matcher.py`,
`exclusion_analyst.py`, `adjudication_drafter.py`;
`application/use_cases/adjudication_pipeline.py`
(`AdjudicationPipelineOrchestrator`, Pipeline pattern, ADR-002).

---

### BR-06 — Tools

The system shall provide at least four tools for the adjudication
workflow.

At least one tool shall perform a write or other side effect and shall
be protected by human approval.

**Acceptance Criteria:**

- At least four tools are available.
- Tool inputs are validated.
- The side-effecting operation cannot execute before approval.

**Status:** Implemented

**Evidence:** `infrastructure/tools/`: `get_policy_version`,
`search_policy`, `calculate_payout`, `detect_anomaly`, plus the
write/side-effecting `finalize_adjudication` (only invoked from
`ApprovalGateUseCase`'s approve/edit branches, never called directly by
the pipeline). Per-agent tool allow-lists enforced via
`application/agents/tool_gateway.py` (`ToolGateway`), raising
`ToolNotAllowedError` on an out-of-scope call.

---

### BR-07 — Deterministic Calculations

Financial calculations such as limits, deductibles, and payouts shall
be performed by deterministic application logic.

**Acceptance Criteria:**

- Financial calculations are performed outside the LLM.
- Calculation results can be tested.

**Status:** Implemented

**Evidence:** `infrastructure/tools/calculate_payout.py` — pure Python,
zero LLM calls, unit-tested in isolation. Agent prompts explicitly
instruct the model never to state a dollar figure.

---

### BR-08 — Human Approval

The system shall require human approval before a consequential final
decision is recorded.

**Acceptance Criteria:**

The Adjuster can:

- Approve.
- Reject.
- Edit and approve.

Approval actions are recorded.

**Status:** Implemented

**Evidence:** `application/use_cases/approval_gate.py`
(`ApprovalGateUseCase`) — enforces `Job.status == WAITING_APPROVAL` before
any decision; reject never calls `finalize_adjudication`; edit-and-approve
requires `original_recommendation` + `outcome` + `rationale` together
(`MissingEditValuesError` otherwise, preventing a silent disguised
approve). `tests/test_day6_orchestration.py`.

---

### BR-09 — Async Long-Running Jobs

The system shall execute long-running adjudication workflows
asynchronously using a queue and workers.

**Acceptance Criteria:**

- Job submission returns immediately.
- A job identifier is returned.
- Work is processed by workers.

**Status:** Implemented

**Evidence:** Celery + Redis (`infrastructure/tasks.py`). Measured:
`POST /api/adjudicate/` returns in 0.130s while the actual pipeline
completes 9.06s later on the worker — response is ~70x faster than the
work it triggers.

---

### BR-10 — Job Lifecycle

The system shall support:

- Progress reporting.
- Restart survival.
- Resumption.
- Cancellation.
- Idempotency.

**Acceptance Criteria:**

- Job state is persisted.
- Jobs can survive service/worker restarts.
- Interrupted jobs can resume where applicable.
- Running jobs can be cancelled.
- Repeated operations do not create unintended duplicate work or
  side effects.

**Status:** Implemented

**Evidence:** `QUEUED → RUNNING → WAITING_APPROVAL → RUNNING →
COMPLETED/FAILED/CANCELLED`. `JobStep`-based resume verified by killing a
worker mid-run and confirming a completed step is skipped on re-invocation.
Step claiming is atomic — unique `(job, name)` DB constraint +
insert-or-fail + `select_for_update()`, verified under real concurrent
task delivery with `tests/test_step_claim_concurrency.py`
(`TransactionTestCase`, real threads). Cooperative cancellation checked
between steps and mid-token-stream. Celery-level guard skips re-running a
task against a job already in a terminal state.

---

### BR-11 — Authentication and Roles

The system shall provide authentication and at least two roles with
different permissions.

The roles are:

- Adjuster.
- Manager.

**Acceptance Criteria:**

- Protected operations require authentication.
- Adjusters can access only permitted claims.
- Managers have broader access within their scope.
- Permissions are enforced server-side.
- The implemented role names match `Adjuster` and `Manager`.

**Status:** Implemented

**Evidence:** JWT auth (Djoser + SimpleJWT). Role names `ADJUSTER`/
`MANAGER` on `User.role`. Access rule in
`domain/policies/claim_access_policy.py` (framework-free), enforced via
`presentation/api/permissions.py` (`CanAccessClaim`, `IsManager`) on every
endpoint including SSE (manual JWT check, since `StreamingHttpResponse`
bypasses DRF's normal permission pipeline). `tests/test_auth_and_roles.py`
verifies: unauthenticated rejected, owning Adjuster allowed, a different
Adjuster forbidden (403), Manager allowed on any claim.

---

### BR-12 — Real-Time Streaming and Progress

The system shall provide real-time updates to the client.

The system shall support:

- Token-level streaming for the Ask/Chat flow.
- Live agent progress events for adjudication jobs.

**Acceptance Criteria:**

- Answer tokens can be streamed to the client.
- Agent/job progress can be sent to the client.
- The user can observe the current workflow status.

**Status:** Implemented

**Evidence:** Agents use `LLMProvider.stream_completion()` (real
provider-level token streaming, not a post-hoc split of a completed
response). `agent_started` / `agent_progress` / `token` / `agent_complete`
events published per job via Redis Streams
(`infrastructure/events/redis_job_event_publisher.py`), consumed over SSE
(`presentation/api/sse.py`) with history replay and `Last-Event-ID`
reconnect support. `tests/test_fr6_realtime.py`, `tests/test_sse_replay.py`.

---

### BR-13 — Observability

The system shall provide traceability for workflow executions.

**Acceptance Criteria:**

A workflow run can be identified and inspected, including relevant
agent, tool, retrieval, and LLM activity.

**Status:** Implemented

**Evidence:** `application/use_cases/get_run_trace.py` +
`infrastructure/persistence/django_trace_repository.py` return the full
Agent → Tool → Evidence → Approval → Decision chain for a Job ID, with
`Approval`/`Decision` scoped by `job_id` (not just `claim_id`) so a trace
for one run cannot include another run's approval on the same claim.
Correlation ID passed explicitly through Celery task arguments (not
thread-local, which does not cross the Django/worker process boundary) and
recorded on every `AgentRun`. Real per-agent input/output token counts
captured from each provider's actual usage data. `GET /api/health/` and
`GET /api/health/ready/` (DB + Redis checks).

---

### BR-14 — Evaluation

The system shall include an evaluation set containing at least 25
question/answer pairs, including at least 5 adversarial cases.

The evaluation shall report:

- Retrieval hit-rate.
- Groundedness.
- Refusal correctness.

**Acceptance Criteria:**

- At least 25 evaluation cases exist.
- At least 5 are adversarial.
- The evaluation can be executed.
- Results are recorded.

**Status:** Implemented

**Evidence:** `backend/evaluation/golden_set.py` — 26 cases (20 normal, 6
adversarial: 2 out-of-corpus, 2 ambiguous, 1 prompt injection, 1
conflicting policy version). Runnable via `manage.py run_evaluation`. Real
recorded baseline in `docs/EVALUATION.md`: 81.0% retrieval hit-rate (17/21),
80.8% refusal correctness (21/26), with honest interpretation of every
miss — including the specific cause found and documented for the
refusal-threshold cases (embedding anisotropy, not a tunable bug).
Groundedness is explicitly scoped as retrieval-level in this evaluation
pass, not yet full answer-level.

---

### BR-15 — HTTP API, Minimal UI, and Session History

The system shall provide a documented HTTP API and a minimal functional
user interface.

The system shall maintain persistent session history.

**Acceptance Criteria:**

- The HTTP API is documented using OpenAPI.
- The required workflow can be used through the minimal UI.
- Session history persists across sessions.
- The UI provides access to the required claim/adjudication workflow.

**Status:** Partial

**Evidence:** OpenAPI schema + Swagger UI via drf-spectacular
(`/api/schema/`, `/api/docs/`), all endpoints annotated with
`@extend_schema` including response serializers. Minimal React UI (Redux
Toolkit, React Query, React Hook Form, React Router, React-Bootstrap)
covers login, claims list/detail, ask, run with live SSE progress,
approval, trace, policy upload, history. **Gap:** JWT refresh keeps a
login session alive across browser restarts, but there is no dedicated
persistent session-history log beyond the existing `AuditLog`/trace
records — a claim's trace effectively serves this purpose today, but a
first-class "session history" view has not been separately built.

---

## 5. Out of Scope

The following are outside the initial MVP scope:

- Fully autonomous final claim decisions.
- Replacing the human Adjuster.
- Real insurance company integrations.
- Real customer payment processing.
- Features not required by D02 or T07.
- Unnecessary UI polish beyond a functional MVP.

---

## 6. Business Rules

### RULE-01 — Correct Policy Version

The policy version applicable to the claim date must be used.

### RULE-02 — Human Decision

The AI provides a recommendation; the human Adjuster makes the final
consequential decision.

### RULE-03 — Approval Gate

A consequential side effect cannot execute before the required human
approval.

### RULE-04 — Deterministic Calculation

Financial calculations must be performed by application logic rather
than relying on LLM arithmetic.

### RULE-05 — Grounded Information

The system must not present unsupported information as factual.

### RULE-06 — Adjuster Scope

An Adjuster can access only the claims within their permitted scope.

### RULE-07 — Manager Scope

A Manager can access claims and Adjusters within the Manager's
permitted management scope.

### RULE-08 — Manager Document Management

Policy document ingestion and related management capabilities are
available under the Manager role within the Manager's permitted scope.

### RULE-09 — Async Processing

Long-running workflows must be executed through the asynchronous
queue/worker mechanism.

---

## 7. Assumptions

### ASSUMP-01

The project will initially use public or synthetic insurance data.

### ASSUMP-02

The insurance corpus will contain policy information sufficient to
demonstrate the required adjudication workflow.

### ASSUMP-03

Adjusters have assigned claims within the system.

### ASSUMP-04

Managers have a defined scope containing their assigned Adjusters and
claims.

### ASSUMP-05

The exact technical implementation will be defined in the System
Design document.

---

## 8. Risks

| ID | Risk | Impact | Mitigation |
|---|---|---|---|
| R-01 | Wrong policy version | Incorrect recommendation | Date-aware policy version selection |
| R-02 | LLM hallucination | Incorrect information | Grounded retrieval and citations |
| R-03 | Incorrect financial calculation | Incorrect payout | Deterministic calculation logic |
| R-04 | Unauthorized claim access | Data exposure | Server-side authorization |
| R-05 | Side effect without approval | Incorrect final decision | Mandatory approval gate |
| R-06 | Job failure/restart | Lost or incomplete work | Persisted job state |
| R-07 | Duplicate job execution | Duplicate side effects | Idempotency |
| R-08 | Poor retrieval | Incorrect recommendation | Hybrid retrieval and evaluation |

---

## 9. Traceability Matrix

| Requirement | Status | Evidence |
|---|---|---|
| BR-01 | Implemented | `infrastructure/ingestion/`, `IngestDocumentUseCase` |
| BR-02 | Implemented | `DenseRetriever` + `KeywordRetriever` + RRF (ADR-005) |
| BR-03 | Implemented | `get_policy_version` tool, adversarial eval case |
| BR-04 | Implemented | `format_citation.py`, refusal gating (ADR-005) |
| BR-05 | Implemented | 3 agents + `AdjudicationPipelineOrchestrator` (ADR-002) |
| BR-06 | Implemented | 4 tools + gated `finalize_adjudication`, `ToolGateway` |
| BR-07 | Implemented | `calculate_payout.py`, unit-tested |
| BR-08 | Implemented | `ApprovalGateUseCase`, `test_day6_orchestration.py` |
| BR-09 | Implemented | Celery + Redis; measured 0.130s response vs 9.06s work |
| BR-10 | Implemented | Atomic `JobStep` claiming, `test_step_claim_concurrency.py` |
| BR-11 | Implemented | JWT + domain access policy, `test_auth_and_roles.py` |
| BR-12 | Implemented | Real `stream_completion`, SSE + replay, `test_fr6_realtime.py` |
| BR-13 | Implemented | Job-scoped trace, explicit correlation ID, real token counts |
| BR-14 | Implemented | 26-case golden set, real recorded results in `EVALUATION.md` |
| BR-15 | Partial | OpenAPI + minimal UI done; dedicated session-history view not built |

### Status Definitions

- **Implemented:** Requirement is implemented and supported by evidence.
- **Partial:** Requirement is partially implemented and the remaining
  gap is documented.
- **Deferred:** Requirement is intentionally postponed and the reason
  and mitigation are documented.

---

## 10. Document Status

This BRD has been updated from the Day-1 baseline to reflect actual
implementation status and evidence. 14 of 15 business requirements are
fully implemented; BR-15 is partial, with the specific gap (a dedicated
session-history view, distinct from the existing audit/trace records)
stated explicitly rather than left silent.

Technical implementation details belong in:

`docs/SYSTEM-DESIGN.md`