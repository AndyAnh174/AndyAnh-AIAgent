from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.db.models.journal import JournalEntry, MediaAsset
from app.schemas.journal import JournalEntryRequest
from app.services.graph import GraphRAGService
from app.services.multimodal import MultimodalService
from app.services.storage import StorageService

logger = logging.getLogger(__name__)


class IngestionService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.settings = get_settings()
        self.multimodal_service = MultimodalService(self.settings)

    async def ingest_entry(self, payload: JournalEntryRequest) -> JournalEntry:
        logger.info("Ingesting journal entry '%s'", payload.title)
        
        # Process media files (images/PDFs) and extract content
        media_content = []
        media_assets = []
        
        for media in payload.media:
            try:
                storage_path = await self._persist_media(media)
                
                # Process with vision model if it's an image, PDF, or video
                extracted_content = None
                if media.type in ["image", "pdf", "video"]:
                    try:
                        # Get local path for processing
                        local_path = await self._get_local_path(storage_path)
                        if media.type == "image":
                            extracted_content = await self.multimodal_service.process_image(local_path)
                        elif media.type == "pdf":
                            extracted_content = await self.multimodal_service.process_pdf(local_path)
                        elif media.type == "video":
                            extracted_content = await self.multimodal_service.process_video(local_path)
                        logger.info("Extracted content from %s: %s", media.type, extracted_content[:100] if extracted_content else "None")
                    except Exception as exc:
                        logger.warning("Failed to extract content from %s: %s", media.type, exc)
                
                # Store asset info for later
                media_assets.append({
                    "asset_type": media.type,
                    "storage_path": storage_path,
                    "caption": media.caption,
                    "extracted_content": extracted_content,
                })
                
                # Add extracted content to entry content
                if extracted_content:
                    media_content.append(f"[{media.type.upper()}]: {extracted_content}")
            except Exception as exc:
                logger.error("Failed to process media: %s", exc)

        # Combine original content with extracted media content
        full_content = payload.content
        if media_content:
            full_content += "\n\n" + "\n".join(media_content)

        entry = JournalEntry(
            title=payload.title,
            content=full_content,
            mood=payload.mood,
            sentiment_score=None,
            tags=payload.tags,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        self.session.add(entry)
        await self.session.flush()

        # Now create media assets with entry_id
        for asset_info in media_assets:
            asset = MediaAsset(
                entry_id=entry.id,
                asset_type=asset_info["asset_type"],
                storage_path=asset_info["storage_path"],
                details={
                    "caption": asset_info["caption"],
                    "extracted_content": asset_info["extracted_content"],
                },
            )
            self.session.add(asset)

        await GraphRAGService.index_entry(entry)

        return entry

    async def _get_local_path(self, storage_path: str) -> Path:
        """Get local file path from storage path."""
        # Check if it's already a local path
        local_path = Path(storage_path)
        if local_path.exists():
            return local_path
        
        # Try data/uploads
        uploads_path = Path("data/uploads") / Path(storage_path).name
        if uploads_path.exists():
            return uploads_path
        
        # Try data/local
        local_storage_path = Path("data/local") / storage_path
        if local_storage_path.exists():
            return local_storage_path
        
        # Download from Minio if available
        try:
            download_path = Path("data/temp") / Path(storage_path).name
            return await StorageService.download_file(storage_path, download_path)
        except Exception:
            # Fallback: return the original path and hope it exists
            return local_path

    async def _persist_media(self, media_payload) -> str:
        """Persist media file from URL or base64 data."""
        uploads_dir = Path("data/uploads")
        uploads_dir.mkdir(parents=True, exist_ok=True)
        
        file_ext = ""
        if media_payload.type == "image":
            file_ext = ".jpg"  # Default, can be detected from URL or data
        elif media_payload.type == "pdf":
            file_ext = ".pdf"
        elif media_payload.type == "video":
            file_ext = ".mp4"
        
        temp_file = uploads_dir / f"{uuid4()}{file_ext}"
        
        # Check if URL is base64 data
        if media_payload.url.startswith("data:"):
            # Base64 encoded data
            import base64
            header, encoded = media_payload.url.split(",", 1)
            file_data = base64.b64decode(encoded)
            temp_file.write_bytes(file_data)
        elif media_payload.url.startswith("http://") or media_payload.url.startswith("https://"):
            # Download from URL
            import httpx
            async with httpx.AsyncClient() as client:
                response = await client.get(media_payload.url)
                response.raise_for_status()
                temp_file.write_bytes(response.content)
        else:
            # Assume it's a local file path
            source_path = Path(media_payload.url)
            if source_path.exists():
                temp_file.write_bytes(source_path.read_bytes())
            else:
                # Fallback: treat as text (for backward compatibility)
                temp_file.write_text(media_payload.url)
        
        object_name = f"media/{uuid4()}{file_ext}"
        path = StorageService.upload_file(temp_file, object_name)
        temp_file.unlink(missing_ok=True)
        return path

