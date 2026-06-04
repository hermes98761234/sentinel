# Sentinel — Web Automation & Intelligence Platform

Sentinel is an autonomous web agent platform that exposes four powerful APIs — **Navigator**, **Browsing**, **Research**, and **Scouting** — to automate browser tasks, run deep research jobs, and continuously monitor topics of interest.

## Features

- 🧭 **Navigator** — Chat completions proxy to OpenRouter with tool-use support
- 🌐 **Browsing** — Submit URL-based browsing tasks, track execution, retrieve step-by-step trajectories
- 🔬 **Research** — Create deep-research jobs with structured output and view URLs
- 🔭 **Scouting** — Recurring monitoring agents with pause/resume/restart lifecycle, paginated updates, and email notifications
- 🔑 **Authentication** — Simple API key auth via `X-API-Key` or `Authorization: Bearer` headers
- 📊 **Usage** — Query active scouts, rate limits, and activity counters
- ⚡ **Async Workers** — Celery + Redis for background task processing
- 🐳 **Docker Ready** — One-command startup with Docker Compose

## Tech Stack

| Component | Technology |
|-----------|------------|
| Language | Python 3.12+ |
| Framework | FastAPI |
| Database | PostgreSQL (async via SQLAlchemy + asyncpg) |
| Cache / Broker | Redis |
| Task Queue | Celery |
| Browser Automation | Playwright |
| LLM Proxy | OpenRouter |
| Migrations | Alembic |
| Testing | pytest + pytest-asyncio |

## Quick Start

```bash
cp .env.example .env
# Edit .env and set OPENROUTER_API_KEY
docker compose up --build
```

The API will be available at `http://localhost:8000`.

## Authentication

All endpoints (except `/v1/health`) require an API key. Send it in one of two ways:

| Header | Example |
|--------|---------|
| `X-API-Key` | `X-API-Key: your-api-key-here` |
| `Authorization` | `Authorization: Bearer your-api-key-here` |

The Navigator API (`/v1/chat/completions`) requires the `Authorization: Bearer` header specifically. All other endpoints accept either header.

## API Overview

### Health

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/v1/health` | Service health check (no auth required) |

### Navigator

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/v1/chat/completions` | OpenRouter chat completions proxy |

### Browsing

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/v1/browsing/tasks` | Create a browsing task |
| `GET` | `/v1/browsing/tasks/{task_id}` | Get task status and result |
| `GET` | `/v1/browsing/tasks/{task_id}/trajectory` | Get step-by-step trajectory |

### Research

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/v1/research/tasks` | Create a research task |
| `GET` | `/v1/research/tasks/{task_id}` | Get task status and result |

### Scouting

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/v1/scouting/tasks` | Create a scout |
| `GET` | `/v1/scouting/tasks` | List scouts (optional `?status=` filter) |
| `GET` | `/v1/scouting/tasks/{scout_id}` | Get scout details |
| `PUT` | `/v1/scouting/tasks/{scout_id}` | Full scout update |
| `PATCH` | `/v1/scouting/tasks/{scout_id}` | Partial scout update |
| `DELETE` | `/v1/scouting/tasks/{scout_id}` | Delete a scout |
| `POST` | `/v1/scouting/tasks/{scout_id}/pause` | Pause a scout |
| `POST` | `/v1/scouting/tasks/{scout_id}/resume` | Resume a paused scout |
| `POST` | `/v1/scouting/tasks/{scout_id}/restart` | Restart a scout |
| `POST` | `/v1/scouting/tasks/{scout_id}/done` | Mark scout as completed |
| `GET` | `/v1/scouting/tasks/{scout_id}/updates` | Paginated updates (cursor-based) |
| `PUT` | `/v1/scouting/tasks/{scout_id}/email-settings` | Update email notification settings |

### Usage

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/v1/usage` | Get usage stats and rate limit status |

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL async connection string | `postgresql+asyncpg://sentinel:sentinel@postgres:5432/sentinel` |
| `REDIS_URL` | Redis connection string | `redis://redis:6379/0` |
| `OPENROUTER_API_KEY` | OpenRouter API key (required) | `your_openrouter_key_here` |
| `SENTINEL_VISION_MODEL` | OpenRouter model for vision tasks | `meta-llama/llama-3.2-11b-vision-instruct:free` |
| `SENTINEL_DEFAULT_MODEL` | OpenRouter default chat model | `google/gemma-3-27b-it:free` |
| `SENTINEL_API_BASE_URL` | Base URL for the Sentinel API | `http://localhost:8000` |
| `SECRET_KEY` | Secret key for internal use | `changeme-use-openssl-rand-hex-32` |

## Development Setup

```bash
# Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install in editable mode with dev dependencies
pip install -e '.[dev]'

# Run the test suite
pytest
```

## Project Structure

```
sentinel/
├── alembic/              # Database migrations
├── alembic.ini           # Alembic configuration
├── api/
│   ├── core/             # Auth, DB, OpenRouter client
│   │   ├── auth.py
│   │   ├── db.py
│   │   └── openrouter.py
│   ├── models/           # SQLAlchemy models
│   │   └── api_key.py
│   ├── routers/          # FastAPI route handlers
│   │   ├── browsing.py
│   │   ├── health.py
│   │   ├── navigator.py
│   │   ├── research.py
│   │   ├── scouting.py
│   │   └── usage.py
│   ├── schemas/          # Pydantic request/response models
│   ├── services/         # Business logic layer
│   │   ├── browsing.py
│   │   ├── research.py
│   │   └── scouting.py
│   └── workers/          # Celery task workers
│       ├── browsing.py
│       ├── research.py
│       └── scouting.py
├── tests/                # Test suite
│   ├── conftest.py
│   ├── test_auth.py
│   ├── test_browsing.py
│   ├── test_health.py
│   ├── test_navigator.py
│   ├── test_research.py
│   ├── test_scouting.py
│   └── test_webhook.py
├── docker-compose.yml
├── Dockerfile
├── main.py               # FastAPI application entry point
├── pyproject.toml
└── LICENSE
```

## License

MIT
