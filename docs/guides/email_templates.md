# Customizing Email Templates

Out of the box, `SMTPMailer` ships with a plain-text message. Extend or replace the template logic to match your brand.

## Override with a Template Builder

```python
from email.message import EmailMessage

from magic_link.config import MagicLinkConfig
from magic_link.interfaces import MagicLinkMessage
from magic_link.mailer import create_mailer

config = MagicLinkConfig.from_env()


def build_branded_message(message: MagicLinkMessage) -> EmailMessage:
    email = EmailMessage()
    email["From"] = config.from_address or "no-reply@example.com"
    email["To"] = message.recipient
    email["Subject"] = "Sign in to Example"
    email.set_content(
        f"""
        Hi,

        Click this secure link to sign in: {message.link}

        This link expires at {message.expires_at:%Y-%m-%d %H:%M:%S %Z}.

        Cheers,
        The Example Team
        """
    )
    email.add_alternative(
        f"""
        <p>Hello,</p>
        <p>Click <a href="{message.link}">this secure link</a> to sign in.</p>
        <p>This link expires at {message.expires_at:%Y-%m-%d %H:%M:%S %Z}.</p>
        <p>Cheers,<br/>The Example Team</p>
        """,
        subtype="html",
    )
    return email

mailer = create_mailer(config, template_builder=build_branded_message)
```

## Subclass SMTPMailer

For more control (e.g., inline images or different transport settings), subclass `SMTPMailer` and register it.

```python
from magic_link.mailer import MailerInterface, register_mailer
from magic_link.mailer.smtp import SMTPMailer


class BrandedMailer(SMTPMailer):
    def _build_text_body(self, message: MagicLinkMessage) -> str:
        return "Your custom body here"


register_mailer("brand", lambda config, **overrides: BrandedMailer(**overrides))
```

Then set `MAGIC_LINK_MAILER_BACKEND=brand` or pass `backend="brand"` to `create_mailer`.

## Testing Templates

Use the `magic-link test-email` CLI command with your overrides to render and send a sample email to yourself before deploying changes.
