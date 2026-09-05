# Agentic Workflow

This document describes how Claude was used as an engineering assistant throughout the project, how the working process evolved during implementation, and how the practices that proved useful were later formalized.

The workflow was not designed completely upfront and then followed mechanically. It evolved alongside the project as implementation, debugging, testing, and review exposed areas where a more explicit process was useful. The practices documented below therefore reflect the actual way the project was developed, including cases where Claude's suggestions were rejected, corrected, or validated through additional testing.

## How Claude Was Actually Used

Claude was used as a pair-programming and review assistant across the project, including Django/Clean Architecture implementation, database and migration design, retrieval and agent logic, async job infrastructure (Celery/Redis/SSE), authentication, the React frontend, and project documentation.

The important distinction was that Claude was used to **assist with implementation and reasoning, not to make engineering decisions independently**. Implementation requests were driven by the project's requirements and architecture, and proposed changes were reviewed and verified before being considered complete.

Two interaction patterns emerged naturally during development:

1. **Step-by-step implementation** — used explicitly from Day 2 onward, particularly while learning Clean Architecture / Ports & Adapters alongside implementing it. Larger features were broken into smaller steps, with the expected result defined before implementation and the actual command output checked before continuing.

2. **Targeted review** — used repeatedly after features were implemented. Instead of assuming that an implementation satisfied the requirement because it worked at a basic level, Claude was asked to review the existing implementation against the actual requirement and identify missing cases, architectural violations, or incorrect assumptions. This review process caught several of the real defects documented in `AI-USAGE-LOG.md`.

This separation between **implementation assistance and independent review** became important. A feature was not considered complete simply because code had been generated or a basic test had passed; the resulting behavior had to be checked against the intended requirement.

## What Was Configured Originally

Nothing was committed to the repository as agentic configuration before this pass.

The project rules were initially maintained as explicit working context during development: Clean Architecture boundaries, one-step-at-a-time implementation, verification before proceeding, and no assumption of success without actual command output.

As the project grew, these rules were formalized into repository files so that the same constraints could be applied consistently in future sessions.

## What Was Used Informally Before Formalizing

Several practices were already being followed during development even though they were not initially stored as repository configuration:

* Restating architecture rules at the beginning of sessions.
* Breaking implementation into small, independently verifiable steps.
* Using a consistent implementation-step structure:
  **What / Why / What should exist / Files / Commands / Code / Verify / Expect / Checklist**.
* Using a consistent GitHub issue structure:
  **Title / Description / Acceptance Criteria**.
* Using a consistent pull-request structure:
  **What / Why / How tested**.
* Following a Conventional Commits convention, with the commit body explaining the reason behind a fix when appropriate.
* Separating implementation requests from explicit review requests rather than relying on the implementation pass to validate itself.
* Using Django management commands as repeatable project tooling:
  `ingest_corpus`, `backfill_policy_limits`, `seed_demo_users`, `run_pipeline_demo`, `run_approval_demo`, `run_evaluation`, and `create_test_claim`.

The practical pattern was therefore:

**define the requirement → implement a small change → run it → inspect the result → review against the requirement → add or update tests → continue.**

## What Is Being Formalized / Versioned Now

Five of the seven listed practices are satisfied. They were selected because they correspond directly to practices already used during development rather than being added simply to satisfy a tooling checklist.

### 1. Project instruction file (`CLAUDE.md`)

`CLAUDE.md` makes the project's architectural and domain constraints explicit.

It defines the Clean Architecture boundary rule (`domain`/`application` must not import Django, an LLM SDK, or `pgvector`), D2-specific requirements such as deterministic payout calculations, date-aware policy version resolution, and mandatory citations, as well as the working discipline around incremental implementation and verification.

Previously, these constraints were maintained as conversational context. Committing them makes them versioned, reviewable, and reusable by future sessions.

### 2. Sub-agents scoped to distinct roles (`.claude/agents/`)

The repository contains:

* `builder.md`
* `reviewer.md`
* `test-writer.md`
* `docs-reviewer.md`

`builder.md` and `reviewer.md` formalize patterns that were genuinely used during development. In particular, the reviewer role reflects the explicit second-pass reviews that identified issues such as the Day 6 approval-gate gaps and the FR-6 real-time implementation gaps documented in `AI-USAGE-LOG.md`.

`test-writer.md` and `docs-reviewer.md` are different: they were not used as independent roles throughout the original implementation. They formalize responsibilities that were previously handled inline by the Builder/Reviewer process so that those checks can be performed more consistently in future work.

### 3. Custom commands for repeated operations

The project's existing Django management commands provide the repeatable operational tooling used during development.

These include seeding demo data, corpus ingestion, policy-limit backfilling, evaluation execution, and end-to-end pipeline and approval demonstrations.

These commands were not introduced simply to satisfy an agentic-workflow requirement; they were already part of the project's development and verification workflow.

### 4. Versioned prompt library (`.claude/prompts/`)

The issue, PR, implementation-step, and commit-message templates that had been repeatedly used during development are now stored as versioned files.

This converts a conversational convention into something explicit and reusable.

The goal is not to make every interaction rigid, but to preserve the parts of the workflow that consistently helped maintain scope, document intent, and make changes easier to review.

### 5. Hooks enforcing quality gates (`.githooks/pre-commit`)

The pre-commit hook is **new and was not used during the original development period**.

Previously, tests and linting were run manually and their actual output was used to verify changes.

The new hook provides an additional automated quality gate by running the test suite and linting when `ruff` is available. It is installed through `scripts/install-hooks.sh` because Git does not automatically execute hooks stored inside the repository.

This is therefore documented as a **future consistency mechanism**, not as something that was retroactively part of the development process.

### Not Claimed

Reusable skills beyond the prompt templates and MCP server usage are not claimed as practices used in this project because they were not actually part of the development workflow.

## How the Workflow Protects the Architecture

`CLAUDE.md` treats the Clean Architecture boundary as a hard constraint rather than a stylistic preference. The Builder and Reviewer roles are both instructed to check implementation decisions against this boundary.

Importantly, the workflow does not assume that defining a rule prevents mistakes. Instead, the rule provides a concrete reference for reviewing and correcting them.

For example, the correlation-ID mechanism was initially implemented using `threading.local()`. That approach did not work across the Django-process/Celery-worker-process boundary. The issue was identified during review and corrected by passing the correlation ID explicitly through task arguments.

This illustrates why the workflow uses both implementation and review: the architectural rule existed, but the implementation still needed to be tested against the actual process model.

## How the Workflow Affects Implementation, Debugging, Testing, Refactoring, and Documentation

### Implementation

New capabilities are implemented incrementally rather than accepting a large generated change as a complete feature.

The expected files, behavior, and verification command are established for each step. The actual output is then checked before moving to the next step.

### Debugging

Debugging is treated as an investigation rather than simply asking for another implementation.

The Reviewer process compares the observed behavior with the original requirement and examines assumptions made by the implementation. This second pass was responsible for identifying many of the real issues recorded in `AI-USAGE-LOG.md`.

### Testing

Testing is part of the verification process rather than an optional final step.

When a bug is identified, the goal is to turn the discovered behavior into a regression test where practical.

Examples include:

* `tests/test_step_claim_concurrency.py` — verifies the step-claiming behavior using real multi-threaded execution rather than relying only on mocked timing.
* `tests/test_sse_replay.py` — verifies the SSE replay behavior after the replay issue was identified.

The Test Writer role formalizes this pattern for future work.

### Refactoring

Refactoring is intentionally scoped to real problems found during implementation or review.

The goal is not to rewrite working code simply to make it look different. Changes should address an identified architectural, correctness, maintainability, or requirement gap while avoiding unnecessary expansion of scope.

### Documentation

Documentation is reviewed against the implementation rather than treated as independent prose.

For example, `ARCHITECTURE.md` contained a stale "planned additions" section that contradicted components already completed elsewhere in the document. It was corrected during review.

A container diagram was also corrected after review because it represented Postgres and pgvector as separate databases even though ADR-003 defined them as a single co-located instance.

## Where Claude Made Mistakes or Gave Unsuitable Suggestions

Claude's output was not treated as automatically correct. Several cases required rejection, correction, or additional verification.

The full history is documented in `docs/AI-USAGE-LOG.md`. Important examples include:

* An initial corpus containing meta/AI-facing language instead of authentic policy-style text.
* A chunking regex that incorrectly interpreted a PDF-wrapped mid-sentence fragment as a section heading.
* A refusal threshold that was mathematically unreachable, followed by a second threshold that was miscalibrated in the opposite direction.
* A concurrency race in step claiming that was not adequately addressed until a real multi-threaded test exposed it.
* A correlation-ID implementation based on `threading.local()` that did not cross process boundaries.
* A proposed Redis-outage fallback using background threads that would have bypassed the guarantees required by T7.

These examples are important because they demonstrate the purpose of the workflow: **Claude's output is a proposal that must be checked against the system's actual requirements and runtime behavior.**

## What Decisions Remain Under Human Control

Architectural and product decisions remain under human control.

This includes:

* technology and stack choices;
* Clean Architecture boundaries;
* ADR decisions;
* domain and requirement interpretation;
* deciding which proposed implementation is appropriate;
* deciding whether a bug requires further investigation or should instead be documented as a known limitation;
* deciding whether a partially satisfied requirement such as BR-15 is acceptable.

Claude can propose an implementation or identify a possible issue, but it does not determine that a requirement has been satisfied.

Completion is based on actual verification: running the relevant command or test, inspecting the result, and reviewing it against the intended requirement.

Examples include the decision to document the embedding-anisotropy refusal limitation in `docs/EVALUATION.md` and the decision to document the cooperative-not-instant nature of cancellation in ADR-006.

## Limitations of the Agentic Approach Observed in This Project

The workflow itself has limitations.

* Review quality depends on the clarity and completeness of the requirement being reviewed.
* Some gaps, including job-scoping on `Approval`/`Decision` and the edit-and-approve validation gap, were identified only after an explicit second review pass.
* Claude repeated an incorrect assumption more than once in the `complete_job` abstract-method incident, demonstrating why described fixes cannot replace actually running the relevant command.
* Claude also made incorrect assumptions about the existing repository state, such as assuming a `generate_corpus.py` script existed when the actual workflow used a hand-curated corpus.

These limitations reinforce the main principle of the workflow: **AI assistance reduces implementation and review effort, but verification remains necessary.**

## How This Makes Future AI-Assisted Development More Consistent

The main value of formalizing the workflow is not to make development dependent on Claude.

`CLAUDE.md`, the role files, and the prompt templates capture the project's architecture, domain constraints, implementation conventions, and review process in a versioned form.

A future session can therefore start from the repository's actual rules instead of relying on conversational memory.

More importantly, the workflow establishes a repeatable engineering loop:

**Requirement → Plan → Implement → Run → Review → Test → Verify → Document.**

Claude can participate at multiple points in that loop, but the decision that a change is correct remains based on the project's requirements, tests, runtime behavior, and human review.

