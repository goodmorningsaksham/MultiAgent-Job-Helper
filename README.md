# RecruitAI — AI Recruiting Agent Platform

Multi-agent AI platform for company research and recruiting intelligence.

## Architecture

```
Frontend (Next.js 14) → FastAPI Backend → LangGraph Orchestrator
                                              ├── Research Agent (Tavily search)
                                              ├── People Agent (key contacts)
                                              ├── Synthesis Agent (company profile)
                                              ├── Writer Agent (emails/DMs)
                                              ├── Evaluator Agent (quality scores)
                                              └── Chat Agent (RAG Q&A)
```

## Quick Start

### Prerequisites
- Python 3.12+
- Node.js 20+
- Docker & Docker Compose (for PostgreSQL + Redis)

### 1. Start Infrastructure

```bash
docker-compose up db redis -d
```

### 2. Backend Setup

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Create .env from template
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY and TAVILY_API_KEY

# Run migrations
alembic upgrade head

# Start server
uvicorn app.main:app --reload --port 8000
```

### 3. Frontend Setup

```bash
cd frontend
npm install

# Create .env.local
cp .env.local.example .env.local

# Start dev server
npm run dev
```

Open http://localhost:3000

## Environment Variables

### Backend (.env)
| Variable | Required | Description |
|----------|----------|-------------|
| `GEMINI_API_KEY` | Yes | Google Gemini API key |
| `TAVILY_API_KEY` | Yes | Tavily search API key |
| `DATABASE_URL` | Yes | PostgreSQL connection string |
| `REDIS_URL` | No | Redis URL (defaults to localhost) |
| `SEARCH_PROVIDER` | No | `tavily` or `duckduckgo` |

### Frontend (.env.local)
| Variable | Required | Description |
|----------|----------|-------------|
| `NEXT_PUBLIC_API_URL` | Yes | Backend API URL |

## Deployment

### Vercel (Frontend)
1. Connect repo to Vercel
2. Set root directory to `frontend`
3. Add `NEXT_PUBLIC_API_URL` env var pointing to Railway backend

### Railway (Backend)
1. Connect repo to Railway
2. Add PostgreSQL plugin (enables pgvector)
3. Add Redis plugin
4. Set environment variables (Gemini key, Tavily key)
5. Deploy will auto-run migrations

## API Documentation

Once running: http://localhost:8000/api/docs

## Tech Stack

- **Backend**: FastAPI, LangChain, LangGraph, SQLAlchemy, pgvector
- **Frontend**: Next.js 14, TypeScript, Tailwind CSS, Zustand
- **AI**: Gemini 2.0 Flash, Tavily Search
- **Database**: PostgreSQL + pgvector
- **Deployment**: Vercel + Railway
