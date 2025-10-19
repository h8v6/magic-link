"""Explicit configuration models for the magic_link package."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
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
class TokenConfig:
    """Settings governing token generation and validation."""

    ttl_seconds: int = 900
    length: int = 32
    hash_algorithm: str = "sha256"
    signature_algorithm: str = "sha256"

    def __post_init__(self) -> None:
        if self.ttl_seconds <= 0:
            raise ConfigurationError("Token TTL must be a positive integer.")
        if self.length <= 0:
            raise ConfigurationError("Token length must be a positive integer.")


@dataclass(frozen=True, slots=True)
class RateLimitConfig:
    """Settings for rate limiting issuance requests."""

    window_seconds: int = 60
    max_requests: int = 5

    def __post_init__(self) -> None:
        if self.window_seconds <= 0:
            raise ConfigurationError("Rate limit window must be positive.")
        if self.max_requests <= 0:
            raise ConfigurationError("Rate limit max requests must be positive.")

    def to_rule(self, identifier: str):
        from .interfaces import RateLimitRule  # Imported lazily to avoid circular imports

        return RateLimitRule(
            identifier=identifier,
            window_seconds=self.window_seconds,
            max_requests=self.max_requests,
        )


@dataclass(frozen=True, slots=True)
class SMTPConfig:
    """SMTP delivery configuration."""

    host: str = "localhost"
    port: int = 587
    username: Optional[str] = None
    password: Optional[str] = None
    use_tls: bool = True
    use_ssl: bool = False
    timeout: Optional[float] = None

    def __post_init__(self) -> None:
        if self.port <= 0:
            raise ConfigurationError("SMTP port must be positive.")
        if self.use_ssl and self.use_tls:
            raise ConfigurationError("Enable either TLS or SSL for SMTP, not both.")
        if self.timeout is not None and self.timeout <= 0:
            raise ConfigurationError("SMTP timeout must be positive when provided.")


@dataclass(frozen=True, slots=True)
class MagicLinkConfig:
    """Top-level configuration object for the magic_link library."""

    secret_key: str
    token: TokenConfig = field(default_factory=TokenConfig)
    rate_limit: RateLimitConfig = field(default_factory=RateLimitConfig)
    issuer: Optional[str] = None
    base_url: Optional[str] = None
    login_path: str = "/auth/magic-link"
    debug: bool = False
    storage_backend: str = "memory"
    mailer_backend: str = "smtp"
    from_address: Optional[str] = None
    smtp: SMTPConfig = field(default_factory=SMTPConfig)

    def __post_init__(self) -> None:
        if self.secret_key.strip() == "":
            raise ConfigurationError("SECRET_KEY must be provided.")
        if not self.login_path.startswith("/"):
            raise ConfigurationError("LOGIN_PATH must be an absolute path (start with '/').")

    @classmethod
    def from_env(cls) -> "MagicLinkConfig":
        """Load configuration from environment variables."""
        _load_dotenv()
        secret_key = _get_required("SECRET_KEY")
        token = TokenConfig(
            ttl_seconds=_get_int("TOKEN_TTL_SECONDS", default=900),
            length=_get_int("TOKEN_LENGTH", default=32),
            hash_algorithm=_getenv("TOKEN_HASH_ALGORITHM", default="sha256"),
            signature_algorithm=_getenv("TOKEN_SIGNATURE_ALGORITHM", default="sha256"),
        )
        rate_limit = RateLimitConfig(
            window_seconds=_get_int("RATE_LIMIT_WINDOW_SECONDS", default=60),
            max_requests=_get_int("RATE_LIMIT_MAX_REQUESTS", default=5),
        )
        smtp = SMTPConfig(
            host=_getenv("SMTP_HOST", default="localhost"),
            port=_get_int("SMTP_PORT", default=587),
            username=_getenv("SMTP_USERNAME"),
            password=_getenv("SMTP_PASSWORD"),
            use_tls=_get_bool("SMTP_USE_TLS", default=True),
            use_ssl=_get_bool("SMTP_USE_SSL", default=False),
            timeout=_get_float("SMTP_TIMEOUT_SECONDS", default=None),
        )
        return cls(
            secret_key=secret_key,
            token=token,
            rate_limit=rate_limit,
            issuer=_getenv("ISSUER"),
            base_url=_getenv("BASE_URL"),
            login_path=_getenv("LOGIN_PATH", default="/auth/magic-link"),
            debug=_get_bool("DEBUG", default=False),
            storage_backend=_getenv("STORAGE_BACKEND", default="memory"),
            mailer_backend=_getenv("MAILER_BACKEND", default="smtp"),
            from_address=_getenv("FROM_ADDRESS"),
            smtp=smtp,
        )


@lru_cache(maxsize=1)
def load_settings() -> MagicLinkConfig:
    """
    Load and cache runtime settings from environment variables.

    This function returns a ``MagicLinkConfig`` instance for backward compatibility
    with earlier versions of the library.
    """
    return MagicLinkConfig.from_env()


def reset_settings_cache() -> None:
    """Clear the cached configuration, forcing a reload on next access."""
    load_settings.cache_clear()
