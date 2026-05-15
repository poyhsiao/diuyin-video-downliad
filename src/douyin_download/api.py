"""FastAPI server (placeholder)."""

from fastapi import FastAPI

app = FastAPI()


@app.get("/")
def root() -> dict:
    """Placeholder endpoint."""
    return {"status": "coming_soon"}


@app.get("/download")
def download_endpoint(url: str, output_dir: str | None = None) -> dict:
    """Download a Douyin video (future implementation)."""
    return {"status": "coming_soon", "url": url, "output_dir": output_dir}
