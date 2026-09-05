# Prompt Asset: Step-by-Step Implementation Template

**Status: USED. This workflow was used throughout development, especially during Days 1–3. The implementation process was directed by the developer: requirements, architecture constraints, expected behavior, and verification criteria were defined and reviewed before moving forward. The AI was used as an implementation and reasoning assistant, providing code and suggestions that were then reviewed, run, tested, and corrected as needed. The template was extracted into its own file on Day 10 to formalize the workflow.**

## Request Shape

Use the following request when implementing a day or feature step by step:

> **"Guide me through [Day/feature] step by step. Do not skip steps. For each step, explain the approach, show the exact implementation, and tell me how to verify it. I will review and run each step before we continue."**

The developer provides the requirements, architectural constraints, expected behavior, and relevant project context. The AI assists with implementation details, code, debugging, and verification suggestions.

## Output Shape — Per Step

Each step should follow this structure:

```text
STEP N — <name>

1. What we are doing
2. Why we need it (tied to a specific requirement)
3. Technical approach and design considerations
4. What should exist after this step
5. Exact files/folders to create or modify
6. Exact commands to run
7. Implementation code
8. How to verify
9. What to expect
10. Review points
11. Checklist
```

The implementation code is provided as a proposal to be reviewed and executed by the developer. It is not considered correct simply because the AI generated it.

After completing the step, **stop**.

The developer reviews the implementation, runs the provided commands, examines the actual output, and confirms whether the step is correct before continuing.

## Rules

### 1. Developer-Directed, Step-by-Step Execution

The developer remains responsible for the technical direction and final decision.

The AI should not independently decide that an implementation is complete.

The workflow is:

**Requirement → Technical Discussion → Proposed Implementation → Developer Review → Run → Test → Observe Real Output → Correct if Needed → Confirm → Continue**

### 2. Review Before Accepting AI-Generated Code

AI-generated code must be treated as an implementation proposal, not as proof of correctness.

The developer should review:

* Architecture boundaries.
* Business logic.
* Dependencies and imports.
* Error handling.
* Security implications.
* Edge cases.
* Consistency with the existing project structure.
* Whether the implementation actually satisfies the requirement.

If something is incorrect, incomplete, or inconsistent, the developer identifies the issue and asks the AI to revise it.

### 3. Always Verify With Real Output

After implementation, run the relevant command or test and inspect the **actual output**.

Do not consider a step complete based on statements such as:

* "This should work."
* "The implementation looks correct."
* "The tests should pass."

The verification workflow is:

**Write → Review → Run → Observe → Confirm**

If the output differs from expectations, diagnose the problem from the actual output and revise the implementation.

### 4. Do Not Assume Project Structure

The AI must not assume that files, folders, functions, classes, or scripts exist without confirmation.

When implementation depends on existing code, inspect the actual project structure and relevant files first.

Do not invent paths, helper functions, scripts, or infrastructure components.

### 5. Tests Are Part of the Development Process

For meaningful behavior, the developer should ask for an appropriate test or verification method rather than relying only on manual inspection.

Tests should verify actual behavior and important edge cases.

For bug fixes, the preferred workflow is:

**Bug Found → Reproduce → Add/Update Regression Test → Apply Fix → Run Test → Confirm**

A passing test is evidence of the specific behavior covered by that test, not proof that the entire system is correct.

### 6. Diagnose From Actual Evidence

If a command, test, or implementation behaves differently from what was expected, use the actual evidence to determine the cause.

Do not blindly repeat the previous implementation.

The developer may provide:

* Command output.
* Test failures.
* Tracebacks.
* Logs.
* Existing source code.
* Database state.
* Configuration.
* Runtime behavior.

The AI should reason from that evidence and propose the smallest appropriate correction.

This principle was important in several real debugging cases in the project and is recorded in `docs/AI-USAGE-LOG.md`.

### 7. Keep the Developer in Control

The AI may:

* Explain implementation options.
* Propose code.
* Suggest tests.
* Analyze errors.
* Identify potential edge cases.
* Suggest architectural improvements.

The developer decides:

* Which approach to use.
* Whether the implementation matches the requirements.
* Whether a change should be accepted.
* Whether additional tests are needed.
* Whether the step is complete.

## Real Examples From This Project

### Day 2

The **Clean Architecture foundation**, **database setup**, and **LLM provider abstraction** were implemented through this iterative process.

The developer defined the architectural direction and constraints, reviewed the proposed implementation, ran the commands, and confirmed the resulting behavior before continuing.

### Day 3

The **ingestion pipeline** followed the same process.

Implementation was performed incrementally, with the resulting behavior checked through real commands and verification rather than being accepted solely because the generated code appeared correct.

### Later Development

The same workflow was used to identify and correct implementation problems, including:

* Retrieval and chunking behavior.
* RRF refusal-threshold logic.
* Correlation ID propagation across Django and Celery.
* Accurate token accounting.
* Concurrent async step claiming.
* SSE replay behavior.

These cases reinforced the principle that generated code must be **reviewed, executed, tested, and corrected based on evidence**.

## Purpose

Keep implementation incremental while maintaining developer ownership of the technical decisions.

The core workflow is:

**Requirement → Design → AI-Assisted Implementation → Developer Review → Run → Test → Observe Real Output → Correct → Confirm → Continue**

The AI assists with implementation and reasoning.

The developer remains responsible for understanding the system, reviewing the generated code, validating the behavior, requesting tests, identifying problems, and deciding when the implementation is complete.

