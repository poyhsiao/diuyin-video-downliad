# FastAPI + Docker 部署設計文件

**日期：** 2026-05-15
**狀態：** 已核准

---

## 1. 概述

將現有 Douyin CLI 工具擴展為 API 服務，支援 Docker/Docker Compose 部署。

---

## 2. 架構

```
┌─────────────┐     ┌─────────────┐     ┌──────────────┐
│   Nginx     │────▶│  FastAPI    │────▶│  Playwright  │
│ (反向代理)   │     │  (Gunicorn) │     │  (下載器)     │
└─────────────┘     └─────────────┘     └──────────────┘
     Port 80/443         Port 8000           內部
```

### 組件職責

| 組件 | 職責 |
|------|------|
| Nginx | 反向代理、SSL 終止、負載均衡 |
| Gunicorn + Uvicorn workers | WSGI 伺服器，處理並發 |
| FastAPI | API 邏輯、任務管理 |
| Playwright | 影片 URL 提取 |

---

## 3. API Endpoints

URL Prefix: `/api/v1`

| Method | Path | 說明 |
|--------|------|------|
| POST | `/api/v1/download` | 建立下載任務 |
| GET | `/api/v1/tasks/{task_id}` | 查詢任務狀態 |
| GET | `/api/v1/tasks` | 列出所有任務 |
| DELETE | `/api/v1/tasks/{task_id}` | 取消任務 |
| GET | `/health` | 健康檢查 |
| GET | `/docs` | Swagger UI (OpenAPI) |
| GET | `/redoc` | ReDoc 文件 |

### POST /api/v1/download

**請求：**
```json
{
  "url": "https://www.douyin.com/video/xxx",
  "quality": "720p",
  "callback_url": "https://example.com/webhook",
  "output_dir": "/data/downloads"
}
```

**響應（同步模式）：**
```json
{
  "status": "completed",
  "task_id": "uuid",
  "video_id": "xxx",
  "path": "/data/downloads/xxx.mp4",
  "file_size": 1024000
}
```

**響應（非同步模式，callback_url 提供時）：**
```json
{
  "status": "pending",
  "task_id": "uuid"
}
```

---

## 4. 環境變數

所有配置透過 `.env` 管理，有預設值：

```env
# API 設定
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=4
API_RELOAD=false

# 路徑設定
DOWNLOAD_OUTPUT_DIR=/data/downloads
TEMP_DIR=/data/temp

# Nginx
NGINX_PORT=80
NGINX_SSL_PORT=443

# 預設值
DEFAULT_QUALITY=original
MAX_CONCURRENT_DOWNLOADS=5
TASK_TIMEOUT_SECONDS=300

# Playwright
PLAYWRIGHT_BROWSERS_PATH=/ms-playwright
```

---

## 5. Docker 部署

### 新增檔案

- `Dockerfile` - FastAPI 應用容器
- `docker-compose.yml` - 完整部署配置
- `docker-compose.prod.yml` - 生產環境配置
- `.env.example` - 環境變數範例
- `nginx.conf` - Nginx 配置

### Docker Compose 結構

```yaml
services:
  app:
    build: .
    volumes:
      - ./data:/data
    env_file:
      - .env
    depends_on:
      - nginx

  nginx:
    image: nginx:latest
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./data:/data
```

---

## 6. 測試要求

### 覆蓋率目標
- 單元測試：80%+ coverage
- API endpoints：e2e 測試
- BDD 整合測試

### 測試工具
- pytest + pytest-asyncio（單元測試）
- pytest-bdd（BDD 測試）
- httpx + TestClient（API 測試）

---

## 7. CI/CD 整合

- GitHub Actions workflow 需更新以支援：
  - Docker build + push
  - docker-compose 測試
  - API e2e 測試

---

## 8. 開發規範

- 完全使用 uv 管理套件
- 參考 Context7 文件
- TDD 方式開發
- 所有配置透過環境變數