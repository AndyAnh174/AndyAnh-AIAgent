import os

from fastapi.testclient import TestClient

os.environ["API_KEYS"] = "test-key"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./tests.db"
os.environ["REDIS_URL"] = "redis://localhost:6379/0"
os.environ["QDRANT_URL"] = "http://localhost:6333"
os.environ["MINIO_ENDPOINT"] = "localhost:9000"
os.environ["MINIO_ACCESS_KEY"] = "minio"
os.environ["MINIO_SECRET_KEY"] = "minio"
os.environ["MINIO_BUCKET"] = "ai-life-companion"
os.environ["GMAIL_USERNAME"] = "user@example.com"
os.environ["GMAIL_APP_PASSWORD"] = "app-password"
os.environ["OLLAMA_BASE_URL"] = "http://localhost:11434"
os.environ["SESSION_SECRET"] = "super-secret-value"
os.environ["GMAIL_SMTP_HOST"] = "smtp.gmail.com"
os.environ["GMAIL_SMTP_PORT"] = "587"
os.environ["GRAPH_INDEX_PATH"] = "data/graph_index"

from app.main import create_app  # noqa: E402


def test_api_key_required(monkeypatch):
    client = TestClient(create_app())
    response = client.post("/journal", json={"title": "Test", "content": "hello"})
    assert response.status_code == 401

