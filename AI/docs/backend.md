# Backend Overview

## Services
- FastAPI app (`app/main.py`)
- Background reminder worker (`app/workers/reminder_worker.py`)
- PostgreSQL, Redis, Minio, Qdrant (docker-compose)

## Configuration
Copy `.env.example` to `.env` and adjust secrets (API keys, SMTP, DB URLs).

## Commands
- `uvicorn app.main:app --reload`
- `pytest tests`
- `docker compose up --build`

## API Highlights
- `/health` – service status
- `/journal` – ingest entries (requires `x-api-key`)
- `/retrieval` – GraphRAG answers
- `/reminders` – schedule proactive Gmail reminders

