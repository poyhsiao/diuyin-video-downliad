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