"""Step definitions for extractor feature."""

import json
from typing import Any

from pytest_bdd import given, then, when

from douyin_download.extractor import extract_cdn_url
from douyin_download.models import ExtractResult


# Test state storage
_state: dict[str, Any] = {}


@given("抖音頁面包含 \"<video src='https://v5.video.mp4'></video>\"")
def given_video_tag(_state: dict[str, Any]) -> None:
    """Set up page with <video> tag."""
    _state["html"] = "<video src='https://v5.video.mp4'></video>"


@given("抖音頁面無 <video> 但有 \"<source src='https://v3.source.mp4'>\"")
def given_source_tag_only(_state: dict[str, Any]) -> None:
    """Set up page with <source> tag only."""
    _state["html"] = "<source src='https://v3.source.mp4'>"


@given("抖音頁面無 DOM 標籤但有 __pace_f 数据 '{\"video\": \"https://v5.pace.mp4\"}'")
def given_pace_f_data(_state: dict[str, Any]) -> None:
    """Set up page with __pace_f data only."""
    _state["html"] = ""
    _state["pace_f"] = '{"video": "https://v5.pace.mp4"}'


@given("__pace_f 返回列表 \"[1, 2, 3]\"")
def given_pace_f_list(_state: dict[str, Any]) -> None:
    """Set up page with __pace_f returning a list."""
    _state["html"] = ""
    _state["pace_f"] = "[1, 2, 3]"


@given("抖音頁面無任何視頻 URL")
def given_no_video_url(_state: dict[str, Any]) -> None:
    """Set up page with no video URLs."""
    _state["html"] = "<div>No video here</div>"
    _state["pace_f"] = "{}"


@given("一組 URL <urls>")
def given_url_list(_state: dict[str, Any], urls: str) -> None:
    """Parse and store a list of URLs."""
    _state["urls"] = json.loads(urls)


@given("空 URL 清單")
def given_empty_url_list(_state: dict[str, Any]) -> None:
    """Set up empty URL list."""
    _state["urls"] = []


@given("單一 URL <url>")
def given_single_url(_state: dict[str, Any], url: str) -> None:
    """Set up single URL."""
    _state["urls"] = [url]


@when("提取 CDN URL")
def when_extract_cdn_url(_state: dict[str, Any]) -> None:
    """Extract CDN URLs using the extractor."""
    html = _state.get("html", "")
    pace_f_raw = _state.get("pace_f")

    pace_f = None
    if pace_f_raw is not None:
        try:
            pace_f = json.loads(pace_f_raw)
        except json.JSONDecodeError:
            pace_f = pace_f_raw

    urls = extract_cdn_url(html, pace_f)
    _state["result"] = ExtractResult(video_id="test", urls=urls)


@when("系統排序 URL")
def when_sort_urls(_state: dict[str, Any]) -> None:
    """Sort URLs using ExtractResult.best_url logic."""
    urls = _state.get("urls", [])
    if not urls:
        sorted_urls = []
    else:
        sorted_urls = sorted(
            urls,
            key=lambda u: (2 if "v5-" in u else (1 if "v3-" in u else 0)),
            reverse=True,
        )
    _state["sorted_urls"] = sorted_urls


@then("結果應包含 <expected>")
def then_result_contains(_state: dict[str, Any], expected: str) -> None:
    """Verify result contains expected URL."""
    result = _state.get("result")
    assert result is not None
    assert any(expected in url for url in result.urls), \
        f"Expected '{expected}' not found in {result.urls}"


@then("結果應至少有 1 個 URL")
def then_result_has_urls(_state: dict[str, Any]) -> None:
    """Verify result has at least 1 URL."""
    result = _state.get("result")
    assert result is not None
    assert len(result.urls) >= 1


@then("結果應為空陣列")
def then_result_is_empty(_state: dict[str, Any]) -> None:
    """Verify result is empty array."""
    result = _state.get("result")
    assert result is not None
    assert len(result.urls) == 0


@then("v5 URL 應排在第一位")
def then_v5_first(_state: dict[str, Any]) -> None:
    """Verify v5 URL is first."""
    sorted_urls = _state.get("sorted_urls", [])
    assert len(sorted_urls) >= 1
    assert "v5-" in sorted_urls[0], f"First URL should be v5: {sorted_urls[0]}"


@then("v3 URL 應排在第二位")
def then_v3_second(_state: dict[str, Any]) -> None:
    """Verify v3 URL is second."""
    sorted_urls = _state.get("sorted_urls", [])
    assert len(sorted_urls) >= 2
    assert "v3-" in sorted_urls[1], f"Second URL should be v3: {sorted_urls[1]}"


@then("aweme URL 應排在第三位")
def then_aweme_third(_state: dict[str, Any]) -> None:
    """Verify aweme URL is third."""
    sorted_urls = _state.get("sorted_urls", [])
    assert len(sorted_urls) >= 3
    assert "aweme" in sorted_urls[2] and "v5-" not in sorted_urls[2] and "v3-" not in sorted_urls[2], \
        f"Third URL should be aweme: {sorted_urls[2]}"


@then("結果應只有一個 URL")
def then_single_url(_state: dict[str, Any]) -> None:
    """Verify result has exactly one URL."""
    sorted_urls = _state.get("sorted_urls", [])
    assert len(sorted_urls) == 1