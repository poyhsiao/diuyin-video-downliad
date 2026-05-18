import re
import httpx


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
    with httpx.Client(follow_redirects=True, timeout=timeout) as client:
        response = client.get(url)
        if not response.is_success:
            raise InvalidURLError(f"HTTP {response.status_code}")
        return str(response.url)