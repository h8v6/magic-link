"""Mailer backend registry and exports."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Protocol

from ..config import MagicLinkSettings
from ..errors import ConfigurationError
from ..interfaces import MailerInterface, MagicLinkMessage
from .smtp import SMTPMailer

class MailerFactory(Protocol):
    def __call__(self, settings: MagicLinkSettings, **kwargs: Any) -> MailerInterface:
        ...

_MAILER_FACTORIES: Dict[str, MailerFactory] = {}


def register_mailer(name: str, factory: MailerFactory) -> None:
    """Register a mailer factory for runtime selection."""
    _MAILER_FACTORIES[name] = factory


def available_mailers() -> List[str]:
    """Return the list of registered mailer backend names."""
    return sorted(_MAILER_FACTORIES.keys())


def create_mailer(
    settings: MagicLinkSettings,
    *,
    backend: Optional[str] = None,
    **overrides: Any,
) -> MailerInterface:
    """Instantiate the configured mailer backend."""
    backend_name = backend or settings.mailer_backend
    factory = _MAILER_FACTORIES.get(backend_name)
    if factory is None:
        raise ConfigurationError(f"Mailer backend '{backend_name}' is not registered.")
    return factory(settings, **overrides)


def _smtp_factory(settings: MagicLinkSettings, **overrides: Any) -> MailerInterface:
    params: Dict[str, Any] = {
        "host": settings.smtp_host,
        "port": settings.smtp_port,
        "username": settings.smtp_username,
        "password": settings.smtp_password,
        "use_tls": settings.smtp_use_tls,
        "use_ssl": settings.smtp_use_ssl,
        "timeout": settings.smtp_timeout,
        "default_sender": settings.from_address,
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
