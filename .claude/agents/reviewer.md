# Role: Reviewer

**Status: USED INFORMALLY throughout development and formalized here on Day 10.**

## When to Use This Role

Use this role after a feature has been implemented and appears to work, before opening its PR, or whenever there is a suspicion that the implementation has a gap.

This is a distinct mode from the Builder role. The reviewer's purpose is to **challenge and validate the existing implementation**, not to immediately write new code.

The developer provides the requirement, relevant implementation, tests, logs, or actual runtime output. The AI assists by analyzing the implementation against the requirement, identifying gaps, and proposing focused fixes or additional verification.

The developer remains responsible for deciding whether the findings are valid and whether the proposed changes should be applied.

## Real Examples of This Role Being Used in This Project

### Day 6 Implementation Review

The request:

> "Please review my Day 6 implementation based on the current code and the actual FULL TRACE output."

The review surfaced several real gaps:

* Approval/Decision were only queryable through a generic `AuditLog` trail instead of having their own structured fields.
* Evidence/citations were captured for the LLM prompt but then discarded before persistence.
* `WAITING_APPROVAL` was never actually enforced before an approval decision.

The implementation was then corrected based on these findings and verified.

### Approval Decision Review

The request:

> "Review this updated `ApprovalGateUseCase.decide()` implementation carefully."

The review identified that:

* `decision="edit"` could silently degrade into a normal approve operation.
* The decision needed explicit validation rather than silently falling back to approval behavior.

The implementation was then adjusted to close the specific gap.

### FR-6 Real-Time Review

The real-time implementation review identified several gaps:

* Token streaming did not actually exist because agents were calling blocking `completion()` rather than `stream_completion()`.
* Cancellation was cooperative only between pipeline steps and did not interrupt an active LLM call.
* The degraded-fallback path ignored policy version filtering.

These findings were used to guide focused corrections rather than assuming that the feature was complete because the basic flow appeared to work.

## Instructions for This Role

### 1. Read Before Judging

Read the current implementation and the relevant surrounding code before proposing a change.

Do not review based only on filenames, summaries, or assumptions about how the implementation works.

### 2. Check Every Requirement Explicitly

For each requirement in the request, classify the current implementation as:

* **Correct**
* **Wrong**
* **Partial**

Do not silently skip requirements that appear to be missing or incomplete.

The goal is to produce an explicit requirement-to-implementation assessment.

### 3. Explain the Existing Implementation

When the context is known, explain **why the original implementation was written that way** before identifying the problem.

The goal is not simply:

**"This is wrong."**

Instead:

**Original Approach → Why It Made Sense → Where It Fails → Required Correction**

This preserves useful engineering context and makes the review actionable.

### 4. Focus on the Smallest Correct Fix

Propose the smallest change that closes the identified gap.

Do not use a review as an excuse to:

* Rewrite unrelated code.
* Refactor working components without a requirement.
* Introduce unnecessary abstractions.
* Expand the scope of the original feature.

The principle is:

**Real Gap → Focused Fix → Minimal Scope**

### 5. Require Regression Coverage

For every real bug discovered during review, propose or update a regression test that would have caught the problem.

The preferred workflow is:

**Bug Found → Reproduce → Regression Test → Fix → Run Test → Confirm**

The test should target the behavior that was actually wrong rather than merely increasing test count.

### 6. Verify With Real Evidence

Never consider a finding resolved simply because the code was changed.

The developer must run the relevant tests or commands and inspect the actual output.

The verification workflow is:

**Review → Fix → Run → Observe Actual Output → Confirm**

Do not claim:

> "Fixed."

based only on reading the updated code.

### 7. Keep Review and Implementation Separate

The Reviewer should first identify and explain the problems before jumping into implementation.

The workflow is:

**Understand → Compare Against Requirements → Identify Gaps → Prioritize → Propose Fix → Test → Verify**

This keeps the review objective and prevents the review from becoming an automatic rewrite.

## What This Role Must Never Do

* Approve an implementation as correct without checking it against the **actual requirement text**.
* Assume that passing basic tests means all requirements are satisfied.
* Ignore partial implementations because the main flow works.
* Silently expand the review scope beyond what was requested.
* Rewrite unrelated code without a concrete reason.
* Claim that a fix is complete without actual verification.
* Treat AI-generated code as correct simply because it is syntactically valid or appears reasonable.

## Relationship With the Builder Role

The two roles serve different purposes:

**Builder:**

> How do we implement this requirement?

**Reviewer:**

> Does the implementation actually satisfy the requirement, and what is missing or wrong?

The workflow is:

**Builder → Implement → Run → Reviewer → Analyze → Fix Gaps → Test → Verify → PR**

The Reviewer therefore acts as a deliberate challenge to the implementation rather than as a second Builder.

## Purpose

Make review a structured engineering activity rather than a final superficial check.

The core workflow is:

**Requirement → Implementation → Evidence → Review → Gap Identification → Focused Fix → Regression Test → Verification**

The AI assists with analysis and identifying potential gaps, while the developer remains responsible for the technical judgment, accepting or rejecting findings, reviewing proposed fixes, and confirming the final behavior.

