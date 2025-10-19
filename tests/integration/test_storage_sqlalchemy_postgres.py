from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone

import pytest
import secrets

from magic_link.interfaces import RateLimitRule, TokenRecord
from magic_link.storage.sqlalchemy import Base, SQLAlchemyStorage


@pytest.fixture(scope="module")
def postgres_engine():
    url = os.getenv("MAGIC_LINK_TEST_DATABASE_URL")
    if not url:
        pytest.skip("MAGIC_LINK_TEST_DATABASE_URL not configured")

    try:
        from sqlalchemy import create_engine
    except ImportError:  # pragma: no cover - handled by optional extras
        pytest.skip("SQLAlchemy extras not installed")

    engine = create_engine(url, future=True)
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)

    yield engine

    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture(scope="module")
def postgres_storage(postgres_engine):
    from sqlalchemy.orm import sessionmaker

    SessionLocal = sessionmaker(bind=postgres_engine, expire_on_commit=False)

    storage = SQLAlchemyStorage(session_factory=SessionLocal)
    yield storage

    postgres_engine.dispose()


def _make_record(subject: str = "user@example.com") -> TokenRecord:
    issued_at = datetime.now(timezone.utc)
    expires_at = issued_at + timedelta(minutes=10)
    return TokenRecord(
        token_hash=secrets.token_hex(16),
        subject=subject,
        signature=secrets.token_hex(16),
        issued_at=issued_at,
        expires_at=expires_at,
        metadata={"ip": "127.0.0.1"},
    )


def test_postgres_token_lifecycle(postgres_storage: SQLAlchemyStorage) -> None:
    record = _make_record()
    postgres_storage.create_token(record)

    fetched = postgres_storage.get_token(record.token_hash)
    assert fetched is not None
    assert fetched.token_hash == record.token_hash
    assert fetched.metadata == {"ip": "127.0.0.1"}

    consumed = postgres_storage.consume_token(record.token_hash)
    assert consumed is not None
    assert consumed.consumed_at is not None

    post_consume = postgres_storage.get_token(record.token_hash)
    assert post_consume is not None
    assert post_consume.consumed_at is not None


def test_postgres_rate_limit(postgres_storage: SQLAlchemyStorage) -> None:
    now = datetime.now(timezone.utc)
    rule = RateLimitRule(identifier="user@example.com", window_seconds=60, max_requests=1)

    assert postgres_storage.enforce_rate_limit(rule, at=now) is True
    assert postgres_storage.enforce_rate_limit(rule, at=now + timedelta(seconds=10)) is False
    assert postgres_storage.enforce_rate_limit(rule, at=now + timedelta(seconds=70)) is True
