"""Douyin video downloader."""

__version__ = "0.1.0"

from douyin_download.url_normalizer import (
    normalize,
    extract_url_from_text,
    extract_video_id,
    resolve_short_url,
    validate_video_id,
    InvalidURLError,
    VideoUnavailableError,
)

__all__ = [
    "normalize",
    "extract_url_from_text",
    "extract_video_id",
    "resolve_short_url",
    "validate_video_id",
    "InvalidURLError",
    "VideoUnavailableError",
]