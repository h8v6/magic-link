from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
from unittest.mock import MagicMock, patch

import pytest

from magic_link.errors import MailerError
from magic_link.interfaces import MagicLinkMessage
from magic_link.mailer.smtp import SMTPMailer


def _message(sender: str | None = "from@example.com") -> MagicLinkMessage:
    return MagicLinkMessage(
        recipient="user@example.com",
        link="https://example.com/login?token=abc",
        subject="Your login link",
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=15),
        sender=sender,
    )


@patch("magic_link.mailer.smtp.smtplib.SMTP")
def test_smtp_mailer_sends_email(mock_smtp: MagicMock) -> None:
    smtp_instance = MagicMock()
    mock_smtp.return_value.__enter__.return_value = smtp_instance

    mailer = SMTPMailer(host="localhost", port=1025, use_tls=False, default_sender="from@example.com")
    mailer.send_magic_link(_message())

    mock_smtp.assert_called_once_with(host="localhost", port=1025, timeout=None)
    smtp_instance.send_message.assert_called_once()


def test_missing_sender_raises() -> None:
    mailer = SMTPMailer(host="localhost", port=25, use_tls=False)
    with pytest.raises(MailerError):
        mailer.send_magic_link(_message(sender=None))


def test_custom_template_builder() -> None:
    sent_messages: list[EmailMessage] = []

    def build_template(message: MagicLinkMessage) -> EmailMessage:
        email = EmailMessage()
        email["From"] = "builder@example.com"
        email["To"] = message.recipient
        email["Subject"] = "Custom"
        email.set_content("Custom body")
        sent_messages.append(email)
        return email

    with patch("magic_link.mailer.smtp.smtplib.SMTP") as mock_smtp:
        smtp_instance = MagicMock()
        mock_smtp.return_value.__enter__.return_value = smtp_instance

        mailer = SMTPMailer(
            host="localhost",
            port=25,
            use_tls=False,
            template_builder=build_template,
        )
        mailer.send_magic_link(_message())

    assert len(sent_messages) == 1
    smtp_instance.send_message.assert_called_once_with(sent_messages[0])
