import pytest

from magic_link.config import (
    MagicLinkConfig,
    RateLimitConfig,
    SMTPConfig,
    TokenConfig,
    load_settings,
    reset_settings_cache,
)
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
    with pytest.raises(ConfigurationError) as exc:
        load_settings()
    assert "MAGIC_LINK_SECRET_KEY" in str(exc.value)


def test_token_config_validation() -> None:
    with pytest.raises(ConfigurationError):
        TokenConfig(ttl_seconds=0)
    with pytest.raises(ConfigurationError):
        TokenConfig(length=0)


def test_rate_limit_config_validation() -> None:
    config = RateLimitConfig()
    rule = config.to_rule("identifier")
    assert rule.identifier == "identifier"
    with pytest.raises(ConfigurationError):
        RateLimitConfig(window_seconds=0)
    with pytest.raises(ConfigurationError):
        RateLimitConfig(max_requests=0)


def test_smtp_config_validation() -> None:
    with pytest.raises(ConfigurationError):
        SMTPConfig(port=0)
    with pytest.raises(ConfigurationError):
        SMTPConfig(use_tls=True, use_ssl=True)
    with pytest.raises(ConfigurationError):
        SMTPConfig(timeout=0)


def test_magic_link_config_validation() -> None:
    with pytest.raises(ConfigurationError):
        MagicLinkConfig(secret_key="  ")
    with pytest.raises(ConfigurationError):
        MagicLinkConfig(secret_key="secret", login_path="invalid")


def test_invalid_integer_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MAGIC_LINK_SECRET_KEY", "secret")
    monkeypatch.setenv("MAGIC_LINK_TOKEN_TTL_SECONDS", "abc")
    reset_settings_cache()
    with pytest.raises(ConfigurationError) as exc:
        load_settings()
    assert "must be an integer" in str(exc.value)


def test_invalid_boolean_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MAGIC_LINK_SECRET_KEY", "secret")
    monkeypatch.setenv("MAGIC_LINK_SMTP_USE_TLS", "maybe")
    reset_settings_cache()
    with pytest.raises(ConfigurationError) as exc:
        load_settings()
    assert "boolean-like" in str(exc.value)
    monkeypatch.setenv("MAGIC_LINK_SMTP_USE_TLS", "true")
    monkeypatch.setenv("MAGIC_LINK_SMTP_TIMEOUT_SECONDS", "abc")
    reset_settings_cache()
    with pytest.raises(ConfigurationError) as exc2:
        load_settings()
    assert "must be a number" in str(exc2.value)
