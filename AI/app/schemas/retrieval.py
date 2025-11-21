from typing import Literal

from pydantic import BaseModel, Field


class RetrievalQuery(BaseModel):
    query: str = Field(..., min_length=3)
    top_k: int = Field(5, ge=1, le=20)
    mode: str = Field("graph", description="graph or hybrid")
    model: Literal["gemini", "ollama"] | None = Field(
        default=None,
        description="Optional: Override LLM model for this query. If not provided, uses LLM_PROVIDER from config (only if API key is available)."
    )
    ollama_model: str | None = Field(
        default=None,
        description="Optional: Specific Ollama model name to use (e.g., 'qwen2.5:7b'). Only used when model='ollama'."
    )


class RetrievalResult(BaseModel):
    answer: str
    references: list[dict]

