from datetime import datetime, timedelta, timezone

import pytest

from dataclasses import replace

from magic_link.config import MagicLinkConfig, RateLimitConfig, TokenConfig
from magic_link.errors import RateLimitExceededError
from magic_link.service import MagicLinkService, VerificationResult
from magic_link.token_engine import TokenEngine
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
    assert result == VerificationResult(success=True, subject="user@example.com", reason=None, detail=None)


def test_verify_token_expired() -> None:
    config = _config()
    storage = InMemoryStorage()
    service = MagicLinkService(config=config, storage=storage)

    issued = service.issue_token(subject="user@example.com", now=datetime.now(timezone.utc) - timedelta(minutes=10))
    result = service.verify_token(issued.token, now=datetime.now(timezone.utc))
    assert result.success is False
    assert result.reason == "expired"


def test_verify_token_invalid_signature() -> None:
    config = _config()
    storage = InMemoryStorage()
    service = MagicLinkService(config=config, storage=storage)

    issued = service.issue_token(subject="user@example.com")
    storage._tokens[issued.token_hash] = replace(  # type: ignore[attr-defined]
        storage._tokens[issued.token_hash], signature="bad-signature"
    )
    result = service.verify_token(issued.token)
    assert result.success is False
    assert result.reason == "invalid_signature"
    assert result.detail


def test_verify_token_subject_mismatch() -> None:
    config = _config()
    storage = InMemoryStorage()
    service = MagicLinkService(config=config, storage=storage)

    issued = service.issue_token(subject="user@example.com")
    result = service.verify_token(issued.token, expected_subject="other@example.com")
    assert result.success is False
    assert result.reason == "subject_mismatch"


def test_rate_limit_enforcement() -> None:
    config = _config()
    storage = InMemoryStorage()
    service = MagicLinkService(config=config, storage=storage)

    service.enforce_rate_limit("user@example.com")
    with pytest.raises(RateLimitExceededError):
        service.enforce_rate_limit("user@example.com")


def test_service_properties() -> None:
    config = _config()
    storage = InMemoryStorage()
    service = MagicLinkService(config=config, storage=storage)

    assert service.config is config
    assert isinstance(service.token_engine, TokenEngine)
    issued = service.token_engine.issue("user@example.com")
    assert issued.subject == "user@example.com"


def test_verify_token_not_found() -> None:
    config = _config()
    storage = InMemoryStorage()
    service = MagicLinkService(config=config, storage=storage)

    result = service.verify_token("missing-token")
    assert result.success is False
    assert result.reason == "not_found"
