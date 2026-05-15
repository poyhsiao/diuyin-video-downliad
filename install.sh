#!/bin/bash
set -e
uv sync
uv run playwright install chromium --with-deps
