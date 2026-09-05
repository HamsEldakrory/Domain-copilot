# Role: Test Writer

**Status: NEW. Not used as a separate, dedicated role during development. Tests were written inline as part of the Builder or Reviewer roles when needed. This role is formalized here for future consistency, not retroactively claimed as part of the original workflow.**

During the actual development process, tests were created as part of implementation and review steps.

For example:

* `tests/test_day6_orchestration.py`
* `tests/test_fr6_realtime.py`
* `tests/test_step_claim_concurrency.py`

These tests were produced as part of a build or review step rather than through a separate request such as "write tests for X."

Therefore, **Test Writer** is now defined as an independent workflow role for future development, while keeping the project's historical record accurate about how tests were actually created.

## When to Use This Role

Use the Test Writer role after a use case, port implementation, or bug fix has been manually verified to work.

The purpose is to convert that manual verification into a committed, repeatable regression test so that the behavior does not need to be manually verified from scratch every time.

The intended flow is:

**Manual Verification → Regression Test → Repeatable Verification**

## Instructions for This Role

### 1. Identify the Correct Test Type

Choose the test type according to the testing approach defined in `CLAUDE.md`.

#### Domain / Application Logic

For pure domain or application logic:

* Use unit tests.
* Use fakes for Port dependencies.
* Do not use a real database.
* Do not make real LLM calls.

#### Concurrency or Timing

For behavior that depends on real concurrency or timing:

* Use `TransactionTestCase`.
* Use real threads.
* Do not rely on mocked sleep or mocked timing to prove a race condition.

Example:

`tests/test_step_claim_concurrency.py`

This is important when the bug itself depends on actual concurrent execution.

#### External Dependencies

For tests that require a real external dependency, such as:

* Redis
* a live LLM

the test must first check whether the dependency is available.

If the dependency is not running, the test should skip cleanly rather than failing in a way that suggests the application behavior itself is broken.

## 2. Make Sure the Regression Test Actually Proves the Bug

Before considering a test a real regression test, verify that it would have failed against the old/buggy implementation.

This can be done mentally or literally when appropriate.

The key principle is:

> **If the test would have passed before the bug was fixed, it does not prove that the fix was necessary.**

The test should therefore target the actual behavior that was broken rather than simply checking that the code can execute.

The verification flow is:

**Old Buggy Behavior → Test Should Fail → Apply Fix → Test Passes**

This provides evidence that the test protects the behavior that the fix actually corrected.

## 3. Name Tests After the Behavior

Test names should describe the behavior being proven rather than the method being called.

Prefer:

`test_reject_never_finalizes`

over:

`test_decide_reject`

The first name describes the business behavior that must remain correct, while the second only describes an implementation detail.

This also makes tests easier to understand when the underlying implementation changes.

## 4. Prefer a Small Number of Strong Tests

The goal is not to increase the number of tests simply to increase coverage.

Prefer a small number of sharp tests that clearly prove important behaviors instead of creating many similar or low-value tests.

This follows the project's principle:

> **Ten sharp tests beat a hundred trivial ones.**

The focus should be on important behaviors and failure modes rather than creating a large parameter sweep with little additional value.

## What This Role Must Never Do

### Do Not Test Only the Happy Path

Do not write only a happy-path test when the original bug is caused by a specific edge condition.

For example, if a bug appears only during:

* concurrent access,
* cancellation during a stream,
* restart/resume,
* or external dependency failure,

then a happy-path test alone is not a sufficient regression test.

The test must reproduce the condition under which the bug actually appeared.

### Do Not Mark a Test as Passing Without Running It

A test must not be considered successful simply because the code looks correct or the expected result seems obvious.

The test must actually be executed and its output reviewed.

The rule is:

**Written ≠ Verified**

A test becomes evidence only after:

**Write → Run → Observe → Confirm**

## Relationship With Builder and Reviewer

During the original development process, tests were created within other roles:

* **Builder:** wrote tests as part of implementing a feature or step.
* **Reviewer:** added or modified tests when review identified behavior that needed explicit verification.
* **Test Writer:** is now a separate role for converting verified behavior into repeatable regression tests.

This separation does not change the historical development record. It simply turns a practice that was previously performed within other roles into an explicit workflow that can be applied consistently in future development.

## Purpose of the Role

The main purpose of Test Writer is to ensure that important manually verified behaviors are protected by clear, repeatable tests.

The resulting workflow is:

**Implement → Manual Verify → Identify Critical Behavior → Write Regression Test → Run → Confirm → Commit**

