# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-10-19

This is the first stable, production-ready release of `magic-link`.

### Added

* **Core Authentication Engine:** Secure, HMAC-signed, single-use token generation and verification.
* **Modular Architecture:** A lightweight core with optional "extras" for dependencies.
* **SQLAlchemy Storage Backend:** A storage backend for any SQLAlchemy-compatible database (install via `sqlalchemy` extra).
* **Redis Storage Backend:** A high-performance storage backend for Redis, recommended for production (install via `redis` extra).
* **SMTP Mailer Backend:** A mailer for sending emails via any standard SMTP server (install via `smtp` extra).
* **Configuration System:** Type-safe configuration via environment variables and `.env` files, validated on startup.
* **Security Features:** Built-in rate limiting per email and IP address.
* **Comprehensive Documentation:** Including Quickstart guides for FastAPI and Flask, in-depth guides, and a full API reference.
* **Full Test Suite:** Including integration tests against live PostgreSQL and Redis services in CI.
