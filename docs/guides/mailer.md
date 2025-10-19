## Mailer Integration Guide

This guide covers the built-in SMTP mailer and how to register custom delivery providers.

### SMTP Mailer Setup

```python
from datetime import datetime, timedelta, timezone

from magic_link.config import load_settings
from magic_link.mailer import create_mailer
from magic_link.interfaces import MagicLinkMessage

settings = load_settings()
mailer = create_mailer(settings)  # defaults to SMTP

test_message = MagicLinkMessage(
    recipient="user@example.com",
    link="https://example.com/login?token=abc",
    subject="Your login link",
    expires_at=datetime.now(timezone.utc) + timedelta(minutes=15),
)

mailer.send_magic_link(test_message)
```

Set the following environment variables to configure SMTP:

- `MAGIC_LINK_SMTP_HOST`
- `MAGIC_LINK_SMTP_PORT`
- `MAGIC_LINK_SMTP_USERNAME`
- `MAGIC_LINK_SMTP_PASSWORD`
- `MAGIC_LINK_SMTP_USE_TLS`
- `MAGIC_LINK_SMTP_USE_SSL`
- `MAGIC_LINK_SMTP_TIMEOUT_SECONDS`

### Registering a Custom Mailer

```python
from magic_link.mailer import MailerInterface, register_mailer
from magic_link.interfaces import MagicLinkMessage

class ConsoleMailer(MailerInterface):
    def send_magic_link(self, message: MagicLinkMessage) -> None:
        print(f"Send to {message.recipient}: {message.link}")


def console_factory(settings, **overrides):
    return ConsoleMailer()

register_mailer("console", console_factory)
```

Set `MAGIC_LINK_MAILER_BACKEND=console` to use the custom backend.

### Overriding Parameters Per-Call

```python
mailer = create_mailer(settings, timeout=10)
```

### CLI Test Command

Use the CLI to verify mail delivery without running the full app:

```bash
magic-link test-email user@example.com
```
