# Douyin Video Downloader

A Playwright-based tool for downloading Douyin videos from share links. Supports both CLI and FastAPI interface.

## Features

- **Share Link Support** — Paste raw Douyin share text directly, no need to extract URL manually
- **Automatic URL Resolution** — Handles short URLs (v.douyin.com) and extracts video IDs
- **Video Validation** — Verifies videos exist before attempting download
- **CLI Interface** — Simple `douyin download <url>` command
- **REST API** — FastAPI server with `/api/v1/download` endpoint
- **Docker Deployment** — Pre-built container with Chromium browser

## Quick Start

### CLI

```bash
# Install
uv sync
playwright install chromium --with-deps

# Download via share text
douyin download "7.61 复制打开抖音，看看【一蛙AI的作品】 https://v.douyin.com/NdvdvNIN50I/"

# Download via clean URL
douyin download "https://www.douyin.com/video/7385822337847635259"
```

### Docker

```bash
# Build and run
docker compose up --build

# Test the API
curl -X POST http://localhost:8080/api/v1/download \
  -H "Content-Type: application/json" \
  -d '{"url": "7.61 复制打开抖音，看看【一蛙AI的作品】 https://v.douyin.com/NdvdvNIN50I/"}'
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/download` | Download video from URL |
| GET | `/api/v1/health` | Health check |
| GET | `/docs` | API documentation |

## Architecture

```
cli.py       — Click-based CLI entrypoint
core.py      — Download orchestration
extractor.py — Playwright extraction logic
url_normalizer.py — URL parsing and validation
models.py    — Pydantic models
api.py       — FastAPI server
```

## Development

```bash
uv sync
playwright install chromium --with-deps
pytest                    # Run tests
pytest --cov=src          # With coverage
```

Download Douyin (抖音) videos via CLI or REST API.

## Quick Start

### CLI
```bash
uv sync
playwright install chromium --with-deps
source .venv/bin/activate
douyin download "https://www.douyin.com/video/123456789"
douyin download "https://v.douyin.com/abc123" -o ~/my-videos
douyin info "https://www.douyin.com/video/123456789"
```

### API Server
```bash
# Development
docker-compose up

# Production
docker-compose -f docker-compose.prod.yml up
```

Then access:
- API: `http://localhost:80/api/v1`
- Swagger UI: `http://localhost:80/docs`
- ReDoc: `http://localhost:80/redoc`

## CLI Commands

Activate the virtual environment before running commands:
```bash
source .venv/bin/activate
```

Commands (after activation):
```bash
douyin download <url> [-q quality] [-o output_dir]  # Download video
douyin info <url>                                     # Show video info
douyin session <url>                                 # Test URL resolution
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/download` | Download video (sync or async with callback) |
| GET | `/api/v1/tasks` | List all tasks |
| GET | `/api/v1/tasks/{task_id}` | Get task status |
| DELETE | `/api/v1/tasks/{task_id}` | Cancel task |
| GET | `/health` | Health check |
| GET | `/docs` | Swagger UI (OpenAPI) |
| GET | `/redoc` | ReDoc documentation |

### Download Request
```bash
# Sync mode (returns immediately with result)
curl -X POST http://localhost/api/v1/download \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.douyin.com/video/123456789", "quality": "720p"}'

# Async mode (with callback notification)
curl -X POST http://localhost/api/v1/download \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.douyin.com/video/123456789", "callback_url": "https://example.com/webhook"}'
```

## Features

- **Multi-layer fallback DOM extraction** (video tag → source tags → pace_f → data attributes → network interception)
- **Playwright headless Chrome extraction**
- **Short URL resolution** (v.douyin.com)
- **Quality ranking**: v5 > v3 > aweme/v1/play/
- **REST API** with OpenAPI/Redoc documentation
- **Docker/Docker Compose deployment**
- **Background task execution** with callback support
- **Error handling**: VideoNotFoundError, ExtractionTimeoutError

## Environment Variables

All configuration via `.env` (defaults in parentheses):

```env
# API Settings
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=4
API_RELOAD=false

# Paths
DOWNLOAD_OUTPUT_DIR=/data/downloads
TEMP_DIR=/data/temp

# Docker Ports
NGINX_PORT=80
NGINX_SSL_PORT=443
APP_PORT=8000

# Defaults
DEFAULT_QUALITY=original
MAX_CONCURRENT_DOWNLOADS=5
TASK_TIMEOUT_SECONDS=300

# Playwright
PLAYWRIGHT_BROWSERS_PATH=/ms-playwright
```

## Development

```bash
# Setup
uv sync
playwright install chromium --with-deps

# Run tests
uv run pytest tests/ --cov=src/douyin_download

# Lint
uv run ruff check src/ tests/
```

## Docker Deployment

```bash
# Development
docker-compose up

# Production
docker-compose -f docker-compose.prod.yml up

# Custom ports
NGINX_PORT=8080 APP_PORT=9000 docker-compose up
```

## CI/CD

Automated CI via GitHub Actions on every push to main/develop and PRs.
Releases are published automatically when a `v*` tag is pushed.

## Test Coverage

- **95 unit tests** passing
- **17 BDD integration tests** passing
- **88% code coverage**