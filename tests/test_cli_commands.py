from __future__ import annotations

import sys
from typing import List

import pytest
from click.testing import CliRunner

from magic_link.cli import cli, main
from magic_link.config import MagicLinkConfig, RateLimitConfig, SMTPConfig, TokenConfig


def _stub_config() -> MagicLinkConfig:
    return MagicLinkConfig(
        secret_key="cli-secret",
        token=TokenConfig(ttl_seconds=900, length=32),
        rate_limit=RateLimitConfig(window_seconds=60, max_requests=5),
        base_url="https://example.com",
        from_address="sender@example.com",
        smtp=SMTPConfig(host="localhost", port=587, use_tls=True, use_ssl=False),
    )


class StubMailer:
    def __init__(self) -> None:
        self.sent: List = []

    def send_magic_link(self, message) -> None:
        self.sent.append(message)


def test_generate_config_outputs_template(monkeypatch: pytest.MonkeyPatch) -> None:
    runner = CliRunner()
    result = runner.invoke(cli, ["generate-config"])
    assert result.exit_code == 0
    assert "MAGIC_LINK_SECRET_KEY" in result.output


def test_generate_config_write_file(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    runner = CliRunner()
    output_file = tmp_path / "env.example"
    result = runner.invoke(cli, ["generate-config", "-o", str(output_file)])
    assert result.exit_code == 0
    assert output_file.exists()
    content = output_file.read_text()
    assert "MAGIC_LINK_SMTP_HOST" in content


def test_test_email_success(monkeypatch: pytest.MonkeyPatch) -> None:
    runner = CliRunner()
    stub_mailer = StubMailer()

    monkeypatch.setenv("MAGIC_LINK_SECRET_KEY", "cli-secret")
    monkeypatch.setenv("MAGIC_LINK_FROM_ADDRESS", "sender@example.com")
    monkeypatch.setenv("MAGIC_LINK_BASE_URL", "https://example.com")

    monkeypatch.setattr("magic_link.cli.test_email.load_settings", _stub_config)
    monkeypatch.setattr("magic_link.cli.test_email.create_mailer", lambda settings, backend=None: stub_mailer)

    result = runner.invoke(cli, ["test-email", "user@example.com"])
    assert result.exit_code == 0
    assert "Sent test email" in result.output
    assert len(stub_mailer.sent) == 1


def test_test_email_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    from magic_link.errors import MailerError

    runner = CliRunner()

    monkeypatch.setenv("MAGIC_LINK_SECRET_KEY", "cli-secret")
    monkeypatch.setenv("MAGIC_LINK_FROM_ADDRESS", "sender@example.com")

    def failing_mailer(*args, **kwargs):
        class _Mailer:
            def send_magic_link(self, message):
                raise MailerError("boom")

        return _Mailer()

    monkeypatch.setattr("magic_link.cli.test_email.load_settings", _stub_config)
    monkeypatch.setattr("magic_link.cli.test_email.create_mailer", failing_mailer)

    result = runner.invoke(cli, ["test-email", "user@example.com"])
    assert result.exit_code != 0
    assert "boom" in result.output


def test_cli_main_invokes_group(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MAGIC_LINK_SECRET_KEY", "cli-secret")
    monkeypatch.setattr(sys, "argv", ["magic-link", "--help"])
    with pytest.raises(SystemExit) as exc:
        main()
    assert exc.value.code == 0
