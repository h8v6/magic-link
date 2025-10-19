"""CLI command for sending test emails."""

from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone

import click

from ..config import load_settings
from ..errors import MailerError
from ..interfaces import MagicLinkMessage
from ..mailer import create_mailer


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


@click.command(name="test-email", help="Send a test magic link email using current settings.")
@click.argument("recipient")
@click.option("--backend", type=str, default=None, help="Override the configured mailer backend.")
@click.option("--link", type=str, default=None, help="Provide a custom magic link URL.")
def send_test_email(recipient: str, backend: str | None, link: str | None) -> None:
    """Dispatch a verification email to confirm mail delivery configuration."""
    settings = load_settings()
    chosen_backend = backend or settings.mailer_backend

    mailer = create_mailer(settings, backend=chosen_backend)
    token = secrets.token_urlsafe(12)
    base_url = settings.base_url or "http://localhost"
    login_path = settings.login_path or "/auth/magic-link"
    sample_link = link or f"{base_url.rstrip('/')}{login_path}?token={token}"
    expires_at = _utcnow() + timedelta(seconds=settings.token.ttl_seconds)

    message = MagicLinkMessage(
        recipient=recipient,
        link=sample_link,
        subject="Magic Link Test Email",
        expires_at=expires_at,
        sender=settings.from_address,
        text_body=(
            "This is a test email from magic_link.\n\n"
            f"Use the following link to verify delivery: {sample_link}\n\n"
            "If you were not expecting this message you can delete it."
        ),
    )

    try:
        mailer.send_magic_link(message)
    except MailerError as exc:
        raise click.ClickException(str(exc)) from exc

    click.echo(f"Sent test email to {recipient} via {chosen_backend} backend.")


send_test_email.__test__ = False
