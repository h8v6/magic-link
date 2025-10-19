# magic_link

A modular, framework-agnostic engine for passwordless authentication using secure magic links.

## Motivation

Engineering teams often reinvent passwordless login flows, which results in fragile security and duplicated effort. `magic_link` delivers a hardened token engine with clear integration points so teams can wire magic-link authentication into their existing stack in minutes while retaining full control over infrastructure, migrations, and UX.

## Who It’s For

- Backend-heavy Python teams building APIs or web apps with FastAPI, Flask, Django, or similar frameworks.
- Developers who want passwordless auth without surrendering their logging, database, or email delivery stack to a hosted service.
- Security-conscious teams that prefer explicit configuration and zero hidden side effects.

## What’s In Scope

- Token generation, signing, hashing, and verification with safe defaults.
- Extensible storage and mailer interfaces plus maintained implementations for in-memory, SQLAlchemy, Redis, and SMTP.
- Tooling to help developers configure and test their setup quickly (`magic-link generate-config`, `magic-link test-email`).

## What’s Out of Scope

- User profile management, frontend components, or hosted dashboards.
- Automatic migrations or schema changes in your database.
- Support for OAuth, social login, or password-based flows.
- Multi-tenant orchestration or session management.

## Technology Agnosticism

Everything is opt-in by design. The core package ships with almost no third-party dependencies and treats storage, mail, and CLI features as extras. You choose which integrations to install, wire them explicitly, and continue using your preferred tooling without vendor lock-in.

## Key Features

- Minimal core with optional extras for storage (SQLAlchemy, Redis) and email delivery (SMTP)
- Cryptographically secure token generation, hashing, signing, and verification
- Pluggable storage and mailer interfaces so you can integrate with existing infrastructure
- Sensible defaults with explicit configuration via environment variables
- Developer-friendly CLI utilities for configuration scaffolding and delivery testing

## Installation

Install the core package:

```bash
pip install magic-link
```

Add extras as needed:

```bash
# SQLAlchemy + Redis + SMTP support
pip install "magic-link[sqlalchemy,redis,smtp]"
```

## FastAPI Quick Start

```python
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

from magic_link.config import load_settings
from magic_link.interfaces import MagicLinkMessage, RateLimitRule, TokenRecord
from magic_link.logging import configure_logger
from magic_link.mailer import create_mailer
from magic_link.storage.in_memory import InMemoryStorage
from magic_link.token_engine import TokenEngine

app = FastAPI()
configure_logger()
settings = load_settings()
engine = TokenEngine(
    secret_key=settings.secret_key,
    token_length=settings.token_length,
    ttl_seconds=settings.token_ttl_seconds,
)
storage = InMemoryStorage()
mailer = create_mailer(settings)


@app.post("/auth/magic-link")
async def issue_magic_link(request: Request) -> JSONResponse:
    payload = await request.json()
    email = payload.get("email")
    if not email:
        raise HTTPException(status_code=400, detail="Email is required")

    rate_allowed = storage.enforce_rate_limit(
        RateLimitRule(identifier=email, window_seconds=settings.rate_limit_window_seconds, max_requests=settings.rate_limit_max_requests)
    )
    if not rate_allowed:
        raise HTTPException(status_code=429, detail="Too many requests")

    issued = engine.issue(subject=email)
    storage.create_token(
        TokenRecord(
            token_hash=issued.token_hash,
            subject=issued.subject,
            signature=issued.signature,
            issued_at=issued.issued_at,
            expires_at=issued.expires_at,
        )
    )

    link = f"https://example.com/login?token={issued.token}"
    mailer.send_magic_link(
        MagicLinkMessage(
            recipient=email,
            link=link,
            subject="Your sign-in link",
            expires_at=issued.expires_at,
        )
    )

    return JSONResponse({"status": "ok"})


@app.post("/auth/magic-link/verify")
async def verify_magic_link(request: Request) -> JSONResponse:
    payload = await request.json()
    token = payload.get("token")
    if not token:
        raise HTTPException(status_code=400, detail="Token is required")

    record = storage.get_token(engine.hash_token(token))
    if record is None:
        raise HTTPException(status_code=400, detail="Invalid or expired token")

    try:
        engine.verify(
            token,
            subject=record.subject,
            signature=record.signature,
            issued_at=record.issued_at,
            expires_at=record.expires_at,
        )
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid or expired token")

    storage.consume_token(record.token_hash)
    return JSONResponse({"status": "verified", "subject": record.subject})
```

This example uses the in-memory storage backend for simplicity. Swap it with `SQLAlchemyStorage` or `RedisStorage` for production deployments.

## License

`magic_link` is released as open source under the [MIT License](../LICENSE). Contributions are welcome via issues and pull requests.
