# Douyin Extractor 多層 Fallback 修復設計

**日期：** 2026-05-15
**狀態：** Approved

---

## 目標

修復 `extract_cdn_url()` 使其能在 Douyin 頁面結構變更時，仍能可靠地提取影片 CDN URL。

---

## 問題

目前 `extract_cdn_url()` 只依賴 `window.__pace_f`，當 Douyin 變更 JS 結構後，提取功能完全失效（回傳空列表）。

---

## 解決方案：多層 Fallback DOM 提取

### 優先級順序

| 優先級 | Method | 說明 |
|-------|--------|------|
| 1 | `_extract_from_video_tag()` | 從 `<video>` 標籤提取 `src` |
| 2 | `_extract_from_source_tags()` | 從 `<source>` 標籤提取 `src` |
| 3 | `_extract_from_pace_f()` | 現有邏輯：解析 `window.__pace_f` |
| 4 | `_extract_from_data_attributes()` | 掃描包含 `mp4`/`play` 的屬性 |

所有 method 回傳 `list[str]`。找不到 URL 時回傳空列表，不拋例外（由上層決定如何處理）。

---

## 檔案結構

```
src/douyin_download/
  └─ extractor.py          # 修改：新增 3 個 helper methods

tests/
  └─ test_extractor_unit.py   # 新增：單元測試（各 method）

features/
  └─ extractor.feature        # 修改：更新 BDD 情境
  └─ steps/extractor_steps.py # 修改：新增 step definitions
```

---

## 介面

```python
def extract_cdn_url(url: str, wait_seconds: int = 10) -> list[str]:
    """Extract video CDN URLs with multi-layer fallback.

    Tries in order:
    1. <video> tag src
    2. <source> tags src
    3. window.__pace_f JSON (existing logic)
    4. data attributes with mp4/play

    Returns:
        List of CDN URLs found (empty if none)
    """
```

---

## 單元測試

| 測試 | 驗證 |
|------|------|
| `test_extract_from_video_tag_found` | 找到 `<video src>` 時回傳 URL |
| `test_extract_from_video_tag_not_found` | 無 `<video>` 時回傳空列表 |
| `test_extract_from_source_tags_found` | 找到 `<source>` 時回傳 URL |
| `test_extract_from_source_tags_not_found` | 無 `<source>` 時回傳空列表 |
| `test_extract_from_pace_f_dict` | 輸入為 dict 時正常解析 |
| `test_extract_from_pace_f_list` | 輸入為 list 時不回傳（已修復） |
| `test_extract_fallback_chain` | 依優先級順序嘗試 |

---

## BDD 情境

### 情境 1：DOM 提取成功
```gherkin
Given 抖音頁面包含 <video src="https://example.com/video.mp4">
When 提取 CDN URL
Then 結果應包含 "https://example.com/video.mp4"
```

### 情境 2：Fallback 鏈
```gherkin
Given 抖音頁面無 <video> 但有 <source src="https://example.com/src.mp4">
When 提取 CDN URL
Then 結果應包含 "https://example.com/src.mp4"
```

### 情境 3：全部失敗
```gherkin
Given 抖音頁面無任何視頻 URL
When 提取 CDN URL
Then 結果應為空陣列
```

---

## Mock Fixtures

使用預先快取的 HTML 字串測試，不需實際網路請求：

```python
HTML_WITH_VIDEO = '<html><video src="https://v5.video.mp4"></video></html>'
HTML_WITH_SOURCE = '<html><source src="https://source.video.mp4"></html>'
HTML_EMPTY = '<html><body>No video</body></html>'
```

---

## 實作順序（TDD）

1. **RED** — 寫測試（`test_extractor_unit.py`）
2. **GREEN** — 實作最小解法（`_extract_from_video_tag`）
3. **REFACTOR** — 重構並擴展到其他 method
4. **BDD** — 更新 `extractor.feature` 情境並驗證

---

## 風險

| 風險 | 緩解 |
|------|------|
| Douyin 頁面需要登入才能看到 video | 預留 `VideoNotFoundError` 例外處理 |
| JavaScript 執行時間過長 | `wait_seconds` 參數可調整，預設 10 秒 |
| 測試 fixture 與實際 DOM 不符 | 初期使用 mock，真實環境需驗證 |

---

## 預期產出

修復完成後：
- `douyin info <url>` — 能顯示找到的 URL 數量
- `douyin download <url>` — 能成功下載影片

---

*建立日期：2026-05-15*
* Brainstorming 通過：2026-05-15*