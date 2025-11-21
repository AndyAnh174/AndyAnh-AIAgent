# AI Life Companion - UI

Frontend interface for the AI Life Companion project, built with Next.js, TypeScript, and Tailwind CSS.

## Features

- 📝 **Journal Entries**: Create and manage journal entries with text, images, PDFs, and videos
- 🔍 **AI Query**: Query your journal using GraphRAG with natural language
- 🔔 **Reminders**: Set up proactive email reminders for important events
- ⚙️ **Settings**: Configure API connection and preferences

## Getting Started

### Prerequisites

- Node.js 18+ and pnpm (or npm/yarn)
- Backend API running (see `../AI/README.md`)

### Installation

1. Install dependencies:

```bash
pnpm install
```

2. Create a `.env.local` file (optional, defaults are provided):

```bash
cp .env.example .env.local
```

Edit `.env.local`:
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_APP_URL=http://localhost:3000
```

3. Run the development server:

```bash
pnpm dev
```

4. Open [http://localhost:3000](http://localhost:3000) in your browser

## Configuration

### API Setup

1. Go to **Settings** page (`/settings`)
2. Enter your API Base URL (default: `http://localhost:8000`)
3. Enter your API Key (configured in backend `.env` as `API_KEYS`)
4. Click "Save & Test Connection"

### API Key Configuration

In your backend `.env` file:
```env
API_KEYS=your-api-key-here
# Or multiple keys:
API_KEYS=key1,key2,key3
```

## Project Structure

```
ui/
├── src/
│   ├── app/              # Next.js app router pages
│   │   ├── page.tsx      # Dashboard
│   │   ├── journal/      # Journal entry creation
│   │   ├── query/        # AI query interface
│   │   ├── reminders/    # Reminder management
│   │   └── settings/     # Settings page
│   ├── components/
│   │   ├── sections/     # Page sections
│   │   └── ui/           # Reusable UI components
│   └── lib/
│       ├── api.ts        # API client
│       ├── config.tsx     # Configuration
│       ├── site.ts       # Site configuration
│       └── utils.ts      # Utility functions
├── .env.example          # Environment variables example
└── package.json
```

## Features Overview

### Dashboard (`/`)
- Overview of all features
- Connection status indicator
- Quick access to main features

### Journal (`/journal`)
- Create journal entries with:
  - Title and content
  - Mood and tags
  - Media files (images, videos, PDFs)
- Automatic content extraction via Ollama qwen2.5vl:7b

### Query (`/query`)
- Natural language queries
- GraphRAG-powered search
- Configurable parameters:
  - Top K results
  - Mode (graph/hybrid)
  - Model (Gemini/OpenAI)

### Reminders (`/reminders`)
- Create email reminders
- Recurring schedules:
  - Once
  - Daily
  - Weekly
  - Monthly
  - Yearly
- Link to journal entries

### Settings (`/settings`)
- Configure API connection
- Set API key
- Test connection

## Technology Stack

- **Framework**: Next.js 15 (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **UI Components**: shadcn/ui, Magic UI
- **Animations**: Motion (Framer Motion)
- **Icons**: Lucide React

## Development

### Build for Production

```bash
pnpm build
pnpm start
```

### Linting

```bash
pnpm lint
```

## API Integration

The UI communicates with the backend API via the API client (`src/lib/api.ts`). All requests require an API key configured in Settings.

### Endpoints Used

- `GET /health` - Health check
- `POST /journal` - Create journal entry
- `POST /retrieval` - Query journal with GraphRAG
- `POST /reminders` - Create reminder

See `../AI/docs/API.md` for full API documentation.

## License

See parent directory for license information.