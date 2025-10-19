# Quickstart

Follow this guide to integrate `magic_link` into a new project in minutes.

## 1. Install Dependencies

```bash
pip install "magic-link[sqlalchemy,redis,smtp]"
```

## 2. Generate Configuration

```bash
magic-link generate-config -o .env
```

Edit the `.env` file with real values:

```env
MAGIC_LINK_SECRET_KEY=replace-with-random-string
MAGIC_LINK_FROM_ADDRESS=auth@example.com
MAGIC_LINK_SMTP_HOST=smtp.example.com
MAGIC_LINK_SMTP_USERNAME=apikey
MAGIC_LINK_SMTP_PASSWORD=super-secret
```

## 3. Prepare Database (Optional)

If you plan to use the SQLAlchemy backend, import the models into your migration workflow:

```python
from magic_link.storage.sqlalchemy import Base

# In your Alembic env.py
from myapp.database import engine
Base.metadata.create_all(engine)
```

## 4. Build a Minimal FastAPI App

```python
import os

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

from magic_link.config import load_settings, reset_settings_cache
from magic_link.interfaces import MagicLinkMessage, RateLimitRule, TokenRecord
from redis import Redis

from magic_link.mailer import create_mailer
from magic_link.storage.redis import RedisStorage
from magic_link.token_engine import TokenEngine

reset_settings_cache()
settings = load_settings()
app = FastAPI()
engine = TokenEngine(
    secret_key=settings.secret_key,
    token_length=settings.token_length,
    ttl_seconds=settings.token_ttl_seconds,
)
client = Redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/0"))
storage = RedisStorage(client)
mailer = create_mailer(settings)


@app.post("/magic-link")
async def request_link(payload: dict[str, str]) -> JSONResponse:
    email = payload.get("email")
    if not email:
        raise HTTPException(status_code=400, detail="Email is required")

    allowed = storage.enforce_rate_limit(
        RateLimitRule(
            identifier=email,
            window_seconds=settings.rate_limit_window_seconds,
            max_requests=settings.rate_limit_max_requests,
        )
    )
    if not allowed:
        raise HTTPException(status_code=429, detail="Too many requests")

    issued = engine.issue(subject=email)
    storage.create_token(
        TokenRecord(
            token_hash=issued.token_hash,
            subject=issued.subject,
            signature=issued.signature,
            issued_at=issued.issued_at,
            expires_at=issued.expires_at,
        )
    )

    base = settings.base_url or "http://localhost:8000"
    link = f"{base.rstrip('/')}{settings.login_path}?token={issued.token}"
    mailer.send_magic_link(
        MagicLinkMessage(
            recipient=email,
            link=link,
            subject="Login with this link",
            expires_at=issued.expires_at,
        )
    )

    return JSONResponse({"status": "sent"})


def verify_token(token: str) -> TokenRecord:
    record = storage.get_token(engine.hash_token(token))
    if record is None:
        raise HTTPException(status_code=400, detail="Invalid token")
    engine.verify(
        token,
        subject=record.subject,
        signature=record.signature,
        issued_at=record.issued_at,
        expires_at=record.expires_at,
    )
    storage.consume_token(record.token_hash)
    return record


@app.post("/magic-link/verify")
async def verify_magic_link(payload: dict[str, str]) -> JSONResponse:
    token = payload.get("token")
    if not token:
        raise HTTPException(status_code=400, detail="Token is required")
    record = verify_token(token)
    return JSONResponse({"status": "verified", "subject": record.subject})
```

Run the app:

```bash
uvicorn main:app --reload
```

Visit `/magic-link` to request a link and `/magic-link/verify` to consume it.
