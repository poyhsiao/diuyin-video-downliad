# Changelog

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