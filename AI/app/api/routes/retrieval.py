from fastapi import APIRouter, Depends

from app.core.security import validate_api_key
from app.core.session import get_or_create_session
from app.schemas.retrieval import RetrievalQuery, RetrievalResult
from app.services.retrieval import RetrievalService

router = APIRouter(dependencies=[Depends(validate_api_key)])


@router.post("", response_model=RetrievalResult, summary="Retrieve memories via GraphRAG")
async def retrieve(payload: RetrievalQuery, session_id: str = Depends(get_or_create_session)):
    result = await RetrievalService.retrieve(payload)
    return RetrievalResult(answer=result["answer"], references=result["references"])

