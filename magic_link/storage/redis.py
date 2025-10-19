"""Redis storage backend optimized for production workloads."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from ..errors import StorageError
from ..interfaces import RateLimitRule, StorageInterface, TokenRecord

try:
    from redis import Redis
except ImportError as exc:  # pragma: no cover - import validated in tests
    raise ImportError(
        "Redis extras are required: install with `pip install \"magic-link[redis]\"`."
    ) from exc


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class RedisStorage(StorageInterface):
    """Redis-backed storage for tokens and rate limits."""

    def __init__(self, client: Redis, *, namespace: str = "magic_link") -> None:
        self._client = client
        self._namespace = namespace

    def create_token(self, record: TokenRecord) -> None:
        key = self._token_key(record.token_hash)
        payload = {
            "token_hash": record.token_hash,
            "subject": record.subject,
            "signature": record.signature,
            "issued_at": record.issued_at.isoformat(),
            "expires_at": record.expires_at.isoformat(),
            "consumed_at": record.consumed_at.isoformat() if record.consumed_at else "",
            "metadata": json.dumps(record.metadata),
        }
        ttl_seconds = max(
            int((record.expires_at - _utcnow()).total_seconds()),
            0,
        )
        with self._client.pipeline() as pipeline:
            pipeline.hset(key, mapping=payload)
            if ttl_seconds > 0:
                pipeline.expire(key, ttl_seconds)
            pipeline.execute()

    def get_token(self, token_hash: str) -> Optional[TokenRecord]:
        key = self._token_key(token_hash)
        data = self._client.hgetall(key)
        if not data:
            return None
        return self._to_record(data)

    def consume_token(
        self,
        token_hash: str,
        *,
        consumed_at: Optional[datetime] = None,
    ) -> Optional[TokenRecord]:
        key = self._token_key(token_hash)
        with self._client.pipeline() as pipeline:
            pipeline.hgetall(key)
            pipeline.delete(key)
            raw_data, _ = pipeline.execute()
        if not raw_data:
            return None
        record = self._to_record(raw_data)
        consumed_time = (consumed_at or _utcnow()).astimezone(timezone.utc)
        return TokenRecord(
            token_hash=record.token_hash,
            subject=record.subject,
            signature=record.signature,
            issued_at=record.issued_at,
            expires_at=record.expires_at,
            metadata=record.metadata,
            consumed_at=consumed_time,
        )

    def enforce_rate_limit(
        self,
        rule: RateLimitRule,
        *,
        at: Optional[datetime] = None,
    ) -> bool:
        key = self._rate_key(rule.identifier)
        with self._client.pipeline() as pipeline:
            pipeline.incr(key)
            pipeline.expire(key, rule.window_seconds)
            count, _ = pipeline.execute()
        return int(count) <= rule.max_requests

    def _token_key(self, token_hash: str) -> str:
        return f"{self._namespace}:token:{token_hash}"

    def _rate_key(self, identifier: str) -> str:
        return f"{self._namespace}:rate:{identifier}"

    def _to_record(self, raw: Dict[bytes, bytes]) -> TokenRecord:
        try:
            subject = raw[b"subject"].decode()
            token_hash = raw[b"token_hash"].decode()
            signature = raw[b"signature"].decode()
            issued_at = datetime.fromisoformat(raw[b"issued_at"].decode())
            expires_at = datetime.fromisoformat(raw[b"expires_at"].decode())
            consumed_raw = raw.get(b"consumed_at", b"").decode()
            metadata_raw = raw.get(b"metadata", b"{}").decode()
            consumed_at = datetime.fromisoformat(consumed_raw) if consumed_raw else None
            metadata: Dict[str, Any] = json.loads(metadata_raw) if metadata_raw else {}
        except (KeyError, ValueError, json.JSONDecodeError) as exc:
            raise StorageError("Stored Redis token data is malformed.") from exc
        return TokenRecord(
            token_hash=token_hash,
            subject=subject,
            signature=signature,
            issued_at=issued_at,
            expires_at=expires_at,
            consumed_at=consumed_at,
            metadata=metadata,
        )
