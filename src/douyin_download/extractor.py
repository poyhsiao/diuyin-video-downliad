"""Playwright-based CDN URL extractor."""

import json

from playwright.sync_api import TimeoutError

from douyin_download.models import VideoNotFoundError


class ExtractionTimeoutError(Exception):
    """Raised when extraction times out."""


def _extract_from_video_tag(page) -> list[str]:
    """Extract URLs from video tag.

    Args:
        page: Playwright page object

    Returns:
        List of URLs found in video src (empty if none)
    """
    video = page.query_selector("video")
    if not video:
        return []

    src = video.get_attribute("src")
    if src and ("mp4" in src or "play" in src):
        return [src]
    return []


def _extract_from_data_attributes(page) -> list[str]:
    """Extract URLs from page attributes containing mp4/play.

    Args:
        page: Playwright page object

    Returns:
        List of URLs found in data-* and href attributes
    """
    import re

    all_html = page.content()
    pattern = r'(?:href|data-src|data-url)=["\']([^"\']*(?:mp4|play)[^"\']*)["\']'
    matches = re.findall(pattern, all_html, re.IGNORECASE)
    return list(set(matches))


def extract_cdn_url(url: str, wait_seconds: int = 5) -> list[str]:
    """Headless Chrome extraction of video CDN URLs.

    Args:
        url: Douyin video URL
        wait_seconds: Maximum wait time for page load

    Returns:
        List of CDN URLs found on page

    Raises:
        VideoNotFoundError: If page returns 404 or is blocked
        ExtractionTimeoutError: If extraction times out
    """
    from playwright.sync_api import sync_playwright

    timeout_ms = wait_seconds * 1000

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            response = page.goto(
                url,
                wait_until="domcontentloaded",
                timeout=timeout_ms,
            )

            if response is None:
                raise VideoNotFoundError(f"Page returned no response: {url}")

            if response.status in (404, 403):
                raise VideoNotFoundError(f"Video not found (HTTP {response.status}): {url}")

            page.wait_for_timeout(timeout_ms)

            urls: set[str] = set()

            pace_data = page.evaluate("""() => {
                try { return JSON.stringify(window.__pace_f || {}); }
                catch (e) { return '{}'; }
            }""")
            try:
                data = json.loads(pace_data)
                if isinstance(data, dict):
                    for val in data.values():
                        if isinstance(val, str) and ("mp4" in val or "play" in val):
                            urls.add(val)
                        elif isinstance(val, dict):
                            for v in val.values():
                                if isinstance(v, str) and ("mp4" in v or "play" in v):
                                    urls.add(v)
            except (json.JSONDecodeError, ValueError):
                pass

            for el in page.query_selector_all("source"):
                src = el.get_attribute("src")
                if src:
                    urls.add(src)

            return list(urls)

        except TimeoutError:
            raise ExtractionTimeoutError(f"Extraction timed out after {wait_seconds}s")
        finally:
            browser.close()
