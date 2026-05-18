.PHONY: help release install-hooks test lint

help:
	@echo "Available targets:"
	@echo "  make release       - Run the release script"
	@echo "  make install-hooks - Install git hooks"
	@echo "  make test          - Run tests"
	@echo "  make lint          - Run linter"

release:
	./scripts/release.sh

install-hooks:
	@mkdir -p .git/hooks
	@cp .githooks/pre-push .git/hooks/pre-push
	@chmod +x scripts/*.sh
	@chmod +x .git/hooks/pre-push
	@echo "Git hooks installed successfully"

test:
	uv run pytest --cov=src -q

lint:
	uv run ruff check .

.DEFAULT_GOAL := help
