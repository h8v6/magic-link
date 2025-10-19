"""High-level service for issuing and verifying magic links."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Mapping, Optional

from .config import MagicLinkConfig
from .interfaces import MagicLinkMessage, StorageInterface, TokenRecord
from .token_engine import IssuedToken, TokenEngine
from .errors import RateLimitExceededError, TokenExpiredError, TokenInvalidSignatureError


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True, slots=True)
class VerificationResult:
    """Structured outcome of a token verification attempt."""

    success: bool
    subject: Optional[str] = None
    reason: Optional[str] = None
    detail: Optional[str] = None


class MagicLinkService:
    """Facade coordinating token issuance, storage, and mail delivery."""

    def __init__(
        self,
        config: MagicLinkConfig,
        storage: StorageInterface,
        token_engine: Optional[TokenEngine] = None,
    ) -> None:
        self._config = config
        self._storage = storage
        self._token_engine = token_engine or TokenEngine(
            secret_key=config.secret_key,
            token_length=config.token.length,
            ttl_seconds=config.token.ttl_seconds,
            hash_algorithm=config.token.hash_algorithm,
            signature_algorithm=config.token.signature_algorithm,
        )

    @property
    def config(self) -> MagicLinkConfig:
        return self._config

    @property
    def token_engine(self) -> TokenEngine:
        return self._token_engine

    def issue_token(
        self,
        subject: str,
        *,
        metadata: Optional[Mapping[str, str]] = None,
        now: Optional[datetime] = None,
    ) -> IssuedToken:
        """Create and persist a new token for the subject."""
        issued = self._token_engine.issue(subject=subject, now=now)
        record = TokenRecord(
            token_hash=issued.token_hash,
            subject=issued.subject,
            signature=issued.signature,
            issued_at=issued.issued_at,
            expires_at=issued.expires_at,
            metadata=dict(metadata or {}),
        )
        self._storage.create_token(record)
        return issued

    def verify_token(
        self,
        token: str,
        *,
        now: Optional[datetime] = None,
        expected_subject: Optional[str] = None,
    ) -> VerificationResult:
        """Validate and consume a token, enforcing single-use semantics."""
        token_hash = self._token_engine.hash_token(token)
        consumed = self._storage.consume_token(token_hash, consumed_at=now)
        if consumed is None:
            return VerificationResult(success=False, reason="not_found")

        if expected_subject is not None and consumed.subject != expected_subject:
            return VerificationResult(success=False, subject=consumed.subject, reason="subject_mismatch")

        try:
            self._token_engine.verify(
                token,
                subject=consumed.subject,
                signature=consumed.signature,
                issued_at=consumed.issued_at,
                expires_at=consumed.expires_at,
                now=now,
            )
        except TokenExpiredError as exc:
            return VerificationResult(success=False, subject=consumed.subject, reason="expired", detail=str(exc))
        except TokenInvalidSignatureError as exc:
            return VerificationResult(success=False, subject=consumed.subject, reason="invalid_signature", detail=str(exc))

        return VerificationResult(success=True, subject=consumed.subject, reason=None)

    def enforce_rate_limit(self, identifier: str, *, now: Optional[datetime] = None) -> None:
        """Raise if rate limit has been exceeded for an identifier."""
        rule = self._config.rate_limit.to_rule(identifier)
        allowed = self._storage.enforce_rate_limit(
            rule=rule,
            at=now or _utcnow(),
        )
        if not allowed:
            raise RateLimitExceededError("Rate limit exceeded for identifier.")
