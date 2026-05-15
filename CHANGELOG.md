# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Fixed
- **Route.fetch "Request context disposed" error**: Add try/except in `_intercept_aweme_detail_api` to gracefully handle fetch errors when request context is disposed
- **Multi-layer fallback extraction**: Fixed issue where Douyin page structure changes would cause extraction to fail

### Added
- **TestInterceptAwemeDetailApi**: TDD tests for API interception error handling
- **API response interception**: New `_intercept_aweme_detail_api` function to capture aweme/detail API responses

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