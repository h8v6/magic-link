# magic_link

[![PyPI](https://img.shields.io/pypi/v/magic-link.svg)](https://pypi.org/project/magic-link/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![CI](https://github.com/h8v6/magic-link/actions/workflows/ci.yml/badge.svg)](https://github.com/h8v6/magic-link/actions/workflows/ci.yml)
[![Coverage](https://img.shields.io/badge/Coverage-100%25-brightgreen.svg)](#testing)

A modular, framework-agnostic engine for delivering passwordless authentication via secure magic links. The project follows a “minimal core + opt-in extras” philosophy so you can embed the library inside any Python stack without surrendering control of storage, email, or infrastructure.

> **Docs live in [`/docs`](docs/)**. This README highlights the essentials; detailed guides, recipes, and release instructions are all linked below.

---

## Table of Contents

- [Features](#features)
- [Requirements](#requirements)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Extras](#extras)
- [CLI Utilities](#cli-utilities)
- [Documentation](#documentation)
- [Testing](#testing)
- [Release Process](#release-process)
- [Contributing](#contributing)
- [License](#license)

## Features

- 🔐 **Secure token engine** – deterministic HMAC signing, hashing, TTL enforcement, property-based tests.
- 🗃️ **Pluggable storage** – in-memory for dev, SQLAlchemy for RDBMS, Redis for low-latency workloads.
- ✉️ **Mailer registry** – SMTP implementation plus extensible template hooks.
- 🎛️ **Service facade** – `MagicLinkService` coordinates issuance, verification, rate limiting, and single-use guarantees.
- 🛠️ **CLI helpers** – `magic-link generate-config` and `magic-link test-email` streamline setup and diagnostics.
- 📚 **Extensive documentation** – quickstarts, framework recipes (FastAPI, Flask), and in-depth guides for email, migrations, and security.
- ✅ **100% test coverage** – unit, integration, and property-based suites validated in CI against live PostgreSQL, Redis, and audo SMTP servers.

## Requirements

- Python 3.8+
- Optional services depending on extras:
  - PostgreSQL (or any SQLAlchemy-supported database) for the SQL backend
  - Redis 5+ for the Redis backend
  - SMTP relay for outbound email

## Installation

Core library:

```bash
pip install magic-link
```

With common extras:

```bash
pip install "magic-link[sqlalchemy,redis,smtp]"
```

Add `cli` if you want the command-line utilities bundled:

```bash
pip install "magic-link[sqlalchemy,redis,smtp,cli]"
```

## Quick Start

1. Generate a configuration template:
   ```bash
   magic-link generate-config -o .env
   ```
2. Fill in the environment variables (secret key, SMTP credentials, database connection, etc.).
3. Wire the library into your framework. For FastAPI:

   ```python
   from fastapi import FastAPI, HTTPException
   from fastapi.responses import JSONResponse

   from magic_link import MagicLinkConfig, MagicLinkService
   from magic_link.interfaces import MagicLinkMessage
   from magic_link.mailer import create_mailer
   from magic_link.storage.redis import RedisStorage

   app = FastAPI()
   config = MagicLinkConfig.from_env()
   storage = RedisStorage.from_url("redis://localhost:6379/0")  # see docs for helper
   service = MagicLinkService(config=config, storage=storage)
   mailer = create_mailer(config)

   @app.post("/auth/magic-link")
   async def issue(payload: dict[str, str]) -> JSONResponse:
       email = payload.get("email")
       if not email:
           raise HTTPException(status_code=400, detail="Email is required")
       service.enforce_rate_limit(email)
       issued = service.issue_token(email)
       link = f"{config.base_url}{config.login_path}?token={issued.token}"
       mailer.send_magic_link(MagicLinkMessage(recipient=email, link=link, subject="Sign in", expires_at=issued.expires_at))
       return JSONResponse({"status": "sent"})
   ```

4. Verify tokens using `service.verify_token(...)` in your callback endpoint.

For a complete, copy-pasteable example (including Flask), consult the [Quickstart guide](docs/quickstart.md) and [recipes](docs/recipes/).

## Extras

| Extra        | Installs            | Purpose                                          |
|--------------|--------------------|--------------------------------------------------|
| `sqlalchemy` | `SQLAlchemy`, `psycopg[binary]` | Persistent token storage in relational DBs |
| `redis`      | `redis`, `hiredis`  | High-throughput storage + rate limiting          |
| `smtp`       | `email-validator`   | SMTP mailer backend and email utilities          |
| `cli`        | `click`             | Command-line helpers (`magic-link` CLI)          |

## CLI Utilities

```bash
# Print an annotated configuration template
magic-link generate-config

# Send a test email using your configured mailer
magic-link test-email user@example.com
```

## Documentation

- [Overview & FastAPI quickstart](docs/README.md)
- [Step-by-step Quickstart](docs/quickstart.md)
- [Framework recipes](docs/recipes/) – Flask and more
- [Guides](docs/guides/) – email templates, database migrations, security considerations
- [Architecture](docs/architecture.md)
- [Release process](docs/release.md)

## Testing

```bash
pip install -e ".[dev,sqlalchemy,redis,smtp,cli]"
pytest --cov=magic_link
```

CI runs the full suite (unit, property-based, integration) against PostgreSQL, Redis, and a local SMTP server. Coverage must stay ≥95% (currently 100%).

## Release Process

1. Follow the checklist in [docs/release.md](docs/release.md) (trusted publisher + semver workflow).
2. Alpha / beta versions: bump `pyproject.toml`, update `CHANGELOG.md`, tag, and publish.
3. Official releases are cut via GitHub Releases, which triggers the trusted publisher workflow to upload builds to PyPI.

## Contributing

- Open an issue or draft PR for discussion.
- Ensure tests and linters pass (`pytest`, `ruff check`, `black --check`, `mypy`).
- Update documentation for user-facing changes.

## License

Distributed under the [MIT License](LICENSE).
