"""Configuration loader for the magic_link package."""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from typing import Optional

from dotenv import load_dotenv

from .errors import ConfigurationError

ENV_PREFIX = "MAGIC_LINK_"


def _load_dotenv() -> None:
    """Load environment variables from a local .env file if present."""
    load_dotenv(override=False)


def _getenv(key: str, default: Optional[str] = None) -> Optional[str]:
    """Fetch a namespaced environment variable."""
    return os.getenv(f"{ENV_PREFIX}{key}", default)


def _get_required(key: str) -> str:
    value = _getenv(key)
    if value is None or value.strip() == "":
        raise ConfigurationError(f"Missing required configuration: {ENV_PREFIX}{key}")
    return value


def _get_int(key: str, default: int) -> int:
    raw = _getenv(key)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError as exc:
        raise ConfigurationError(
            f"Configuration {ENV_PREFIX}{key} must be an integer."
        ) from exc


def _get_bool(key: str, default: bool) -> bool:
    raw = _getenv(key)
    if raw is None:
        return default
    truthy = {"1", "true", "t", "yes", "y", "on"}
    falsy = {"0", "false", "f", "no", "n", "off"}
    lowered = raw.strip().lower()
    if lowered in truthy:
        return True
    if lowered in falsy:
        return False
    raise ConfigurationError(
        f"Configuration {ENV_PREFIX}{key} must be a boolean-like value."
    )


def _get_float(key: str, default: Optional[float] = None) -> Optional[float]:
    raw = _getenv(key)
    if raw is None or raw == "":
        return default
    try:
        return float(raw)
    except ValueError as exc:
        raise ConfigurationError(
            f"Configuration {ENV_PREFIX}{key} must be a number."
        ) from exc


@dataclass(frozen=True, slots=True)
class MagicLinkSettings:
    """Immutable configuration object for the magic_link package."""

    secret_key: str
    token_ttl_seconds: int
    token_length: int
    rate_limit_window_seconds: int
    rate_limit_max_requests: int
    issuer: Optional[str]
    base_url: Optional[str]
    login_path: str
    debug: bool
    storage_backend: str
    mailer_backend: str
    from_address: Optional[str]
    smtp_host: str
    smtp_port: int
    smtp_username: Optional[str]
    smtp_password: Optional[str]
    smtp_use_tls: bool
    smtp_use_ssl: bool
    smtp_timeout: Optional[float]


@lru_cache(maxsize=1)
def load_settings() -> MagicLinkSettings:
    """Load and cache runtime settings from environment variables."""
    _load_dotenv()
    secret_key = _get_required("SECRET_KEY")
    token_ttl_seconds = _get_int("TOKEN_TTL_SECONDS", default=900)
    token_length = _get_int("TOKEN_LENGTH", default=32)
    rate_limit_window_seconds = _get_int("RATE_LIMIT_WINDOW_SECONDS", default=60)
    rate_limit_max_requests = _get_int("RATE_LIMIT_MAX_REQUESTS", default=5)
    issuer = _getenv("ISSUER")
    base_url = _getenv("BASE_URL")
    login_path = _getenv("LOGIN_PATH", default="/auth/magic-link")
    debug = _get_bool("DEBUG", default=False)
    storage_backend = _getenv("STORAGE_BACKEND", default="memory")
    mailer_backend = _getenv("MAILER_BACKEND", default="smtp")
    from_address = _getenv("FROM_ADDRESS")
    smtp_host = _getenv("SMTP_HOST", default="localhost")
    smtp_port = _get_int("SMTP_PORT", default=587)
    smtp_username = _getenv("SMTP_USERNAME")
    smtp_password = _getenv("SMTP_PASSWORD")
    smtp_use_tls = _get_bool("SMTP_USE_TLS", default=True)
    smtp_use_ssl = _get_bool("SMTP_USE_SSL", default=False)
    smtp_timeout = _get_float("SMTP_TIMEOUT_SECONDS", default=None)
    return MagicLinkSettings(
        secret_key=secret_key,
        token_ttl_seconds=token_ttl_seconds,
        token_length=token_length,
        rate_limit_window_seconds=rate_limit_window_seconds,
        rate_limit_max_requests=rate_limit_max_requests,
        issuer=issuer,
        base_url=base_url,
        login_path=login_path,
        debug=debug,
        storage_backend=storage_backend,
        mailer_backend=mailer_backend,
        from_address=from_address,
        smtp_host=smtp_host,
        smtp_port=smtp_port,
        smtp_username=smtp_username,
        smtp_password=smtp_password,
        smtp_use_tls=smtp_use_tls,
        smtp_use_ssl=smtp_use_ssl,
        smtp_timeout=smtp_timeout,
    )


def reset_settings_cache() -> None:
    """Clear the cached configuration, forcing a reload on next access."""
    load_settings.cache_clear()
