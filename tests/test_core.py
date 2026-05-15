"""Unit tests for core module - URL parsing, sorting, and download."""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import requests

from douyin_download.core import (
    resolve_video_id,
    sort_urls,
    _download_file,
    download_video,
    DownloadFailedError,
    NoCDNAvailableError,
)


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


class TestDownloadFile:
    """Tests for _download_file function."""

    @patch("douyin_download.core.requests.get")
    @patch("douyin_download.core.open", create=True)
    @patch("douyin_download.core.tqdm")
    def test_download_with_progress_callback(
        self, mock_tqdm, mock_open, mock_get
    ) -> None:
        """Test that progress_callback is called during download."""
        # Setup mock response
        mock_response = Mock()
        mock_response.headers = {"content-length": "1024"}
        mock_response.iter_content = Mock(return_value=iter([b"chunk1", b"chunk2"]))
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        # Setup mocks for context manager
        mock_tqdm_instance = Mock()
        mock_tqdm_instance.n = 0
        mock_tqdm.return_value.__enter__ = Mock(return_value=mock_tqdm_instance)
        mock_tqdm.return_value.__exit__ = Mock(return_value=None)

        mock_file = Mock()
        mock_open.return_value.__enter__ = Mock(return_value=mock_file)
        mock_open.return_value.__exit__ = Mock(return_value=None)

        # Call _download_file with progress_callback
        progress_calls = []
        callback = lambda downloaded, total: progress_calls.append((downloaded, total))

        _download_file("https://example.com/video.mp4", Path("/tmp/video.mp4"), callback)

        # Verify progress_callback was called
        assert len(progress_calls) > 0

    @patch("douyin_download.core.requests.get")
    @patch("douyin_download.core.open", create=True)
    @patch("douyin_download.core.tqdm")
    def test_download_without_progress_callback(
        self, mock_tqdm, mock_open, mock_get
    ) -> None:
        """Test that download works without progress_callback."""
        mock_response = Mock()
        mock_response.headers = {"content-length": "1024"}
        mock_response.iter_content = Mock(return_value=iter([b"data"]))
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        mock_tqdm_instance = Mock()
        mock_tqdm_instance.n = 0
        mock_tqdm.return_value.__enter__ = Mock(return_value=mock_tqdm_instance)
        mock_tqdm.return_value.__exit__ = Mock(return_value=None)

        mock_file = Mock()
        mock_open.return_value.__enter__ = Mock(return_value=mock_file)
        mock_open.return_value.__exit__ = Mock(return_value=None)

        # Should not raise even without callback
        _download_file(
            "https://example.com/video.mp4",
            Path("/tmp/video.mp4"),
            progress_callback=None
        )


class TestDownloadFileErrors:
    """Tests for _download_file error handling."""

    @patch("douyin_download.core.requests.get")
    def test_download_request_exception(self, mock_get) -> None:
        """Test that DownloadFailedError is raised on request exception."""
        mock_get.side_effect = requests.RequestException("Connection failed")

        with pytest.raises(DownloadFailedError, match="Download failed"):
            _download_file(
                "https://example.com/video.mp4",
                Path("/tmp/video.mp4"),
            )

    @patch("douyin_download.core.requests.get")
    def test_download_http_error(self, mock_get) -> None:
        """Test that DownloadFailedError is raised on HTTP error."""
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = requests.HTTPError("404 Not Found")
        mock_get.return_value = mock_response

        with pytest.raises(DownloadFailedError, match="Download failed"):
            _download_file(
                "https://example.com/video.mp4",
                Path("/tmp/video.mp4"),
            )


class TestDownloadFileWriteError:
    """Tests for _download_file file write errors."""

    @patch("douyin_download.core.requests.get")
    @patch("douyin_download.core.open", create=True)
    @patch("douyin_download.core.tqdm")
    def test_download_file_write_error(self, mock_tqdm, mock_open, mock_get) -> None:
        """Test that DownloadFailedError is raised on file write error."""
        mock_response = Mock()
        mock_response.headers = {"content-length": "1024"}
        mock_response.iter_content = Mock(return_value=iter([b"chunk"]))
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        mock_tqdm_instance = Mock()
        mock_tqdm_instance.n = 0
        mock_tqdm.return_value.__enter__ = Mock(return_value=mock_tqdm_instance)
        mock_tqdm.return_value.__exit__ = Mock(return_value=None)

        # Simulate file write error
        mock_file = Mock()
        mock_file.write.side_effect = IOError("Disk full")
        mock_open.return_value.__enter__ = Mock(return_value=mock_file)
        mock_open.return_value.__exit__ = Mock(return_value=None)

        with pytest.raises((DownloadFailedError, IOError)):
            _download_file(
                "https://example.com/video.mp4",
                Path("/tmp/video.mp4"),
            )


class TestDownloadVideo:
    """Tests for download_video function."""

    @patch("douyin_download.core._download_file")
    @patch("douyin_download.core.extract_cdn_url")
    @patch("douyin_download.core.resolve_video_id")
    def test_download_video_with_progress_callback(
        self, mock_resolve, mock_extract, mock_download
    ) -> None:
        """Test download_video calls _download_file with progress_callback."""
        mock_resolve.return_value = "123456789"
        mock_extract.return_value = ["https://cdn.example.com/video.mp4"]

        progress_calls = []
        callback = lambda downloaded, total: progress_calls.append((downloaded, total))

        video_id, output_path = download_video(
            "https://www.douyin.com/video/123456789",
            Path("/tmp"),
            progress_callback=callback
        )

        assert video_id == "123456789"
        mock_download.assert_called_once()
        call_kwargs = mock_download.call_args.kwargs
        assert call_kwargs.get("progress_callback") is callback

    @patch("douyin_download.core._download_file")
    @patch("douyin_download.core.extract_cdn_url")
    @patch("douyin_download.core.resolve_video_id")
    def test_download_video_no_cdn_urls(self, mock_resolve, mock_extract, mock_download) -> None:
        """Test NoCDNAvailableError when no CDN URLs extracted."""
        mock_resolve.return_value = "123456789"
        mock_extract.return_value = []

        with pytest.raises(NoCDNAvailableError, match="No video URLs extracted"):
            download_video(
                "https://www.douyin.com/video/123456789",
                Path("/tmp"),
            )