# Douyin Video Extractor 修復計畫

## 問題摘要

| 症狀 | 嚴重程度 | 根因 |
|------|---------|------|
| `'list' object has no attribute 'values'` | 🔴 已修復 | `extractor.py` 未檢查 JSON 解析後是否為 dict |
| `No video URLs extracted` | 🔴 進行中 | Douyin 網站 JS 結構變更，`window.__pace_f` 已非影片 URL 來源 |

---

## 已修復問題

### 1. `extractor.py` list 錯誤

**檔案：** `src/douyin_download/extractor.py:57-66`

**問題：** `json.loads(pace_data)` 可能返回 list 而非 dict，直接呼叫 `.values()` 導致錯誤。

**修復：**
```python
# 修復前
data = json.loads(pace_data)
for val in data.values():

# 修復後
data = json.loads(pace_data)
if isinstance(data, dict):  # <-- 新增檢查
    for val in data.values():
```

---

## 待修復問題

### 2. URL 提取失效 — Douyin JS 結構變更

**檔案：** `src/douyin_download/extractor.py`

**問題描述：**
- `window.__pace_f` 不再是影片 URL 的存放位置
- Playwright 抓取到的 JSON 結構已改變
- 目前 `extract_cdn_url()` 返回空清單 `[]`

**影響範圍：**
| 命令 | 現況 |
|------|------|
| `douyin session` | ✅ 正常（只做 URL 解析） |
| `douyin info` | ⚠️ 可執行但找不到 URL |
| `douyin download` | ❌ 失敗（NoCDNAvailableError） |

---

## 修復方案

### Phase 1: 探索當前 Douyin 頁面結構

需要找出當前 Douyin 頁面中影片 URL 的實際位置。

**可能的 JS 目標：**
1. `window.__INIT_PROPS__` 或 `window.__NEXT_DATA__`
2. `window.RENDER_DATA` 或類似的伺服器渲染資料
3. `<script id="__NEXT_DATA__">` 標籤內容
4. GraphQL endpoint 回應
5. `<video>` 或 `<source>` 標籤的 direct src

**建議研究方式：**
```bash
# 在瀏覽器 DevTools 中執行
JSON.stringify(window)
# 搜尋 mp4, play, video 等關鍵字
```

---

### Phase 2: 更新 extraction 邏輯

根據 Phase 1 的研究結果，更新 `extract_cdn_url()` 函式。

**目標讀取位置（待確認）：**
1. 頁面 `<video>` 標籤的 `src` 屬性
2. 頁面 `<script>` 標籤內的 JSON 資料
3. Network 請求中的影片 API 回應

---

### Phase 3: 驗證測試

```bash
# 基本測試
.venv/bin/douyin info https://v.douyin.com/dTnyWmNCaxA

# 預期輸出（有 URL）
# Video ID: dTnyWmNCaxA
# Available URLs: 3
# Best quality URL: https://...

# 下載測試
.venv/bin/douyin download https://v.douyin.com/dTnyWmNCaxA
```

---

## 實作建議

### 檔案：`src/douyin_download/extractor.py`

建議增加多個 fallback 策略：

```python
# 1. 嘗試 window.__pace_f（目前失效，保留作為 fallback）
# 2. 嘗試讀取 <script id="__NEXT_DATA__"> 內容
# 3. 嘗試讀取 <video> 標籤的 src
# 4. 嘗試 Network interception（進階，需 Playwright 的 route API）
```

---

## 預期產出

修復完成後，預期以下命令能正常運作：

```bash
.venv/bin/douyin info https://v.douyin.com/dTnyWmNCaxA
# → Video ID: dTnyWmNCaxA
# → Available URLs: N
# → Best quality URL: https://...

.venv/bin/douyin download https://v.douyin.com/dTnyWmNCaxA
# → 下載影片至 ~/Downloads/douyin_{video_id}.mp4
```

---

## 時間預估

| Phase | 工作內容 | 複雜度 |
|-------|---------|--------|
| Phase 1 | 研究當前 Douyin 頁面結構 | 中 |
| Phase 2 | 更新 extraction 邏輯 | 高 |
| Phase 3 | 驗證測試 | 低 |

---

## 待確認事項

1. 目標影片 URL 是否仍然有效（可能影片已下架）
2. 是否需要處理 Cloudflare 或 Bot 檢測
3. 是否考慮備援方案（如使用其他第三方解析 API）

---

*建立日期：2026-05-15*