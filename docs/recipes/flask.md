# Flask Integration Recipe

This recipe shows how to embed `magic_link` inside a Flask application while keeping full control over persistence and mail delivery.

## Requirements

```bash
pip install flask "magic-link[sqlalchemy,smtp]"
```

## Example Application (`app.py`)

```python
from flask import Flask, jsonify, request
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from magic_link import (
    MagicLinkConfig,
    MagicLinkService,
    RateLimitConfig,
    TokenConfig,
)
from magic_link.interfaces import MagicLinkMessage
from magic_link.mailer import create_mailer
from magic_link.storage.sqlalchemy import Base, SQLAlchemyStorage

DATABASE_URL = "sqlite:///./magic_link.db"

def build_service() -> MagicLinkService:
    config = MagicLinkConfig(
        secret_key="replace-me",  # load from environment or secrets manager
        token=TokenConfig(ttl_seconds=600, length=32),
        rate_limit=RateLimitConfig(window_seconds=60, max_requests=3),
        from_address="auth@example.com",
        base_url="http://localhost:5000",
    )

    engine = create_engine(DATABASE_URL, future=True)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)

    storage = SQLAlchemyStorage(session_factory=SessionLocal)
    mailer = create_mailer(config)

    return MagicLinkService(config=config, storage=storage)

app = Flask(__name__)
service = build_service()

@app.post("/auth/magic-link")
def issue_magic_link():
    payload = request.get_json(force=True)
    email = payload.get("email")
    if not email:
        return jsonify({"error": "email is required"}), 400

    try:
        service.enforce_rate_limit(email)
    except Exception:
        return jsonify({"error": "too many requests"}), 429

    issued = service.issue_token(subject=email)
    base = service.config.base_url or request.host_url.rstrip("/")
    login_link = f"{base}{service.config.login_path}?token={issued.token}"

    mailer = create_mailer(service.config)
    mailer.send_magic_link(
        MagicLinkMessage(
            recipient=email,
            link=login_link,
            subject="Sign in to Example",
            expires_at=issued.expires_at,
        )
    )

    return jsonify({"status": "sent"})

@app.post("/auth/magic-link/verify")
def verify_magic_link():
    payload = request.get_json(force=True)
    token = payload.get("token")
    if not token:
        return jsonify({"error": "token is required"}), 400

    result = service.verify_token(token)
    if not result.success:
        return jsonify({"error": result.error}), 400

    return jsonify({"status": "verified", "subject": result.subject})

if __name__ == "__main__":
    app.run(debug=True)
```

## Notes

- Replace hard-coded values with `MagicLinkConfig.from_env()` for production deployments.
- Handle session lifecycle explicitly in larger apps by integrating SQLAlchemy’s scoped session helpers.
- Swap the SQLite engine with PostgreSQL and configure Redis storage for higher volume deployments.
