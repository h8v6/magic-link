"""Mailer backend registry and exports."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Protocol

from ..config import MagicLinkConfig, SMTPConfig
from ..errors import ConfigurationError
from ..interfaces import MailerInterface, MagicLinkMessage
from .smtp import SMTPMailer

class MailerFactory(Protocol):
    def __call__(self, config: MagicLinkConfig, **kwargs: Any) -> MailerInterface:
        ...

_MAILER_FACTORIES: Dict[str, MailerFactory] = {}


def register_mailer(name: str, factory: MailerFactory) -> None:
    """Register a mailer factory for runtime selection."""
    _MAILER_FACTORIES[name] = factory


def available_mailers() -> List[str]:
    """Return the list of registered mailer backend names."""
    return sorted(_MAILER_FACTORIES.keys())


def create_mailer(
    config: MagicLinkConfig,
    *,
    backend: Optional[str] = None,
    **overrides: Any,
) -> MailerInterface:
    """Instantiate the configured mailer backend."""
    backend_name = backend or config.mailer_backend
    factory = _MAILER_FACTORIES.get(backend_name)
    if factory is None:
        raise ConfigurationError(f"Mailer backend '{backend_name}' is not registered.")
    return factory(config, **overrides)


def _smtp_factory(config: MagicLinkConfig, **overrides: Any) -> MailerInterface:
    smtp: SMTPConfig = config.smtp
    params: Dict[str, Any] = {
        "host": smtp.host,
        "port": smtp.port,
        "username": smtp.username,
        "password": smtp.password,
        "use_tls": smtp.use_tls,
        "use_ssl": smtp.use_ssl,
        "timeout": smtp.timeout,
        "default_sender": config.from_address,
    }
    params.update(overrides)
    return SMTPMailer(**params)


register_mailer("smtp", _smtp_factory)

__all__ = [
    "SMTPMailer",
    "register_mailer",
    "create_mailer",
    "available_mailers",
    "MailerFactory",
    "MailerInterface",
    "MagicLinkMessage",
]
