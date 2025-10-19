from __future__ import annotations

from dataclasses import dataclass
from typing import List

import pytest
from click.testing import CliRunner

from magic_link.cli import cli


@dataclass
class StubSettings:
    secret_key: str = "cli-secret"
    token_ttl_seconds: int = 900
    token_length: int = 32
    rate_limit_window_seconds: int = 60
    rate_limit_max_requests: int = 5
    issuer: str | None = None
    base_url: str | None = "https://example.com"
    login_path: str = "/auth/magic-link"
    debug: bool = False
    storage_backend: str = "memory"
    mailer_backend: str = "smtp"
    from_address: str | None = "sender@example.com"
    smtp_host: str = "localhost"
    smtp_port: int = 587
    smtp_username: str | None = None
    smtp_password: str | None = None
    smtp_use_tls: bool = True
    smtp_use_ssl: bool = False
    smtp_timeout: float | None = None


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

    monkeypatch.setattr("magic_link.cli.test_email.load_settings", lambda: StubSettings())
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

    monkeypatch.setattr("magic_link.cli.test_email.load_settings", lambda: StubSettings())
    monkeypatch.setattr("magic_link.cli.test_email.create_mailer", failing_mailer)

    result = runner.invoke(cli, ["test-email", "user@example.com"])
    assert result.exit_code != 0
    assert "boom" in result.output
