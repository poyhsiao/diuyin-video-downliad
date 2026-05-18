# Douyin Downloader

## Architecture

- `cli.py` — Click-based CLI entrypoint
- `core.py` — Download orchestration
- `extractor.py` — Playwright extraction logic
- `models.py` — Pydantic models
- `api.py` — FastAPI server (placeholder)

## Development

```bash
uv sync
playwright install chromium --with-deps
python -m douyin download <url>
```

<!-- gitnexus:start -->
# Development Standards

## API Development
- Use FastAPI with OpenAPI/Redoc documentation at `/docs` and `/redoc`
- API URL prefix: `/api/v1`
- All configuration via environment variables with defaults in `.env`

## Docker Deployment
- Use `docker-compose.yml` for development
- Use `docker-compose.prod.yml` for production
- Gunicorn + Uvicorn workers for production

## Package Management
- Always use `uv` for package and environment management

## Testing Requirements
- Minimum 80% test coverage
- TDD approach: write tests first, then implementation
- BDD integration tests with pytest-bdd
- API e2e tests with httpx TestClient

## Context7 Usage
- Use Context7 MCP tools for up-to-date library documentation

<!-- gitnexus:start -->
# GitNexus — Code Intelligence

This project is indexed by GitNexus as **diuyin-video-downliad** (523 symbols, 697 relationships, 11 execution flows). Use the GitNexus MCP tools to understand code, assess impact, and navigate safely.

> If any GitNexus tool warns the index is stale, run `npx gitnexus analyze` in terminal first.

## Always Do

- **MUST run impact analysis before editing any symbol.** Before modifying a function, class, or method, run `gitnexus_impact({target: "symbolName", direction: "upstream"})` and report the blast radius (direct callers, affected processes, risk level) to the user.
- **MUST run `gitnexus_detect_changes()` before committing** to verify your changes only affect expected symbols and execution flows.
- **MUST warn the user** if impact analysis returns HIGH or CRITICAL risk before proceeding with edits.
- When exploring unfamiliar code, use `gitnexus_query({query: "concept"})` to find execution flows instead of grepping. It returns process-grouped results ranked by relevance.
- When you need full context on a specific symbol — callers, callees, which execution flows it participates in — use `gitnexus_context({name: "symbolName"})`.

## Never Do

- NEVER edit a function, class, or method without first running `gitnexus_impact` on it.
- NEVER ignore HIGH or CRITICAL risk warnings from impact analysis.
- NEVER rename symbols with find-and-replace — use `gitnexus_rename` which understands the call graph.
- NEVER commit changes without running `gitnexus_detect_changes()` to check affected scope.

## Resources

| Resource | Use for |
|----------|---------|
| `gitnexus://repo/diuyin-video-downliad/context` | Codebase overview, check index freshness |
| `gitnexus://repo/diuyin-video-downliad/clusters` | All functional areas |
| `gitnexus://repo/diuyin-video-downliad/processes` | All execution flows |
| `gitnexus://repo/diuyin-video-downliad/process/{name}` | Step-by-step execution trace |

## CLI

| Task | Read this skill file |
|------|---------------------|
| Understand architecture / "How does X work?" | `.claude/skills/gitnexus/gitnexus-exploring/SKILL.md` |
| Blast radius / "What breaks if I change X?" | `.claude/skills/gitnexus/gitnexus-impact-analysis/SKILL.md` |
| Trace bugs / "Why is X failing?" | `.claude/skills/gitnexus/gitnexus-debugging/SKILL.md` |
| Rename / extract / split / refactor | `.claude/skills/gitnexus/gitnexus-refactoring/SKILL.md` |
| Tools, resources, schema reference | `.claude/skills/gitnexus/gitnexus-guide/SKILL.md` |
| Index, status, clean, wiki CLI commands | `.claude/skills/gitnexus/gitnexus-cli/SKILL.md` |

<!-- gitnexus:end -->

## Version and Release Management

### Version Number Rules
- Update `pyproject.toml` version BEFORE creating git tag
- Use semantic versioning: `major.minor.patch`
- Version must match in:
  - `pyproject.toml` → `[project] version`
  - `CHANGELOG.md` → `[X.Y.Z] — YYYY-MM-DD`
  - Git tag → `vX.Y.Z`

### Release Checklist
When completing a release, ensure ALL of these are updated together:
1. `pyproject.toml` version field
2. `CHANGELOG.md` with new version section and changes
3. Git commit with message describing changes
4. Git tag `vX.Y.Z`
5. GitHub Release with title and changelog notes

### Release Commands
```bash
# Update version and create release
git add pyproject.toml CHANGELOG.md
git commit -m "release: vX.Y.Z"
git tag -a vX.Y.Z -m "vX.Y.Z: <description>"
git push origin main --tags
gh release create vX.Y.Y --title "vX.Y.Z - <title>" --notes "<changelog>"
```

### Never Forget
- NEVER create git tag without first updating pyproject.toml
- NEVER skip CHANGELOG.md when releasing
- ALWAYS push tags with `git push origin vX.Y.Z`

### Automated Release Workflow

This project uses an automated release workflow with pre-push hooks:

**Setup:**
```bash
make install-hooks
```

**Flow:**
```
git push → pre-push hook → prompts for version type → auto-updates version → commits → tags → pushes → creates GitHub release
```

**Commands:**
- `make install-hooks` - Install git hooks (one-time setup)
- `make release` - Run release script manually
- `make test` - Run test suite
- `make lint` - Run linter

**Release Scripts:**
- `scripts/release.sh` - Core release automation
- `scripts/version-bump.sh` - Version number management
- `scripts/changelog.sh` - CHANGELOG.md generation
- `.githooks/pre-push` - Git hook template

**Version Selection:**
When running release, you'll be prompted to choose:
- `[p]` patch (default for bug fixes)
- `[m]` minor (for new features)
- `[M]` major (for breaking changes)
