"""CLI command for generating configuration templates."""

from __future__ import annotations

from pathlib import Path
from textwrap import dedent

import click


def _build_template() -> str:
    return dedent(
        """
        # magic_link configuration template
        # Required settings
        MAGIC_LINK_SECRET_KEY=change-me

        # Token configuration
        MAGIC_LINK_TOKEN_TTL_SECONDS=900
        MAGIC_LINK_TOKEN_LENGTH=32

        # Rate limiting
        MAGIC_LINK_RATE_LIMIT_WINDOW_SECONDS=60
        MAGIC_LINK_RATE_LIMIT_MAX_REQUESTS=5

        # Optional metadata
        # MAGIC_LINK_ISSUER=
        # MAGIC_LINK_BASE_URL=https://example.com
        # MAGIC_LINK_LOGIN_PATH=/auth/magic-link

        # Storage backend selection: memory, sqlalchemy, redis
        MAGIC_LINK_STORAGE_BACKEND=memory

        # Mailer backend selection
        MAGIC_LINK_MAILER_BACKEND=smtp
        MAGIC_LINK_FROM_ADDRESS=no-reply@example.com

        # SMTP configuration
        MAGIC_LINK_SMTP_HOST=localhost
        MAGIC_LINK_SMTP_PORT=587
        # MAGIC_LINK_SMTP_USERNAME=
        # MAGIC_LINK_SMTP_PASSWORD=
        MAGIC_LINK_SMTP_USE_TLS=true
        MAGIC_LINK_SMTP_USE_SSL=false
        # MAGIC_LINK_SMTP_TIMEOUT_SECONDS=

        # Debug tooling
        MAGIC_LINK_DEBUG=false
        """
    ).strip()


@click.command(name="generate-config", help="Print a sample .env configuration template.")
@click.option(
    "output_path",
    "-o",
    type=click.Path(path_type=Path),
    default=None,
    help="Write the template to a file instead of stdout.",
)
def generate_config(output_path: Path | None) -> None:
    """Output an annotated configuration template."""
    template = _build_template()
    if output_path is not None:
        output_path.write_text(template + "\n", encoding="utf-8")
        click.echo(f"Wrote configuration template to {output_path}")
    else:
        click.echo(template)
