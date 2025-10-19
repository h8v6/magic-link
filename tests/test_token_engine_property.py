from datetime import timedelta, timezone

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from magic_link.errors import TokenExpiredError, TokenInvalidSignatureError
from magic_link.token_engine import TokenEngine


@st.composite
def token_inputs(draw):
    secret = draw(st.text(min_size=1))
    subject = draw(st.emails())
    ttl = draw(st.integers(min_value=1, max_value=3600))
    token_length = draw(st.integers(min_value=8, max_value=64))
    now = draw(st.datetimes(timezones=st.just(timezone.utc)))
    return secret, subject, ttl, token_length, now


@settings(deadline=None)
@given(token_inputs())
def test_token_round_trip(data):
    secret, subject, ttl, token_length, now = data
    engine = TokenEngine(secret_key=secret, ttl_seconds=ttl, token_length=token_length)
    issued = engine.issue(subject=subject, now=now)

    # Token should verify during its lifetime
    engine.verify(
        issued.token,
        subject=issued.subject,
        signature=issued.signature,
        issued_at=issued.issued_at,
        expires_at=issued.expires_at,
        now=issued.issued_at,
    )

    # Tampering with signature should fail
    with pytest.raises(TokenInvalidSignatureError):
        engine.verify(
            issued.token,
            subject=issued.subject,
            signature="deadbeef",
            issued_at=issued.issued_at,
            expires_at=issued.expires_at,
            now=issued.issued_at,
        )

    # Expired token should fail
    with pytest.raises(TokenExpiredError):
        engine.verify(
            issued.token,
            subject=issued.subject,
            signature=issued.signature,
            issued_at=issued.issued_at,
            expires_at=issued.expires_at,
            now=issued.expires_at + timedelta(seconds=ttl + 1),
        )
