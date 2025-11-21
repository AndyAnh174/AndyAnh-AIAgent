from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from sqlalchemy.orm import selectinload

from app.core.security import validate_api_key
from app.core.session import get_or_create_session
from app.db.session import get_session
from app.db.models.journal import JournalEntry, MediaAsset

router = APIRouter(dependencies=[Depends(validate_api_key)])


@router.get("/search", summary="Search journal entries with optional media filter")
async def search_entries(
    query: str = Query(..., min_length=1, description="Search query"),
    has_media: bool | None = Query(None, description="Filter entries with media"),
    media_type: str | None = Query(None, description="Filter by media type: image, video, pdf"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of results"),
    session: AsyncSession = Depends(get_session),
    session_id: str = Depends(get_or_create_session),
):
    """Search journal entries. Can filter by media presence and type."""
    # Build query
    stmt = select(JournalEntry).options(selectinload(JournalEntry.media_assets))
    
    # Text search in title and content
    search_filter = or_(
        JournalEntry.title.ilike(f"%{query}%"),
        JournalEntry.content.ilike(f"%{query}%")
    )
    stmt = stmt.where(search_filter)
    
    # Filter by media presence
    if has_media is not None:
        if has_media:
            # Only entries with media
            stmt = stmt.join(MediaAsset).distinct()
            if media_type:
                stmt = stmt.where(MediaAsset.asset_type == media_type)
        else:
            # Only entries without media
            stmt = stmt.outerjoin(MediaAsset).where(MediaAsset.id.is_(None))
    
    # Order by created_at desc and limit
    stmt = stmt.order_by(JournalEntry.created_at.desc()).limit(limit)
    
    result = await session.execute(stmt)
    entries = result.scalars().all()
    
    # Format response
    results = []
    for entry in entries:
        media_urls = []
        for media in entry.media_assets:
            # Build media URL
            media_url = f"/api/media/{media.id}"
            media_urls.append({
                "id": media.id,
                "type": media.asset_type,
                "url": media_url,
                "storage_path": media.storage_path,
                "details": media.details
            })
        
        results.append({
            "entry_id": entry.id,
            "title": entry.title,
            "content": entry.content[:200] + "..." if len(entry.content) > 200 else entry.content,
            "mood": entry.mood,
            "tags": entry.tags,
            "created_at": entry.created_at.isoformat(),
            "media": media_urls
        })
    
    return {
        "query": query,
        "count": len(results),
        "results": results
    }

