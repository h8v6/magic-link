from datetime import datetime, timedelta, timezone

import pytest

from magic_link.config import MagicLinkConfig, RateLimitConfig, TokenConfig
from magic_link.errors import RateLimitExceededError
from magic_link.interfaces import MagicLinkMessage
from magic_link.mailer.smtp import SMTPMailer
from magic_link.service import MagicLinkService, VerificationResult
from magic_link.storage.in_memory import InMemoryStorage


def _config() -> MagicLinkConfig:
    return MagicLinkConfig(
        secret_key="secret",
        token=TokenConfig(ttl_seconds=300, length=16),
        rate_limit=RateLimitConfig(window_seconds=60, max_requests=1),
    )


def test_issue_and_verify_token() -> None:
    config = _config()
    storage = InMemoryStorage()
    service = MagicLinkService(config=config, storage=storage)

    issued = service.issue_token(subject="user@example.com")
    result = service.verify_token(issued.token)
    assert result == VerificationResult(success=True, subject="user@example.com")


def test_verify_token_expired() -> None:
    config = _config()
    storage = InMemoryStorage()
    service = MagicLinkService(config=config, storage=storage)

    issued = service.issue_token(subject="user@example.com", now=datetime.now(timezone.utc) - timedelta(minutes=10))
    result = service.verify_token(issued.token, now=datetime.now(timezone.utc))
    assert result.success is False
    assert result.error == "expired"


def test_verify_token_invalid_signature() -> None:
    config = _config()
    storage = InMemoryStorage()
    service = MagicLinkService(config=config, storage=storage)

    service.issue_token(subject="user@example.com")
    result = service.verify_token("tampered-token")
    assert result.success is False
    assert result.error == "not_found"


def test_verify_token_subject_mismatch() -> None:
    config = _config()
    storage = InMemoryStorage()
    service = MagicLinkService(config=config, storage=storage)

    issued = service.issue_token(subject="user@example.com")
    result = service.verify_token(issued.token, expected_subject="other@example.com")
    assert result.success is False
    assert result.error == "subject_mismatch"


def test_rate_limit_enforcement() -> None:
    config = _config()
    storage = InMemoryStorage()
    service = MagicLinkService(config=config, storage=storage)

    service.enforce_rate_limit("user@example.com")
    with pytest.raises(RateLimitExceededError):
        service.enforce_rate_limit("user@example.com")
