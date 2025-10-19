"""Command-line entry point for magic_link."""

from __future__ import annotations

import click

from .config import generate_config
from .test_email import send_test_email


@click.group(help="Utility commands for the magic_link library.")
def cli() -> None:
    """Root CLI group."""


cli.add_command(generate_config)
cli.add_command(send_test_email)


def main() -> None:
    """Entry point used by the console script."""
    cli()


__all__ = ["cli", "main"]
