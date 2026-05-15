"""pytest configuration and shared fixtures."""

import shutil
import tempfile
from pathlib import Path
from typing import Generator

import pytest


@pytest.fixture
def temp_output_dir() -> Generator[Path, None, None]:
    """Create a temporary output directory for tests."""
    temp_dir = Path(tempfile.mkdtemp())
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def sample_video_id() -> str:
    """Sample video ID for testing."""
    return "7637075230132849971"


@pytest.fixture
def sample_douyin_url(sample_video_id: str) -> str:
    """Sample Douyin URL for testing."""
    return f"https://www.douyin.com/video/{sample_video_id}"


@pytest.fixture
def mock_cdn_urls() -> list[str]:
    """Mock CDN URLs with different quality levels."""
    return [
        "https://aweme/v1/play/?id=test.mp4",
        "https://v3-dy-o.zjcdn.com/test-v3.mp4",
        "https://v5-hl-mly-ov.zjcdn.com/test-v5.mp4",
    ]


@pytest.fixture
def sorted_urls():
    """Fixture to store sorted URLs for extractor tests."""
    return None


@pytest.fixture
def extract_result():
    """Fixture to store extraction results."""
    return None