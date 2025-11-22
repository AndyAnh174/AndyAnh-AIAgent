from datetime import datetime, date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.security import validate_api_key
from app.core.session import get_or_create_session
from app.db.models.journal import JournalEntry, MediaAsset
from app.db.session import get_session
from app.schemas.journal import (
    JournalEntryDetail,
    JournalEntryRequest,
    JournalEntryResponse,
    JournalEntrySummary,
    JournalEntryUpdate,
    MediaInfo,
)
from app.services.ingestion import IngestionService

router = APIRouter(dependencies=[Depends(validate_api_key)])


@router.post(
    "",
    response_model=JournalEntryResponse,
    summary="Ingest journal entry",
)
async def create_entry(
    payload: JournalEntryRequest,
    session: AsyncSession = Depends(get_session),
    session_id: str = Depends(get_or_create_session),
):
    """Create a new journal entry via ingestion pipeline."""
    service = IngestionService(session)
    entry = await service.ingest_entry(payload)
    return JournalEntryResponse(entry_id=entry.id, created_at=entry.created_at, tags=entry.tags)


@router.get(
    "",
    response_model=list[JournalEntrySummary],
    summary="List journal entries",
)
async def list_entries(
    limit: int | None = Query(None, ge=1, description="Number of entries to return (None = no limit)"),
    offset: int = Query(0, ge=0),
    sort_by: str = Query("created_at", description="Sort by: 'title' or 'created_at'"),
    sort_order: str = Query("desc", description="Sort order: 'asc' or 'desc'"),
    date_from: str | None = Query(None, description="Filter from date (YYYY-MM-DD)"),
    date_to: str | None = Query(None, description="Filter to date (YYYY-MM-DD)"),
    session: AsyncSession = Depends(get_session),
    session_id: str = Depends(get_or_create_session),
):
    """Return a list of journal entries with media counts. Supports sorting and optional pagination."""
    # Validate sort_by
    if sort_by not in ["title", "created_at"]:
        raise HTTPException(status_code=400, detail="sort_by must be 'title' or 'created_at'")
    
    # Validate sort_order
    if sort_order not in ["asc", "desc"]:
        raise HTTPException(status_code=400, detail="sort_order must be 'asc' or 'desc'")
    
    # Build order_by clause
    if sort_by == "title":
        order_column = JournalEntry.title
    else:  # created_at
        order_column = JournalEntry.created_at
    
    if sort_order == "desc":
        order_clause = order_column.desc()
    else:
        order_clause = order_column.asc()
    
    stmt = (
        select(JournalEntry)
        .options(
            selectinload(JournalEntry.media_assets),
            selectinload(JournalEntry.analysis_notes)
        )
    )
    
    # Apply date filters
    if date_from:
        try:
            from_date = datetime.strptime(date_from, "%Y-%m-%d").date()
            stmt = stmt.where(JournalEntry.created_at >= datetime.combine(from_date, datetime.min.time()))
        except ValueError:
            raise HTTPException(status_code=400, detail="date_from must be in YYYY-MM-DD format")
    
    if date_to:
        try:
            to_date = datetime.strptime(date_to, "%Y-%m-%d").date()
            stmt = stmt.where(JournalEntry.created_at <= datetime.combine(to_date, datetime.max.time()))
        except ValueError:
            raise HTTPException(status_code=400, detail="date_to must be in YYYY-MM-DD format")
    
    stmt = stmt.order_by(order_clause).offset(offset)
    
    # Only apply limit if specified
    if limit is not None:
        stmt = stmt.limit(limit)
    result = await session.execute(stmt)
    entries: list[JournalEntry] = result.scalars().all()

    summaries: list[JournalEntrySummary] = []
    for entry in entries:
        summaries.append(
            JournalEntrySummary(
                entry_id=entry.id,
                title=entry.title,
                mood=entry.mood,
                tags=entry.tags,
                created_at=entry.created_at,
                media_count=len(entry.media_assets or []),
            )
        )

    return summaries


@router.get(
    "/{entry_id}",
    response_model=JournalEntryDetail,
    summary="Get journal entry details",
)
async def get_entry(
    entry_id: int,
    session: AsyncSession = Depends(get_session),
    session_id: str = Depends(get_or_create_session),
):
    """Get a single journal entry with full content and media info."""
    stmt = (
        select(JournalEntry)
        .where(JournalEntry.id == entry_id)
        .options(selectinload(JournalEntry.media_assets))
    )
    result = await session.execute(stmt)
    entry: JournalEntry | None = result.scalar_one_or_none()

    if entry is None:
        raise HTTPException(status_code=404, detail="Journal entry not found")

    media_items: list[MediaInfo] = []
    for media in entry.media_assets or []:
        media_items.append(
            MediaInfo(
                id=media.id,
                type=media.asset_type,
                url=f"/api/media/{media.id}",
                storage_path=media.storage_path,
                details=media.details or {},
            )
        )

    return JournalEntryDetail(
        entry_id=entry.id,
        title=entry.title,
        content=entry.content,
        mood=entry.mood,
        tags=entry.tags,
        created_at=entry.created_at,
        updated_at=entry.updated_at,
        media=media_items,
    )


@router.put(
    "/{entry_id}",
    response_model=JournalEntryDetail,
    summary="Update a journal entry",
)
async def update_entry(
    entry_id: int,
    payload: JournalEntryUpdate,
    session: AsyncSession = Depends(get_session),
    session_id: str = Depends(get_or_create_session),
):
    """Update basic fields of a journal entry (title, content, mood, tags)."""
    stmt = (
        select(JournalEntry)
        .where(JournalEntry.id == entry_id)
        .options(
            selectinload(JournalEntry.media_assets),
            selectinload(JournalEntry.analysis_notes)
        )
    )
    result = await session.execute(stmt)
    entry: JournalEntry | None = result.scalar_one_or_none()

    if entry is None:
        raise HTTPException(status_code=404, detail="Journal entry not found")

    if payload.title is not None:
        entry.title = payload.title
    if payload.content is not None:
        entry.content = payload.content
    if payload.mood is not None:
        entry.mood = payload.mood
    if payload.tags is not None:
        entry.tags = payload.tags

    # Updated_at will be handled by DB default/trigger if configured; otherwise set here
    if hasattr(entry, "updated_at"):
        entry.updated_at = datetime.utcnow()

    await session.flush()

    media_items: list[MediaInfo] = []
    for media in entry.media_assets or []:
        media_items.append(
            MediaInfo(
                id=media.id,
                type=media.asset_type,
                url=f"/api/media/{media.id}",
                storage_path=media.storage_path,
                details=media.details or {},
            )
        )

    return JournalEntryDetail(
        entry_id=entry.id,
        title=entry.title,
        content=entry.content,
        mood=entry.mood,
        tags=entry.tags,
        created_at=entry.created_at,
        updated_at=entry.updated_at,
        media=media_items,
    )


@router.delete(
    "/{entry_id}",
    status_code=204,
    summary="Delete a journal entry",
)
async def delete_entry(
    entry_id: int,
    session: AsyncSession = Depends(get_session),
    session_id: str = Depends(get_or_create_session),
):
    """Delete a journal entry and its media/reminders safely."""
    # Load entry with related media and reminders
    stmt = (
        select(JournalEntry)
        .where(JournalEntry.id == entry_id)
        .options(
            selectinload(JournalEntry.media_assets),
            selectinload(JournalEntry.reminders),
            selectinload(JournalEntry.analysis_notes)
        )
    )
    result = await session.execute(stmt)
    entry: JournalEntry | None = result.scalar_one_or_none()

    if entry is None:
        raise HTTPException(status_code=404, detail="Journal entry not found")

    # Explicitly delete media assets (even though FK has CASCADE)
    for media in list(entry.media_assets or []):
        await session.delete(media)

    # Detach reminders by nulling entry_id to avoid FK issues
    for reminder in list(entry.reminders or []):
        # Some DBs may not honor ON DELETE SET NULL as expected in async context,
        # so we proactively clear the reference.
        reminder.entry_id = None

    # Finally delete the journal entry itself
    await session.delete(entry)

    return None