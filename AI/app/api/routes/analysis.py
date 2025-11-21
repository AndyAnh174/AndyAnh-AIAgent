from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import validate_api_key
from app.core.session import get_or_create_session
from app.db.session import get_session
from app.services.analysis import AnalysisService

router = APIRouter(
    dependencies=[Depends(validate_api_key)],
    prefix="/analysis",
    tags=["analysis"],
)


@router.get("/summary", summary="Get human analysis summary")
async def get_analysis_summary(
    limit: int = Query(200, ge=10, le=1000),
    session: AsyncSession = Depends(get_session),
    session_id: str = Depends(get_or_create_session),
):
    service = AnalysisService(session)
    return await service.get_summary(limit=limit)

