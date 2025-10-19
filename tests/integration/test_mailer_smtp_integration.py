from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from magic_link.interfaces import MagicLinkMessage
from magic_link.mailer.smtp import SMTPMailer

try:
    from aiosmtpd.controller import Controller
except ImportError:  # pragma: no cover - optional dependency
    Controller = None


class _Collector:
    def __init__(self) -> None:
        self.messages = []

    async def handle_DATA(self, server, session, envelope):  # type: ignore[override]
        self.messages.append(envelope)
        return "250 OK"


@pytest.fixture(scope="module")
def smtp_server():
    if Controller is None:
        pytest.skip("aiosmtpd is not installed")

    handler = _Collector()
    controller = Controller(handler, hostname="127.0.0.1", port=0)
    controller.start()
    port = controller.port
    try:
        yield handler, port
    finally:
        controller.stop()


def test_smtp_mailer_integration(smtp_server) -> None:
    handler, port = smtp_server
    mailer = SMTPMailer(
        host="127.0.0.1",
        port=port,
        use_tls=False,
        default_sender="sender@example.com",
    )

    expires_at = datetime.now(timezone.utc) + timedelta(minutes=15)
    message = MagicLinkMessage(
        recipient="user@example.com",
        link="https://example.com/login?token=token",
        subject="Magic Link",
        expires_at=expires_at,
    )

    mailer.send_magic_link(message)

    assert len(handler.messages) == 1
    envelope = handler.messages[0]
    assert envelope.mail_from == "sender@example.com"
    assert "https://example.com/login?token=token" in envelope.content.decode()
