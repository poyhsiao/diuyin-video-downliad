# 抖音連結格式優化計劃

## 問題分析

### 用戶分享格式
```
7.61 复制打开抖音，看看【一蛙AI的作品】到底什么是Agent Harness? 视频源详细... https://v.douyin.com/NdvdvNIN50I/ NWZ:/ y@g.bn :0pm 02/20
```

### 問題點

| # | 問題 | 嚴重性 | 說明 |
|---|------|--------|------|
| 1 | **URL 夾帶在文字中** | HIGH | 直接複製分享文字，URL 與描述混在一起 |
| 2 | **短網址未解析** | HIGH | `v.douyin.com/xxx` 需要 follow redirect 取得完整 URL |
| 3 | **無 URL 正規化** | MEDIUM | 各式格式（`/video/`, `aweme`, `v.douyin.com`）未統一處理 |
| 4 | **分享文字編碼** | MEDIUM | 可能包含 URL 編碼或特殊字符 |

### 現有程式碼缺口

- `extractor.py` - 直接假設輸入是乾淨的 URL
- `api.py` - Download endpoint 無 URL 前處理
- 無 URL 解析/清理模組

---

## 解決方案

### Phase 1: URL 正規化模組

新增 `src/douyin_download/url_normalizer.py`:

```python
"""URL normalization for Douyin video links."""

import re
from urllib.parse import urlparse

class InvalidURLError(Exception):
    """Raised when URL cannot be parsed."""

def extract_url_from_text(text: str) -> str | None:
    """Extract URL from messy share text.

    Args:
        text: Raw text from clipboard, possibly with extra content

    Returns:
        Extracted URL or None if not found
    """
    # Match common URL patterns
    pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
    matches = re.findall(pattern, text)
    return matches[0] if matches else None

def normalize_douyin_url(url: str) -> str:
    """Normalize various Douyin URL formats to standard form.

    Args:
        url: Douyin URL (various formats)

    Returns:
        Normalized URL
    """
    # Remove trailing slashes
    url = url.rstrip('/')

    # Handle short links (v.douyin.com)
    # TODO: implement short link resolution

    # Handle /video/ format
    # TODO: normalize to standard form

    return url

def resolve_short_url(url: str, timeout: int = 10) -> str:
    """Resolve short URL to final URL.

    Args:
        url: Short URL (v.douyin.com/xxx)
        timeout: Request timeout in seconds

    Returns:
        Resolved final URL

    Raises:
        InvalidURLError: If URL cannot be resolved
    """
    # TODO: implement HTTP redirect follow
    pass
```

### Phase 2: 整合進 API

修改 `api.py` 的 `create_download`:
- 新增 URL 前處理（extract + normalize）
- 失敗時回傳明確的錯誤訊息

---

## TDD 測試案例

### Unit Tests

```python
# tests/test_url_normalizer.py

def test_extract_url_from_clean_text():
    url = extract_url_from_text("https://www.douyin.com/video/7385822337847635259")
    assert url == "https://www.douyin.com/video/7385822337847635259"

def test_extract_url_from_share_text():
    text = "7.61 复制打开抖音，看看【一蛙AI的作品】 https://v.douyin.com/NdvdvNIN50I/ NWZ:/"
    url = extract_url_from_text(text)
    assert url == "https://v.douyin.com/NdvdvNIN50I"

def test_extract_url_from_mixed_content():
    text = "看看這個影片 https://v.douyin.com/iR2syBRn/ 复制此链接，打开Dou音搜索"
    url = extract_url_from_text(text)
    assert "v.douyin.com" in url

def test_extract_url_returns_none_when_no_url():
    text = "這是普通文字，沒有網址"
    url = extract_url_from_text(text)
    assert url is None

def test_normalize_strips_trailing_slash():
    url = normalize_douyin_url("https://www.douyin.com/video/7385822337847635259/")
    assert url == "https://www.douyin.com/video/7385822337847635259"

def test_normalize_handles_ampersand_encoded():
    url = normalize_douyin_url("https://www.douyin.com/video/7385822337847635259&amp;")
    assert not url.endswith("&amp;")
```

### BDD Scenarios

```gherkin
# tests/url_normalizer.feature

Feature: URL 正規化功能

  Scenario: 從分享文字正確取出 URL
    Given 用戶分享文字 "7.61 复制打开抖音，看看【一蛙AI的作品】 https://v.douyin.com/NdvdvNIN50I/ NWZ:/"
    When 系統提取 URL
    Then 結果應為 "https://v.douyin.com/NdvdvNIN50I"

  Scenario: 處理空無 URL 的文字
    Given 用戶輸入 "這只是普通文字"
    When 系統嘗試提取 URL
    Then 應回傳 None 或空值

  Scenario: 清理多餘斜線
    Given URL "https://www.douyin.com/video/7385822337847635259/"
    When 系統正規化 URL
    Then 不應有結尾斜線

  Scenario: 處理編碼的 URL
    Given URL "https://www.douyin.com/video/7385822337847635259&amp;test=1"
    When 系統正規化 URL
    Then 應解碼為標準格式

  Scenario: 解析短網址
    Given 短網址 "https://v.douyin.com/NdvdvNIN50I"
    When 系統解析為完整 URL
    Then 結果應為 "https://www.douyin.com/video/7385822337847635259" 或類似格式
```

---

## 實施順序

```
1. [TDD] 建立 url_normalizer.py + 單元測試
   - extract_url_from_text()
   - normalize_douyin_url()

2. [TDD] 建立短網址解析
   - resolve_short_url() with HTTP redirect follow

3. [BDD] 更新 url_normalizer.feature
   - 完整情境覆盖

4. [INTEGRATION] 整合進 api.py
   - create_download() 前處理

5. [INTEGRATION] 更新 extractor.feature
   - 加入 URL 前處理情境
```

---

## 預期產出

| 檔案 | 說明 |
|------|------|
| `src/douyin_download/url_normalizer.py` | URL 處理模組 |
| `tests/test_url_normalizer.py` | 單元測試 |
| `tests/url_normalizer.feature` | BDD 測試 |
| `src/douyin_download/api.py` (修改) | 整合 URL 前處理 |

---

## 驗收標準

- [ ] `extract_url_from_text()` 從分享文字正確取出 URL
- [ ] `normalize_douyin_url()` 清理多餘斜線與編碼
- [ ] `resolve_short_url()` 解析 v.douyin.com 短網址
- [ ] API 接受分享文字格式的輸入
- [ ] BDD 測試全部通過
- [ ] 80%+ 測試覆蓋率