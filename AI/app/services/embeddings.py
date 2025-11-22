from __future__ import annotations

import logging
from typing import List

import httpx
from llama_index.core.embeddings import BaseEmbedding

logger = logging.getLogger(__name__)


class RemoteBGEM3Embedding(BaseEmbedding):
    """Embedding wrapper that calls external HTTP endpoint returning BGE-m3 vectors."""

    def __init__(self, endpoint: str, max_length: int = 512, timeout: float = 30.0, **kwargs) -> None:
        super().__init__(**kwargs)
        object.__setattr__(self, "endpoint", endpoint.rstrip("/"))
        object.__setattr__(self, "max_length", max_length)
        object.__setattr__(self, "timeout", timeout)
        object.__setattr__(self, "_client", httpx.Client(timeout=timeout))
        object.__setattr__(self, "_async_client", httpx.AsyncClient(timeout=timeout))

    def _fetch_embeddings(self, texts: List[str]) -> List[List[float]]:
        payload = {"texts": texts, "max_length": self.max_length}
        response = self._client.post(self.endpoint, json=payload)
        response.raise_for_status()
        data = response.json()
        embeddings = data.get("embeddings")
        if embeddings is None:
            raise ValueError("Remote embedding endpoint did not return 'embeddings'")
        return embeddings

    def _get_text_embedding(self, text: str) -> List[float]:
        return self._fetch_embeddings([text])[0]

    def _get_query_embedding(self, query: str) -> List[float]:
        return self._fetch_embeddings([query])[0]

    def _get_text_embeddings(self, texts: List[str]) -> List[List[float]]:
        return self._fetch_embeddings(texts)

    def _get_query_embeddings(self, queries: List[str]) -> List[List[float]]:
        return self._fetch_embeddings(queries)

    async def _afetch_embeddings(self, texts: List[str]) -> List[List[float]]:
        payload = {"texts": texts, "max_length": self.max_length}
        response = await self._async_client.post(self.endpoint, json=payload)
        response.raise_for_status()
        data = response.json()
        embeddings = data.get("embeddings")
        if embeddings is None:
            raise ValueError("Remote embedding endpoint did not return 'embeddings'")
        return embeddings

    async def _aget_text_embedding(self, text: str) -> List[float]:
        embeddings = await self._afetch_embeddings([text])
        return embeddings[0]

    async def _aget_query_embedding(self, query: str) -> List[float]:
        embeddings = await self._afetch_embeddings([query])
        return embeddings[0]

    async def _aget_text_embeddings(self, texts: List[str]) -> List[List[float]]:
        return await self._afetch_embeddings(texts)

    async def _aget_query_embeddings(self, queries: List[str]) -> List[List[float]]:
        return await self._afetch_embeddings(queries)

    def close(self) -> None:
        try:
            self._client.close()
        except Exception:  # pragma: no cover - best effort
            pass

    async def aclose(self) -> None:
        try:
            await self._async_client.aclose()
        except Exception:  # pragma: no cover - best effort
            pass

    def __del__(self) -> None:
        self.close()

