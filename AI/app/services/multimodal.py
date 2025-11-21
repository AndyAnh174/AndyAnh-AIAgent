"""Multimodal processing service for images, PDFs, and videos using Ollama qwen2.5vl:7b."""

import base64
import logging
from pathlib import Path

import httpx

from app.core.config import Settings

logger = logging.getLogger(__name__)


class MultimodalService:
    """Service for processing images, PDFs, and videos.
    
    NOTE: This service ALWAYS uses Ollama qwen2.5vl:7b for vision processing.
    No model selection is available - it automatically uses qwen2.5vl:7b for all media files.
    """

    def __init__(self, settings: Settings):
        self.settings = settings

    async def process_image(self, image_path: str | Path) -> str:
        """Process image and extract content using Ollama qwen2.5vl:7b.
        
        Automatically uses qwen2.5vl:7b - no model selection needed.
        """
        image_path = Path(image_path)
        if not image_path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")
        return await self._process_with_ollama_vision(image_path, media_type="image")

    async def process_pdf(self, pdf_path: str | Path) -> str:
        """Process PDF and extract content using Ollama qwen2.5vl:7b.
        
        Automatically uses qwen2.5vl:7b - no model selection needed.
        PDFs are converted to images first, then processed.
        """
        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")
        return await self._process_with_ollama_vision(pdf_path, media_type="pdf")

    async def process_video(self, video_path: str | Path) -> str:
        """Process video and extract content using Ollama qwen2.5vl:7b.
        
        Automatically uses qwen2.5vl:7b - no model selection needed.
        Videos are processed by extracting frames, then analyzing them.
        """
        video_path = Path(video_path)
        if not video_path.exists():
            raise FileNotFoundError(f"Video not found: {video_path}")
        return await self._process_with_ollama_vision(video_path, media_type="video")

    async def _process_with_ollama_vision(self, file_path: Path, media_type: str) -> str:
        """Process file with Ollama vision model (qwen2.5vl:7b) - supports images, PDFs, and videos."""
        try:
            images_base64 = []
            prompt = ""
            
            if media_type == "image":
                # For images, read directly
                with open(file_path, "rb") as f:
                    file_data = f.read()
                file_base64 = base64.b64encode(file_data).decode("utf-8")
                images_base64 = [file_base64]
                prompt = "Describe this image in detail. Include all text, objects, people, and context."
            
            elif media_type == "pdf":
                # For PDFs, convert to images first (qwen2.5vl works better with images)
                try:
                    from pdf2image import convert_from_path
                    images = convert_from_path(str(file_path))
                    if images:
                        # Process all pages (or first few pages for large PDFs)
                        import io
                        for img in images[:5]:  # Limit to first 5 pages
                            img_byte_arr = io.BytesIO()
                            img.save(img_byte_arr, format="PNG")
                            img_byte_arr.seek(0)
                            img_data = img_byte_arr.read()
                            img_base64 = base64.b64encode(img_data).decode("utf-8")
                            images_base64.append(img_base64)
                        prompt = "Extract and summarize the content of this PDF document. Describe what you see in each page."
                    else:
                        raise ValueError("Could not convert PDF to images")
                except ImportError:
                    logger.warning("pdf2image not installed. For PDF processing, install: pip install pdf2image")
                    # Fallback: read PDF as binary
                    with open(file_path, "rb") as f:
                        file_data = f.read()
                    file_base64 = base64.b64encode(file_data).decode("utf-8")
                    images_base64 = [file_base64]
                    prompt = "Extract and summarize the content of this PDF document."
            
            elif media_type == "video":
                # For videos, extract frames and process them
                try:
                    import cv2
                    cap = cv2.VideoCapture(str(file_path))
                    frame_count = 0
                    max_frames = 10  # Process up to 10 frames
                    
                    while cap.isOpened() and frame_count < max_frames:
                        ret, frame = cap.read()
                        if not ret:
                            break
                        
                        # Extract frame every 2 seconds (assuming ~30fps)
                        if frame_count % 60 == 0:
                            # Convert frame to base64
                            import io
                            from PIL import Image
                            img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                            img_byte_arr = io.BytesIO()
                            img.save(img_byte_arr, format="PNG")
                            img_byte_arr.seek(0)
                            img_data = img_byte_arr.read()
                            img_base64 = base64.b64encode(img_data).decode("utf-8")
                            images_base64.append(img_base64)
                        
                        frame_count += 1
                    
                    cap.release()
                    
                    if images_base64:
                        prompt = "Describe what you see in these video frames. Include actions, people, objects, text, and context. Summarize the overall content of the video."
                    else:
                        raise ValueError("Could not extract frames from video")
                except ImportError:
                    logger.warning("opencv-python not installed. For video processing, install: pip install opencv-python")
                    raise ValueError("Video processing requires opencv-python")
            
            if not images_base64:
                raise ValueError(f"Could not process {media_type} file: {file_path}")

            # Call Ollama API with all frames/images
            # Ensure URL doesn't have double slashes
            ollama_url = str(self.settings.ollama_base_url).rstrip('/')
            async with httpx.AsyncClient(timeout=300.0) as client:  # Longer timeout for videos
                response = await client.post(
                    f"{ollama_url}/api/generate",
                    json={
                        "model": self.settings.ollama_vision_model,
                        "prompt": prompt,
                        "images": images_base64,
                        "stream": False,
                    },
                )
                response.raise_for_status()
                result = response.json()
                return result.get("response", "No response from Ollama")

        except Exception as exc:
            logger.error("Failed to process %s with Ollama vision: %s", media_type, exc)
            raise


