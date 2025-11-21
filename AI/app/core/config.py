from functools import lru_cache
from typing import Literal, List, Union

from pydantic import AnyHttpUrl, EmailStr, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    environment: Literal["local", "dev", "prod"] = "local"
    debug: bool = False

    api_v1_prefix: str = "/api/v1"
    api_keys_raw: str = Field("dev-key", alias="API_KEYS", description="Comma separated API keys")
    session_secret: str = Field(default="change-me-change-me", min_length=12)
    session_ttl_seconds: int = 60 * 60 * 24 * 30  # 30 days

    database_url: str = Field("postgresql+asyncpg://user:password@localhost:5432/ai_life_db", alias="DATABASE_URL")
    redis_url: str = Field("redis://localhost:6379/0", alias="REDIS_URL")
    qdrant_url: AnyHttpUrl = Field("http://localhost:6333", alias="QDRANT_URL")
    minio_endpoint: str = Field("localhost:9000", alias="MINIO_ENDPOINT")
    minio_access_key: str = Field("minioadmin", alias="MINIO_ACCESS_KEY")
    minio_secret_key: str = Field("minioadmin", alias="MINIO_SECRET_KEY")
    minio_bucket: str = Field("ai-life-companion", alias="MINIO_BUCKET")

    gmail_smtp_host: str = Field("smtp.gmail.com", alias="GMAIL_SMTP_HOST")
    gmail_smtp_port: int = Field(587, alias="GMAIL_SMTP_PORT")
    gmail_username: EmailStr = Field("me@example.com", alias="GMAIL_USERNAME")
    gmail_app_password: str = Field("app-password", alias="GMAIL_APP_PASSWORD")

    ollama_base_url: AnyHttpUrl = Field("http://222.253.80.30:11434", alias="OLLAMA_BASE_URL")
    gemini_api_key: str | None = Field(default=None, alias="GEMINI_API_KEY")
    
    # LLM Provider for text queries (GraphRAG): "gemini" or "ollama"
    llm_provider: Literal["gemini", "ollama"] = Field("gemini", alias="LLM_PROVIDER")
    
    # Vision model: Always use Ollama qwen2.5vl:7b for images/PDFs/videos
    ollama_vision_model: str = Field("qwen2.5vl:7b", alias="OLLAMA_VISION_MODEL")

    embedding_model: str = "bge-m3"
    embedding_api_url: str | None = Field(default=None, alias="EMBEDDING_API_URL", description="Optional HTTP endpoint that returns embeddings for texts payload")
    analysis_cache_ttl: int = Field(3600, alias="ANALYSIS_CACHE_TTL", description="Seconds to cache human analysis summary")
    graph_index_path: str = "data/graph_index"
    
    # CORS configuration (can be comma-separated string or list)
    cors_origins: Union[str, List[str]] = Field(
        default="http://localhost:3000,http://localhost:3001,http://127.0.0.1:3000",
        alias="CORS_ORIGINS",
        description="Comma-separated list of allowed CORS origins"
    )

    @property
    def normalized_api_keys(self) -> set[str]:
        return {key.strip() for key in self.api_keys_raw.split(",") if key.strip()}
    
    @property
    def normalized_cors_origins(self) -> List[str]:
        """Parse CORS origins from comma-separated string or list."""
        if isinstance(self.cors_origins, str):
            return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]
        return self.cors_origins


@lru_cache(1)
def get_settings() -> Settings:
    return Settings()

