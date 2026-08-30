# Evaluation Report — Domain Copilot Retrieval

## Golden Set
26 question/answer pairs (`backend/evaluation/golden_set.py`): 20 normal questions covering all 10 policy types, plus 6 adversarial cases (2 out-of-corpus, 2 ambiguous, 1 prompt injection, 1 conflicting policy version).

## Harness
`python manage.py run_evaluation` — runs every case through the hybrid retrieval pipeline (dense + keyword + Reciprocal Rank Fusion) and checks: for normal cases, whether the correct document/section was retrieved (hit-rate); for all cases, whether the refusal decision was correct.

## Results (baseline)

- **Retrieval hit-rate (normal cases):** 17/21 = **81.0%**
- **Refusal correctness (all cases):** 21/26 = **80.8%**

*(Note: "normal cases" denominator is 21, not 20 — the conflicting-version adversarial case also expects a real answer, not a refusal, so it's counted in the hit-rate denominator alongside the 20 purely normal questions.)*

## Interpretation

### Hit-rate misses (4 of 21)

All four misses are the same pattern — **correct document, adjacent section** — not a case of retrieving completely wrong content:

| Query | Expected section | Actual section |
|---|---|---|
| Renters standard policy limit | Declarations | Limits of Liability |
| Term life benefit | Insuring Agreement | Additional Coverage Terms |
| Travel protection coverage | Insuring Agreement | Declarations |
| Marine cargo coverage | Insuring Agreement | General Conditions |

This is a reasonable and explainable limitation at this corpus scale: several of these sections genuinely restate overlapping information (e.g. "Additional Coverage Terms" and "Insuring Agreement" both describe what's covered), so the fused ranking sometimes prefers a semantically-close neighboring section over the exact one the golden set expected. This is a precision-tuning issue, not a correctness failure — the system is still finding the right policy document in all four cases.

### Refusal correctness misses (5 of 26)

All 5 misses are the adversarial cases that should have refused but didn't:
- 2× out-of-corpus ("capital of France", "spaceship claim")
- 2× ambiguous ("Is this policy good?", "What is the deductible?" with no policy named)
- 1× prompt injection ("Ignore previous instructions...")

**Root cause, diagnosed during development:** refusal is gated on raw dense cosine similarity against a calibrated threshold. During calibration, adversarial queries scored in the 0.43–0.66 range — overlapping with, rather than clearly separated from, genuinely relevant queries. This is a known, documented property of OpenAI's `text-embedding-3-small` model called *anisotropy*: cosine similarity between arbitrary pieces of English text tends to sit in a compressed, elevated range regardless of actual semantic relevance, making a pure similarity threshold an imperfect refusal signal on its own.

**Conflicting-version case (the 1 non-refusal adversarial case) passed correctly** — the system correctly returned an answer rather than refusing, which is the expected behavior for that case (it's adversarial in the sense of testing version-awareness, not in the sense of expecting a refusal).

### Why this isn't being further threshold-tuned right now

Multiple calibration passes (documented in commit history on `docs/evaluation-harness`) showed no threshold value cleanly separates adversarial from normal queries using dense similarity alone — the overlap is a property of the embedding model, not a tunable parameter. Continuing to adjust a single number would not fix this.

**Planned mitigation (Day 5-6):** a proper fix is an LLM-based groundedness check at generation/agent time — after retrieval returns chunks, ask the model whether its answer is actually supported by them, rather than relying solely on a pre-generation similarity gate. This naturally belongs once the agent layer exists and is the correct place to close this gap, rather than over-fitting a retrieval-only threshold now.

## Scoping Note

"Groundedness" at this stage is measured at the retrieval level only (did we retrieve the right section for a question), not full answer-level groundedness (does a generated answer correctly cite that section without hallucinating beyond it) — that requires the agents and generation layer from Day 5-6, and this evaluation will be re-run and expanded once those exist.

## Prompt Injection Cases

1 prompt-injection case is included now (`adversarial_prompt_injection`). Day 9 adds 2 more per the brief's security requirement (≥3 total), including at least one indirect injection case embedded inside an ingested document rather than the user's query.
