# Prompt Asset: Pull Request Template

**Status: USED. This request shape was used consistently from Day 1 onward. It was extracted into its own file on Day 10 to formalize the workflow.**

## Request Shape

Use the following request when creating a Pull Request:

> **"Give me the PR for [branch/issue]"**

## Output Shape

The AI must produce the PR using this structure:

```text
## What
<what changed, concretely, at file/component level>

## Why
<which requirement, FR number, or discovered defect this change addresses>

## How tested
<the actual command that was run and the actual output observed — never "should work">

Closes #<issue-number>
```

## Rules

### 1. `How tested` Must Be Based on Real Verification

The `How tested` section must describe verification that has **already been performed**.

It should include, where applicable:

* The actual command that was executed.
* The actual output that was observed.
* A test file that actually passed.

Do not describe an intended future test or write statements such as:

> `should work`

The principle is:

**Written ≠ Verified**

Instead:

**Write → Run → Observe → Confirm**

### 2. Bugs Found During Development Must Be Documented

If the PR includes a bug discovered during its own development, the `How tested` section must explicitly describe the problem and the fix.

This includes real patterns that occurred in this project, such as:

* The **RRF refusal-threshold miscalculation**.
* The **correlation ID `threading.local()` bug**, where the value did not cross the Django/Celery process boundary.

The PR must not be presented as though the implementation was correct on the first attempt when a bug was actually discovered and fixed during development.

The history should reflect:

**Initial Implementation → Bug Found → Fix → Verification**

rather than:

**Implementation → Everything Worked**

### 3. Add One Self-Review Inline Comment Before Merge

Before merging the PR, add **one self-review inline comment** on the diff, according to the repository's own PR discipline requirement.

The comment should identify a point that was explicitly reviewed before merge rather than being added as a purely formal step.

## Real Examples From This Project

This request shape was used across **every PR from Days 1–9**.

Examples include:

* Repo scaffolding
* Database foundation
* Retrieval
* Agents
* Approval gate
* T7 async jobs
* Authentication

All of these PRs followed the same structure without requiring the template to be re-specified each time.

Therefore, the **Pull Request Template was used in practice from Day 1**, while the Prompt Asset itself was extracted and formalized as a standalone file on **Day 10**.

## Purpose

Provide a consistent Pull Request format that clearly connects:

**What Changed → Why → How It Was Actually Tested → Issue**

while preserving an accurate record of the development process, including bugs that were discovered and fixed during implementation.

