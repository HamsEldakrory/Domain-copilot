# Project Instructions — Domain Copilot (D2 + T7)

This file captures the engineering rules and constraints that governed AI-assisted development throughout the project.

The rules were formalized on Day 10 after being applied and refined during implementation. From Day 1 onward, I treated these as working constraints: I restated the relevant rules when starting implementation work, reviewed Claude's proposed changes against them, and required the resulting behavior to be verified before considering a step complete.

The purpose of these instructions was not to let Claude make architectural decisions independently, but to give it clear boundaries within which I could use it as an implementation and review assistant.

## Architecture Boundaries — Non-Negotiable

* **Clean Architecture / Ports & Adapters.** The system is organized into `domain` → `application` → `infrastructure`/`presentation`.
* `domain/` and `application/` must **never** import Django, an LLM SDK (`openai`, `ollama`), `pgvector`, or any other framework/SDK. If an implementation appears to require such an import, the change must stop and be restructured by introducing a Port instead.
* Concrete implementations of Ports belong in `infrastructure/`, for example:

  * `infrastructure/llm/`
  * `infrastructure/persistence/`
  * `infrastructure/retrieval/`
  * `infrastructure/tools/`
* The practical acceptance test for this boundary is provider substitution: changing the LLM provider or vector-store implementation should require a new adapter and configuration change, not modifications to `domain/` or `application/`.

I did not treat this boundary as theoretical. It was exercised during implementation when `EMBEDDING_PROVIDER` was made switchable between OpenAI and Ollama without changing `application/use_cases/ingest_document.py`. This gave me a concrete check that the provider dependency was actually isolated behind the Port.

## Domain-Specific Rules — D2 Insurance Claims Adjudication

### Deterministic Financial Calculations

All monetary calculations, including `calculate_payout`, are performed deterministically in Python.

The LLM is never responsible for producing the final dollar amount. Agent prompts explicitly instruct the model not to state dollar figures so that the financial result remains controlled by application logic.

This separation was treated as an architectural requirement rather than a prompt-level preference: even if the model produces a plausible number, that number is not accepted as the source of truth.

### Policy Version Resolution

Policy version selection must be date-aware.

`get_policy_version` resolves the applicable policy based on the claim date rather than relying on whichever policy version happens to be pre-assigned.

This is important because an apparently valid policy document is not necessarily the correct policy for a particular claim date.

### Grounded Answers and Citations

Every retrieved answer must contain a structured citation identifying the relevant source information:

* chunk
* page
* document
* policy version

If the system cannot provide sufficient grounding, it must explicitly refuse instead of presenting an unsupported answer as authoritative.

## Working Discipline

### One Step at a Time

When working in step-by-step implementation mode, I do not ask Claude to generate an entire feature in one shot.

The implementation is broken into smaller steps. I run and inspect each step before allowing the workflow to continue.

This made it possible to catch implementation mistakes early instead of discovering several unrelated problems after a large feature had already been generated.

The detailed implementation pattern is documented in `.claude/agents/builder.md`.

### Verify Before Proceeding

A step is not considered complete simply because Claude says that the code should work.

The actual command must be executed, and the output must be reviewed before proceeding.

The working rule was:

> **Generated code is a proposal until it has been run and verified.**

This was particularly important for migrations, integration behavior, concurrency, SSE, and provider-specific behavior where static inspection alone was not enough.

### No Fabricated Success

If a command fails, the failure is recorded and investigated.

I do not treat a plausible explanation from the AI as proof of the root cause, and I do not repeatedly apply guesses without narrowing down what actually failed.

The debugging process therefore follows:

**Run → Observe → Narrow the cause → Fix → Re-run → Verify**

rather than:

**Guess → Patch → Assume success**

### Own Real Mistakes

When an AI-introduced problem is identified, it is treated as an actual engineering defect rather than silently patched.

Relevant mistakes are documented in `docs/AGENTIC-WORKFLOW.md` under **"Where Claude Made Mistakes"**.

When appropriate, the correction is captured with a `fix:` commit that explains:

1. what was wrong,
2. why the implementation was incorrect,
3. what was changed,
4. how the correction was verified.

This creates a traceable record instead of hiding the fact that the initial implementation was wrong.

## Testing Approach

Testing strategy was chosen based on the behavior being verified rather than using the same type of test everywhere.

### Domain/Application Logic

Domain and application logic use unit tests with fakes or mocks for Ports.

These tests avoid real databases and real LLM calls so that business rules can be verified independently of infrastructure.

Examples include:

* `tests/test_day6_orchestration.py`
* `tests/test_fr6_realtime.py`

### Concurrency-Sensitive Logic

Concurrency behavior is tested using Django's `TransactionTestCase` with real threads rather than mocked timing.

For example:

* `tests/test_step_claim_concurrency.py`

This distinction mattered because a mocked concurrency test could easily hide the database race that the implementation was supposed to prevent.

### Integration Behavior

Infrastructure-dependent behavior is tested separately using real Redis and PostgreSQL where required.

For example:

* `tests/test_sse_replay.py`

When an external dependency is not running, the integration test checks for its availability and skips cleanly instead of pretending the integration passed.

This keeps the difference between:

* unit-test success,
* integration-test success,
* and an unavailable external dependency

explicit.

## API Boundaries

### Business Logic Does Not Live in Django Views

Django views are responsible for:

1. parsing input,
2. validating request-level data,
3. calling the appropriate use case,
4. translating the result into an HTTP response.

Business rules belong in the application/domain layers.

This boundary was also used as a review criterion. A real violation was found in `CancelJobView`, where validation/business logic had started to leak into the presentation layer.

The implementation was corrected by moving that logic into `CancelJobUseCase`, leaving the view as a thin adapter.

### Authorization and Permission Rules

Permission and authorization rules belong in `domain/policies/`.

DRF permission classes act as adapters over those domain rules rather than becoming the location where business authorization decisions are implemented.

This keeps authorization behavior reusable and prevents framework-specific code from becoming the source of domain policy.

## AI/RAG Design Constraints

### Retrieved Content Is Data, Not Instructions

Retrieved documents are always treated as **data**.

The content of an ingested document must never gain authority to modify the agent's instructions or workflow.

This boundary is specifically exercised by the indirect prompt-injection evaluation case, where a malicious instruction is placed inside retrieved document content.

The expected behavior is that the agent uses the document as evidence/data while continuing to follow the system's actual instructions.

### Shared LLM Provider Boundary

Embeddings and completions both use the shared `LLMProvider` Port.

The concrete provider implementation remains in infrastructure, keeping provider-specific SDK dependencies outside the domain and application layers.

However, embeddings and completions are allowed to use different configured providers:

* `EMBEDDING_PROVIDER`
* `LLM_PROVIDER`

This separation is intentional because the two workloads have different correctness and operational requirements.

Embedding behavior depends on a stable vector dimension and retrieval compatibility, while completion behavior has different resilience and fallback considerations.

The configuration therefore allows these concerns to evolve independently without breaking the architectural boundary.

## How These Instructions Were Used With Claude

These rules were not intended to replace engineering judgment.

During an AI-assisted implementation session, I used the relevant rules as constraints when reviewing Claude's proposed approach. When a proposal conflicted with the architecture or acceptance criteria, the proposal was revised rather than accepted simply because it was technically executable.

The practical loop was:

**Requirement → Constrained Plan → Implementation → Run → Review → Test → Verify → Document**

This ensured that Claude accelerated implementation and debugging while the architectural decisions, acceptance criteria, and final verification remained under human control.

