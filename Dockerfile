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
ENV PATH="/root/.local/bin:${PATH}"

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

# Expose port (can override with APP_PORT build arg)
EXPOSE ${APP_PORT:-8000}

# Run with gunicorn - internal settings hardcoded to defaults
CMD ["uv", "run", "gunicorn", "douyin_download.api:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "-b", "0.0.0.0:8000"]