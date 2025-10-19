"""Top-level package exports for magic_link."""

from .config import MagicLinkConfig, RateLimitConfig, SMTPConfig, TokenConfig, load_settings, reset_settings_cache
from .service import MagicLinkService, VerificationResult
from .token_engine import IssuedToken, TokenEngine

__all__ = [
    "MagicLinkConfig",
    "RateLimitConfig",
    "SMTPConfig",
    "TokenConfig",
    "load_settings",
    "reset_settings_cache",
    "MagicLinkService",
    "VerificationResult",
    "IssuedToken",
    "TokenEngine",
]
