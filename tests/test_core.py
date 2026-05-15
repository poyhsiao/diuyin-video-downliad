"""Unit tests for core module - URL parsing and sorting."""

import pytest
from pathlib import Path

from douyin_download.core import resolve_video_id, sort_urls


class TestResolveVideoId:
    """Tests for resolve_video_id function."""

    def test_long_url(self) -> None:
        """Test extracting video ID from standard URL."""
        url = "https://www.douyin.com/video/723456789"
        assert resolve_video_id(url) == "723456789"

    def test_short_url(self) -> None:
        """Test extracting video ID from short URL."""
        url = "https://v.douyin.com/abc123"
        assert resolve_video_id(url) == "abc123"

    def test_short_url_with_query(self) -> None:
        """Test extracting video ID from short URL with query params."""
        url = "https://v.douyin.com/xyz789?is_from_web=1"
        assert resolve_video_id(url) == "xyz789"

    def test_unsupported_url(self) -> None:
        """Test ValueError for unsupported URL format."""
        with pytest.raises(ValueError, match="Unsupported URL"):
            resolve_video_id("https://example.com")


class TestSortUrls:
    """Tests for sort_urls function."""

    def test_v5_priority(self) -> None:
        """Test that v5 URLs are prioritized."""
        urls = [
            "https://aweme/v1/play/?v3-test.mp4",
            "https://aweme/v5-test.mp4",
            "https://aweme/v3-test.mp4",
        ]
        sorted_urls = sort_urls(urls)
        assert sorted_urls[0] == "https://aweme/v5-test.mp4"

    def test_v3_vs_aweme(self) -> None:
        """Test that v3 URLs are prioritized over aweme."""
        urls = [
            "https://aweme/v1/play/?id=test.mp4",
            "https://aweme/v3-test.mp4",
        ]
        sorted_urls = sort_urls(urls)
        assert sorted_urls[0] == "https://aweme/v3-test.mp4"

    def test_empty_list(self) -> None:
        """Test sorting empty list."""
        assert sort_urls([]) == []

    def test_single_url(self) -> None:
        """Test sorting single URL."""
        url = ["https://example.com/video.mp4"]
        assert sort_urls(url) == url