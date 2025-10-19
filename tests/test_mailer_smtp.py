from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
from unittest.mock import MagicMock, patch
import smtplib

import pytest

from magic_link.config import MagicLinkConfig, SMTPConfig
from magic_link.errors import ConfigurationError, MailerError
from magic_link.interfaces import MagicLinkMessage
from magic_link.mailer import available_mailers, create_mailer
from magic_link.mailer.smtp import SMTPMailer


def _message(sender: str | None = "from@example.com", html: str | None = None) -> MagicLinkMessage:
    return MagicLinkMessage(
        recipient="user@example.com",
        link="https://example.com/login?token=abc",
        subject="Your login link",
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=15),
        sender=sender,
        html_body=html,
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


@patch("magic_link.mailer.smtp.smtplib.SMTP")
def test_create_mailer_uses_registry(mock_smtp: MagicMock) -> None:
    config = MagicLinkConfig(
        secret_key="secret",
        from_address="sender@example.com",
        smtp=SMTPConfig(host="localhost", port=2525, use_tls=False),
    )

    mailer = create_mailer(config, timeout=5)
    assert isinstance(mailer, SMTPMailer)
    assert "smtp" in available_mailers()

    message = _message()
    mailer.send_magic_link(message)
    mock_smtp.assert_called_once()


@patch("magic_link.mailer.smtp.smtplib.SMTP")
def test_smtp_mailer_tls_flow(mock_smtp: MagicMock) -> None:
    smtp_instance = MagicMock()
    mock_smtp.return_value.__enter__.return_value = smtp_instance

    mailer = SMTPMailer(
        host="localhost",
        port=587,
        use_tls=True,
        default_sender="sender@example.com",
        username="user",
        password="pass",
    )

    mailer.send_magic_link(_message(sender=None))
    smtp_instance.starttls.assert_called_once()
    smtp_instance.login.assert_called_once_with("user", "pass")


@patch("magic_link.mailer.smtp.smtplib.SMTP_SSL")
def test_smtp_mailer_ssl_flow(mock_smtp_ssl: MagicMock) -> None:
    smtp_instance = MagicMock()
    mock_smtp_ssl.return_value.__enter__.return_value = smtp_instance

    mailer = SMTPMailer(
        host="localhost",
        port=465,
        use_tls=False,
        use_ssl=True,
        default_sender="sender@example.com",
    )

    mailer.send_magic_link(_message())
    mock_smtp_ssl.assert_called_once()


@patch("magic_link.mailer.smtp.smtplib.SMTP")
def test_smtp_mailer_handles_errors(mock_smtp: MagicMock) -> None:
    smtp_instance = MagicMock()
    mock_smtp.return_value.__enter__.return_value = smtp_instance
    smtp_instance.send_message.side_effect = smtplib.SMTPException("boom")

    mailer = SMTPMailer(host="localhost", port=1025, use_tls=False, default_sender="from@example.com")

    with pytest.raises(MailerError):
        mailer.send_magic_link(_message())


def test_create_mailer_unknown_backend() -> None:
    config = MagicLinkConfig(secret_key="secret")
    with pytest.raises(ConfigurationError):
        create_mailer(config, backend="does-not-exist")


@patch("magic_link.mailer.smtp.smtplib.SMTP")
def test_html_body_adds_alternative(mock_smtp: MagicMock) -> None:
    smtp_instance = MagicMock()
    mock_smtp.return_value.__enter__.return_value = smtp_instance

    mailer = SMTPMailer(host="localhost", port=1025, use_tls=False, default_sender="from@example.com")
    mailer.send_magic_link(_message(html="<p>Hello</p>"))
    smtp_instance.send_message.assert_called_once()
