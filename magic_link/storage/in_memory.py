"""In-memory storage backend for development and testing."""

from __future__ import annotations

import threading
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

from ..interfaces import RateLimitRule, StorageInterface, TokenRecord


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class InMemoryStorage(StorageInterface):
    """Simple in-memory storage implementation."""

    def __init__(self) -> None:
        self._tokens: Dict[str, TokenRecord] = {}
        self._rate_limits: Dict[str, List[datetime]] = {}
        self._lock = threading.RLock()

    def create_token(self, record: TokenRecord) -> None:
        with self._lock:
            self._tokens[record.token_hash] = record

    def get_token(self, token_hash: str) -> Optional[TokenRecord]:
        with self._lock:
            return self._tokens.get(token_hash)

    def consume_token(
        self,
        token_hash: str,
        *,
        consumed_at: Optional[datetime] = None,
    ) -> Optional[TokenRecord]:
        with self._lock:
            record = self._tokens.pop(token_hash, None)
            if record is None:
                return None
            consumed_time = (consumed_at or _utcnow()).astimezone(timezone.utc)
            return replace(record, consumed_at=consumed_time)

    def enforce_rate_limit(
        self,
        rule: RateLimitRule,
        *,
        at: Optional[datetime] = None,
    ) -> bool:
        current_time = (at or _utcnow()).astimezone(timezone.utc)
        window_start = current_time - timedelta(seconds=rule.window_seconds)
        with self._lock:
            entries = self._rate_limits.setdefault(rule.identifier, [])
            entries = [ts for ts in entries if ts > window_start]
            allowed = len(entries) < rule.max_requests
            if allowed:
                entries.append(current_time)
            self._rate_limits[rule.identifier] = entries
            return allowed
