"""Playwright-based CDN URL extractor."""

import json
import re

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


def _extract_from_source_tags(page) -> list[str]:
    """Extract URLs from source tags.

    Args:
        page: Playwright page object

    Returns:
        List of URLs found in source elements (empty if none)
    """
    urls: list[str] = []
    for el in page.query_selector_all("source"):
        src = el.get_attribute("src")
        if src:
            urls.append(src)
    return urls


def _extract_from_pace_f(page) -> list[str]:
    """Extract URLs from window.__pace_f data.

    Args:
        page: Playwright page object

    Returns:
        List of URLs found in __pace_f object (empty if none)
    """
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
    return list(urls)


def _extract_from_data_attributes(page) -> list[str]:
    """Extract URLs from page attributes containing mp4/play.

    Args:
        page: Playwright page object

    Returns:
        List of URLs found in data-* and href attributes
    """
    all_html = page.content()
    pattern = r'(?:href|data-src|data-url)=["\']([^"\']*(?:mp4|play)[^"\']*)["\']'
    matches = re.findall(pattern, all_html, re.IGNORECASE)
    return list(set(matches))


VIDEO_URL_PATTERNS = re.compile(
    r'\.(?:mp4|m3u8|ts|chunk)(?:\?|$)|/video/|\.play\.googlevideo\.'
)

# Douyin API endpoints that contain video metadata
AWEME_DETAIL_PATTERNS = re.compile(r'/aweme/v\d+/web/aweme/detail/')

# CDN domains used by Douyin for video delivery
VIDEO_CDN_PATTERNS = re.compile(
    r'(byteeffecttos\.com|douyinstatic\.com|bytedstatic\.com|tiktokcdn\.com)'
)


def _intercept_aweme_detail_api(page, timeout_ms: int = 8000) -> list[str]:
    """Intercept Douyin aweme/detail API response for video URLs.

    Douyin loads video metadata via the /aweme/v1/web/aweme/detail/ endpoint.
    The response contains play_addr.url_list with actual CDN video URLs.

    Args:
        page: Playwright page object
        timeout_ms: How long to collect requests (default 8s)

    Returns:
        List of video URLs extracted from API responses
    """
    video_urls: list[str] = []
    api_responses: dict[str, str] = {}  # url -> response body

    def handle_route(route):
        url = route.request.url
        # Capture aweme detail API responses
        if AWEME_DETAIL_PATTERNS.search(url):
            try:
                response = route.fetch()
                if response.ok:
                    try:
                        api_responses[url] = response.text()
                    except Exception:
                        pass
            except Exception:
                pass  # Request context disposed or other fetch errors
            route.abort()  # Don't let it continue, we handle it
        else:
            route.continue_()

    page.route(re.compile(r".*"), handle_route)

    # Wait for API calls to complete
    import time
    start = time.time()
    while time.time() - start < timeout_ms / 1000:
        page.wait_for_timeout(500)
        if api_responses:
            break

    page.unroute_all()

    # Parse API responses to extract video URLs
    for url, body in api_responses.items():
        try:
            data = json.loads(body)
            aweme_data = data.get("aweme_detail", {})
            if aweme_data:
                # Try play_addr (primary video source)
                play_addr = aweme_data.get("video", {}).get("play_addr", {})
                url_list = play_addr.get("url_list", [])
                if url_list:
                    # Prefer H.265 or highest quality
                    video_urls.extend(url_list)

                # Also check video_addr as fallback
                video_addr = aweme_data.get("video", {}).get("video_addr", {})
                if isinstance(video_addr, dict):
                    url_list2 = video_addr.get("url_list", [])
                    if url_list2:
                        video_urls.extend(url_list2)

                # Check bitrate info for quality selection
                video_meta = aweme_data.get("video", {})
                video_meta.get("bitrate", 0)  # noqa: F841 (kept for future use)
        except (json.JSONDecodeError, ValueError, KeyError):
            continue

    return list(set(video_urls))


def _extract_from_network_interception(page, timeout_ms: int = 5000) -> list[str]:
    """Extract video URLs by intercepting network requests.

    Uses Playwright's route API to capture requests matching video patterns.

    Args:
        page: Playwright page object
        timeout_ms: How long to collect requests (default 5s)

    Returns:
        List of video URLs captured from network
    """
    captured_urls: list[str] = []

    def handle_route(route):
        url = route.request.url
        if VIDEO_URL_PATTERNS.search(url):
            captured_urls.append(url)
        route.continue_()

    page.route(re.compile(r".*"), handle_route)

    import time

    start = time.time()
    while time.time() - start < timeout_ms / 1000:
        page.wait_for_timeout(500)

    page.unroute_all()

    return list(set(captured_urls))


def extract_cdn_url(url: str, wait_seconds: int = 10) -> list[str]:
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
            # Start capturing BEFORE navigation so we don't miss API calls
            # Use 'commit' to just start navigation and not wait for full load
            page.route(re.compile(r".*"), lambda route: route.continue_())
            response = page.goto(
                url,
                wait_until="domcontentloaded",
                timeout=timeout_ms,
            )

            if response is None:
                raise VideoNotFoundError(f"Page returned no response: {url}")

            if response.status in (404, 403):
                raise VideoNotFoundError(f"Video not found (HTTP {response.status}): {url}")

            # Now do targeted interception for aweme detail API
            urls = _intercept_aweme_detail_api(page, timeout_ms)
            if not urls:
                urls = _extract_from_network_interception(page, timeout_ms)
            if not urls:
                # Fallback to DOM-based extraction
                urls = _extract_from_video_tag(page)
            if not urls:
                urls = _extract_from_source_tags(page)
            if not urls:
                urls = _extract_from_pace_f(page)
            if not urls:
                urls = _extract_from_data_attributes(page)

            return urls

        except TimeoutError:
            raise ExtractionTimeoutError(f"Extraction timed out after {wait_seconds}s")
        finally:
            browser.close()
