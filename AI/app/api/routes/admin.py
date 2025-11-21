import logging

from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete, select
from qdrant_client import QdrantClient

from app.core.security import validate_api_key
from app.core.session import get_or_create_session
from app.db.session import get_session
from app.db.models.journal import JournalEntry, MediaAsset
from app.services.graph import GraphRAGService
from app.core.config import get_settings

logger = logging.getLogger(__name__)

router = APIRouter(dependencies=[Depends(validate_api_key)], prefix="/admin", tags=["admin"])


@router.post("/clear", summary="Clear all journal entries and media")
async def clear_all_data(
    payload: dict = Body(..., description="Payload with confirm flag"),
    session: AsyncSession = Depends(get_session),
    session_id: str = Depends(get_or_create_session),
):
    """
    Clear all journal entries and media assets.
    Requires confirm=true to prevent accidental deletion.
    """
    confirm = payload.get("confirm", False)
    if not confirm:
        raise HTTPException(
            status_code=400,
            detail="Must set confirm=true to clear all data. This action cannot be undone."
        )
    
    try:
        # Delete media assets first (due to foreign key)
        await session.execute(delete(MediaAsset))
        
        # Delete journal entries
        await session.execute(delete(JournalEntry))
        
        await session.commit()
        
        # Clear Qdrant collection + reset GraphRAG
        try:
            settings = get_settings()
            qdrant_client = QdrantClient(url=str(settings.qdrant_url))
            if qdrant_client.collection_exists("journal_entries"):
                qdrant_client.delete_collection("journal_entries")
                logger.info("Deleted Qdrant collection 'journal_entries'")
            GraphRAGService.configure(settings)
        except Exception as e:
            # Log but don't fail if GraphRAG reset fails
            logger.warning("Failed to reset GraphRAG indices: %s", e)
        
        return {
            "status": "success",
            "message": "All journal entries and media have been cleared. GraphRAG indices reset."
        }
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to clear data: {str(e)}")


@router.get("/stats", summary="Get database statistics")
async def get_stats(
    session: AsyncSession = Depends(get_session),
    session_id: str = Depends(get_or_create_session),
):
    """Get statistics about journal entries and media."""
    # Count entries
    entries_result = await session.execute(select(JournalEntry))
    entries = entries_result.scalars().all()
    entry_count = len(entries)
    
    # Count media
    media_result = await session.execute(select(MediaAsset))
    media = media_result.scalars().all()
    media_count = len(media)
    
    # Count by type
    media_by_type = {}
    for m in media:
        media_by_type[m.asset_type] = media_by_type.get(m.asset_type, 0) + 1
    
    # Count entries with media
    entries_with_media = sum(1 for e in entries if e.media_assets)
    
    return {
        "total_entries": entry_count,
        "total_media": media_count,
        "entries_with_media": entries_with_media,
        "media_by_type": media_by_type
    }

