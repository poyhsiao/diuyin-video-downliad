# 抖音影片下載功能 — TDD + BDD 開發計畫

> **實驗結果（2026-05-10）**
> URL `7637075230132849971` 匿名提取測試：
> - Video ID: ✅ 正確解析
> - Title: ✅ `如何让Agent写的代码能够运用于生产环境`
> - CDN URL: ✅ 在 `<video src>` 中找到（324kbps, ~700秒）
> - 匿名下載: ✅ 206 Partial Content, `ftyp isom` 有效 MP4
> - **結論：無需登入即可下載，品質約 480p（324kbps bitrate）**

---

## 一、開發原則

```
┌──────────────────────────────────────────────────────────────┐
│  開發策略：匿名先行，選擇性登入                                │
│                                                              │
│  Phase 0: Anonymous Extractor（核心功能，優先實作）          │
│    → 無需登入即可提取 + 下載                                  │
│    → 品質上限：480p（324kbps）                                │
│                                                              │
│  Phase 5: Login（可選功能，有需要再啟用）                    │
│    → 提供更高品質（720p/1080p）                               │
│    → 非必要，預設關閉                                          │
└──────────────────────────────────────────────────────────────┘

每個功能都遵循 TDD 循環：
  1. 寫一個 BDD 測試（Red — 測試失敗）
  2. 實作功能（Green — 測試通過）
  3. 重構（Refactor — 保持測試綠燈）

驗證方式：
  - 單元測試：pytest 單元測試
  - BDD 情境：pytest-bdd 執行 .feature 檔案
  - 整合測試：端到端 CLI 指令測試
```

---

## 二、測試架構

```
douyin_download/              # 原始碼（本體）
├── src/douyin_download/
│   ├── __init__.py
│   ├── models.py             # Data class（Session, VideoQuality, ExtractResult）
│   ├── extractor.py          # Playwright CDN URL 提取（核心）
│   ├── core.py               # 下載器（requests + Range 支援）
│   ├── auth.py               # 選擇性登入（Phase 5 才啟用）
│   ├── cli.py                # 互動式 CLI
│   └── api.py                # FastAPI 端點（Phase 6，可選）

tests/                        # 測試
├── unit/                     # 純單元測試（小範圍）
│   ├── test_models.py        # Data class 結構驗證
│   ├── test_extractor.py     # 提取邏輯（mock Playwright）
│   ├── test_core.py          # 下載、Range、進度邏輯
│   └── test_auth.py          # Auth 邏輯（Phase 5 才啟用）
└── integration/              # BDD 整合測試（大範圍）
    ├── features/             # Gherkin 規格文件（交付文件）
    │   ├── anonymous_extractor.feature   # Phase 0
    │   ├── extractor.feature             # Phase 1
    │   ├── download.feature              # Phase 2
    │   ├── cli.feature                   # Phase 3
    │   ├── auth.feature                  # Phase 5（可選）
    │   └── api.feature                   # Phase 6（可選）
    └── steps/              # Step definitions（與 .feature 一一對應）
        ├── __init__.py
        ├── anonymous_extractor_steps.py
        ├── extractor_steps.py
        ├── download_steps.py
        ├── cli_steps.py
        ├── auth_steps.py      # Phase 5
        └── api_steps.py       # Phase 6
```

---

## 三、Phase 0 — Anonymous Extractor（匿名先行核心）

> **已驗證可行**：Playwright 讀取 `<video src>` 即可取得 CDN URL，requests 即可下載。

### Step 0.1：寫測試（Red）

**`features/anonymous_extractor.feature`**
```gherkin
Feature: 匿名影片提取與下載

  Scenario: 提取公開影片 CDN URL
    Given 抖音 URL "https://www.douyin.com/video/7637075230132849971"
    When 使用 Playwright 提取影片資訊
    Then 結果應包含 video_id "7637075230132849971"
    And 結果應包含 title
    And 結果應包含至少一個 CDN URL

  Scenario: 匿名下載成功
    Given 已取得 CDN URL
    When 使用 requests 下載影片
    Then HTTP 狀態應為 206 或 200
    And 檔案內容應為有效的 MP4（ftyp isom）

  Scenario: URL 解析為有效的 video ID
    Given 抖音 URL "https://www.douyin.com/video/7637075230132849971"
    When 解析 URL
    Then video_id 應為 "7637075230132849971"
    And 不應拋出例外

  Scenario: 解析無效 URL
    Given 非抖音 URL "https://example.com/video/123"
    When 解析 URL
    Then 應拋出 ValueError

  Scenario: 下載進度百分比
    Given CDN URL 和輸出路徑
    When 下載並回報進度
    Then 進度百分比應從 0 到 100
    And 最終應為 100

  Scenario: 輸出目錄不存在時自動建立
    Given CDN URL 和不存在的輸出目錄
    When 執行下載
    Then 目錄應被自動建立
    And 檔案應成功寫入

  Scenario: 檔名自動命名（使用 video_id）
    Given CDN URL 和輸出目錄
    When 執行下載（未指定檔名）
    Then 檔名應為 {video_id}.mp4
```

### Step 0.2：實作（Green）

**`src/douyin_download/models.py`**
```python
from dataclasses import dataclass, field

@dataclass
class VideoQuality:
    quality: str           # "480p", "360p", "auto"
    url: str
    size_mb: float | None = None
    bitrate: int | None = None

@dataclass
class ExtractResult:
    video_id: str
    title: str | None
    cover_url: str | None = None
    duration: float | None = None       # 秒
    qualities: list[VideoQuality] = field(default_factory=list)
    source: str = "anonymous"           # "anonymous" | "logged_in"
```

**`src/douyin_download/extractor.py`**（擴展）
```python
from playwright.sync_api import sync_playwright

def extract_video_info(url: str, timeout: int = 15) -> ExtractResult:
    """使用 Playwright 從頁面讀取 video src，解析為 ExtractResult。"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=timeout * 1000)
            import time; time.sleep(3)

            # 讀取 <video> elements
            videos = page.evaluate("""() => [
                ...document.querySelectorAll('video')
            ].map(v => ({ src: v.src || v.currentSrc || '', duration: v.duration || 0 }))""")

            # 找到有 src 的 video element（第一個就是主要播放源）
            video_data = next((v for v in videos if v['src']), None)

            if not video_data:
                raise RuntimeError("無可用的 CDN URL")

            # 從 URL 解析 video_id
            import re
            match = re.search(r'/video/(\d+)', url)
            video_id = match.group(1) if match else None

            title = page.title().replace(' - 抖音', '').strip()

            # 估算 bitrate → quality label
            # 324kbps → 480p（匿名通常在此範圍）
            qual = _estimate_quality(video_data['src'])

            return ExtractResult(
                video_id=video_id or "unknown",
                title=title,
                duration=video_data['duration'] or None,
                qualities=[VideoQuality(quality=qual, url=video_data['src'])],
                source="anonymous",
            )
        finally:
            browser.close()

def _estimate_quality(cdn_url: str) -> str:
    """從 URL 參數或 bitrate 估算品質標籤。"""
    # 例：br=324 → 480p
    import re
    m = re.search(r'br=(\d+)', cdn_url)
    if m:
        br = int(m.group(1))
        if br >= 800: return "720p"
        if br >= 400: return "480p"
        return "360p"
    return "480p"  # 預設匿名為 480p
```

**`src/douyin_download/core.py`**（新增下載器）
```python
import requests
from pathlib import Path
from dataclasses import dataclass

@dataclass
class DownloadResult:
    path: Path
    size_bytes: int
    quality: str
    duration_s: float

def download_video(
    cdn_url: str,
    output_dir: Path,
    quality: str = "auto",
    progress_callback=None,  # (bytes_received, total_bytes) -> None
) -> DownloadResult:
    """使用 requests Range header 下載影片（斷點續傳支援）。"""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "Referer": "https://www.douyin.com/",
    }

    with requests.get(cdn_url, headers=headers, stream=True, timeout=30) as r:
        total = int(r.headers.get("Content-Length", 0))
        ext = cdn_url.split("?")[0].split(".")[-1] or "mp4"
        out_path = output_dir / f"video.{ext}"

        bytes_downloaded = 0
        with open(out_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=65536):
                if chunk:
                    f.write(chunk)
                    bytes_downloaded += len(chunk)
                    if progress_callback:
                        progress_callback(bytes_downloaded, total or bytes_downloaded)

    return DownloadResult(
        path=out_path,
        size_bytes=bytes_downloaded,
        quality=quality,
        duration_s=0,
    )
```

### Step 0.3：重構（Refactor）

- 將 `_estimate_quality` 移至獨立的 `quality_estimator.py`
- Playwright 啟動參數抽為常數
- 加入 logging
- 加入 `DownloadProgress` dataclass 取代 tuple

---

## 四、Phase 1 — Extractor（強化提取）

### Step 1.1：寫測試（Red）

**`features/extractor.feature`**
```gherkin
Feature: CDN URL 提取（強化）

  Scenario: 提取公開影片資訊
    Given 抖音 URL "https://www.douyin.com/video/7637075230132849971"
    When 提取影片資訊
    Then 結果應包含 video_id "7637075230132849971"
    And 結果應包含 title
    And 結果應包含至少一個品質選項

  Scenario: URL 解析失敗
    Given 無效的抖音 URL "https://example.com/video/123"
    When 嘗試提取
    Then 應拋出 ValueError "無法解析 URL"

  Scenario: 網頁載入超時
    Given 抖音 URL 但網頁回應過慢
    When 提取超過 10 秒
    Then 應拋出 TimeoutError

  Scenario: 頁面無 CDN URL（iframe 或私人影片）
    Given 頁面解析後 CDN URL 為空
    When 提取影片資訊
    Then 應拋出 RuntimeError "無可用 CDN URL"

### Step 1.2：實作（Green）

### Step 1.3：重構（Refactor）

- 將品質估算移至獨立的 `quality_estimator.py`
- Playwright 啟動參數抽為常數
- 加入 logging

---

## 五、Phase 2 — Download 模組

### Step 2.1：寫測試（Red）

**`features/download.feature`**
```gherkin
Feature: 影片下載

  Scenario: 下載最高品質影片
    Given 已登入
    And 抖音 URL "https://www.douyin.com/video/7637075230132849971"
    And 輸出目錄 "/tmp/downloads"
    When 執行下載（未指定品質）
    Then 應下載最高可用品質
    And 檔案副檔名應為 .mp4
    And 檔案大小應 > 1MB

  Scenario: 下載指定品質（720p）
    Given 已登入
    And 抖音 URL
    When 執行下載並指定品質 "720p"
    Then 檔案應為 720p 品質
    And 檔案應存在

  Scenario: 指定品質不可用時回退
    Given 該影片最高只有 480p
    And 使用者指定品質 "1080p"
    When 執行下載
    Then 應自動降級至 480p
    And 系統應記錄 log "品質 1080p 不可用，降級至 480p"

  Scenario: 斷點續傳 - 網路中斷後繼續
    Given 下載到一半的檔案（部分下載）
    And 輸出目錄
    When 再次執行下載（相同 URL）
    Then 應從上次中斷處繼續
    And 不應重新下載已完成部分

  Scenario: 輸出目錄不存在時自動建立
    Given 輸出目錄 "/tmp/nonexistent/path"
    And 抖音 URL
    When 執行下載
    Then 系統應自動建立目錄
    And 檔案應成功寫入

  Scenario: 下載進度回傳
    Given 抖音 URL
    And 輸出目錄
    When 執行下載
    Then 進度回呼應被呼叫多次
    And 最終進度應為 100%

  Scenario: 檔名衝突處理
    Given 輸出目錄已有同名檔案
    And 抖音 URL
    When 執行下載
    Then 應覆蓋舊檔或附加時間戳
    And 不應拋出錯誤

  Scenario: 下載失敗 - 無效 URL
    Given 無效的抖音 URL
    When 執行下載
    Then 應拋出 ValueError
    And 錯誤訊息應包含 "無法解析"

  Scenario: 下載失敗 - 無可用品質
    Given 抖音 URL 但 CDN 無可用 URL
    When 執行下載
    Then 應拋出 RuntimeError "無可用 CDN URL"
```

### Step 2.2：實作（Green）

### Step 2.3：重構（Refactor）

- 斷點續傳：支援 Range header 檢查並resume
- 進度回呼抽為 protocol
- 錯誤類型統一（VideoNotFound, DownloadFailed, NoCDNAvailable）

---

## 六、Phase 3 — CLI 模組

### Step 4.1：寫測試（Red）

**`features/cli.feature`**
```gherkin
Feature: 命令列介面

  Scenario: 登入指令 - 互動式輸入
    Given 使用者未登入
    When 執行 "douyin login"
    Then 系統應提示輸入帳號
    And 系統應提示輸入密碼（隱藏）
    And 登入成功後顯示 "登入成功，xxx 歡迎您"

  Scenario: 登入指令 - 免互動模式
    When 執行 "douyin login -u test@example.com -p password123"
    Then 系統應直接嘗試登入
    And 成功後顯示 "登入成功"

  Scenario: 登入失敗
    When 執行 "douyin login -u wrong@example.com -p wrongpass"
    Then 應顯示錯誤 "帳號或密碼錯誤"
    And 退出碼應為 1

  Scenario: 下載指令 - 基本用法
    Given 抖音 URL
    When 執行 "douyin download <URL>"
    Then 應下載至 ~/Downloads
    And 顯示進度條

  Scenario: 下載指令 - 指定輸出目錄
    When 執行 "douyin download <URL> /tmp/myVideos"
    Then 應下載至 /tmp/myVideos
    And 顯示進度條

  Scenario: 下載指令 - 指定品質
    When 執行 "douyin download <URL> --quality 720p"
    Then 應下載 720p 品質
    And 顯示進度條

  Scenario: 下載指令 - 顯示所有可用品質
    When 執行 "douyin info <URL>"
    Then 應顯示標題、所有品質、預估大小

  Scenario: 下載指令 - 品質參數錯誤
    When 執行 "douyin download <URL> --quality invalid"
    Then 應顯示錯誤 "無效的品質選項：invalid"
    And 顯示可用選項

  Scenario: Session 狀態查詢
    When 執行 "douyin session"
    Then 若已登入顯示用戶資訊
    And 若未登入顯示 "未登入"

  Scenario: 登出指令
    When 執行 "douyin logout"
    Then Session 應被刪除
    And 顯示 "已登出"

  Scenario: 說明指令
    When 執行 "douyin --help"
    Then 應顯示所有可用指令
    And 顯示版本資訊

  Scenario: 未知指令
    When 執行 "douyin unknown_command"
    Then 應顯示錯誤 "未知的指令：unknown_command"
    And 顯示說明
    And 退出碼應為 1
```

### Step 4.2：實作（Green）

### Step 4.3：重構（Refactor）

---

## 七、Phase 5 — Login（選擇性登入）

> 非必要功能。預設關閉。有高畫質需求時再啟用。

### Step 5.1：寫測試（Red）

**`features/auth.feature`**
```gherkin
Feature: 選擇性登入

  Scenario: 登入成功，取得更高品質
    Given 使用者提供正確帳密
    When 執行登入
    Then 系統應建立有效 session
    And session 應包含 user_id, nickname, csrf_token

  Scenario: 登入失敗
    Given 使用者輸入錯誤帳密
    When 執行登入
    Then 系統應回應錯誤訊息 "帳號或密碼錯誤"
    And 不應建立 session

  Scenario: Session 檔案損壞
    Given 已存在 session 檔案但內容損壞
    When 使用者嘗試載入 session
    Then 系統應回應錯誤 "Session 無效"
    And 系統應提示重新登入

  Scenario: 使用者登出
    Given 使用者已登入
    When 執行登出
    Then session 應被刪除
    And 系統應回應 "已登出"
```

### Step 5.2：實作（Green）

**`src/douyin_download/auth.py`**
```python
import keyring
from pathlib import Path
import json

SESSION_FILE = Path("~/.config/douyin/session.json")

@dataclass
class UserSession:
    user_id: str
    nickname: str
    csrf_token: str
    cookies: dict
    expires_at: datetime

@dataclass
class LoginResult:
    success: bool
    session: UserSession | None
    error_message: str | None

def login(username: str, password: str) -> LoginResult:
    """POST /passport/web/login/v2/ with curl-cffi"""
    ...

def save_session(session: UserSession) -> None:
    ...

def load_session() -> UserSession | None:
    ...

def is_session_valid(session: UserSession) -> bool:
    ...

def logout() -> None:
    SESSION_FILE.unlink(missing_ok=True)
```

### Step 5.3：重構（Refactor）

- 提取加密/解密密碼的 helper
- 將 SESSION_FILE 改為可注入的 dependency

---

## 八、Phase 6 — API 模組（可選）

```gherkin
Feature: FastAPI 端點

  Scenario: 根路徑健康檢查
    When GET /api/v1/
    Then 回應 200 + {"status": "ok", "version": "0.1.0"}

  Scenario: 影片資訊端點
    When GET /api/v1/video?url=...
    Then 回應 200 + {video_id, title, qualities: [...]}

  Scenario: 下載端點
    When POST /api/v1/download {"url": "...", "quality": "720p"}
    Then 回應 200 + {"task_id": "...", "status": "started"}
```

---

## 九、完整 Phase 與 Step 對照表

```
Phase 0: Anonymous Extractor（7 個 BDD 情境）
  ├─ Step 0.1: 寫 anonymous_extractor.feature + anonymous_extractor_steps.py
  ├─ Step 0.2: 實作 models.py（VideoQuality, ExtractResult）, extractor.py, core.py
  └─ Step 0.3: 重構 + 寫 unit test_models.py, unit test_extractor.py

Phase 1: Extractor 強化（4 個 BDD 情境）
  ├─ Step 1.1: 寫 extractor.feature + extractor_steps.py
  ├─ Step 1.2: 實作 extractor.py（超時、錯誤處理）
  └─ Step 1.3: 重構 + 寫 unit test_extractor.py

Phase 2: Download（9 個 BDD 情境）
  ├─ Step 2.1: 寫 download.feature + download_steps.py
  ├─ Step 2.2: 實作 core.py（斷點續傳、進度回呼）
  └─ Step 2.3: 重構 + 寫 unit test_download.py

Phase 3: CLI（11 個 BDD 情境）
  ├─ Step 3.1: 寫 cli.feature + cli_steps.py
  ├─ Step 3.2: 實作 cli.py
  └─ Step 3.3: 重構 + 寫 unit test_cli.py

Phase 5: Login（4 個 BDD 情境，可選）
  ├─ Step 5.1: 寫 auth.feature + auth_steps.py
  ├─ Step 5.2: 實作 auth.py
  └─ Step 5.3: 重構 + 寫 unit test_auth.py

Phase 6: API（3 個 BDD 情境，可選）
```

---

## 十、預估產出

```
新增：
  src/douyin_download/
    ├── models.py             # VideoQuality, ExtractResult, DownloadResult
    ├── extractor.py          # Playwright CDN 提取（Phase 0 核心）
    ├── core.py               # 下載器（Phase 0 核心）
    ├── auth.py               # 選擇性登入（Phase 5）
    ├── cli.py                # 互動式 CLI（Phase 3）
    └── api.py                # FastAPI（Phase 6，可選）

  features/
    ├── anonymous_extractor.feature   # Phase 0
    ├── extractor.feature             # Phase 1
    ├── download.feature              # Phase 2
    ├── cli.feature                   # Phase 3
    ├── auth.feature                  # Phase 5（可選）
    └── api.feature                   # Phase 6（可選）

  tests/integration/steps/
    ├── anonymous_extractor_steps.py  # Phase 0
    ├── extractor_steps.py           # Phase 1
    ├── download_steps.py            # Phase 2
    ├── cli_steps.py                 # Phase 3
    ├── auth_steps.py                # Phase 5（可選）
    └── api_steps.py                 # Phase 6（可選）

  tests/unit/
    ├── test_models.py
    ├── test_extractor.py
    ├── test_core.py
    ├── test_download.py
    ├── test_cli.py
    └── test_auth.py                 # Phase 5

預估測試數量：
  - BDD 情境：38 個（7+4+9+11+4+3）
  - 單元測試：40+ 個
  - 總計：78+ 個測試
```