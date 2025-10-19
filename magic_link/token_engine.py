"""Token engine handling secure generation, hashing, signing, and verification."""

from __future__ import annotations

import hashlib
import hmac
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Optional

from .errors import TokenExpiredError, TokenInvalidSignatureError


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True, slots=True)
class IssuedToken:
    """Data container for an issued magic link token."""

    token: str
    token_hash: str
    signature: str
    subject: str
    issued_at: datetime
    expires_at: datetime


class TokenEngine:
    """Encapsulates token lifecycle operations."""

    def __init__(
        self,
        secret_key: str,
        *,
        token_length: int = 32,
        ttl_seconds: int = 900,
        hash_algorithm: str = "sha256",
        signature_algorithm: str = "sha256",
    ) -> None:
        if token_length <= 0:
            raise ValueError("token_length must be a positive integer.")
        if ttl_seconds <= 0:
            raise ValueError("ttl_seconds must be a positive integer.")
        self._secret_key = secret_key.encode("utf-8")
        self._token_length = token_length
        self._ttl_seconds = ttl_seconds
        self._hash_algorithm = hash_algorithm
        self._signature_algorithm = signature_algorithm

    def issue(
        self,
        subject: str,
        *,
        now: Optional[datetime] = None,
    ) -> IssuedToken:
        """Create a new token for the provided subject."""
        issued_at = now.astimezone(timezone.utc) if now else _utcnow()
        token = secrets.token_urlsafe(self._token_length)
        token_hash = self.hash_token(token)
        signature = self.sign_token(token, subject=subject, issued_at=issued_at)
        expires_at = issued_at + timedelta(seconds=self._ttl_seconds)
        return IssuedToken(
            token=token,
            token_hash=token_hash,
            signature=signature,
            subject=subject,
            issued_at=issued_at,
            expires_at=expires_at,
        )

    def hash_token(self, token: str) -> str:
        """Hash the token for persistent storage."""
        digest = hashlib.new(self._hash_algorithm)
        digest.update(token.encode("utf-8"))
        return digest.hexdigest()

    def sign_token(self, token: str, *, subject: str, issued_at: datetime) -> str:
        """Produce an HMAC signature for the token."""
        payload = self._signature_payload(token=token, subject=subject, issued_at=issued_at)
        signature = hmac.new(
            self._secret_key,
            payload,
            digestmod=self._signature_algorithm,
        )
        return signature.hexdigest()

    def verify(
        self,
        token: str,
        *,
        subject: str,
        signature: str,
        issued_at: datetime,
        expires_at: datetime,
        now: Optional[datetime] = None,
    ) -> None:
        """Validate the token signature and expiration."""
        expected_signature = self.sign_token(token, subject=subject, issued_at=issued_at)
        if not hmac.compare_digest(signature, expected_signature):
            raise TokenInvalidSignatureError("Token signature validation failed.")

        current_time = now.astimezone(timezone.utc) if now else _utcnow()
        if current_time > expires_at.astimezone(timezone.utc):
            raise TokenExpiredError("Token has expired.")

    def _signature_payload(self, *, token: str, subject: str, issued_at: datetime) -> bytes:
        """Create the HMAC payload for signature generation."""
        issued_timestamp = int(issued_at.astimezone(timezone.utc).timestamp())
        payload = f"{subject}|{token}|{issued_timestamp}"
        return payload.encode("utf-8")
