from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from pathlib import Path
import os

from app.core.security import validate_api_key
from app.core.session import get_or_create_session
from app.db.session import get_session
from app.db.models.journal import MediaAsset
from app.services.storage import StorageService
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

router = APIRouter(dependencies=[Depends(validate_api_key)], prefix="/media", tags=["media"])


@router.get("/{media_id}", summary="Get media file by ID")
async def get_media(
    media_id: int,
    session: AsyncSession = Depends(get_session),
    session_id: str = Depends(get_or_create_session),
):
    """Download or stream media file by ID."""
    # Get media asset from database
    result = await session.execute(select(MediaAsset).where(MediaAsset.id == media_id))
    media = result.scalar_one_or_none()
    
    if not media:
        raise HTTPException(status_code=404, detail="Media not found")
    
    storage_path = media.storage_path
    
    # Check if file exists locally
    local_path = Path(storage_path)
    if local_path.exists() and local_path.is_file():
        return FileResponse(
            path=str(local_path),
            media_type=media.details.get("content_type", "application/octet-stream"),
            filename=Path(storage_path).name
        )
    
    # Try to get from temp download location
    temp_path = Path("data/temp") / Path(storage_path).name
    if temp_path.exists():
        return FileResponse(
            path=str(temp_path),
            media_type=media.details.get("content_type", "application/octet-stream"),
            filename=Path(storage_path).name
        )
    
    # Try to download from MinIO if available
    try:
        if StorageService._client:
            # Download to temp location
            await StorageService.download_file(storage_path, temp_path)
            if temp_path.exists():
                return FileResponse(
                    path=str(temp_path),
                    media_type=media.details.get("content_type", "application/octet-stream"),
                    filename=Path(storage_path).name
                )
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.warning("Failed to download from storage: %s", e)
    
    raise HTTPException(status_code=404, detail="Media file not found in storage")

