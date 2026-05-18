# Changelog

All notable changes to this project will be documented in this file.

## [0.2.0] — 2026-05-18

### Added
- **URL Normalization Module** — Full pipeline for handling Douyin share links
  - `extract_url_from_text()` — Extract URL from messy share text
  - `resolve_short_url()` — Resolve v.douyin.com short URLs
  - `extract_video_id()` — Extract video ID from various URL formats
  - `validate_video_id()` — Verify video exists and is accessible
  - `normalize()` — Complete extraction → resolution → validation → normalization flow
- **Share Link Support** — Paste raw Douyin share text directly, no manual URL extraction needed
- **API Error Codes** — Structured error responses with `code` field for client handling
- **BDD Tests** — pytest-bdd integration tests for URL normalizer feature
- **Browser Headers** — User-agent and accept headers for Douyin accessibility

### Changed
- `validate_video_id()` changed from HEAD to GET requests (Douyin requires it)
- API error responses now include `code` field: `URL_RESOLVE_FAILED`, `VIDEO_NOT_AVAILABLE`

### Fixed
- Network errors now properly wrapped in `InvalidURLError`
- 5xx server errors return `False` instead of `True` (video may be accessible later)
- Tests updated to match implementation (GET instead of HEAD)

## [0.1.1] — 2026-05-15

### Added
- FastAPI server with `/api/v1/download` and `/api/v1/health` endpoints
- Docker Compose configuration for local development
- API documentation at `/docs` and `/redoc`
- `gunicorn` for production deployment

### Changed
- `uvicorn` replaced by `gunicorn` + uvicorn workers in Docker

## [0.1.0] — 2026-05-10

### Added
- Initial CLI tool with `douyin download <url>` command
- Playwright-based video extraction
- Support for standard Douyin video URLs

All notable changes to this project will be documented in this file.

## [Unreleased]

## [0.2.0] - 2026-05-15

### Added
- **FastAPI API Server**: Full REST API at `/api/v1` with OpenAPI/Redoc documentation
  - `POST /api/v1/download` - Download video (sync or async with callback)
  - `GET /api/v1/tasks` - List all tasks
  - `GET /api/v1/tasks/{task_id}` - Get task status
  - `DELETE /api/v1/tasks/{task_id}` - Cancel task
  - `GET /health` - Health check endpoint
- **Docker Deployment**: Complete Docker/Docker Compose setup
  - `Dockerfile` with Python 3.12, uv, Playwright, Gunicorn
  - `docker-compose.yml` for development
  - `docker-compose.prod.yml` for production
  - `nginx.conf` reverse proxy configuration
- **Environment Configuration**: All settings via `.env` with defaults
  - API, path, Nginx, quality, timeout configurations
  - Pydantic-settings based configuration management
- **Task Management System**: Background task execution with callback support
  - Thread-safe singleton TaskManager
  - Async task execution with timeout handling
  - Optional callback URL for async completion notification
- **GitHub Actions CI/CD**: Docker build and test pipeline
  - Trivy vulnerability scanning
  - Docker Compose integration tests

### Changed
- **API URL Prefix**: All endpoints now under `/api/v1`
- **Docker Config**: Simplified to only expose port customization

## [0.1.1] - 2026-05-15

### Fixed
- **Route.fetch "Request context disposed" error**: Add try/except in `_intercept_aweme_detail_api` to gracefully handle fetch errors when request context is disposed

### Added
- **CI/CD**: GitHub Actions workflows for automated testing, linting, and releases
- **Documentation**: Updated README with development and CI/CD sections

## [0.1.0] - 2026-05-15

### Added
- `douyin download` CLI command for downloading Douyin videos
- `douyin info` CLI command for showing video information
- `douyin session` CLI command for testing URL resolution
- Playwright headless Chrome extraction
- Short URL resolution (v.douyin.com)
- Quality ranking: v5 > v3 > aweme/v1/play/
- requests + tqdm progress bar
- Error handling: VideoNotFoundError, ExtractionTimeoutError
- Multi-layer fallback DOM extraction (video tag → source tags → pace_f → data attributes → network interception)
- BDD integration tests
- Unit tests with 85%+ coverage