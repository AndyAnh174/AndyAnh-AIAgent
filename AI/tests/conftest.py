import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

DEFAULT_ENV = {
    "API_KEYS": "test-key",
    "DATABASE_URL": "sqlite+aiosqlite:///./tests.db",
    "REDIS_URL": "redis://localhost:6379/0",
    "QDRANT_URL": "http://localhost:6333",
    "MINIO_ENDPOINT": "localhost:9000",
    "MINIO_ACCESS_KEY": "minio",
    "MINIO_SECRET_KEY": "minio",
    "MINIO_BUCKET": "ai-life-companion",
    "GMAIL_USERNAME": "user@example.com",
    "GMAIL_APP_PASSWORD": "app-password",
    "OLLAMA_BASE_URL": "http://localhost:11434",
    "SESSION_SECRET": "super-secret-value",
}

for key, value in DEFAULT_ENV.items():
    os.environ.setdefault(key, value)

