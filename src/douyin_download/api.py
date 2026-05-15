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
