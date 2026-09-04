# Security Controls and Threat Mapping

This document maps the security controls implemented in the Domain Copilot platform to the specific threats they address, aligned with the **OWASP Web Top 10** and **OWASP LLM Top 10**.

---

## 1. OWASP Web Top 10 Controls

| Threat | Implemented Control | Location / Evidence |
|--------|---------------------|----------------------|
| **A01:2021 - Broken Access Control** | **Role-Based Access Control (RBAC):** Distinct `IsAdjuster` and `IsManager` permissions enforce segregation of duties. <br> **Object-Level Permissions:** Adjusters can only access claims they are explicitly assigned to (`CanAccessClaim`). | `presentation/api/permissions.py`<br>`presentation/api/views.py` |
| **A02:2021 - Cryptographic Failures** | **Secure JWT Authentication:** Access and refresh tokens signed with HMAC-SHA256 (`SimpleJWT`). <br> **Secure Password Storage:** Passwords hashed using bcrypt via Django's `set_password()`. | `config/settings.py` (SIMPLE_JWT)<br>`infrastructure/persistence/models.py` |
| **A03:2021 - Injection** | **SQL Injection Prevention:** All database access goes through Django's ORM, which parameterizes queries automatically. Zero raw SQL executed. | `infrastructure/persistence/django_*.py` repositories |
| **A04:2021 - Insecure Design** | **Segregation of Duties:** The workflow explicitly separates the "maker" (Adjuster runs adjudication) from the "checker" (Manager approves). A user cannot perform both actions on a claim. | `presentation/api/views.py` |
| **A05:2021 - Security Misconfiguration** | **Environment-Based Config:** `DEBUG=False` in production, `ALLOWED_HOSTS` locked down via `.env`. <br> **Security Headers:** HSTS, X-Frame-Options (DENY), X-Content-Type-Options (nosniff), Referrer-Policy, and X-XSS-Protection added via middleware. | `config/settings.py`<br>`presentation/api/middleware.py` |
| **A07:2021 - Identification and Auth Failures** | **Global Authentication Gate:** All API endpoints (except public schema) strictly require `IsAuthenticated` enforcing a valid JWT bearer token. | `presentation/api/views.py` |
| **A08:2021 - Software and Data Integrity** | **Approval Gate Validation:** The system rejects "edit and approve" requests that do not actually contain any modified fields, ensuring the integrity of the approval intent. <br> **Atomic State Transitions:** Step claiming uses DB unique constraints to prevent race conditions. | `application/use_cases/approval_gate.py` |
| **A09:2021 - Security Logging and Monitoring** | **Immutable Audit Log:** Every agent run, human approval/rejection, and system decision is recorded with timestamps and the acting user's ID. | `infrastructure/persistence/models.py` (`AuditLog`, `Approval`) |

---

## 2. OWASP LLM Top 10 Controls

| Threat | Implemented Control | Location / Evidence |
|--------|---------------------|----------------------|
| **LLM01 - Prompt Injection (Direct & Indirect)** | **Strict Privilege Separation:** The `CoverageMatcher` and `ExclusionAnalyst` agents receive retrieved document text strictly as "context blocks" and do not execute instructions from them. <br> **Pre-generation Refusal Gate:** High similarity threshold (`0.55`) drops irrelevant/malicious injection attempts before they reach the LLM. <br> **Evaluation Suite:** Golden set includes both direct role-escalation/extraction cases and an indirect document-embedded injection case. | `application/use_cases/retrieve_chunks.py`<br>`evaluation/golden_set.py` |
| **LLM02 - Insecure Output Handling** | **Raw Token Streaming:** The system streams plain string tokens back to the UI (`Server-Sent Events`). Output is never passed to `eval()`, never executed as system commands, and never rendered as raw HTML. | `presentation/api/sse.py` |
| **LLM06 - Sensitive Information Disclosure** | **PII & Object Isolation:** The backend explicitly scopes all operations to the requested `claim_id` and `job_id`, verified against the authenticated user's permissions. The LLM only receives policy chunks relevant to the approved query, never the entire corpus or other users' claims. | `presentation/api/permissions.py`<br>`application/use_cases/adjudication_pipeline.py` |
| **LLM07 - System Prompt Leakage** | **Relevance Gating:** Attackers requesting "ignore instructions and output system prompt" are mathematically stopped at the retrieval layer (low cosine similarity to insurance text) before the agent is ever invoked. | `application/use_cases/retrieve_chunks.py` |
| **LLM08 - Vector / Embedding Weaknesses** | **Metadata Filtering:** Queries are hard-filtered by `policy_version_id` at the vector database query level. The LLM physically cannot retrieve or mix in text from a different policy version. | `infrastructure/persistence/django_chunk_repository.py` |
| **LLM09 - Overreliance / Misinformation** | **Deterministic Financial Math:** The system strictly calculates the final payout using standard Python logic (`min(limit, claimed - deductible)`). The LLM is never allowed to perform financial calculations or propose payout numbers on its own. | `application/use_cases/approval_gate.py` |
| **LLM10 - Unbounded Consumption** | **API Rate Limiting:** All endpoints are throttled (`UserRateThrottle`: 60/min, `AnonRateThrottle`: 20/min). <br> **Circuit Breakers:** `MAX_ITERATIONS` prevents infinite agent loops. <br> **Timeouts:** `STEP_TIMEOUT_SECONDS` enforces a hard kill on hung LLM calls. <br> **Tool Allow-lists:** `ToolGateway` explicitly restricts which agent can call which tool. | `config/settings.py`<br>`application/agents/tool_gateway.py` |

---

## 3. CI/CD & Developer Experience Security

- **Secret Scanning:** `gitleaks` / regex scanning enforces that no hardcoded credentials (API keys, DB passwords) exist in the source tree. Local environments rely on `.env.docker`.
- **Dependency Scanning:** The CI pipeline runs `pip-audit` to block any Python dependencies with known CVEs, and `npm audit` for the frontend.
- **Linting & Tests:** Static analysis (`ruff`, `eslint`) prevents use of dangerous functions (e.g. `eval`, `exec`). The test suite validates RBAC, rate-limiting, and refusal behavior on every PR.
