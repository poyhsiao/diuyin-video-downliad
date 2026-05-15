"""Environment configuration management."""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field
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
    api_port: int = Field(default=8000, ge=1, le=65535)
    api_workers: int = Field(default=4, ge=1)
    api_reload: bool = False

    # 路徑設定
    download_output_dir: Path = Path("/data/downloads")
    temp_dir: Path = Path("/data/temp")

    # Docker 映射
    nginx_port: int = Field(default=80, ge=1, le=65535)
    nginx_ssl_port: int = Field(default=443, ge=1, le=65535)
    app_port: int = Field(default=8000, ge=1, le=65535)

    # 預設值
    default_quality: Literal["original", "480p", "720p", "1080p"] = "original"
    max_concurrent_downloads: int = Field(default=5, ge=1)
    task_timeout_seconds: int = Field(default=300, ge=1)

    # Playwright
    playwright_browsers_path: Path = Path("/ms-playwright")


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()