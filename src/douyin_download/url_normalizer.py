import re
import httpx
from httpx import TimeoutException, HTTPError


class InvalidURLError(Exception):
    """Raised when URL cannot be parsed or validated."""


class VideoUnavailableError(Exception):
    """Raised when video is not available or accessible."""


def extract_url_from_text(text: str) -> str | None:
    """Extract first URL from messy share text.

    Args:
        text: Raw text from clipboard

    Returns:
        Extracted URL or None if not found
    """
    pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
    matches = re.findall(pattern, text)
    if not matches:
        return None
    url = matches[0]
    return url.rstrip('/')


def resolve_short_url(url: str, timeout: int = 10) -> str:
    """Follow HTTP redirects to resolve short URL to final URL.

    Args:
        url: Short URL (v.douyin.com/xxx)
        timeout: Request timeout in seconds

    Returns:
        Resolved final URL

    Raises:
        InvalidURLError: If URL cannot be resolved
    """
    try:
        with httpx.Client(follow_redirects=True, timeout=timeout) as client:
            response = client.get(url)
            if not response.is_success:
                raise InvalidURLError(f"HTTP {response.status_code} for URL: {url}")
            return str(response.url)
    except TimeoutException:
        raise InvalidURLError(f"Request timed out for URL: {url}")
    except HTTPError:
        raise InvalidURLError(f"Connection error for URL: {url}")


def extract_video_id(url: str) -> str | None:
    """Extract video ID from Douyin URL.

    Args:
        url: Douyin URL (various formats)

    Returns:
        Video ID or None if not found
    """
    patterns = [
        r'/video/(\d+)',
        r'/aweme/(\d+)',
        r'video_id=(\d+)',
    ]
    for pattern in patterns:
        if match := re.search(pattern, url):
            return match.group(1)
    return None


def validate_video_id(video_id: str, timeout: int = 10) -> bool:
    """Validate that video ID exists and is accessible.

    Args:
        video_id: Video ID to validate
        timeout: Request timeout in seconds

    Returns:
        True if video exists and is accessible
        False if server error (video might be accessible later)

    Raises:
        VideoUnavailableError: If video is not available or access denied
        InvalidURLError: If request fails due to network error
    """
    check_url = f"https://www.douyin.com/video/{video_id}"
    try:
        with httpx.Client(timeout=timeout) as client:
            response = client.head(check_url)
            if response.status_code == 404:
                raise VideoUnavailableError(f"Video {video_id} not found")
            if response.status_code == 403:
                raise VideoUnavailableError(f"Video {video_id} access denied")
            if response.status_code >= 500:
                # Server error - video might be accessible later
                return False
            return True
    except (TimeoutException, HTTPError) as e:
        raise InvalidURLError(f"Failed to validate video {video_id}: {e}")