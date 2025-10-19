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

## 3. Prepare Database Schema (Optional)

If you use the SQLAlchemy backend, import the models into your migration workflow. Example Alembic snippet:

```python
# alembic/env.py
from magic_link.storage.sqlalchemy import Base as MagicLinkBase
from myapp.database import engine

# within run_migrations_online()
with connectable.connect() as connection:
    context.configure(connection=connection, target_metadata=[MagicLinkBase.metadata, myapp_base])
    context.run_migrations()
```

Generate an Alembic revision that includes `magic_link` tables and apply it like any other migration.

## 4. Build a Minimal FastAPI App

```python
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

from redis import Redis

from magic_link import MagicLinkConfig, MagicLinkService
from magic_link.interfaces import MagicLinkMessage
from magic_link.mailer import create_mailer
from magic_link.storage.redis import RedisStorage

config = MagicLinkConfig.from_env()
app = FastAPI()
redis_client = Redis.from_url("redis://localhost:6379/0")
storage = RedisStorage(redis_client)
service = MagicLinkService(config=config, storage=storage)
mailer = create_mailer(config)

@app.post("/magic-link")
async def request_link(payload: dict[str, str]) -> JSONResponse:
    email = payload.get("email")
    if not email:
        raise HTTPException(status_code=400, detail="Email is required")

    service.enforce_rate_limit(email)

    issued = service.issue_token(subject=email)
    base = config.base_url or "http://localhost:8000"
    link = f"{base.rstrip('/')}{config.login_path}?token={issued.token}"

    mailer.send_magic_link(
        MagicLinkMessage(
            recipient=email,
            link=link,
            subject="Login with this link",
            expires_at=issued.expires_at,
        )
    )

    return JSONResponse({"status": "sent"})

@app.post("/magic-link/verify")
async def verify_magic_link(payload: dict[str, str]) -> JSONResponse:
    token = payload.get("token")
    if not token:
        raise HTTPException(status_code=400, detail="Token is required")

    result = service.verify_token(token)
    if not result.success:
        raise HTTPException(status_code=400, detail=result.reason or "invalid_token")

    return JSONResponse({"status": "verified", "subject": result.subject})
```

Run the app:

```bash
uvicorn main:app --reload
```

Visit `/magic-link` to request a link and `/magic-link/verify` to consume it.

## 5. Next Steps

- Replace Redis with the SQLAlchemy backend or your custom storage implementation.
- Hook `MagicLinkMessage` into your templating pipeline to customize email content.
- Review additional recipes in `docs/recipes/` for Flask and other frameworks.
