# Architecture & Philosophy

`magic_link` treats authentication as an engine that you plug into your existing stack, not a fully managed platform. The core package remains dependency-light and defers all I/O to optional extras so developers remain in control.

## Guiding Principles

1. **Minimal Core** – The core library focuses on token lifecycle management, configuration, and abstractions. Storage, mail, and CLI functions live in opt-in extras to keep the default footprint tiny.
2. **Explicit Integration** – Developers wire the engine into their applications explicitly. No `magic-link init` command touches your project files or databases.
3. **Security First** – Tokens are generated with `secrets`, signed via HMAC, and stored as hashes. Rate limiting is built into the storage interface to enforce throttling.
4. **Observable and Testable** – Logging uses the standard library so logs flow into existing pipelines. Each component exposes interfaces that are easy to mock during testing.

## Layered Components

- **Configuration (`magic_link.config`)** – Loads settings from the environment with `.env` fallback. All runtime behaviour is controlled through explicit variables.
- **Token Engine (`magic_link.token_engine`)** – Issues cryptographically secure tokens, produces signatures, and validates expiry.
- **Interfaces (`magic_link.interfaces`)** – Defines contracts for storage and mailers so custom implementations can drop in without modifying the core.
- **Storage Extras** – In-memory for tests, SQLAlchemy for relational databases, and Redis for high-performance deployments.
- **Mailer Extras** – SMTP mailer plus a registry to register alternative providers.
- **CLI** – Utilities for generating configuration templates and sending test emails, keeping the feedback loop short.

## Why No Auto-Migrations?

Database migrations are left to the host application so teams keep using existing workflows (Alembic, Django migrations, etc.). The library exports SQLAlchemy models to make integration straightforward but never executes schema changes automatically.

## Extending the Library

- Register new mailers with `magic_link.mailer.register_mailer` to integrate providers like SendGrid or AWS SES.
- Implement `StorageInterface` to back tokens with alternative datastores such as DynamoDB or Firestore.
- Tune security defaults via environment variables (token TTL, length, rate limits) without modifying code.

This philosophy keeps `magic_link` predictable, secure, and flexible enough to embed inside any Python web application.
