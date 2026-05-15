"""Data models for Douyin downloader."""

from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


class TaskStatus(str, Enum):
    """Task status enum."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class DownloadTask:
    """Download task for API."""
    task_id: str
    video_url: str
    quality: str | None = None
    output_dir: Path | None = None
    callback_url: str | None = None
    status: TaskStatus = TaskStatus.PENDING
    video_id: str | None = None
    path: Path | None = None
    file_size: int | None = None
    error: str | None = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class VideoQuality:
    """Video quality enum."""
    ORIGINAL = "original"
    RESOLUTION_480P = "480p"
    RESOLUTION_720P = "720p"
    RESOLUTION_1080P = "1080p"


class VideoNotFoundError(Exception):
    """Raised when video cannot be found or extracted."""


@dataclass
class DownloadResult:
    """Result of a successful download."""
    video_id: str
    path: Path
    file_size: int