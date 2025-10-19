"""Abstract interfaces defining extensibility points for magic_link."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Mapping, Optional


def _ensure_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


@dataclass(frozen=True, slots=True)
class TokenRecord:
    """Represents a stored magic link token."""

    token_hash: str
    subject: str
    signature: str
    issued_at: datetime
    expires_at: datetime
    metadata: Mapping[str, Any] = field(default_factory=dict)
    consumed_at: Optional[datetime] = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "issued_at", _ensure_utc(self.issued_at))
        object.__setattr__(self, "expires_at", _ensure_utc(self.expires_at))
        if self.consumed_at is not None:
            object.__setattr__(self, "consumed_at", _ensure_utc(self.consumed_at))


@dataclass(frozen=True, slots=True)
class RateLimitRule:
    """Defines parameters for rate limiting."""

    identifier: str
    window_seconds: int
    max_requests: int


class StorageInterface(ABC):
    """Storage abstraction for persisting tokens and rate limit state."""

    @abstractmethod
    def create_token(self, record: TokenRecord) -> None:
        """Persist a newly issued token."""

    @abstractmethod
    def get_token(self, token_hash: str) -> Optional[TokenRecord]:
        """Fetch a token by its hash."""

    @abstractmethod
    def consume_token(self, token_hash: str, *, consumed_at: Optional[datetime] = None) -> Optional[TokenRecord]:
        """Mark a token as consumed and remove or update it as appropriate."""

    @abstractmethod
    def enforce_rate_limit(
        self,
        rule: RateLimitRule,
        *,
        at: Optional[datetime] = None,
    ) -> bool:
        """Return True if the request is permitted, False if the rate limit is exceeded."""


@dataclass(frozen=True, slots=True)
class MagicLinkMessage:
    """Payload supplied to mailers for delivering magic link emails."""

    recipient: str
    link: str
    subject: str
    expires_at: datetime
    sender: Optional[str] = None
    text_body: Optional[str] = None
    html_body: Optional[str] = None
    context: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "expires_at", _ensure_utc(self.expires_at))


class MailerInterface(ABC):
    """Interface all mailer implementations must satisfy."""

    @abstractmethod
    def send_magic_link(self, message: MagicLinkMessage) -> None:
        """Deliver the supplied magic link message to the recipient."""
