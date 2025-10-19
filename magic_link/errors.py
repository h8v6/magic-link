"""Error types raised by the magic_link package."""

from __future__ import annotations


class MagicLinkError(Exception):
    """Base class for all magic_link errors."""


class ConfigurationError(MagicLinkError):
    """Raised when application configuration is invalid or missing."""


class TokenError(MagicLinkError):
    """Base error for token lifecycle failures."""


class TokenExpiredError(TokenError):
    """Raised when a token is past its expiration timestamp."""


class TokenInvalidSignatureError(TokenError):
    """Raised when a token's signature does not match the expected value."""


class RateLimitExceededError(MagicLinkError):
    """Raised when rate limit thresholds are exceeded."""


class StorageError(MagicLinkError):
    """Base error raised by storage backends."""


class MailerError(MagicLinkError):
    """Base error raised by mailer backends."""
