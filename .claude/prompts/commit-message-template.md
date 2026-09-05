# Prompt Asset: Commit Message Convention

**Status: USED. This convention was used consistently from Day 1 onward. It was extracted into its own file on Day 10 to formally document the existing practice.**

## Convention

Use **Conventional Commits**, with a body that explains **why** when the change needs additional context, not just what changed:

```text
<type>: <short summary, imperative mood, no trailing period>

<body - only when the change needs explaining: what was wrong, why this
approach was chosen, what the previous behavior was>
```

Types used in this project:

* `feat` — new feature
* `fix` — bug fix
* `docs` — documentation
* `test` — tests
* `chore` — maintenance or configuration

## Rules

### 1. `fix:` Commits Must Explain What Was Actually Wrong

A `fix:` commit should describe **the actual problem that existed**, not merely what was changed.

For example:

```text
fix: correct RRF threshold that made refusal unreachable
```

The body should explain the actual mathematical ceiling of the RRF score and why the configured threshold was unreachable, rather than using a vague message such as:

```text
fix threshold bug
```

The goal is for the commit to remain understandable even when read later without the original conversation.

### 2. Commits Must Be Atomic

Each commit should represent **one logical change**, rather than a dump of everything completed at the end of the day.

This was enforced throughout the project.

For example, **domain errors**, **configuration**, and **dependency injection** were kept as three separate commits on the same branch instead of being combined into one end-of-day commit.

Principle:

**One Logical Change → One Commit**

### 3. Avoid Unclear Commit Messages

Do not use messages such as:

```text
WIP
fix2
final-final
changes
update
```

The commit message should clearly communicate the nature and purpose of the change.

## Real Examples From This Project

### Embedding Provider

```text
fix: decouple embedding provider from completion provider
```

The commit explains the embedding-dimension mismatch that caused the issue, specifically the **1536 vs 768 dimension** mismatch.

### Atomic Step Claiming

```text
fix: atomic step claiming to prevent concurrent duplicate agent execution
```

The commit explains why `select_for_update()` alone does not solve the race condition when the row being claimed does not exist yet.

### SSE Replay

```text
fix: SSE replays event history before deciding to close or live-tail
```

The commit directly describes the **late-connect bug** caused by replaying event history before deciding whether the connection should close or continue live-tailing.

## Purpose

Keep the project's commit history:

* Clear
* Atomic
* Understandable later
* Connected to the actual problem or purpose
* Honest about bugs and fixes discovered during development

The core principle is:

**Commit Message → What Changed + Why It Changed**

Not simply:

**Commit Message → What Changed**

