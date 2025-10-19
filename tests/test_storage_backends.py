from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone
from typing import Dict

import pytest

from magic_link.errors import StorageError
from magic_link.interfaces import RateLimitRule, TokenRecord
from magic_link.storage.in_memory import InMemoryStorage

try:  # pragma: no cover - optional dependency
    from magic_link.storage.redis import RedisStorage
except ImportError:  # pragma: no cover
    RedisStorage = None  # type: ignore[assignment]

try:  # pragma: no cover - optional dependency
    from magic_link.storage.sqlalchemy import Base, SQLAlchemyStorage
except ImportError:  # pragma: no cover
    Base = None  # type: ignore[assignment]
    SQLAlchemyStorage = None  # type: ignore[assignment]


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _make_record(subject: str = "user@example.com") -> TokenRecord:
    issued = _utcnow()
    return TokenRecord(
        token_hash=secrets.token_hex(16),
        subject=subject,
        signature=secrets.token_hex(16),
        issued_at=issued,
        expires_at=issued + timedelta(minutes=15),
    )


class FakePipeline:
    def __init__(self, client: "FakeRedis") -> None:
        self.client = client
        self.commands = []

    def hset(self, key: str, *, mapping: Dict[str, str]) -> "FakePipeline":
        self.commands.append(("hset", key, mapping))
        return self

    def expire(self, key: str, ttl: int) -> "FakePipeline":
        self.commands.append(("expire", key, ttl))
        return self

    def hgetall(self, key: str) -> "FakePipeline":
        self.commands.append(("hgetall", key))
        return self

    def delete(self, key: str) -> "FakePipeline":
        self.commands.append(("delete", key))
        return self

    def incr(self, key: str) -> "FakePipeline":
        self.commands.append(("incr", key))
        return self

    def execute(self):
        results = []
        for op, key, *rest in self.commands:
            if op == "hset":
                mapping = rest[0]
                self.client._hashes[key] = {
                    k.encode(): v.encode() for k, v in mapping.items()
                }
                results.append(True)
            elif op == "expire":
                results.append(True)
            elif op == "hgetall":
                results.append(dict(self.client._hashes.get(key, {})))
            elif op == "delete":
                existed = key in self.client._hashes
                self.client._hashes.pop(key, None)
                results.append(1 if existed else 0)
            elif op == "incr":
                value = self.client._counters.get(key, 0) + 1
                self.client._counters[key] = value
                results.append(value)
        self.commands.clear()
        return results

    def __enter__(self) -> "FakePipeline":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.commands.clear()


class FakeRedis:
    def __init__(self) -> None:
        self._hashes: Dict[str, Dict[bytes, bytes]] = {}
        self._counters: Dict[str, int] = {}

    def pipeline(self) -> FakePipeline:
        return FakePipeline(self)

    def hgetall(self, key: str) -> Dict[bytes, bytes]:
        return dict(self._hashes.get(key, {}))


@pytest.fixture
def redis_storage():
    if RedisStorage is None:
        pytest.skip("redis extra not installed")
    return RedisStorage(FakeRedis())


@pytest.fixture
def sqlite_storage(tmp_path):
    if SQLAlchemyStorage is None or Base is None:
        pytest.skip("sqlalchemy extra not installed")
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
    return SQLAlchemyStorage(session_factory=SessionLocal)


def test_in_memory_storage_roundtrip() -> None:
    storage = InMemoryStorage()
    record = _make_record()
    storage.create_token(record)
    fetched = storage.get_token(record.token_hash)
    assert fetched == record

    consumed = storage.consume_token(record.token_hash)
    assert consumed is not None
    assert consumed.consumed_at is not None
    assert storage.get_token(record.token_hash) is None
    assert storage.consume_token("missing") is None

    rule = RateLimitRule(identifier="user@example.com", window_seconds=60, max_requests=2)
    assert storage.enforce_rate_limit(rule, at=_utcnow())
    assert storage.enforce_rate_limit(rule, at=_utcnow())
    assert not storage.enforce_rate_limit(rule, at=_utcnow())


def test_sqlalchemy_storage_roundtrip(sqlite_storage: SQLAlchemyStorage) -> None:
    record = _make_record()
    sqlite_storage.create_token(record)
    fetched = sqlite_storage.get_token(record.token_hash)
    assert fetched == record

    consumed = sqlite_storage.consume_token(record.token_hash)
    assert consumed is not None
    assert consumed.consumed_at is not None
    assert sqlite_storage.consume_token(record.token_hash) is None
    assert sqlite_storage.get_token("missing") is None
    assert sqlite_storage.consume_token("missing") is None

    rule = RateLimitRule(identifier="id", window_seconds=60, max_requests=1)
    assert sqlite_storage.enforce_rate_limit(rule, at=_utcnow())
    assert not sqlite_storage.enforce_rate_limit(rule, at=_utcnow())
    assert sqlite_storage.enforce_rate_limit(rule, at=_utcnow() + timedelta(seconds=120))


def test_redis_storage_roundtrip(redis_storage: RedisStorage) -> None:
    record = _make_record()
    redis_storage.create_token(record)
    fetched = redis_storage.get_token(record.token_hash)
    assert fetched == record

    consumed = redis_storage.consume_token(record.token_hash)
    assert consumed is not None
    assert consumed.consumed_at is not None

    rule = RateLimitRule(identifier="id", window_seconds=60, max_requests=1)
    assert redis_storage.enforce_rate_limit(rule, at=_utcnow())
    assert not redis_storage.enforce_rate_limit(rule, at=_utcnow())
    redis_storage._client._counters.clear()  # type: ignore[attr-defined]
    assert redis_storage.enforce_rate_limit(rule, at=_utcnow() + timedelta(seconds=70))


def test_redis_storage_missing_token(redis_storage: RedisStorage) -> None:
    assert redis_storage.get_token("missing") is None
    assert redis_storage.consume_token("missing") is None


def test_redis_storage_malformed_data(redis_storage: RedisStorage) -> None:
    key = redis_storage._token_key("bad")  # type: ignore[attr-defined]
    redis_storage._client._hashes[key] = {b"token_hash": b"bad"}  # type: ignore[attr-defined]
    with pytest.raises(StorageError):
        redis_storage.get_token("bad")
