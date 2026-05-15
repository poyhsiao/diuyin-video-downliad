"""Core download orchestration."""

import re
from pathlib import Path

import requests
from tqdm import tqdm

from douyin_download.extractor import extract_cdn_url


class DownloadFailedError(Exception):
    """Raised when download fails."""


class NoCDNAvailableError(Exception):
    """Raised when no CDN URLs are available."""


def resolve_video_id(url: str) -> str:
    """Extract video_id from URL (supports short URLs)."""
    if "/video/" in url:
        match = re.search(r"/video/(\d+)", url)
        if match:
            return match.group(1)
    if "/v.douyin.com/" in url:
        return url.split("/")[-1].split("?")[0]
    raise ValueError(f"Unsupported URL format: {url}")


def sort_urls(urls: list[str]) -> list[str]:
    """Sort URLs by quality: v5 > v3 > aweme/v1/play/."""
    def key(u: str) -> int:
        if "v5-" in u:
            return 2
        if "v3-" in u:
            return 1
        if "aweme/v1/play/" in u:
            return 0
        return -1
    return sorted(urls, key=key, reverse=True)


def download_video(
    url: str,
    output_dir: Path,
    quality: str | None = None,
    progress_callback=None,
) -> tuple[str, Path]:
    """Full download pipeline with progress reporting.

    Args:
        url: Douyin video URL
        output_dir: Output directory for downloaded video
        quality: Desired quality (None = best available, "480p" for constrained)
        progress_callback: Optional callback(downloaded, total) for progress updates

    Returns:
        tuple of (video_id, output_path)

    Raises:
        VideoNotFoundError: If video cannot be found
        NoCDNAvailableError: If no CDN URLs are available
        DownloadFailedError: If download fails
    """
    video_id = resolve_video_id(url)

    cdn_urls = extract_cdn_url(url, wait_seconds=5)
    sorted_urls = sort_urls(cdn_urls)

    if not sorted_urls:
        raise NoCDNAvailableError("No video URLs extracted")

    chosen = sorted_urls[0]
    output_path = output_dir / f"douyin_{video_id}.mp4"

    _download_file(chosen, output_path, progress_callback=progress_callback)

    return video_id, output_path


def _download_file(url: str, output_path: Path, progress_callback=None) -> None:
    """Download file with progress bar.

    Args:
        url: Source URL
        output_path: Destination path
        progress_callback: Optional callback(downloaded, total)
    """
    try:
        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status()

        total_size = int(response.headers.get("content-length", 0))
        chunk_size = 1024 * 1024  # 1MB chunks

        with open(output_path, "wb") as f:
            with tqdm(
                total=total_size,
                unit="B",
                unit_scale=True,
                unit_divisor=1024,
                desc=f"Downloading {output_path.name}",
            ) as pbar:
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if chunk:
                        f.write(chunk)
                        downloaded = pbar.n
                        if progress_callback:
                            progress_callback(downloaded, total_size)
                        pbar.update(len(chunk))

    except requests.RequestException as e:
        raise DownloadFailedError(f"Download failed: {e}") from e
