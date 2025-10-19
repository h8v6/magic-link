import pytest

from magic_link.config import MagicLinkConfig, load_settings, reset_settings_cache
from magic_link.errors import ConfigurationError


def test_load_settings_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MAGIC_LINK_SECRET_KEY", "abc123")
    reset_settings_cache()
    settings = load_settings()
    assert isinstance(settings, MagicLinkConfig)
    assert settings.secret_key == "abc123"
    assert settings.token.ttl_seconds == 900
    assert settings.smtp.host == "localhost"
    assert settings.smtp.port == 587


def test_custom_overrides(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MAGIC_LINK_SECRET_KEY", "override")
    monkeypatch.setenv("MAGIC_LINK_TOKEN_TTL_SECONDS", "600")
    monkeypatch.setenv("MAGIC_LINK_SMTP_HOST", "mail.example.com")
    monkeypatch.setenv("MAGIC_LINK_SMTP_USE_TLS", "false")
    monkeypatch.setenv("MAGIC_LINK_SMTP_USE_SSL", "true")
    reset_settings_cache()
    settings = load_settings()
    assert settings.token.ttl_seconds == 600
    assert settings.smtp.host == "mail.example.com"
    assert settings.smtp.use_tls is False
    assert settings.smtp.use_ssl is True


def test_missing_secret_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("MAGIC_LINK_SECRET_KEY", raising=False)
    reset_settings_cache()
    with pytest.raises(ConfigurationError):
        load_settings()
