# Business Requirements Document (BRD)

## Insurance Claims Adjudication Copilot

**Domain:** D02 — Insurance Claims Adjudication  
**Mandatory Twist:** T07 — Async Long-Running Jobs  
**Status:** Initial Baseline — Day 1  
**Version:** 0.1

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

**Status:** Planned

---

### BR-02 — Hybrid Retrieval

The system shall provide hybrid retrieval combining semantic and
keyword retrieval.

**Acceptance Criteria:**

- Semantic retrieval is supported.
- Keyword retrieval is supported.
- Results from both approaches are combined.

**Status:** Planned

---

### BR-03 — Policy Version Selection

The system shall use the policy version applicable to the claim date.

**Acceptance Criteria:**

- Policy versions can be identified.
- The claim date is considered.
- The selected policy version is recorded.

**Status:** Planned

---

### BR-04 — Grounded Answers and Citations

The system shall provide evidence supporting retrieved answers.

**Acceptance Criteria:**

- Answers contain citations.
- Citations identify the supporting source/chunk.
- Unsupported questions are handled without inventing information.

**Status:** Planned

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

**Status:** Planned

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

**Status:** Planned

---

### BR-07 — Deterministic Calculations

Financial calculations such as limits, deductibles, and payouts shall
be performed by deterministic application logic.

**Acceptance Criteria:**

- Financial calculations are performed outside the LLM.
- Calculation results can be tested.

**Status:** Planned

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

**Status:** Planned

---

### BR-09 — Async Long-Running Jobs

The system shall execute long-running adjudication workflows
asynchronously using a queue and workers.

**Acceptance Criteria:**

- Job submission returns immediately.
- A job identifier is returned.
- Work is processed by workers.

**Status:** Planned

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

**Status:** Planned

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

**Status:** Planned

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

**Status:** Planned

---

### BR-13 — Observability

The system shall provide traceability for workflow executions.

**Acceptance Criteria:**

A workflow run can be identified and inspected, including relevant
agent, tool, retrieval, and LLM activity.

**Status:** Planned

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

**Status:** Planned

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

**Status:** Planned

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

The matrix is a Day-1 baseline and will be updated as implementation
progresses.

| Requirement | Status | Evidence |
|---|---|---|
| BR-01 | Planned | To be added during implementation |
| BR-02 | Planned | To be added during implementation |
| BR-03 | Planned | To be added during implementation |
| BR-04 | Planned | To be added during implementation |
| BR-05 | Planned | To be added during implementation |
| BR-06 | Planned | To be added during implementation |
| BR-07 | Planned | To be added during implementation |
| BR-08 | Planned | To be added during implementation |
| BR-09 | Planned | To be added during implementation |
| BR-10 | Planned | To be added during implementation |
| BR-11 | Planned | To be added during implementation |
| BR-12 | Planned | To be added during implementation |
| BR-13 | Planned | To be added during implementation |
| BR-14 | Planned | To be added during implementation |
| BR-15 | Planned | To be added during implementation |

### Status Definitions

- **Implemented:** Requirement is implemented and supported by evidence.
- **Partial:** Requirement is partially implemented and the remaining
  gap is documented.
- **Deferred:** Requirement is intentionally postponed and the reason
  and mitigation are documented.

---

## 10. Document Status

This is the initial Day-1 BRD baseline.

The document may be updated during implementation when requirements are
clarified or when the implementation status changes.

Technical implementation details belong in:

`docs/SYSTEM-DESIGN.md`