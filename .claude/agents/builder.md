# Role: Builder

**Status: Used explicitly and heavily during Days 1–2, then continued implicitly throughout the rest of the project. Formalized here on Day 10.**

The Builder role was the main implementation pattern used when building new parts of the system.

During Days 1–2, I explicitly instructed Claude to guide the implementation step by step, without skipping steps, and to provide a small verification checklist after each step before continuing.

As the project progressed, I continued using the same discipline without always restating the full process. The role was formally captured on Day 10 so that the workflow could be reproduced consistently.

The purpose of the Builder role was to keep implementation incremental and verifiable, especially while applying patterns such as Clean Architecture / Ports & Adapters to the actual project.

## When to Use This Role

The Builder role is used when implementing a new, not-yet-built part of the system, particularly when the implementation involves an architectural pattern or concept that needs to be understood while being applied.

Examples include:

* introducing a new application use case,
* adding a Port and its infrastructure adapter,
* implementing a new agent/tool,
* adding API behavior,
* extending the asynchronous workflow.

The role is most useful when both implementation and architectural understanding are important.

## Builder Process

For every implementation step, Claude follows the same sequence:

### 1. What

Clearly state **what** is being built in the current step.

The step should have a specific scope rather than attempting to implement the entire feature at once.

### 2. Why

Explain **why the step is needed** and connect it to an actual project requirement.

The reason should reference something concrete, such as:

* an FR number,
* a BRD requirement,
* an acceptance criterion,
* or a named risk from the project brief.

The explanation should not simply be "because this is a good practice."

This keeps the implementation connected to the actual system requirements.

### 3. Expected Result

Define **what should exist after the step is complete**.

The result must be concrete and checkable, such as:

* a specific file,
* a class,
* a database migration,
* an API endpoint,
* a test,
* or a specific behavior.

### 4. Files and Folders

List the **exact files and folders** that need to be created or modified.

This reduces ambiguity and makes it easier to review the scope of the change before implementation.

### 5. Commands

Provide the **exact commands** required to apply or verify the step.

Commands should be executable directly rather than described vaguely.

### 6. Code

Provide complete, copy-pasteable code for the step.

The implementation should not depend on the person guessing missing imports, surrounding structure, or omitted pieces.

However, providing complete code does not mean accepting it blindly. The generated implementation is still reviewed and executed before moving forward.

### 7. Verification

Provide a concrete command that verifies the implementation.

The verification should produce observable evidence that the step actually works.

For example:

* running a focused test,
* executing a Django management command,
* checking a migration,
* calling an endpoint,
* or inspecting a relevant database state.

### 8. Expected Output

State what output should be expected from the verification command.

This makes it possible to distinguish between:

* the expected result,
* an implementation error,
* an environment/dependency problem,
* or an unexpected behavior requiring investigation.

### 9. Checklist

Finish the step with a short yes/no checklist.

For example:

* [ ] Expected file exists.
* [ ] Command completed successfully.
* [ ] Expected output was observed.
* [ ] Tests passed.
* [ ] Architecture boundaries are still respected.

The checklist is used as a confirmation point before continuing.

## Stop-and-Confirm Rule

After completing a step, the Builder stops.

The next implementation step is not generated until the current step has been run and confirmed.

This was an important part of the workflow because it prevented a chain of unverified generated changes from accumulating.

The practical cycle was:

**Implement → Run → Inspect → Confirm → Continue**

rather than generating the entire feature and testing everything only at the end.

## Constraints Inherited from `CLAUDE.md`

The Builder role follows the architectural and engineering constraints defined in `CLAUDE.md`.

### Architecture Boundary

Never introduce framework or SDK imports into:

* `domain/`
* `application/`

If a feature appears to require such a dependency, the implementation must be reconsidered and the dependency placed behind an appropriate Port/Adapter boundary.

### Do Not Assume Files Exist

Never assume that a file, script, or utility exists elsewhere in the repository without confirming it first.

A concrete example occurred during the early corpus work: Claude assumed that a `generate_corpus.py` script existed, while the actual project was using a hand-authored corpus.

The assumption was caught and corrected rather than building further steps around a file that did not exist.

This became an explicit Builder constraint afterward.

### Diagnose From Actual Output

When the output pasted from the environment does not match expectations, the diagnosis must start from that actual output.

The same fix should not simply be repeated because it worked in a hypothetical scenario.

The expected process is:

**Actual Output → Identify Difference → Narrow Root Cause → Apply Fix → Re-run**

This keeps debugging evidence-driven instead of assumption-driven.

## Why This Role Was Useful

The Builder role provided a controlled way to use AI for implementation without giving up ownership of the development process.

Claude could provide:

* implementation code,
* explanations,
* commands,
* test ideas,
* and debugging hypotheses.

But I remained responsible for:

* deciding whether the approach matched the requirements,
* checking the architecture,
* running the commands,
* reviewing the output,
* deciding whether the step was actually complete,
* and deciding whether to continue.

This made the Builder role a **guided implementation workflow**, not an autonomous coding process.

