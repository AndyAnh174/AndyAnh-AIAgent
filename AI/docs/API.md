# AI Life Companion API Documentation

## Overview

The AI Life Companion API is a self-hosted backend service for managing personal journal entries with AI-powered features including:
- **GraphRAG**: Knowledge graph-based retrieval and querying
- **Multimodal Processing**: Automatic content extraction from images, PDFs, and videos using Ollama qwen2.5vl:7b
- **Proactive Reminders**: Email-based reminder system
- **Long-lived Sessions**: Seamless user experience with Redis-backed sessions

## Base URL

```
http://localhost:8000
```

For production, replace with your server's domain/IP.

## Authentication

All API endpoints (except `/health`) require API key authentication via the `x-api-key` header.

### Headers

```
x-api-key: your-api-key-here
Content-Type: application/json
```

### Configuration

API keys are configured in the `.env` file:
```bash
API_KEYS=key1,key2,key3
```

Multiple keys can be specified, separated by commas.

---

## Endpoints

### Health Check

Check if the API is running and healthy.

**Endpoint:** `GET /health`

**Authentication:** Not required

**Response:**
```json
{
  "status": "ok"
}
```

**Example:**
```bash
curl http://localhost:8000/health
```

---

### Create Journal Entry

Create a new journal entry with optional media files (images, PDFs, videos).

**Endpoint:** `POST /journal`

**Authentication:** Required

**Request Body:**
```json
{
  "title": "string (required)",
  "content": "string (required)",
  "mood": "string (optional)",
  "tags": ["string"] (optional, default: []),
  "media": [
    {
      "type": "image" | "video" | "pdf",
      "url": "string (required)",
      "caption": "string (optional)"
    }
  ] (optional, default: [])
}
```

**Media URL Formats:**
- **Base64 Data URI**: `data:image/jpeg;base64,/9j/4AAQSkZJRg...`
- **HTTP/HTTPS URL**: `https://example.com/image.jpg`
- **Local File Path**: `/path/to/file.pdf` (relative to container)

**Response:**
```json
{
  "entry_id": 1,
  "created_at": "2025-11-21T00:00:00",
  "tags": ["tag1", "tag2"]
}
```

**Example - Text Only:**
```bash
curl -X POST http://localhost:8000/journal \
  -H "x-api-key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "My Day",
    "content": "Had a great day today!",
    "mood": "happy",
    "tags": ["daily", "positive"]
  }'
```

**Example - With Image (Base64):**
```bash
curl -X POST http://localhost:8000/journal \
  -H "x-api-key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Cat Photo",
    "content": "Took a photo of my cat",
    "tags": ["cat", "photo"],
    "media": [
      {
        "type": "image",
        "url": "data:image/jpeg;base64,/9j/4AAQSkZJRg...",
        "caption": "My cute cat"
      }
    ]
  }'
```

**Example - With Image (URL):**
```bash
curl -X POST http://localhost:8000/journal \
  -H "x-api-key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Online Image",
    "content": "Found this image online",
    "media": [
      {
        "type": "image",
        "url": "https://example.com/image.jpg",
        "caption": "Online image"
      }
    ]
  }'
```

**Example - With PDF:**
```bash
curl -X POST http://localhost:8000/journal \
  -H "x-api-key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
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
  }'
```

**Example - With Video:**
```bash
curl -X POST http://localhost:8000/journal \
  -H "x-api-key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Video Diary",
    "content": "Recorded my day",
    "tags": ["video", "daily"],
    "media": [
      {
        "type": "video",
        "url": "https://example.com/video.mp4",
        "caption": "Today activities"
      }
    ]
  }'
```

**Processing Notes:**
- Images, PDFs, and videos are automatically processed by **Ollama qwen2.5vl:7b**
- Extracted content is automatically added to the journal entry
- Processing happens asynchronously (wait 10-20 seconds for completion)
- Check logs for processing status: `docker logs ai_life_companion_api --tail 30`

---

### Retrieve Information (GraphRAG Query)

Query your journal entries using GraphRAG with Gemini or Ollama.

**Endpoint:** `POST /retrieval`

**Authentication:** Required

**Request Body:**
```json
{
  "query": "string (required, min 3 characters)",
  "top_k": 5 (optional, 1-20, default: 5),
  "mode": "graph" | "hybrid" (optional, default: "graph"),
  "model": "gemini" | "ollama" | null (optional, default: uses LLM_PROVIDER from config)
}
```

**Model Selection:**
- If `model` is not provided, uses `LLM_PROVIDER` from `.env` (default: `gemini`)
- `model: "gemini"` - Uses Gemini 2.0 Flash for text queries
- `model: "ollama"` - Uses Ollama models (e.g., llama3:8b) for text queries
- **Note:** Vision processing always uses Ollama qwen2.5vl:7b (not configurable)

**Response:**
```json
{
  "answer": "string",
  "references": [
    {
      "entry_id": 1,
      "tags": ["tag1"]
    }
  ]
}
```

**Example - Default Model:**
```bash
curl -X POST http://localhost:8000/retrieval \
  -H "x-api-key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What did I write about last week?",
    "top_k": 5
  }'
```

**Example - Explicit Gemini:**
```bash
curl -X POST http://localhost:8000/retrieval \
  -H "x-api-key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What animal is in my photos?",
    "top_k": 10,
    "model": "gemini"
  }'
```

**Example - Explicit Ollama:**
```bash
curl -X POST http://localhost:8000/retrieval \
  -H "x-api-key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Summarize my journal entries",
    "top_k": 5,
    "model": "ollama",
    "ollama_model": "llama3:8b"
  }'
```

**Notes:**
- Requires valid LLM API keys (Gemini) or Ollama server in `.env`
- GraphRAG indexing requires embeddings
- If embeddings are not configured, indexing may fail but vision processing still works

---

### Create Reminder

Create an email reminder that will be sent at a specified time.

**Endpoint:** `POST /reminders`

**Authentication:** Required

**Request Body:**
```json
{
  "entry_id": 1 (optional, must exist in journal_entries if provided),
  "email": "user@example.com (required)",
  "subject": "string (required)",
  "body": "string (required)",
  "cadence": "once" | "daily" | "weekly" | "monthly" | "yearly" (optional, default: "yearly"),
  "first_run_at": "2025-11-21T00:00:00 (required, UTC datetime)"
}
```

**Cadence Options:**
- `once` - Send once at `first_run_at`
- `daily` - Send every day at the same time
- `weekly` - Send every week on the same day/time
- `monthly` - Send every month on the same day/time
- `yearly` - Send every year on the same date/time

**Response:**
```json
{
  "reminder_id": 1,
  "next_run_at": "2025-11-21T00:00:00",
  "cadence": "daily"
}
```

**Example - One-time Reminder:**
```bash
curl -X POST http://localhost:8000/reminders \
  -H "x-api-key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "entry_id": 1,
    "email": "user@example.com",
    "subject": "Remember this",
    "body": "Don'\''t forget about this important thing!",
    "cadence": "once",
    "first_run_at": "2025-11-21T10:00:00"
  }'
```

**Example - Daily Reminder:**
```bash
curl -X POST http://localhost:8000/reminders \
  -H "x-api-key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "subject": "Daily Journal Reminder",
    "body": "Time to write your journal entry!",
    "cadence": "daily",
    "first_run_at": "2025-11-21T09:00:00"
  }'
```

**Example - Weekly Reminder:**
```bash
curl -X POST http://localhost:8000/reminders \
  -H "x-api-key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "subject": "Weekly Review",
    "body": "Time for your weekly review!",
    "cadence": "weekly",
    "first_run_at": "2025-11-24T18:00:00"
  }'
```

**Notes:**
- Reminders are processed by a background worker that runs every 60 seconds
- Email is sent via SMTP (Gmail) configured in `.env`
- `first_run_at` must be in UTC format
- If `entry_id` is provided, it must exist in the `journal_entries` table

---

## Error Responses

### 401 Unauthorized
```json
{
  "detail": "Invalid or missing API key"
}
```

**Cause:** Missing or invalid `x-api-key` header.

### 404 Not Found
```json
{
  "detail": "Not Found"
}
```

**Cause:** Invalid endpoint path.

### 422 Validation Error
```json
{
  "detail": [
    {
      "loc": ["body", "title"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

**Cause:** Invalid request body format or missing required fields.

### 500 Internal Server Error
```json
{
  "detail": "Internal server error"
}
```

**Cause:** Server-side error. Check logs: `docker logs ai_life_companion_api --tail 50`

---

## Architecture Notes

### Model Usage

1. **Text Queries (GraphRAG)**
   - **Gemini 2.0 Flash**: Used for chat and text retrieval queries
   - **Ollama**: Alternative option for text queries (e.g., llama3:8b)
   - Configured via `LLM_PROVIDER` in `.env` or `model` parameter in request

2. **Vision Processing (Multimodal)**
   - **Ollama qwen2.5vl:7b**: Always used for images, PDFs, and videos
   - Automatically processes all media files when uploaded
   - No model selection available - always uses qwen2.5vl:7b

### Processing Flow

1. **Journal Entry Creation:**
   ```
   User Request → API → IngestionService
   ├─ Save to Database
   ├─ Upload Media to Storage (Minio/local)
   ├─ Process Media with qwen2.5vl:7b (if present)
   ├─ Extract Content from Media
   ├─ Combine with Text Content
   └─ Index in GraphRAG (if embeddings configured)
   ```

2. **Retrieval Query:**
   ```
   User Query → API → RetrievalService
   ├─ Query GraphRAG Index
   ├─ Use Gemini/Ollama for Response
   └─ Return Answer + References
   ```

3. **Reminder Processing:**
   ```
   Background Worker (every 60s)
   ├─ Check for Due Reminders
   ├─ Send Email via SMTP
   └─ Update next_run_at
   ```

---

## Configuration

### Environment Variables

Required in `.env`:

```bash
# API Security
API_KEYS=key1,key2,key3
SESSION_SECRET=your-secret-key

# Database
DATABASE_URL=postgresql+asyncpg://user:password@postgres:5432/ai_life_db

# Redis (Sessions)
REDIS_URL=redis://redis:6379/0

# Storage
MINIO_ENDPOINT=minio:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET=ai-life-companion

# Vector DB
QDRANT_URL=http://qdrant:6333

# LLM Configuration
LLM_PROVIDER=gemini  # or "ollama"
GEMINI_API_KEY=your-gemini-key  # Required if using Gemini

# Vision Processing (Ollama)
OLLAMA_BASE_URL=http://222.253.80.30:11434
OLLAMA_VISION_MODEL=qwen2.5vl:7b

# Email (Reminders)
GMAIL_SMTP_HOST=smtp.gmail.com
GMAIL_SMTP_PORT=587
GMAIL_USERNAME=your-email@gmail.com
GMAIL_APP_PASSWORD=your-app-password
```

---

## Examples

### Complete Workflow

**1. Create a text journal entry:**
```bash
curl -X POST http://localhost:8000/journal \
  -H "x-api-key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Morning Thoughts",
    "content": "Today is a beautiful day. I feel energized and ready to tackle new challenges.",
    "mood": "energetic",
    "tags": ["morning", "positive"]
  }'
```

**2. Create an image journal entry:**
```bash
# First, convert image to base64 (PowerShell)
$imageBytes = [System.IO.File]::ReadAllBytes("image.jpg")
$imageBase64 = [System.Convert]::ToBase64String($imageBytes)
$dataUri = "data:image/jpeg;base64," + $imageBase64

# Then create entry
curl -X POST http://localhost:8000/journal \
  -H "x-api-key: your-api-key" \
  -H "Content-Type: application/json" \
  -d "{
    \"title\": \"Cat Photo\",
    \"content\": \"Took a photo of my cat\",
    \"tags\": [\"cat\", \"photo\"],
    \"media\": [{
      \"type\": \"image\",
      \"url\": \"$dataUri\",
      \"caption\": \"My cute cat\"
    }]
  }"
```

**3. Query your journal:**
```bash
curl -X POST http://localhost:8000/retrieval \
  -H "x-api-key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What did I write about today?",
    "top_k": 5,
    "model": "gemini"
  }'
```

**4. Create a reminder:**
```bash
curl -X POST http://localhost:8000/reminders \
  -H "x-api-key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "subject": "Daily Journal",
    "body": "Don'\''t forget to write your journal entry!",
    "cadence": "daily",
    "first_run_at": "2025-11-22T09:00:00"
  }'
```

---

## Rate Limits

Currently, there are no rate limits enforced. However, for production use, consider:
- Implementing rate limiting per API key
- Monitoring resource usage
- Setting appropriate timeouts

---

## Support

For issues, check:
1. Docker logs: `docker logs ai_life_companion_api --tail 50`
2. Worker logs: `docker logs ai_life_companion_worker --tail 50`
3. Service status: `docker ps`
4. Configuration: `.env` file

---

## Version

**API Version:** 1.0.0

**Last Updated:** 2025-11-21

