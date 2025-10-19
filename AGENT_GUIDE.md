# Agent Operations Guide

This document captures the conventions, workflows, and safety rails future contributors and automation agents must follow when working on `magic_link`.

## 1. Environment & Tooling

- **Python:** 3.8+ (CI uses 3.12). Install project extras when running the full suite:
  ```bash
  pip install -e ".[dev,sqlalchemy,redis,smtp,cli]"
  ```
- **Services:** Integration tests expect PostgreSQL and Redis. In CI these run via service containers; locally you can point to any accessible instance or skip via `-k "not integration"`.
- **CLI utilities:** `magic-link generate-config` and `magic-link test-email` are available when the `cli` extra is installed.

## 2. Development Workflow

1. Create a topic branch from `main`.
2. Make focused commits; keep changes logically grouped.
3. Run formatting / linting:
   ```bash
   ruff check .
   black .
   mypy magic_link tests
   ```
4. Execute the test suite:
   ```bash
   pytest --cov=magic_link --cov-report=term-missing
   ```
   Coverage is locked at ≥95% (CI enforces 95%, current suite sits at 100%).
5. Update documentation and changelog for user-facing changes.
6. Open a pull request referencing relevant tasks from `tasks/tasks-prd.md`.

## 3. Project Map

- **Core library:** `magic_link/`
- **Tests:** `tests/` (unit, integration, property-based)
- **Documentation:** `docs/`
  - `docs/README.md` – overview + FastAPI quick start
  - `docs/quickstart.md` – step-by-step onboarding
  - `docs/recipes/` – framework recipes (FastAPI, Flask)
  - `docs/guides/` – email templates, migrations, security, etc.
  - `docs/release.md` – release checklist & trusted publishing notes
- **PRD:** `prd.md`
- **Active task list:** `tasks/tasks-prd.md`

## 4. Coding Conventions

- Prefer the shared logger from `magic_link/logging.py`; avoid ad-hoc logging setup inside modules.
- Keep configuration errors actionable by raising `ConfigurationError` with clear messages.
- Guard optional imports (SQLAlchemy, Redis, SMTP extras) with informative `ImportError` messages.
- Preserve type annotations and docstrings; follow existing patterns for new interfaces or backends.

## 5. Testing Notes

- Unit tests live alongside integration suites under `tests/`. Property-based tests use Hypothesis (`tests/test_token_engine_property.py`).
- Integration tests target live PostgreSQL/Redis and aiosmtpd-based SMTP server in CI. When running locally without services, expect those tests to skip.
- New features must include dedicated tests. If coverage drops, add tests before merging.

## 6. Documentation Duties

- Mirror new functionality in both the root `README.md` and the appropriate guide under `docs/`.
- Keep quickstarts in sync (FastAPI + Flask recipes). Update tables or lists when adding extras or CLI commands.
- For architectural or philosophical shifts, revise `docs/architecture.md` and note changes in PRD if scope evolves.

## 7. Release Operations

We publish via PyPI trusted publisher (OIDC); no API tokens required.

1. **Alpha/Beta cadence:** Bump version in `pyproject.toml`, update `CHANGELOG.md`, ensure docs are current, run tests.
2. **Tagging:** Create and push a tag (`git tag vX.Y.Z && git push origin vX.Y.Z`).
3. **GitHub release:** Draft a pre-release or release with changelog notes. Publishing triggers the `Publish` workflow.
4. **Trusted publisher setup:** Already configured for repository `h8v6/magic-link`, workflow `release.yml`, environment `pypi`. If changes are made, update [docs/release.md](docs/release.md).
5. **Verification:** After the workflow succeeds, confirm availability on PyPI (`pip install magic-link==X.Y.Z`).
6. **Post-release:** Announce in the appropriate channels, collect feedback for the next iteration.

## 8. Issue Triage & Support

- Reproduce issues locally using latest `main` and relevant extras.
- Label issues by area (`storage`, `mailer`, `docs`, etc.) for prioritization.
- When closing an issue, link the PR and update documentation if behavior changed.

## 9. Useful Commands

```bash
# Format and lint
ruff check . && black .

# Type check
mypy magic_link tests

# Run focused tests
pytest tests/test_service.py -k "verify"

# Regenerate docs preview (if needed)
python -m build
```

## 10. Escalation

If a change impacts security (token validation, rate limiting, storage atomicity), flag a maintainer for review before merging. For release blockers or production incidents, coordinate via the repository’s issue tracker and follow the mitigation plan outlined in `docs/security.md`.

Stay consistent with these guidelines to keep the project predictable and safe for downstream adopters.
