from app.schemas.retrieval import RetrievalQuery
from app.services.graph import GraphRAGService


class RetrievalService:
    @staticmethod
    async def retrieve(payload: RetrievalQuery) -> dict:
        # Pass model override if provided
        result = await GraphRAGService.query(
            payload.query, 
            top_k=payload.top_k,
            model_override=payload.model,
            ollama_model=payload.ollama_model
        )
        return result

