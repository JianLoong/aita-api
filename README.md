# AITA API

A FastAPI-based REST API for analyzing and serving data from the r/AmItheAsshole subreddit. This is a complete rewrite of reddit-store with enhanced features including sentiment analysis, OpenAI-powered insights, and full-text search capabilities.

## Features

- Reddit data crawling and storage
- Submission and comment retrieval endpoints
- Sentiment analysis using AFINN and NRCLex
- OpenAI-powered content analysis
- Full-text search (FTS) support
- Rate limiting (40 requests/minute)
- CORS enabled
- SQLite database with SQLModel ORM
- Automated hourly data updates
- Health check endpoints

## API Documentation

Interactive Swagger documentation is available at:
- Production: https://vmi1592589.contaboserver.net/docs
- Local: http://localhost:8000/docs (when running locally)

## Requirements

- Python 3.10+
- Docker & Docker Compose (for containerized deployment)
- Reddit API credentials
- OpenAI API key

## Setup

### Environment Configuration

Create a `.env` file in the project root with the following variables:

```env
REDDIT_CLIENT_ID=REMOVED
REDDIT_CLIENT_SECRET=REMOVED
SUBREDDIT_NAME=AmItheAsshole
POST_LIMIT=5
DATABASE_NAME=AmItheAsshole.db
OPENAI_API_KEY=REMOVED
POSTGRES_HOST=db
POSTGRES_PORT=5432
POSTGRES_DB=example
POSTGRES_USER=REMOVED
POSTGRES_PASSWORD=REMOVED

```

### Running with Docker Compose

```bash
docker compose up --build
```

The API will be available at `http://localhost:8000`

### Local Development

1. Create a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -e ".[dev]"
```

3. Run the application:
```bash
uvicorn aita_api.main:app --host 0.0.0.0 --port 8000 --reload
```

## API Endpoints

All endpoints are prefixed with `/api/v2`:

- `GET /health` - Health check endpoint
- `GET /submissions` - Retrieve submissions
- `GET /comments` - Retrieve comments
- `GET /summary` - Get summary statistics
- `GET /openai-analysis` - Get OpenAI-powered analysis

## Development

### Code Quality Tools

The project uses:
- `ruff` for linting and formatting
- `mypy` for type checking
- `pytest` for testing

Run tests:
```bash
pytest
```

Format and lint code:
```bash
ruff format .
ruff check --fix .
```

### Project Structure

```
src/aita_api/
├── endpoints/          # API route handlers
├── models/            # Pydantic/SQLModel models
├── utils/             # Utility modules (crawler, analytics, etc.)
└── main.py           # Application entry point
```

## Troubleshooting

Migrations

```
docker compose down -v
docker compose up --build -d
docker compose exec db psql -U postgres -d aita-db -f /migrations/add_fts.sql
```

## License

Apache 2.0 / MIT

## Contact

Email: jianloongliew@gmail.com