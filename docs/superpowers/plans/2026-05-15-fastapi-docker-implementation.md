# FastAPI + Docker 部署實作計劃

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 將 Douyin CLI 工具擴展為 API 服務，支援 Docker/Docker Compose 部署

**Architecture:** 使用 FastAPI + Gunicorn/Uvicorn workers + Nginx 反向代理。同步響應為主，支援可選 callback_url 回調。

**Tech Stack:** FastAPI, Uvicorn, Gunicorn, Nginx, Playwright, pytest, pytest-bdd, httpx

---

## 檔案結構

```
src/douyin_download/
├── __init__.py
├── api.py          # 擴展：完整的 API 端點
├── cli.py          # 不變
├── config.py       # 新增：環境變數配置管理
├── core.py         # 不變
├── extractor.py    # 不變
├── models.py       # 擴展：新增 API 相關 models
├── tasks.py        # 新增：任務管理（背景任務）
└── webhook.py      # 新增：回調發送

tests/
├── test_api.py              # 新增
├── conftest.py              # 擴展
└── ...

features/
└── api.feature              # 擴展

.github/workflows/
├── ci.yml                   # 擴展：新增 Docker build
└── release.yml              # 不變

Docker/
├── Dockerfile               # 新增
├── docker-compose.yml       # 新增
├── docker-compose.prod.yml  # 新增
└── nginx.conf               # 新增

.env.example                 # 新增
```

---

## 任務清單

### 任務 1: 建立 .env.example 和 config.py

**Files:**
- Create: `.env.example`
- Create: `src/douyin_download/config.py`

- [ ] **Step 1: 建立 .env.example**

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

Run: `cat > .env.example << 'EOF'\n# API 設定\nAPI_HOST=0.0.0.0\nAPI_PORT=8000\n...\nEOF`

- [ ] **Step 2: 建立 config.py**

```python
"""Environment configuration management."""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # API 設定
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_workers: int = 4
    api_reload: bool = False

    # 路徑設定
    download_output_dir: Path = Path("/data/downloads")
    temp_dir: Path = Path("/data/temp")

    # Nginx
    nginx_port: int = 80
    nginx_ssl_port: int = 443

    # 預設值
    default_quality: str = "original"
    max_concurrent_downloads: int = 5
    task_timeout_seconds: int = 300

    # Playwright
    playwright_browsers_path: Path = Path("/ms-playwright")


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
```

Run: `cat > src/douyin_download/config.py << 'EOF'\n"""Environment configuration management."""\n...\nEOF`

- [ ] **Step 3: 測試 config 載入**

Run: `cd /Users/kimhsiao/Templates/git/kimhsiao/diuyin-video-downliad && uv run python -c "from douyin_download.config import get_settings; s = get_settings(); print(f'output_dir={s.download_output_dir}')"`
Expected: `output_dir=/data/downloads`

- [ ] **Step 4: Commit**

```bash
git add .env.example src/douyin_download/config.py
git commit -m "feat: add environment configuration management"
```

---

### 任務 2: 建立任務管理系統 (tasks.py)

**Files:**
- Create: `src/douyin_download/tasks.py`
- Create: `tests/test_tasks.py`
- Modify: `src/douyin_download/models.py` (新增 TaskStatus, DownloadTask)

- [ ] **Step 1: 新增 API models 到 models.py**

```python
# Add to models.py
class TaskStatus(str, Enum):
    """Task status enum."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class DownloadTask:
    """Download task for API."""
    task_id: str
    video_url: str
    quality: str | None = None
    output_dir: Path | None = None
    callback_url: str | None = None
    status: TaskStatus = TaskStatus.PENDING
    video_id: str | None = None
    path: Path | None = None
    file_size: int | None = None
    error: str | None = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
```

Run: `cat src/douyin_download/models.py` 確認現有結構

- [ ] **Step 2: 建立 tasks.py**

```python
"""Task management for background downloads."""

import asyncio
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

import httpx

from douyin_download.models import DownloadTask, TaskStatus


class TaskManager:
    """Manages download tasks and background execution."""

    def __init__(self, timeout_seconds: int = 300):
        self._tasks: dict[str, DownloadTask] = {}
        self._timeout_seconds = timeout_seconds

    def create_task(
        self,
        video_url: str,
        quality: str | None = None,
        output_dir: Path | None = None,
        callback_url: str | None = None,
    ) -> DownloadTask:
        """Create a new download task."""
        task_id = str(uuid.uuid4())
        task = DownloadTask(
            task_id=task_id,
            video_url=video_url,
            quality=quality,
            output_dir=output_dir,
            callback_url=callback_url,
        )
        self._tasks[task_id] = task
        return task

    def get_task(self, task_id: str) -> DownloadTask | None:
        """Get task by ID."""
        return self._tasks.get(task_id)

    def list_tasks(self) -> list[DownloadTask]:
        """List all tasks."""
        return list(self._tasks.values())

    def update_task(self, task_id: str, **kwargs: Any) -> None:
        """Update task fields."""
        if task_id in self._tasks:
            task = self._tasks[task_id]
            for key, value in kwargs.items():
                if hasattr(task, key):
                    setattr(task, key, value)
            task.updated_at = datetime.now()

    async def execute_task(
        self,
        task_id: str,
        download_func: Callable,
    ) -> None:
        """Execute download task and send callback if configured."""
        task = self.get_task(task_id)
        if not task:
            return

        try:
            self.update_task(task_id, status=TaskStatus.RUNNING)
            result = await asyncio.wait_for(
                download_func(task.video_url, task.output_dir, task.quality),
                timeout=self._timeout_seconds,
            )
            self.update_task(
                task_id,
                status=TaskStatus.COMPLETED,
                video_id=result.video_id,
                path=result.path,
                file_size=result.file_size,
            )
        except asyncio.TimeoutError:
            self.update_task(task_id, status=TaskStatus.FAILED, error="Task timeout")
        except Exception as e:
            self.update_task(task_id, status=TaskStatus.FAILED, error=str(e))

        # Send callback if configured
        if task.callback_url:
            await self._send_callback(task)

    async def _send_callback(self, task: DownloadTask) -> None:
        """Send callback notification."""
        payload = {
            "task_id": task.task_id,
            "status": task.status.value,
            "video_id": task.video_id,
            "path": str(task.path) if task.path else None,
            "file_size": task.file_size,
            "error": task.error,
        }
        try:
            async with httpx.AsyncClient() as client:
                await client.post(task.callback_url, json=payload, timeout=10)
        except Exception:
            pass  # Log error in production


# Global task manager instance
_task_manager: TaskManager | None = None


def get_task_manager() -> TaskManager:
    """Get global task manager instance."""
    global _task_manager
    if _task_manager is None:
        from douyin_download.config import get_settings
        settings = get_settings()
        _task_manager = TaskManager(timeout_seconds=settings.task_timeout_seconds)
    return _task_manager
```

Run: `cat > src/douyin_download/tasks.py << 'EOF'\n...\nEOF`

- [ ] **Step 3: 建立 tasks 測試**

```python
"""Tests for task management."""

import pytest
from pathlib import Path

from douyin_download.models import TaskStatus
from douyin_download.tasks import TaskManager, get_task_manager


def test_create_task():
    """Test task creation."""
    manager = TaskManager()
    task = manager.create_task(
        video_url="https://example.com/video/123",
        quality="720p",
    )
    assert task.task_id is not None
    assert task.video_url == "https://example.com/video/123"
    assert task.quality == "720p"
    assert task.status == TaskStatus.PENDING


def test_get_task():
    """Test getting task by ID."""
    manager = TaskManager()
    task = manager.create_task(video_url="https://example.com/video/123")
    found = manager.get_task(task.task_id)
    assert found is not None
    assert found.task_id == task.task_id


def test_get_task_not_found():
    """Test getting non-existent task."""
    manager = TaskManager()
    found = manager.get_task("non-existent-id")
    assert found is None


def test_list_tasks():
    """Test listing all tasks."""
    manager = TaskManager()
    task1 = manager.create_task(video_url="https://example.com/video/1")
    task2 = manager.create_task(video_url="https://example.com/video/2")
    tasks = manager.list_tasks()
    assert len(tasks) == 2


def test_update_task():
    """Test updating task fields."""
    manager = TaskManager()
    task = manager.create_task(video_url="https://example.com/video/123")
    manager.update_task(
        task.task_id,
        status=TaskStatus.RUNNING,
        video_id="vid_123",
    )
    updated = manager.get_task(task.task_id)
    assert updated.status == TaskStatus.RUNNING
    assert updated.video_id == "vid_123"


def test_get_task_manager_singleton():
    """Test task manager singleton."""
    m1 = get_task_manager()
    m2 = get_task_manager()
    assert m1 is m2
```

Run: `cat > tests/test_tasks.py << 'EOF'\n...\nEOF`

- [ ] **Step 4: 執行測試**

Run: `uv run pytest tests/test_tasks.py -v`
Expected: PASS (all 6 tests)

- [ ] **Step 5: Commit**

```bash
git add src/douyin_download/tasks.py src/douyin_download/models.py tests/test_tasks.py
git commit -m "feat: add task management system for background downloads"
```

---

### 任務 3: 實作完整 API 端點

**Files:**
- Modify: `src/douyin_download/api.py`
- Create: `tests/test_api.py`

- [ ] **Step 1: 實作完整 api.py**

```python
"""FastAPI application for Douyin downloader."""

from pathlib import Path
from typing import Annotated

from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from fastapi.responses import FileResponse
from pydantic import BaseModel, HttpUrl

from douyin_download.config import get_settings
from douyin_download.core import download_video
from douyin_download.models import VideoQuality, DownloadResult, TaskStatus
from douyin_download.tasks import get_task_manager, TaskManager


app = FastAPI(
    title="Douyin Downloader API",
    description="API for downloading Douyin videos",
    version="0.2.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

settings = get_settings()


# Pydantic models for API
class DownloadRequest(BaseModel):
    """Download request model."""
    url: HttpUrl
    quality: str | None = None
    callback_url: str | None = None
    output_dir: str | None = None


class DownloadResponse(BaseModel):
    """Download response model."""
    status: str
    task_id: str | None = None
    video_id: str | None = None
    path: str | None = None
    file_size: int | None = None
    error: str | None = None


class TaskResponse(BaseModel):
    """Task status response model."""
    task_id: str
    video_url: str
    status: str
    video_id: str | None = None
    path: str | None = None
    file_size: int | None = None
    error: str | None = None


def get_manager() -> TaskManager:
    """Dependency for task manager."""
    return get_task_manager()


@app.get("/health")
def health_check() -> dict:
    """Health check endpoint."""
    return {"status": "healthy", "version": "0.2.0"}


@app.post("/api/v1/download", response_model=DownloadResponse)
def create_download(
    request: DownloadRequest,
    background_tasks: BackgroundTasks,
    manager: Annotated[TaskManager, Depends(get_manager)],
) -> DownloadResponse:
    """Create a new download task."""
    output_path = Path(request.output_dir) if request.output_dir else settings.download_output_dir

    # If callback_url provided, use async mode
    if request.callback_url:
        task = manager.create_task(
            video_url=str(request.url),
            quality=request.quality or settings.default_quality,
            output_dir=output_path,
            callback_url=request.callback_url,
        )
        background_tasks.add_task(
            manager.execute_task,
            task.task_id,
            lambda url, out, q: download_video(url, out, q),
        )
        return DownloadResponse(status="pending", task_id=task.task_id)

    # Synchronous mode
    try:
        video_id, path = download_video(
            str(request.url),
            output_path,
            quality=request.quality,
        )
        file_size = path.stat().st_size if path.exists() else None
        return DownloadResponse(
            status="completed",
            video_id=video_id,
            path=str(path),
            file_size=file_size,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/tasks/{task_id}", response_model=TaskResponse)
def get_task(
    task_id: str,
    manager: Annotated[TaskManager, Depends(get_manager)],
) -> TaskResponse:
    """Get task status."""
    task = manager.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return TaskResponse(
        task_id=task.task_id,
        video_url=task.video_url,
        status=task.status.value,
        video_id=task.video_id,
        path=str(task.path) if task.path else None,
        file_size=task.file_size,
        error=task.error,
    )


@app.get("/api/v1/tasks", response_model=list[TaskResponse])
def list_tasks(
    manager: Annotated[TaskManager, Depends(get_manager)],
) -> list[TaskResponse]:
    """List all tasks."""
    tasks = manager.list_tasks()
    return [
        TaskResponse(
            task_id=t.task_id,
            video_url=t.video_url,
            status=t.status.value,
            video_id=t.video_id,
            path=str(t.path) if t.path else None,
            file_size=t.file_size,
            error=t.error,
        )
        for t in tasks
    ]


@app.delete("/api/v1/tasks/{task_id}", response_model=DownloadResponse)
def cancel_task(
    task_id: str,
    manager: Annotated[TaskManager, Depends(get_manager)],
) -> DownloadResponse:
    """Cancel a task."""
    task = manager.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if task.status == TaskStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Cannot cancel completed task")
    manager.update_task(task_id, status=TaskStatus.CANCELLED)
    return DownloadResponse(status="cancelled", task_id=task_id)
```

Run: `cat > src/douyin_download/api.py << 'EOF'\n...\nEOF`

- [ ] **Step 2: 建立 API 測試**

```python
"""Tests for API endpoints."""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from fastapi.testclient import TestClient

from douyin_download.api import app
from douyin_download.models import TaskStatus


@pytest.fixture
def client():
    """Test client fixture."""
    return TestClient(app)


def test_health_check(client):
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data


def test_download_sync_mode(client):
    """Test synchronous download."""
    mock_result = ("vid_123", Path("/tmp/test.mp4"))
    mock_result[1].touch()

    with patch("douyin_download.api.download_video", return_value=mock_result):
        response = client.post(
            "/api/v1/download",
            json={
                "url": "https://www.douyin.com/video/123",
                "quality": "720p",
            },
        )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "completed"
    assert data["video_id"] == "vid_123"


def test_download_with_callback(client):
    """Test async download with callback."""
    response = client.post(
        "/api/v1/download",
        json={
            "url": "https://www.douyin.com/video/123",
            "callback_url": "https://example.com/webhook",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "pending"
    assert data["task_id"] is not None


def test_get_task(client):
    """Test get task status."""
    # First create a task
    create_response = client.post(
        "/api/v1/download",
        json={
            "url": "https://www.douyin.com/video/123",
            "callback_url": "https://example.com/webhook",
        },
    )
    task_id = create_response.json()["task_id"]

    # Get task
    response = client.get(f"/api/v1/tasks/{task_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["task_id"] == task_id
    assert data["status"] == "pending"


def test_get_task_not_found(client):
    """Test get non-existent task."""
    response = client.get("/api/v1/tasks/non-existent-id")
    assert response.status_code == 404


def test_list_tasks(client):
    """Test list all tasks."""
    # Create a task first
    client.post(
        "/api/v1/download",
        json={
            "url": "https://www.douyin.com/video/123",
            "callback_url": "https://example.com/webhook",
        },
    )

    response = client.get("/api/v1/tasks")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1


def test_cancel_task(client):
    """Test cancel task."""
    # Create a task
    create_response = client.post(
        "/api/v1/download",
        json={
            "url": "https://www.douyin.com/video/123",
            "callback_url": "https://example.com/webhook",
        },
    )
    task_id = create_response.json()["task_id"]

    # Cancel it
    response = client.delete(f"/api/v1/tasks/{task_id}")
    assert response.status_code == 200
    assert response.json()["status"] == "cancelled"
```

Run: `cat > tests/test_api.py << 'EOF'\n...\nEOF`

- [ ] **Step 3: 執行測試**

Run: `uv run pytest tests/test_api.py -v`
Expected: PASS (all tests)

- [ ] **Step 4: Commit**

```bash
git add src/douyin_download/api.py tests/test_api.py
git commit -m "feat: implement complete API endpoints with task management"
```

---

### 任務 4: 建立 Docker 部署檔案

**Files:**
- Create: `Dockerfile`
- Create: `docker-compose.yml`
- Create: `docker-compose.prod.yml`
- Create: `nginx.conf`

- [ ] **Step 1: 建立 Dockerfile**

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies for Playwright
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.cargo/bin:${PATH}"

# Copy project files
COPY pyproject.toml uv.lock ./
COPY src/ ./src/

# Install Python dependencies
RUN uv sync --frozen

# Install Playwright browsers
RUN uv run playwright install chromium --with-deps

# Create data directories
RUN mkdir -p /data/downloads /data/temp

# Set environment
ENV PYTHONUNBUFFERED=1
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

EXPOSE 8000

# Run with gunicorn
CMD ["uv", "run", "gunicorn", "douyin_download.api:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "-b", "0.0.0.0:8000"]
```

Run: `cat > Dockerfile << 'EOF'\n...\nEOF`

- [ ] **Step 2: 建立 docker-compose.yml**

```yaml
services:
  app:
    build: .
    container_name: douyin-api
    volumes:
      - ./data:/data
    env_file:
      - .env
    ports:
      - "8000:8000"
    depends_on:
      - nginx
    environment:
      - API_HOST=0.0.0.0
      - API_PORT=8000
    restart: unless-stopped

  nginx:
    image: nginx:latest
    container_name: douyin-nginx
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./data:/data:ro
    ports:
      - "80:80"
      - "443:443"
    depends_on:
      - app
    restart: unless-stopped
```

Run: `cat > docker-compose.yml << 'EOF'\n...\nEOF`

- [ ] **Step 3: 建立 docker-compose.prod.yml**

```yaml
services:
  app:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: douyin-api
    volumes:
      - data:/data
    env_file:
      - .env.production
    environment:
      - API_HOST=0.0.0.0
      - API_PORT=8000
      - API_WORKERS=8
      - API_RELOAD=false
    restart: always

  nginx:
    image: nginx:latest
    container_name: douyin-nginx
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./data:/data:ro
      - nginx-secrets:/etc/nginx/secrets
    ports:
      - "80:80"
      - "443:443"
    depends_on:
      - app
    restart: always

volumes:
  data:
  nginx-secrets:
```

Run: `cat > docker-compose.prod.yml << 'EOF'\n...\nEOF`

- [ ] **Step 4: 建立 nginx.conf**

```nginx
events {
    worker_connections 1024;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for"';

    access_log /var/log/nginx/access.log main;
    error_log /var/log/nginx/error.log warn;

    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types text/plain text/css text/xml application/json application/javascript;

    upstream api {
        server app:8000;
        keepalive 32;
    }

    server {
        listen 80;
        server_name localhost;

        # Security headers
        add_header X-Frame-Options "SAMEORIGIN" always;
        add_header X-Content-Type-Options "nosniff" always;
        add_header X-XSS-Protection "1; mode=block" always;

        # API endpoints
        location /api/ {
            proxy_pass http://api;
            proxy_http_version 1.1;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_set_header Connection "";
            proxy_read_timeout 300s;
            proxy_connect_timeout 75s;
        }

        # Health check (no proxy needed)
        location /health {
            proxy_pass http://api;
            proxy_http_version 1.1;
            proxy_set_header Host $host;
        }

        # OpenAPI docs
        location /docs {
            proxy_pass http://api;
            proxy_http_version 1.1;
            proxy_set_header Host $host;
        }

        location /redoc {
            proxy_pass http://api;
            proxy_http_version 1.1;
            proxy_set_header Host $host;
        }

        # Root
        location / {
            return 200 '{"status":"ok","service":"douyin-api"}';
            add_header Content-Type application/json;
        }
    }
}
```

Run: `cat > nginx.conf << 'EOF'\n...\nEOF`

- [ ] **Step 5: Commit**

```bash
git add Dockerfile docker-compose.yml docker-compose.prod.yml nginx.conf
git commit -m "feat: add Docker deployment configuration"
```

---

### 任務 5: 更新 GitHub Actions CI/CD

**Files:**
- Modify: `.github/workflows/ci.yml`

- [ ] **Step 1: 更新 ci.yml 加入 Docker build**

在現有 ci.yml 的 jobs 區塊新增：

```yaml
  docker:
    name: Docker Build
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Build Docker image
        run: |
          docker build -t douyin-api:${{ github.sha }} .
          docker build -t douyin-api:latest .

      - name: Test with docker-compose
        run: |
          docker-compose up -d
          sleep 10
          curl -f http://localhost:8000/health
          docker-compose down

      - name: Trivy vulnerability scan
        uses: aquasecurity/trivy-action@master
        with:
          image-ref: 'douyin-api:${{ github.sha }}'
          format: 'table'
          exit-code: '1'
          severity: 'CRITICAL,HIGH'
        continue-on-error: true
```

Run: 讀取現有 ci.yml 內容並確認結構

- [ ] **Step 2: Commit**

```bash
git add .github/workflows/ci.yml
git commit -m "ci: add Docker build and test to CI pipeline"
```

---

### 任務 6: 更新 AGENTS.md 和 CLAUDE.md

**Files:**
- Modify: `AGENTS.md`
- Modify: `CLAUDE.md`

- [ ] **Step 1: 更新 CLAUDE.md**

在現有內容後新增：

```markdown
## Development Standards

### API Development
- Use FastAPI with OpenAPI/Redoc documentation at `/docs` and `/redoc`
- API URL prefix: `/api/v1`
- All configuration via environment variables with defaults in `.env`

### Docker Deployment
- Use `docker-compose.yml` for development
- Use `docker-compose.prod.yml` for production
- Gunicorn + Uvicorn workers for production

### Package Management
- Always use `uv` for package and environment management

### Testing Requirements
- Minimum 80% test coverage
- TDD approach: write tests first, then implementation
- BDD integration tests with pytest-bdd
- API e2e tests with httpx TestClient

### Context7 Usage
- Use Context7 MCP tools for up-to-date library documentation
```

- [ ] **Step 2: 更新 AGENTS.md**

在現有內容後新增類似章節

- [ ] **Step 3: Commit**

```bash
git add CLAUDE.md AGENTS.md
git commit -m "docs: update development standards for API and Docker"
```

---

### 任務 7: 擴展 BDD API 測試

**Files:**
- Modify: `features/api.feature`
- Modify: `features/steps/api_steps.py`

- [ ] **Step 1: 更新 api.feature**

```gherkin
Feature: FastAPI API Endpoints

  Scenario: Health check returns healthy status
    Given FastAPI client
    When I send GET request to "/health"
    Then response status should be 200
    And response should contain "healthy"

  Scenario: Download video synchronously
    Given FastAPI client
    When I send POST request to "/api/v1/download" with:
      | field         | value                          |
      | url           | https://www.douyin.com/video/123 |
      | quality       | 720p                          |
    Then response status should be 200

  Scenario: Download with callback creates pending task
    Given FastAPI client
    When I send POST request to "/api/v1/download" with:
      | field         | value                          |
      | url           | https://www.douyin.com/video/123 |
      | callback_url  | https://example.com/webhook    |
    Then response status should be 200
    And response should contain "pending"
    And response should contain "task_id"

  Scenario: Get task status
    Given FastAPI client
    And I create a download task with callback
    When I send GET request to "/api/v1/tasks/{task_id}"
    Then response status should be 200
    And response should contain task details

  Scenario: List all tasks
    Given FastAPI client
    And I create a download task with callback
    When I send GET request to "/api/v1/tasks"
    Then response status should be 200
    And response should be a list

  Scenario: Cancel pending task
    Given FastAPI client
    And I create a download task with callback
    When I send DELETE request to "/api/v1/tasks/{task_id}"
    Then response status should be 200
    And response should contain "cancelled"
```

- [ ] **Step 2: Commit**

```bash
git add features/api.feature features/steps/api_steps.py
git commit -m "test: add BDD tests for API endpoints"
```

---

## Self-Review Checklist

- [ ] Spec coverage: 所有 API endpoints 已實作
- [ ] No placeholders: 所有 step 都有實際程式碼
- [ ] Type consistency: TaskManager, Settings 等型別一致
- [ ] Test coverage: 80%+ 目標可达
- [ ] Docker files: 完整的 development + production 配置

---

## Execution Options

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

**Which approach?**