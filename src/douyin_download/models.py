"""Data models for Douyin downloader."""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


class VideoNotFoundError(Exception):
    """Raised when video cannot be found or extracted."""


class VideoQuality(Enum):
    """Available video quality levels."""
    QUALITY_480P = "480p"
    QUALITY_720P = "720p"
    QUALITY_1080P = "1080p"
    QUALITY_ORIGINAL = "original"


@dataclass(frozen=True)
class ExtractResult:
    """Result of CDN URL extraction."""
    video_id: str
    title: str | None = None
    urls: list[str] = field(default_factory=list)
    qualities: list[VideoQuality] = field(default_factory=list)

    def best_url(self) -> str | None:
        """Return highest quality URL (v5 > v3 > aweme)."""
        if not self.urls:
            return None
        sorted_urls = sorted(
            self.urls,
            key=lambda u: (
                2 if "v5-" in u else (1 if "v3-" in u else 0),
            ),
            reverse=True,
        )
        return sorted_urls[0] if sorted_urls else None


@dataclass(frozen=True)
class DownloadResult:
    """Result of a video download operation."""
    video_id: str
    path: Path
    url: str
    file_size: int | None = None


@dataclass
class VideoInfo:
    """Video metadata."""
    video_id: str
    title: str | None = None
    duration: int | None = None
    url: str | None = None
    qualities: list[VideoQuality] = field(default_factory=list)

    @property
    def estimated_size_mb(self) -> float | None:
        """Estimated file size in MB (rough estimate based on duration)."""
        if self.duration is None or self.url is None:
            return None
        bitrate_estimate = 2_000_000  # 2 Mbps for 480p
        return (self.duration * bitrate_estimate) / (8 * 1_000_000)