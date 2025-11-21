# Multimodal Support Setup

## Overview

The AI Life Companion backend supports processing images, PDFs, and videos using **Ollama qwen2.5vl:7b** for vision processing, while using **Gemini** or **Ollama** for text queries (GraphRAG).

## Architecture

- **Text Queries (GraphRAG)**: 
  - Default: Uses `LLM_PROVIDER` from config (Gemini or Ollama)
  - **Optional**: Can override model per-request via `model` parameter in API
- **Vision Processing**: 
  - **Always automatically uses Ollama qwen2.5vl:7b** for images, PDFs, and videos
  - No model selection needed - system automatically detects and processes media files

## Configuration

### Environment Variables

Add these to your `.env` file:

```bash
# LLM Provider for text queries (GraphRAG): "gemini" or "ollama"
LLM_PROVIDER=gemini

# Ollama Configuration for Vision Processing (images/PDFs/videos)
OLLAMA_BASE_URL=http://222.253.80.30:11434
OLLAMA_VISION_MODEL=qwen2.5vl:7b

# API Keys (set based on LLM_PROVIDER)
GEMINI_API_KEY=your_gemini_key  # Required if LLM_PROVIDER=gemini
```

## Supported Models

### Text Processing (GraphRAG Queries)
- **Gemini**: `gemini-2.5-flash` - Used for chat and text retrieval
- **Ollama**: Text models (e.g., `llama3:8b`) - Used for chat and text retrieval
- **Requirements**: Set `LLM_PROVIDER` and corresponding API key (Gemini) or Ollama server URL

### Vision Processing (Images/PDFs/Videos)
- **Ollama qwen2.5vl:7b**: Always used for all vision processing
  - Images: Direct processing
  - PDFs: Converted to images first, then processed
  - Videos: Frames extracted and processed
- **Requirements**: Ollama server must be running and accessible at `OLLAMA_BASE_URL`

## How It Works

1. **Journal Entry Creation**: When you create a journal entry with media (images/PDFs/videos), the system:
   - Uploads the media file to storage (Minio or local)
   - Processes the media with **Ollama qwen2.5vl:7b** vision model
   - Extracts text/content from images, PDFs, and videos
   - Adds the extracted content to the journal entry
   - Indexes the combined content in GraphRAG using **Gemini** or **Ollama**

2. **Media Processing** (Always uses Ollama qwen2.5vl:7b):
   - **Images**: Directly processed by qwen2.5vl:7b
   - **PDFs**: Converted to images first (using pdf2image), then processed by qwen2.5vl:7b
   - **Videos**: Frames extracted (using OpenCV), then processed by qwen2.5vl:7b

3. **Text Queries** (Uses Gemini or Ollama):
   - GraphRAG queries use the configured `LLM_PROVIDER` (Gemini or Ollama)
   - Chat/retrieval responses use the text LLM, not vision models

## API Usage

### Creating Journal Entry with Image

```json
{
  "title": "My Day",
  "content": "Had a great day!",
  "mood": "happy",
  "tags": ["daily"],
  "media": [
    {
      "type": "image",
      "url": "data:image/jpeg;base64,/9j/4AAQSkZJRg...",
      "caption": "Photo from today"
    }
  ]
}
```

**Note**: Image will be automatically processed using qwen2.5vl:7b - no configuration needed.

### Chat/Retrieval with Model Selection

```json
{
  "query": "What did I do last week?",
  "top_k": 5,
  "model": "gemini"  // Optional: "gemini" or "ollama". If omitted, uses LLM_PROVIDER from config
}
```

### Creating Journal Entry with PDF

```json
{
  "title": "Meeting Notes",
  "content": "Important meeting today",
  "tags": ["work", "meeting"],
  "media": [
    {
      "type": "pdf",
      "url": "https://example.com/document.pdf",
      "caption": "Meeting agenda"
    }
  ]
}
```

### Creating Journal Entry with Video

```json
{
  "title": "Video Diary",
  "content": "Recorded my day",
  "tags": ["video", "daily"],
  "media": [
    {
      "type": "video",
      "url": "https://example.com/video.mp4",
      "caption": "Today's activities"
    }
  ]
}
```

## Media URL Formats

The `url` field in media objects supports:

1. **Base64 Data URI**: `data:image/jpeg;base64,/9j/4AAQSkZJRg...`
2. **HTTP/HTTPS URL**: `https://example.com/image.jpg`
3. **Local File Path**: `/path/to/local/file.pdf` (relative to container)

## Notes

- **Vision Processing**: Always uses Ollama qwen2.5vl:7b, regardless of `LLM_PROVIDER` setting
- **Text Processing**: Uses Gemini or Ollama based on `LLM_PROVIDER` setting
- **PDF Processing**: Requires `pdf2image` library and `poppler-utils` system package (already included in Dockerfile)
- **Video Processing**: Requires `opencv-python` library (already included in requirements.txt)
- **Large Files**: 
  - Large PDFs: Processed page by page (first 5 pages)
  - Videos: Up to 10 frames extracted and processed
- **Extracted Content**: The extracted content from images/PDFs/videos is automatically added to the journal entry content and indexed in GraphRAG using the text LLM (Gemini/Ollama)

## Testing

To test multimodal processing:

1. Set `LLM_PROVIDER=gemini` or `LLM_PROVIDER=ollama` in `.env`
2. Ensure `OLLAMA_BASE_URL` points to your Ollama server with qwen2.5vl:7b model
3. Ensure the corresponding text LLM API key is configured (Gemini) or Ollama server is accessible
4. Create a journal entry with an image, PDF, or video
5. Check the logs to see extracted content from qwen2.5vl:7b
6. Query the retrieval endpoint to verify the content was indexed (uses Gemini/Ollama for text queries)

