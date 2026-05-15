"""Unit tests for models module - Exception classes and data models."""

import pytest
from pathlib import Path

from douyin_download.models import (
    VideoNotFoundError,
    VideoQuality,
    ExtractResult,
    DownloadResult,
    VideoInfo,
)


class TestVideoNotFoundError:
    """Tests for VideoNotFoundError exception."""

    def test_default_constructor(self) -> None:
        """Test creating exception with no arguments."""
        exc = VideoNotFoundError()
        assert isinstance(exc, Exception)

    def test_message_constructor(self) -> None:
        """Test creating exception with message."""
        exc = VideoNotFoundError("Video not found")
        assert str(exc) == "Video not found"

    def test_exception_inheritance(self) -> None:
        """Test VideoNotFoundError is an Exception subclass."""
        exc = VideoNotFoundError("Video not found")
        assert isinstance(exc, Exception)


class TestVideoQuality:
    """Tests for VideoQuality enum."""

    def test_quality_values(self) -> None:
        """Test all quality enum values exist."""
        assert VideoQuality.QUALITY_480P.value == "480p"
        assert VideoQuality.QUALITY_720P.value == "720p"
        assert VideoQuality.QUALITY_1080P.value == "1080p"
        assert VideoQuality.QUALITY_ORIGINAL.value == "original"

    def test_enum_count(self) -> None:
        """Test we have expected number of quality levels."""
        assert len(VideoQuality) == 4


class TestExtractResult:
    """Tests for ExtractResult dataclass."""

    def test_basic_construction(self) -> None:
        """Test creating ExtractResult with required fields."""
        result = ExtractResult(video_id="123")
        assert result.video_id == "123"
        assert result.title is None
        assert result.urls == []
        assert result.qualities == []

    def test_full_construction(self) -> None:
        """Test creating ExtractResult with all fields."""
        result = ExtractResult(
            video_id="456",
            title="Test Video",
            urls=["https://example.com/video.mp4"],
            qualities=[VideoQuality.QUALITY_720P],
        )
        assert result.video_id == "456"
        assert result.title == "Test Video"
        assert len(result.urls) == 1
        assert VideoQuality.QUALITY_720P in result.qualities

    def test_best_url_v5(self) -> None:
        """Test best_url returns v5 URL when available."""
        result = ExtractResult(
            video_id="789",
            urls=[
                "https://aweme/v3-test.mp4",
                "https://aweme/v5-test.mp4",
            ],
        )
        assert result.best_url() == "https://aweme/v5-test.mp4"

    def test_best_url_v3(self) -> None:
        """Test best_url returns v3 URL when no v5."""
        result = ExtractResult(
            video_id="789",
            urls=[
                "https://aweme/v1/play/?id=test.mp4",
                "https://aweme/v3-test.mp4",
            ],
        )
        assert result.best_url() == "https://aweme/v3-test.mp4"

    def test_best_url_empty(self) -> None:
        """Test best_url returns None when no URLs."""
        result = ExtractResult(video_id="789", urls=[])
        assert result.best_url() is None

    def test_immutability(self) -> None:
        """Test that ExtractResult is frozen (immutable)."""
        result = ExtractResult(video_id="123")
        with pytest.raises(Exception):  # frozen dataclass raises error
            result.video_id = "456"  # type: ignore


class TestDownloadResult:
    """Tests for DownloadResult dataclass."""

    def test_construction(self) -> None:
        """Test creating DownloadResult."""
        path = Path("/tmp/video.mp4")
        result = DownloadResult(
            video_id="123",
            path=path,
            url="https://example.com/video.mp4",
        )
        assert result.video_id == "123"
        assert result.path == path
        assert result.url == "https://example.com/video.mp4"
        assert result.file_size is None

    def test_with_file_size(self) -> None:
        """Test creating DownloadResult with file_size."""
        result = DownloadResult(
            video_id="123",
            path=Path("/tmp/video.mp4"),
            url="https://example.com/video.mp4",
            file_size=1024000,
        )
        assert result.file_size == 1024000


class TestVideoInfo:
    """Tests for VideoInfo dataclass."""

    def test_basic_construction(self) -> None:
        """Test creating VideoInfo with required fields."""
        info = VideoInfo(video_id="123")
        assert info.video_id == "123"
        assert info.title is None
        assert info.duration is None
        assert info.url is None
        assert info.qualities == []

    def test_full_construction(self) -> None:
        """Test creating VideoInfo with all fields."""
        info = VideoInfo(
            video_id="456",
            title="Test",
            duration=60,
            url="https://example.com/video.mp4",
            qualities=[VideoQuality.QUALITY_720P],
        )
        assert info.title == "Test"
        assert info.duration == 60

    def test_estimated_size_mb_no_duration(self) -> None:
        """Test estimated_size_mb returns None when no duration."""
        info = VideoInfo(video_id="123")
        assert info.estimated_size_mb is None

    def test_estimated_size_mb_no_url(self) -> None:
        """Test estimated_size_mb returns None when no url."""
        info = VideoInfo(video_id="123", duration=60)
        assert info.estimated_size_mb is None

    def test_estimated_size_mb_calculation(self) -> None:
        """Test estimated_size_mb calculates correctly."""
        info = VideoInfo(
            video_id="123",
            duration=60,
            url="https://example.com/video.mp4",
        )
        # 60 seconds * 2_000_000 bits / (8 * 1_000_000) = 15 MB
        assert info.estimated_size_mb == 15.0

    def test_estimated_size_mb_longer_video(self) -> None:
        """Test estimated_size_mb with longer video."""
        info = VideoInfo(
            video_id="123",
            duration=180,
            url="https://example.com/video.mp4",
        )
        # 180 seconds * 2_000_000 bits / (8 * 1_000_000) = 45 MB
        assert info.estimated_size_mb == 45.0