from datetime import datetime, timedelta, timezone

import pytest

from magic_link.errors import TokenExpiredError, TokenInvalidSignatureError
from magic_link.token_engine import IssuedToken, TokenEngine


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def test_issue_produces_expected_fields() -> None:
    engine = TokenEngine(secret_key="secret", token_length=16, ttl_seconds=120)
    issued = engine.issue(subject="user@example.com", now=_utcnow())
    assert isinstance(issued, IssuedToken)
    assert len(issued.token) > 16
    assert issued.subject == "user@example.com"
    assert issued.expires_at > issued.issued_at
    assert issued.token_hash
    assert issued.signature


def test_verify_happy_path() -> None:
    engine = TokenEngine(secret_key="secret", token_length=16, ttl_seconds=60)
    issued = engine.issue(subject="user@example.com", now=_utcnow())
    engine.verify(
        issued.token,
        subject=issued.subject,
        signature=issued.signature,
        issued_at=issued.issued_at,
        expires_at=issued.expires_at,
        now=issued.issued_at + timedelta(seconds=30),
    )


def test_verify_expired_token() -> None:
    engine = TokenEngine(secret_key="secret", token_length=16, ttl_seconds=1)
    issued = engine.issue(subject="user@example.com", now=_utcnow())
    with pytest.raises(TokenExpiredError):
        engine.verify(
            issued.token,
            subject=issued.subject,
            signature=issued.signature,
            issued_at=issued.issued_at,
            expires_at=issued.issued_at + timedelta(seconds=1),
            now=issued.issued_at + timedelta(seconds=120),
        )


def test_verify_invalid_signature() -> None:
    engine = TokenEngine(secret_key="secret", token_length=16, ttl_seconds=60)
    issued = engine.issue(subject="user@example.com", now=_utcnow())
    with pytest.raises(TokenInvalidSignatureError):
        engine.verify(
            issued.token,
            subject=issued.subject,
            signature="deadbeef",
            issued_at=issued.issued_at,
            expires_at=issued.expires_at,
        )


def test_verify_with_mismatched_subject() -> None:
    engine = TokenEngine(secret_key="secret", token_length=16, ttl_seconds=60)
    issued = engine.issue(subject="user@example.com", now=_utcnow())
    with pytest.raises(TokenInvalidSignatureError):
        engine.verify(
            issued.token,
            subject="attacker@example.com",
            signature=issued.signature,
            issued_at=issued.issued_at,
            expires_at=issued.expires_at,
        )


def test_invalid_token_length_raises() -> None:
    with pytest.raises(ValueError):
        TokenEngine(secret_key="secret", token_length=0)


def test_invalid_ttl_raises() -> None:
    with pytest.raises(ValueError):
        TokenEngine(secret_key="secret", ttl_seconds=0)
