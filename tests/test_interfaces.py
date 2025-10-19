from datetime import datetime

from magic_link.interfaces import MagicLinkMessage, TokenRecord


def test_token_record_normalizes_naive_datetimes():
    issued = datetime(2024, 1, 1, 12, 0, 0)
    expires = datetime(2024, 1, 1, 13, 0, 0)
    record = TokenRecord(
        token_hash="hash",
        subject="user@example.com",
        signature="sig",
        issued_at=issued,
        expires_at=expires,
    )
    assert record.issued_at.tzinfo is not None
    assert record.expires_at.tzinfo is not None


def test_magic_link_message_normalizes_expiry():
    expires = datetime(2024, 1, 1, 13, 0, 0)
    message = MagicLinkMessage(
        recipient="user@example.com",
        link="https://example.com",
        subject="test",
        expires_at=expires,
    )
    assert message.expires_at.tzinfo is not None
