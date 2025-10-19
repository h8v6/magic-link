"""SQLAlchemy storage backend implementation."""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from typing import Callable, Iterator, Optional

from ..errors import StorageError
from ..interfaces import RateLimitRule, StorageInterface, TokenRecord

try:
    from sqlalchemy import Column, DateTime, Integer, String, select
    from sqlalchemy.orm import DeclarativeBase, Session
    from sqlalchemy.types import JSON
except ImportError as exc:  # pragma: no cover - import is validated in tests
    raise ImportError(
        "SQLAlchemy extras are required: install with `pip install \"magic-link[sqlalchemy]\"`."
    ) from exc


def _ensure_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


class Base(DeclarativeBase):
    """Declarative base for magic_link SQLAlchemy models."""


class MagicLinkToken(Base):
    """Database model storing issued tokens."""

    __tablename__ = "magic_link_tokens"

    id = Column(Integer, primary_key=True)
    token_hash = Column(String(128), nullable=False, unique=True, index=True)
    subject = Column(String(255), nullable=False, index=True)
    signature = Column(String(128), nullable=False)
    issued_at = Column(DateTime(timezone=True), nullable=False, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    consumed_at = Column(DateTime(timezone=True), nullable=True, index=True)
    payload = Column(JSON, nullable=False, default=dict)


class MagicLinkRateLimit(Base):
    """Database model tracking rate limit counters."""

    __tablename__ = "magic_link_rate_limits"

    identifier = Column(String(255), primary_key=True)
    window_start = Column(DateTime(timezone=True), nullable=False)
    request_count = Column(Integer, nullable=False)
    updated_at = Column(DateTime(timezone=True), nullable=False)


class SQLAlchemyStorage(StorageInterface):
    """Storage backend using SQLAlchemy sessions."""

    def __init__(self, session_factory: Callable[[], Session]) -> None:
        self._session_factory = session_factory

    @contextmanager
    def _session(self) -> Iterator[Session]:
        session = self._session_factory()
        try:
            yield session
            session.commit()
        except Exception as exc:  # pragma: no cover - rethrow for context
            session.rollback()
            raise StorageError("SQLAlchemy storage operation failed.") from exc
        finally:
            session.close()

    def create_token(self, record: TokenRecord) -> None:
        with self._session() as session:
            model = MagicLinkToken(
                token_hash=record.token_hash,
                subject=record.subject,
                signature=record.signature,
                issued_at=record.issued_at,
                expires_at=record.expires_at,
                consumed_at=record.consumed_at,
                payload=dict(record.metadata),
            )
            session.merge(model)

    def get_token(self, token_hash: str) -> Optional[TokenRecord]:
        with self._session() as session:
            stmt = select(MagicLinkToken).where(MagicLinkToken.token_hash == token_hash)
            result = session.execute(stmt).scalar_one_or_none()
            if result is None:
                return None
            return self._to_record(result)

    def consume_token(
        self,
        token_hash: str,
        *,
        consumed_at: Optional[datetime] = None,
    ) -> Optional[TokenRecord]:
        consumed_time = _ensure_utc(consumed_at or datetime.now(timezone.utc))
        with self._session() as session:
            stmt = select(MagicLinkToken).where(MagicLinkToken.token_hash == token_hash)
            result = session.execute(stmt).scalar_one_or_none()
            if result is None:
                return None
            if result.consumed_at is not None:
                return None
            result.consumed_at = consumed_time
            session.add(result)
            return replace(self._to_record(result), consumed_at=consumed_time)

    def enforce_rate_limit(
        self,
        rule: RateLimitRule,
        *,
        at: Optional[datetime] = None,
    ) -> bool:
        current_time = _ensure_utc(at or datetime.now(timezone.utc))
        with self._session() as session:
            record = session.get(MagicLinkRateLimit, rule.identifier)
            if record is None:
                session.add(
                    MagicLinkRateLimit(
                        identifier=rule.identifier,
                        window_start=current_time,
                        request_count=1,
                        updated_at=current_time,
                    )
                )
                return True

            window_start = _ensure_utc(record.window_start)
            window_reset_threshold = window_start + timedelta(seconds=rule.window_seconds)
            if current_time >= window_reset_threshold:
                record.window_start = current_time
                record.request_count = 0

            if record.request_count >= rule.max_requests:
                return False

            record.request_count += 1
            record.updated_at = current_time
            session.add(record)
            return True

    def _to_record(self, model: MagicLinkToken) -> TokenRecord:
        return TokenRecord(
            token_hash=model.token_hash,
            subject=model.subject,
            signature=model.signature,
            issued_at=_ensure_utc(model.issued_at),
            expires_at=_ensure_utc(model.expires_at),
            consumed_at=_ensure_utc(model.consumed_at) if model.consumed_at else None,
            metadata=model.payload or {},
        )
