from __future__ import annotations

import os
import secrets
from datetime import datetime, timedelta, timezone

import pytest

from magic_link.interfaces import RateLimitRule, TokenRecord


@pytest.fixture(scope="module")
def redis_client():
    url = os.getenv("MAGIC_LINK_TEST_REDIS_URL")
    if not url:
        pytest.skip("MAGIC_LINK_TEST_REDIS_URL not configured")

    try:
        import redis
    except ImportError:  # pragma: no cover - handled by optional extras
        pytest.skip("Redis extras not installed")

    client = redis.from_url(url)
    client.flushdb()

    yield client

    client.flushdb()
    client.close()


@pytest.fixture(scope="module")
def redis_storage(redis_client):
    from magic_link.storage.redis import RedisStorage

    return RedisStorage(redis_client, namespace="magic_link_tests")


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


def test_redis_token_lifecycle(redis_storage) -> None:
    record = _make_record()
    redis_storage.create_token(record)

    fetched = redis_storage.get_token(record.token_hash)
    assert fetched is not None
    assert fetched.token_hash == record.token_hash

    consumed = redis_storage.consume_token(record.token_hash)
    assert consumed is not None
    assert consumed.consumed_at is not None

    # token should no longer be retrievable
    assert redis_storage.get_token(record.token_hash) is None


def test_redis_rate_limiting(redis_storage) -> None:
    now = datetime.now(timezone.utc)
    rule = RateLimitRule(identifier="redis-user", window_seconds=30, max_requests=2)

    assert redis_storage.enforce_rate_limit(rule, at=now)
    assert redis_storage.enforce_rate_limit(rule, at=now + timedelta(seconds=5))
    assert not redis_storage.enforce_rate_limit(rule, at=now + timedelta(seconds=10))
    # after window elapses the counter should reset
    assert redis_storage.enforce_rate_limit(rule, at=now + timedelta(seconds=40))
