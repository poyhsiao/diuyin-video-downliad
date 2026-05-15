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