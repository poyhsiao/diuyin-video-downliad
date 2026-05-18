import re
import httpx
from httpx import TimeoutException, HTTPError


class InvalidURLError(Exception):
    """Raised when URL cannot be parsed or validated."""


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