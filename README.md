# Domain Copilot — D2 (Insurance Claims Adjudication) + T7 (Async Jobs)

Agentic RAG platform for insurance claims adjudication. A fully deterministic, highly concurrent, AI-assisted claims processing system powered by Django, Celery, and a modern frontend.

## ⏱️ Prerequisites

- **Docker & Docker Compose** installed.
- **~15 minutes** of time (to pull models and build containers).
- *Nothing else required!* The entire stack (Postgres, Redis, LLMs, Backend, Frontend) runs in Docker.

## 🚀 Quick Start (One Command Setup)

To bring up the **entire system** (including frontend, backend, databases, redis, LLMs, and Celery workers) plus **automatically seed the database and ingest the corpus**, simply run:

```bash
cp backend/.env.example backend/.env
docker compose up -d --build
```

### What this command does:
1. Starts **Postgres** (with `pgvector`) and **Redis**.
2. Initializes **Ollama** and pulls the required local models (`llama3.2` and `nomic-embed-text`).
3. Starts the **Django backend** and **Celery worker**.
4. Runs a **setup container** that automatically executes `python manage.py seed_dev_data` and `python manage.py ingest_corpus`.
5. Starts the **Vite frontend** on `http://localhost:5173`.

> [!NOTE]
> The initial boot may take a few minutes as the Ollama container needs to download the AI models (~3GB). You can track progress with: `docker compose logs -f ollama-init`

---

## 🔑 Environment Variables

The system is configured via `backend/.env`. A template is provided at `backend/.env.example`.

| Variable | Description |
|---|---|
| `DJANGO_SECRET_KEY` | Secret key for Django cryptographic signing. |
| `DJANGO_DEBUG` | Set to `True` for development, `False` for production. |
| `ALLOWED_HOSTS` | Comma-separated list of allowed host/domain names. |
| `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT` | Postgres database connection settings. |
| `CELERY_BROKER_URL` | Redis URL for Celery task queuing. |
| `CORS_ALLOWED_ORIGINS` | Allowed origins for cross-origin requests (e.g., `http://localhost:5173`). |
| `LLM_PROVIDER` | The primary LLM provider (e.g., `ollama`, `openai`). |
| `LLM_FALLBACK_PROVIDER` | Fallback provider if the primary one fails. |
| `EMBEDDING_PROVIDER` | The provider for embeddings (e.g., `ollama`, `openai`). |
| `OLLAMA_MODEL` | Local LLM model to use (default: `llama3.2`). |
| `OLLAMA_EMBEDDING_MODEL` | Local embedding model (default: `nomic-embed-text`). |
| `OLLAMA_HOST` | Host address of the Ollama server. |
| `OPENAI_API_KEY` | Your OpenAI API Key (if using OpenAI). |
| `OPENAI_MODEL` | OpenAI model name (e.g., `gpt-4o`). |
| `OPENAI_EMBEDDING_MODEL` | OpenAI embedding model (e.g., `text-embedding-3-small`). |

### 🆓 How to Obtain Free API Keys
If you prefer not to run local models, you can use OpenAI.
1. Sign up at [platform.openai.com](https://platform.openai.com).
2. Generate a new secret key under "API Keys".
3. Update `backend/.env` with `OPENAI_API_KEY=your_key_here`, `LLM_PROVIDER=openai`, and `EMBEDDING_PROVIDER=openai`.

### 💻 Running with a Local Model (No API Key Required!)
By default, the `docker-compose.yml` configures everything to use **Ollama** locally. No API keys are needed!
The system automatically pulls `llama3.2` and `nomic-embed-text` on the first run.
Just ensure your `.env` has:
```env
LLM_PROVIDER=ollama
EMBEDDING_PROVIDER=ollama
```

---

## 🧪 Testing & Evaluation

### Running Unit & Integration Tests
To run the automated test suite (which uses fakes and mocks for fast execution and predictable outcomes):
```bash
docker compose exec django python manage.py test
```

### Running the Evaluation Harness
The system includes a "Golden Set" evaluation harness that tests the retrieval pipeline, prompt injection resistance, and out-of-corpus handling.
```bash
docker compose exec django python manage.py run_evaluation
```
This runs real embedding lookups against the ingested corpus and reports Hit Rates and Refusal Accuracy.

---

## 👥 Seeded Demo Accounts

The startup scripts automatically provision diverse demo data, including multiple policy types and a variety of claims. Use these accounts to explore the platform:

| Role | Username | Password |
|---|---|---|
| **Manager** | `demo_manager` | `DemoPass123!` |
| **Manager** | `mgr_sarah` | `DemoPass123!` |
| **Adjuster** | `demo_adjuster` | `DemoPass123!` |
| **Adjuster** | `adj_carlos` | `DemoPass123!` |
| **Adjuster** | `adj_priya` | `DemoPass123!` |
| **Adjuster** | `test_adjuster` | `DemoPass123!` |

---

## 🗺️ The 5-Minute Demo Path

Follow this numbered script to experience the core capabilities of Domain Copilot:

1. **Access the Application**: Open [http://localhost:5173](http://localhost:5173) in your browser.
2. **Manager Dashboard View**: Log in as `demo_manager` / `DemoPass123!`. Note the unified dashboard showing claims distribution, statuses, and adjuster workloads. Log out when done.
3. **Adjuster Workflow**: Log back in as `demo_adjuster` / `DemoPass123!`.
4. **Select a Claim**: From the dashboard, click on a claim with a "Submitted" status.
5. **Inspect the Policy**: You can view the policy document directly linked to the claim (date-aware policy resolution).
6. **Run Adjudication Pipeline**: Click the button to start the agentic pipeline.
7. **Real-time Streaming**: Watch the Server-Sent Events (SSE) power the UI, streaming live progress as the backend processes the task asynchronously via Celery.
8. **Coverage & Exclusions**: Observe the **Coverage Matcher Agent** confirm coverage, followed by the **Exclusion Analyst Agent** verifying no exclusions apply. Both use RAG with precise citations.
9. **Deterministic Payout**: Finally, notice that the **Calculate Payout** tool runs deterministically in Python to output the final dollar amount. The LLM is explicitly forbidden from generating financial figures directly!
10. **Review Results**: Read the final agent-generated explanation, backed by policy document citations.

🎥 **Demo and Teach Videos**: [Watch the walkthroughs and demonstrations here](https://drive.google.com/drive/folders/1f0uWILPgVsMI_j1lDymowBalPHAAiNQ1?usp=sharing)

---

## 🛠️ Troubleshooting

- **Containers failing to start?** Ensure ports `5433` (Postgres), `6380` (Redis), `8000` (Backend), and `5173` (Frontend) are not currently in use by other services on your machine.
- **Ollama models taking too long to pull?** If you have a slow internet connection, the `ollama-init` container might time out. You can manually pull the models by running:
  ```bash
  docker compose exec ollama ollama pull llama3.2
  docker compose exec ollama ollama pull nomic-embed-text
  ```
- **Blank database / missing users?** Ensure the `setup` container finished successfully. You can manually trigger the seed script with:
  ```bash
  docker compose exec django python manage.py seed_dev_data
  docker compose exec django python manage.py ingest_corpus
  ```
- **Celery workers not picking up tasks?** Restart the worker container:
  ```bash
  docker compose restart worker
  ```