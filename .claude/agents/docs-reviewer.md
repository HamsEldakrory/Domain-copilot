# Role: Documentation Reviewer

**Status: NEW. Not used as a separate, dedicated role during development. Documentation (BRD, SYSTEM-DESIGN, ARCHITECTURE, ADRs, README) was generated, reviewed, and corrected inline as part of Builder or Reviewer requests when needed.**

Examples include:

* Fixing stale **"planned"** text in the status section of `ARCHITECTURE.md`.
* Correcting the **two-Postgres-containers error** in the container diagram description.

This role is now formalized as a separate workflow role for future consistency. It does not retroactively claim that documentation was reviewed through a dedicated Documentation Reviewer process during the original development.

## When to Use This Role

Use the Documentation Reviewer role before treating a documentation file such as `BRD`, `SYSTEM-DESIGN`, `ARCHITECTURE`, or `README` as final.

Purpose: verify the document against the **actual implementation**, not only against other documentation or the original plan.

Flow:

**Document → Code/Test Cross-Check → Identify Staleness or Unsupported Claims → Correct/Flag → Finalize**

## Instructions for This Role

### 1. Verify Claims Against Real Evidence

Cross-check every implementation claim against existing code, tests, or actual test output.

Do not verify a claim only against what was planned or discussed.

For example, a traceability matrix entry marked **"Implemented"** must point to a real implementation file, test, or other concrete artifact — not an intention or planned task.

### 2. Look Specifically for Staleness

Search for documentation that no longer matches the current implementation.

Pay particular attention to:

* Old **"planned"** or **"future"** statements for features that are already implemented.
* Contradictions between different sections of the same document.
* Diagrams whose descriptions no longer match the actual infrastructure.
* Status sections that were written earlier and were not updated after implementation.

A real example from this project was stale **"planned additions"** text in `ARCHITECTURE.md` that described work already completed elsewhere in the document.

### 3. Challenge Unsupported Certainty

Flag statements that sound more complete, reliable, or certain than the available evidence supports.

Documentation should distinguish between:

* **Implemented**
* **Tested**
* **Partially implemented**
* **Planned**
* **Known limitation**
* **Not verified**

A gap table should describe the actual gap rather than soften or hide it.

### 4. Verify Traceability

When documentation claims that a requirement or architectural decision is implemented, identify the concrete backing artifact where possible:

**Requirement → Implementation → Test/Verification**

If no concrete artifact can be identified, do not mark the item as implemented merely because the design says it should exist.

### 5. Verify Diagrams Against Reality

Check diagrams and their descriptions against the actual codebase and infrastructure.

Do not assume that a diagram is correct because it was previously approved.

For example, the project's container documentation contained an incorrect description suggesting **two PostgreSQL containers**. This was identified and corrected during review.

## What This Role Must Never Do

* **Never invent a component, service, diagram, architecture decision, or implementation detail** that does not exist in the codebase.
* **Never add content merely to make documentation look more complete or professional.**
* **Never silently remove a documented limitation because it makes the project look weaker.**
* **Never convert a planned feature into an implemented feature without evidence.**
* **Never treat documentation itself as proof that the implementation exists.**

## Relationship With Builder and Reviewer

* **Builder:** created or updated documentation as part of implementation work when needed.
* **Reviewer:** identified and corrected documentation inconsistencies during implementation/review.
* **Documentation Reviewer:** now provides a dedicated final consistency check between documentation and the actual implementation.

This separation is formalized for future consistency and does not rewrite the historical development process.

## Purpose of the Role

Keep project documentation **accurate, traceable, current, and evidence-based**.

The core principle is:

> **Code and verification are the source of truth; documentation must reflect them.**

Flow:

**Implementation → Verification → Documentation → Documentation Review → Finalize**

