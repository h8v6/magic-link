"""SMTP mailer implementation."""

from __future__ import annotations

import smtplib
from email.message import EmailMessage
from typing import Callable, Optional

from ..errors import MailerError
from ..logging import get_logger
from ..interfaces import MailerInterface, MagicLinkMessage


TemplateBuilder = Callable[[MagicLinkMessage], EmailMessage]


class SMTPMailer(MailerInterface):
    """Mailer that sends emails using an SMTP server."""

    def __init__(
        self,
        host: str,
        port: int,
        *,
        username: Optional[str] = None,
        password: Optional[str] = None,
        use_tls: bool = True,
        use_ssl: bool = False,
        timeout: Optional[float] = None,
        default_sender: Optional[str] = None,
        template_builder: Optional[TemplateBuilder] = None,
    ) -> None:
        self._host = host
        self._port = port
        self._username = username
        self._password = password
        self._use_tls = use_tls
        self._use_ssl = use_ssl
        self._timeout = timeout
        self._default_sender = default_sender
        self._template_builder = template_builder or self._default_template
        self._logger = get_logger()

    def send_magic_link(self, message: MagicLinkMessage) -> None:
        email = self._template_builder(message)
        sender = email["From"]
        recipient = email["To"]

        try:
            if self._use_ssl:
                smtp: smtplib.SMTP = smtplib.SMTP_SSL(
                    host=self._host,
                    port=self._port,
                    timeout=self._timeout,
                )
            else:
                smtp = smtplib.SMTP(
                    host=self._host,
                    port=self._port,
                    timeout=self._timeout,
                )
            with smtp as client:
                client.ehlo()
                if self._use_tls and not self._use_ssl:
                    client.starttls()
                    client.ehlo()
                if self._username and self._password:
                    client.login(self._username, self._password)
                client.send_message(email)
        except smtplib.SMTPException as exc:
            self._logger.exception(
                "SMTP send failure",
                extra={"recipient": recipient, "sender": sender},
            )
            raise MailerError("Failed to send magic link email via SMTP.") from exc
        else:
            self._logger.info(
                "magic link email dispatched via SMTP", extra={"recipient": recipient, "sender": sender}
            )

    def _default_template(self, message: MagicLinkMessage) -> EmailMessage:
        sender = message.sender or self._default_sender
        if not sender:
            raise MailerError("Sender email address must be provided for SMTP mailer.")

        email = EmailMessage()
        email["From"] = sender
        email["To"] = message.recipient
        email["Subject"] = message.subject or "Your magic link"

        text_body = message.text_body or self._build_text_body(message)
        email.set_content(text_body)

        if message.html_body:
            email.add_alternative(message.html_body, subtype="html")

        return email

    def _build_text_body(self, message: MagicLinkMessage) -> str:
        expires_str = message.expires_at.astimezone().strftime("%Y-%m-%d %H:%M:%S %Z")
        lines = [
            "Hello,",
            "",
            "Click the secure link below to sign in:",
            message.link,
            "",
            f"This link expires at {expires_str}.",
            "",
            "If you did not request this email you can ignore it.",
        ]
        return "\n".join(lines)
