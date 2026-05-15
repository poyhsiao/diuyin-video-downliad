# Douyin Extractor Multi-Layer Fallback Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement multi-layer fallback DOM extraction to replace the broken `window.__pace_f` approach.

**Architecture:** Extract video URLs using 4 prioritized methods: `<video>` tag, `<source>` tags, `__pace_f` JSON, and data attributes. Each method is a separate helper function with unified `list[str]` interface.

**Tech Stack:** Python, Playwright, pytest-bdd, TDD

---

## File Structure

```
src/douyin_download/
  └─ extractor.py              # Modify: add 4 helper methods + chain

tests/
  └─ test_extractor_unit.py   # Create: TDD unit tests

features/
  ├─ extractor.feature        # Modify: update BDD scenarios
  └─ steps/extractor_steps.py # Modify: add step definitions
```

---

## Task 1: Create test_extractor_unit.py with TDD

**Files:**
- Create: `tests/test_extractor_unit.py`
- Test: `tests/test_extractor_unit.py`

- [ ] **Step 1: Write failing test for `_extract_from_video_tag`**

```python
# tests/test_extractor_unit.py
"""Unit tests for extractor helper methods."""

import pytest
from unittest.mock import MagicMock

from douyin_download.extractor import _extract_from_video_tag


class TestExtractFromVideoTag:
    """Tests for _extract_from_video_tag function."""

    def test_video_tag_found(self) -> None:
        """Should return URL when <video> tag has src."""
        mock_page = MagicMock()
        mock_video = MagicMock()
        mock_video.get_attribute.return_value = "https://v5.video.mp4"
        mock_page.query_selector.return_value = mock_video

        result = _extract_from_video_tag(mock_page)
        assert result == ["https://v5.video.mp4"]

    def test_video_tag_not_found(self) -> None:
        """Should return empty list when no <video> tag."""
        mock_page = MagicMock()
        mock_page.query_selector.return_value = None

        result = _extract_from_video_tag(mock_page)
        assert result == []
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_extractor_unit.py::TestExtractFromVideoTag::test_video_tag_found -v`
Expected: FAIL with `AttributeError: module 'douyin_download.extractor' has no attribute '_extract_from_video_tag'`

- [ ] **Step 3: Write minimal implementation stub**

```python
# Add to extractor.py

def _extract_from_video_tag(page) -> list[str]:
    """Extract URLs from <video> tag."""
    return []
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/python -m pytest tests/test_extractor_unit.py::TestExtractFromVideoTag::test_video_tag_not_found -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/test_extractor_unit.py src/douyin_download/extractor.py
git commit -m "feat: add test skeleton for video tag extraction"
```

---

## Task 2: Implement `_extract_from_video_tag`

**Files:**
- Modify: `src/douyin_download/extractor.py`

- [ ] **Step 1: Run all tests to confirm current state**

Run: `.venv/bin/python -m pytest tests/test_extractor_unit.py -v`
Expected: 2 tests pass (both video_tag tests)

- [ ] **Step 2: Implement full `_extract_from_video_tag`**

```python
def _extract_from_video_tag(page) -> list[str]:
    """Extract URLs from <video> tag.

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
```

- [ ] **Step 3: Run tests to verify**

Run: `.venv/bin/python -m pytest tests/test_extractor_unit.py::TestExtractFromVideoTag -v`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add src/douyin_download/extractor.py
git commit -m "feat: implement _extract_from_video_tag helper"
```

---

## Task 3: Create and pass tests for `_extract_from_source_tags`

**Files:**
- Modify: `tests/test_extractor_unit.py`
- Modify: `src/douyin_download/extractor.py`

- [ ] **Step 1: Add failing test for `_extract_from_source_tags`**

```python
def test_source_tags_found(self) -> None:
    """Should return URLs from all <source> tags."""
    mock_page = MagicMock()
    mock_source1 = MagicMock()
    mock_source1.get_attribute.return_value = "https://v5.source1.mp4"
    mock_source2 = MagicMock()
    mock_source2.get_attribute.return_value = "https://v3.source2.mp4"
    mock_page.query_selector_all.return_value = [mock_source1, mock_source2]

    result = _extract_from_source_tags(mock_page)
    assert result == ["https://v5.source1.mp4", "https://v3.source2.mp4"]


def test_source_tags_not_found(self) -> None:
    """Should return empty list when no <source> tags."""
    mock_page = MagicMock()
    mock_page.query_selector_all.return_value = []

    result = _extract_from_source_tags(mock_page)
    assert result == []
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_extractor_unit.py::TestExtractFromSourceTags -v`
Expected: FAIL with `AttributeError: module 'douyin_download.extractor' has no attribute '_extract_from_source_tags'`

- [ ] **Step 3: Implement `_extract_from_source_tags`**

```python
def _extract_from_source_tags(page) -> list[str]:
    """Extract URLs from <source> tags.

    Args:
        page: Playwright page object

    Returns:
        List of URLs found in source src attributes
    """
    sources = page.query_selector_all("source")
    urls = []
    for source in sources:
        src = source.get_attribute("src")
        if src and ("mp4" in src or "play" in src):
            urls.append(src)
    return urls
```

- [ ] **Step 4: Run tests to verify**

Run: `.venv/bin/python -m pytest tests/test_extractor_unit.py::TestExtractFromSourceTags -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/test_extractor_unit.py src/douyin_download/extractor.py
git commit -m "feat: add _extract_from_source_tags helper"
```

---

## Task 4: Add tests for `_extract_from_pace_f` list fix

**Files:**
- Modify: `tests/test_extractor_unit.py`
- Modify: `src/douyin_download/extractor.py`

- [ ] **Step 1: Add test for list input (existing bug)**

```python
def test_pace_f_list_input(self) -> None:
    """Should return empty list when __pace_f returns a list, not dict."""
    mock_page = MagicMock()
    mock_page.evaluate.return_value = '[1, 2, 3]'  # JSON list, not dict

    result = _extract_from_pace_f(mock_page)
    assert result == []  # Should not crash with AttributeError
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_extractor_unit.py::TestExtractFromPaceF -v`
Expected: FAIL with `AttributeError: 'list' object has no attribute 'values'`

- [ ] **Step 3: Fix `_extract_from_pace_f` to handle list**

```python
def _extract_from_pace_f(page) -> list[str]:
    """Extract URLs from window.__pace_f JSON.

    Args:
        page: Playwright page object

    Returns:
        List of URLs found in __pace_f data
    """
    pace_data = page.evaluate("""() => {
        try { return JSON.stringify(window.__pace_f || {}); }
        catch (e) { return '{}'; }
    }""")
    try:
        data = json.loads(pace_data)
        if isinstance(data, dict):  # FIX: check isinstance before .values()
            urls = []
            for val in data.values():
                if isinstance(val, str) and ("mp4" in val or "play" in val):
                    urls.append(val)
                elif isinstance(val, dict):
                    for v in val.values():
                        if isinstance(v, str) and ("mp4" in v or "play" in v):
                            urls.append(v)
            return urls
    except (json.JSONDecodeError, ValueError):
        pass
    return []
```

- [ ] **Step 4: Run tests to verify**

Run: `.venv/bin/python -m pytest tests/test_extractor_unit.py::TestExtractFromPaceF -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/test_extractor_unit.py src/douyin_download/extractor.py
git commit -m "fix: handle list input in _extract_from_pace_f"
```

---

## Task 5: Add tests and implement `_extract_from_data_attributes`

**Files:**
- Modify: `tests/test_extractor_unit.py`
- Modify: `src/douyin_download/extractor.py`

- [ ] **Step 1: Add failing test**

```python
def test_data_attributes_found(self) -> None:
    """Should extract URLs from data-* and href attributes."""
    mock_page = MagicMock()
    mock_page.evaluate.return_value = '{"videoUrl": "https://v5.data.mp4"}'

    result = _extract_from_data_attributes(mock_page)
    assert result == ["https://v5.data.mp4"]


def test_data_attributes_not_found(self) -> None:
    """Should return empty list when no mp4/play in attributes."""
    mock_page = MagicMock()
    mock_page.evaluate.return_value = '{"other": "not-a-video-url"}'

    result = _extract_from_data_attributes(mock_page)
    assert result == []
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_extractor_unit.py::TestExtractFromDataAttributes -v`
Expected: FAIL with `AttributeError: module 'douyin_download.extractor' has no attribute '_extract_from_data_attributes'`

- [ ] **Step 3: Implement `_extract_from_data_attributes`**

```python
def _extract_from_data_attributes(page) -> list[str]:
    """Extract URLs from page attributes containing mp4/play.

    Args:
        page: Playwright page object

    Returns:
        List of URLs found in data-* and href attributes
    """
    import re
    all_html = page.content()
    pattern = r'(?:href|data-src|data-url)=["\']([^"\']*[mp4|play][^"\']*)["\']'
    matches = re.findall(pattern, all_html, re.IGNORECASE)
    return list(set(matches))
```

- [ ] **Step 4: Run tests to verify**

Run: `.venv/bin/python -m pytest tests/test_extractor_unit.py::TestExtractFromDataAttributes -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/test_extractor_unit.py src/douyin_download/extractor.py
git commit -m "feat: add _extract_from_data_attributes helper"
```

---

## Task 6: Update `extract_cdn_url` to chain all methods

**Files:**
- Modify: `src/douyin_download/extractor.py`

- [ ] **Step 1: Run all unit tests first**

Run: `.venv/bin/python -m pytest tests/test_extractor_unit.py -v`
Expected: All tests pass

- [ ] **Step 2: Update `extract_cdn_url` to use fallback chain**

```python
def extract_cdn_url(url: str, wait_seconds: int = 10) -> list[str]:
    """Extract video CDN URLs with multi-layer fallback.

    Args:
        url: Douyin video URL
        wait_seconds: Maximum wait time for page load

    Returns:
        List of CDN URLs found on page (empty if none)

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

            # Try each extraction method in priority order
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
```

- [ ] **Step 3: Run tests to verify**

Run: `.venv/bin/python -m pytest tests/test_extractor_unit.py -v`
Expected: All tests pass

- [ ] **Step 4: Commit**

```bash
git add src/douyin_download/extractor.py
git commit -m "feat: chain all extraction methods in extract_cdn_url"
```

---

## Task 7: Update BDD scenarios

**Files:**
- Modify: `features/extractor.feature`
- Modify: `features/steps/extractor_steps.py`

- [ ] **Step 1: Update `extractor.feature` with new scenarios**

```gherkin
Feature: CDN URL 多層 Fallback 提取功能

  Scenario: 從 <video> 標籤提取 URL
    Given 抖音頁面包含 "<video src='https://v5.video.mp4'></video>"
    When 提取 CDN URL
    Then 結果應包含 "https://v5.video.mp4"
    And 結果應至少有 1 個 URL

  Scenario: Fallback 到 <source> 標籤
    Given 抖音頁面無 <video> 但有 "<source src='https://v3.source.mp4'>"
    When 提取 CDN URL
    Then 結果應包含 "https://v3.source.mp4"

  Scenario: Fallback 到 __pace_f
    Given 抖音頁面無 DOM 標籤但有 __pace_f 数据 '{"video": "https://v5.pace.mp4"}'
    When 提取 CDN URL
    Then 結果應包含 "https://v5.pace.mp4"

  Scenario: __pace_f 返回 list 時不崩潰
    Given __pace_f 返回列表 "[1, 2, 3]"
    When 提取 CDN URL
    Then 結果應為空陣列

  Scenario: 所有方法都失敗
    Given 抖音頁面無任何視頻 URL
    When 提取 CDN URL
    Then 結果應為空陣列

  Scenario: URL 品質排序
    Given 一組 URL ["https://aweme/v1/play/test", "https://aweme/v3-test", "https://aweme/v5-test"]
    When 系統排序 URL
    Then v5 URL 應排在第一位
    And v3 URL 應排在第二位
    And aweme URL 應排在第三位
```

- [ ] **Step 2: Run BDD tests**

Run: `.venv/bin/python -m pytest features/extractor.feature -v`
Expected: BDD scenarios pass

- [ ] **Step 3: Commit**

```bash
git add features/extractor.feature features/steps/extractor_steps.py
git commit -m "test: update BDD scenarios for multi-layer fallback"
```

---

## Task 8: Final verification

**Files:**
- Test: All project tests

- [ ] **Step 1: Run all unit tests**

Run: `.venv/bin/python -m pytest tests/ -v`
Expected: All pass

- [ ] **Step 2: Run all BDD tests**

Run: `.venv/bin/python -m pytest features/ -v`
Expected: All pass

- [ ] **Step 3: Check coverage**

Run: `.venv/bin/python -m pytest tests/ --cov=src/douyin_download --cov-report=term-missing`
Expected: Coverage >= 80%

- [ ] **Step 4: Manual verification**

```bash
.venv/bin/douyin info https://v.douyin.com/dTnyWmNCaxA
# Expected: Video ID: dTnyWmNCaxA, Available URLs: N, Best quality URL: https://...
```

- [ ] **Step 5: Commit all remaining changes**

```bash
git add -A
git commit -m "feat: complete multi-layer fallback extractor"
```

---

## Self-Review

**Spec coverage:**
- ✅ Multi-layer fallback architecture
- ✅ 4 extraction methods (video, source, pace_f, data attrs)
- ✅ TDD tests for each method
- ✅ BDD scenarios updated
- ✅ List handling fix included

**Placeholder scan:**
- ✅ No TBD/TODO
- ✅ No "implement later"
- ✅ All code blocks complete

**Type consistency:**
- ✅ All methods return `list[str]`
- ✅ `extract_cdn_url` signature unchanged (same parameters)
- ✅ Helper methods use `page` as first arg throughout