# Domain Copilot — D2 (Insurance Claims Adjudication) + T7 (Async Jobs)

Agentic RAG platform for insurance claims adjudication. See `docs/` for BRD, system design, and architecture.

## Quick Start (One Command Setup)

To bring up the **entire system** (including frontend, backend, databases, redis, LLMs, and Celery workers) plus **automatically seed the database and ingest the corpus**, simply run:

```bash
docker compose up -d --build
```

### What this command does:
1. Starts the **Postgres** and **Redis** databases.
2. Initializes **Ollama** and pulls the required models (`llama3.2` and `nomic-embed-text`).
3. Starts the **Django backend** and **Celery worker**.
4. Runs a **setup container** that automatically executes `python manage.py seed_dev_data` and `python manage.py ingest_corpus`.
5. Starts the **Vite frontend** on `http://localhost:5173`.