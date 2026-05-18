"""FastAPI application for Douyin downloader."""

from typing import Annotated, Literal

from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends, Form
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from douyin_download import __version__
from douyin_download.config import get_settings
from douyin_download.core import download_video
from douyin_download.models import TaskStatus
from douyin_download.tasks import get_task_manager, TaskManager
from douyin_download.url_normalizer import (
    InvalidURLError,
    VideoUnavailableError,
    normalize,
)


app = FastAPI(
    title="Douyin Video Downloader API",
    description="""
抖音影片下載 API - 支援同步與非同步下載模式。

## 功能特色

- **同步下載**: 立即返回下載結果，適合短影片
- **非同步下載**: 任務佇列模式，支援回調通知，適合長影片
- **任務管理**: 查詢、列出、取消下載任務
- **Playwright 技術**: 使用真實瀏覽器引擎處理抖音反爬機制

## 下載品質選項

| 參數值 | 說明 |
|--------|------|
| `original` | 原始畫質（預設）|
| `1080p` | 1080P 高清 |
| `720p` | 720P |
| `480p` | 480P |
| `360p` | 360P |

## 使用範例

### 同步下載（立即響應）
```bash
curl -X POST http://localhost:8000/api/v1/download \\
  -H "Content-Type: application/json" \\
  -d '{"url": "https://www.douyin.com/video/123456789"}'
```

### 非同步下載（後台處理）
```bash
curl -X POST http://localhost:8000/api/v1/download \\
  -H "Content-Type: application/json" \\
  -d '{"url": "https://www.douyin.com/video/123456789", "callback_url": "https://your-server.com/webhook"}'
```
    """,
    version=__version__,
    docs_url="/docs",
    redoc_url="/redoc",
)

settings = get_settings()


VIDEO_QUALITY_OPTIONS = ["original", "1080p", "720p", "480p", "360p"]


class DownloadRequest(BaseModel):
    """下載請求模型（已棄用，建議使用表單參數）"""

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "url": "https://www.douyin.com/video/7385822337847635259",
                    "quality": "original",
                    "callback_url": None,
                },
                {
                    "url": "https://www.douyin.com/video/7385822337847635259",
                    "quality": "1080p",
                    "callback_url": "https://your-server.com/api/webhook/douyin",
                },
            ]
        }
    }

    url: Annotated[
        str,
        Field(
            description="抖音影片 URL",
            examples=["https://www.douyin.com/video/7385822337847635259"],
        ),
    ]
    quality: Annotated[
        Literal["original", "1080p", "720p", "480p", "360p"],
        Field(
            default="original",
            description="影片畫質設定",
            examples=["original", "1080p", "720p", "480p", "360p"],
        ),
    ] = "original"
    callback_url: Annotated[
        str | None,
        Field(
            default=None,
            description="非同步回調 URL（可選）\n\n下載完成後通知此 URL",
            examples=["https://your-server.com/webhook"],
        ),
    ] = None
    output_dir: Annotated[
        str | None,
        Field(
            default=None,
            description="輸出目錄（可選）\n\n預設使用環境設定的下載目錄",
            examples=["/data/downloads", "./videos"],
        ),
    ] = None


class DownloadResponse(BaseModel):
    """下載響應模型"""

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "status": "completed",
                    "task_id": None,
                    "video_id": "7385822337847635259",
                    "path": "/data/downloads/7385822337847635259.mp4",
                    "file_size": 15728640,
                    "error": None,
                },
                {
                    "status": "pending",
                    "task_id": "task_abc123",
                    "video_id": None,
                    "path": None,
                    "file_size": None,
                    "error": None,
                },
            ]
        }
    }

    status: Annotated[
        str,
        Field(
            description="下載狀態",
            examples=["completed", "pending", "failed", "cancelled"],
        ),
    ]
    task_id: Annotated[
        str | None,
        Field(
            default=None,
            description="任務 ID（非同步模式時提供）",
            examples=["task_abc123"],
        ),
    ] = None
    video_id: Annotated[
        str | None,
        Field(
            default=None,
            description="抖音影片 ID",
            examples=["7385822337847635259"],
        ),
    ] = None
    path: Annotated[
        str | None,
        Field(
            default=None,
            description="下載檔案路徑",
            examples=["/data/downloads/7385822337847635259.mp4"],
        ),
    ] = None
    file_size: Annotated[
        int | None,
        Field(
            default=None,
            description="檔案大小（bytes）",
            examples=[15728640],
        ),
    ] = None
    error: Annotated[
        str | None,
        Field(
            default=None,
            description="錯誤訊息（如有）",
            examples=["Failed to extract video: Network error"],
        ),
    ] = None


class TaskResponse(BaseModel):
    """任務狀態響應模型"""

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "task_id": "task_abc123",
                    "video_url": "https://www.douyin.com/video/7385822337847635259",
                    "status": "COMPLETED",
                    "video_id": "7385822337847635259",
                    "path": "/data/downloads/7385822337847635259.mp4",
                    "file_size": 15728640,
                    "error": None,
                },
            ]
        }
    }

    task_id: Annotated[
        str,
        Field(
            description="任務唯一識別符",
            examples=["task_abc123"],
        ),
    ]
    video_url: Annotated[
        str,
        Field(
            description="原始抖音影片 URL",
            examples=["https://www.douyin.com/video/7385822337847635259"],
        ),
    ]
    status: Annotated[
        Literal["pending", "running", "completed", "failed", "cancelled"],
        Field(
            description="任務狀態",
            examples=["pending", "running", "completed", "failed", "cancelled"],
        ),
    ]
    video_id: Annotated[
        str | None,
        Field(
            default=None,
            description="抖音影片 ID",
            examples=["7385822337847635259"],
        ),
    ] = None
    path: Annotated[
        str | None,
        Field(
            default=None,
            description="下載檔案絕對路徑",
            examples=["/data/downloads/7385822337847635259.mp4"],
        ),
    ] = None
    file_size: Annotated[
        int | None,
        Field(
            default=None,
            description="檔案大小（bytes）",
            examples=[15728640],
        ),
    ] = None
    error: Annotated[
        str | None,
        Field(
            default=None,
            description="任務失敗時的錯誤訊息",
        ),
    ] = None


def get_manager() -> TaskManager:
    """Dependency for task manager."""
    return get_task_manager()


@app.get(
    "/health",
    summary="健康檢查",
    description="檢查 API 服務是否正常運行",
    responses={
        200: {
            "description": "服務正常",
            "content": {
                "application/json": {
                    "example": {"status": "healthy", "version": "0.1.0"}
                }
            },
        },
    },
)
def health_check() -> dict:
    """健康檢查端點 - 返回服務狀態和版本號"""
    return {"status": "healthy", "version": __version__}


@app.post(
    "/api/v1/download",
    response_model=None,
    summary="下載抖音影片",
    description="""
下載抖音影片。

## 兩種模式

### 直接下載（無 callback_url）
立即下載影片並直接返回檔案。

### 非同步模式（設定 callback_url）
建立任務後立即返回 task_id，後台處理下載，完成後通知 callback_url。

## 請求參數

| 參數 | 類型 | 必填 | 說明 |
|------|------|------|------|
| `url` | string | 是 | 抖音影片 URL |
| `quality` | string | 否 | 畫質：original, 1080p, 720p, 480p, 360p |
| `callback_url` | string | 否 | 回調 URL（設定後為非同步模式） |
    """,
)
def create_download(
    manager: Annotated[TaskManager, Depends(get_manager)],
    background_tasks: BackgroundTasks,
    url: Annotated[str, Form(description="抖音影片 URL", examples=["https://www.douyin.com/video/7385822337847635259"])],
    quality: Annotated[
        Literal["original", "1080p", "720p", "480p", "360p"],
        Form(description="影片畫質設定"),
    ] = "original",
    callback_url: Annotated[str | None, Form(description="非同步回調 URL（可選）")] = None,
) -> FileResponse | DownloadResponse:
    """下載抖音影片 - 直接下載或非同步模式"""
    output_path = settings.download_output_dir

    # Normalize URL (handles share text, short URLs, validation)
    try:
        normalized_url = normalize(url)
    except InvalidURLError:
        raise HTTPException(status_code=400, detail="URL_RESOLVE_FAILED")
    except VideoUnavailableError:
        raise HTTPException(status_code=400, detail="VIDEO_NOT_AVAILABLE")

    if callback_url:
        task = manager.create_task(
            video_url=normalized_url,
            quality=quality or settings.default_quality,
            output_dir=output_path,
            callback_url=callback_url,
        )

        async def run_download():
            def sync_download(video_url, out, q):
                return download_video(video_url, out, q)
            await manager.execute_task(task.task_id, sync_download)

        background_tasks.add_task(run_download)
        return DownloadResponse(status="pending", task_id=task.task_id)

    try:
        video_id, path = download_video(normalized_url, output_path, quality=quality)
        return FileResponse(
            path=str(path),
            media_type="video/mp4",
            filename=f"douyin_{video_id}.mp4",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get(
    "/api/v1/tasks/{task_id}",
    response_model=TaskResponse,
    summary="查詢任務狀態",
    description="根據任務 ID 查詢下載任務的當前狀態和詳細資訊",
    responses={
        200: {"description": "任務詳情"},
        404: {"description": "任務不存在"},
    },
)
def get_task(
    task_id: str,
    manager: Annotated[TaskManager, Depends(get_manager)],
) -> TaskResponse:
    """查詢特定任務的狀態"""
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


@app.get(
    "/api/v1/tasks",
    response_model=list[TaskResponse],
    summary="列出所有任務",
    description="列出所有下載任務的摘要資訊",
)
def list_tasks(
    manager: Annotated[TaskManager, Depends(get_manager)],
) -> list[TaskResponse]:
    """列出所有任務"""
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


@app.delete(
    "/api/v1/tasks/{task_id}",
    response_model=DownloadResponse,
    summary="取消任務",
    description="取消一個進行中的下載任務（已完成任務無法取消）",
    responses={
        200: {"description": "任務已取消"},
        400: {"description": "已完成任務無法取消"},
        404: {"description": "任務不存在"},
    },
)
def cancel_task(
    task_id: str,
    manager: Annotated[TaskManager, Depends(get_manager)],
) -> DownloadResponse:
    """取消指定的任務"""
    task = manager.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if task.status == TaskStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Cannot cancel completed task")
    manager.update_task(task_id, status=TaskStatus.CANCELLED)
    return DownloadResponse(status="cancelled", task_id=task_id)