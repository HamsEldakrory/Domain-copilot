# Prompt Asset: Issue Template

**Status: USED. This request shape was used consistently from Day 1 onward. It was extracted into its own file on Day 10 to formalize the workflow.**

## Request Shape

Use the following request whenever an issue needs to be created:

> **"Give me the issue for [scope of work]"**

## Output Shape

The AI must produce the issue using this structure every time:

```text
**Title:**
<one line: "Day N: <scope>" or "fix: <scope>" for bugfix issues>

**Description:**
<2-4 sentences explaining what this covers and why it exists as its own issue>

**Acceptance Criteria:**
- [ ] <concrete, checkable item>
- [ ] <concrete, checkable item>
...
```

## Rules

### 1. Acceptance Criteria Must Be Checkable

Acceptance criteria must describe concrete, verifiable facts.

Prefer:

> `X returns 403 for an unauthorized user`

Avoid vague criteria such as:

> `X works correctly`

Each criterion should be something that can be verified through code inspection, a test, or an explicit command/output.

### 2. One Issue = One Coherent Unit of Work

One issue should normally map to one PR's worth of work.

Granularity is determined by what can form **one coherent commit history**, not simply by how large or small the topic is.

A large topic may therefore be split into multiple issues when it represents separate coherent units of work.

### 3. Fix Issues Must Describe the Actual Finding

When a fix issue follows a review, the description must state **what was found to be wrong** rather than only describing what will be built.

The issue should preserve the connection:

**Review Finding → Problem → Fix → Acceptance Criteria**

This makes the issue useful as both an implementation task and part of the project's engineering history.

## Real Examples From This Project

This request shape was used repeatedly without needing to be re-specified each time.

Examples include:

* Issue for **Day 3 ingestion foundation**
* Issue for **Day 6 orchestration controls**
* Issue for **FR-6 real-time review fixes**
* Issue for the **SSE replay bug**

All followed the same request/output shape.

The template was therefore **used in practice from Day 1**, while the dedicated prompt asset itself was extracted and formalized on **Day 10**.

## Purpose

Provide a consistent issue-creation format that produces:

**Scope → Concrete Description → Checkable Acceptance Criteria → Coherent PR/Commit History**

