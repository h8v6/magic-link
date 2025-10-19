# Agent Operations Guide

## Development Workflow
- Run `pytest` from the repository root after making changes.
- Linting, formatting, and type checks are provided via `ruff`, `black`, and `mypy` (see `pyproject.toml`).
- Continuous integration lives in `.github/workflows/ci.yml`; keep it passing.
- The repository is public and licensed under MIT (see `LICENSE`); keep all contributions compatible with that license.

## Project Map
- Core library code is under `magic_link/`.
- Documentation sits in the `docs/` directory (README, quickstart, guides, reference, architecture).
- The PRD is `prd.md`; the living task list is `tasks/tasks-prd.md`.

## Code Style
- Prefer standard library logging (`magic_link/logging.py`).
- Keep docstrings concise; avoid superfluous inline comments.
- Optional-dependency imports should guard with informative messages, as shown in storage backends.

## Testing Notes
- `tests/` contains unit and integration coverage for config, token engine, storage backends, mailer, and CLI.
- Storage tests skip when optional extras (Redis, SQLAlchemy) are missing.
- CLI tests rely on Click's `CliRunner` and monkeypatching to isolate side effects.

## Documentation Updates
- Mirror new features in `docs/README.md` and `docs/quickstart.md`.
- Extend `docs/guides/` and `docs/reference/api.md` when adding integrations or public APIs.

Stay consistent with these patterns to keep the codebase predictable for future agents and contributors.
