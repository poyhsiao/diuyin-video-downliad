# Douyin Video Downloader

Download Douyin (抖音) videos via CLI.

## Quick Start

```bash
uv sync
playwright install chromium --with-deps
source .venv/bin/activate
douyin download "https://www.douyin.com/video/123456789"
douyin download "https://v.douyin.com/abc123" -o ~/my-videos
douyin info "https://www.douyin.com/video/123456789"
```

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

## Features

- Playwright headless Chrome extraction
- Short URL resolution (v.douyin.com)
- Quality ranking: v5 > v3 > aweme/v1/play/
- requests + tqdm progress bar
- Error handling: VideoNotFoundError, ExtractionTimeoutError
