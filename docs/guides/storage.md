## Storage Backend Integration Guide

This guide explains how to integrate the available storage backends with the `magic_link` library. Pick the backend that best suits your deployment environment.

### In-Memory Storage (Development & Testing)

The in-memory backend is ideal for local development and automated testing where persistence is not required.

```python
from magic_link.interfaces import TokenRecord
from magic_link.storage.in_memory import InMemoryStorage

storage = InMemoryStorage()

# Store a token that was just issued
storage.create_token(
    TokenRecord(
        token_hash=issued.token_hash,
        subject=issued.subject,
        signature=issued.signature,
        issued_at=issued.issued_at,
        expires_at=issued.expires_at,
    )
)
```

### SQLAlchemy Storage (Relational Databases)

The SQLAlchemy backend persists tokens to any SQL database supported by SQLAlchemy. Import the provided models into your migration tool (e.g., Alembic) so that schema changes are handled by your project's existing workflow.

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from magic_link.storage.sqlalchemy import Base, SQLAlchemyStorage

engine = create_engine("postgresql+psycopg://app:secret@localhost/app_db", future=True)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)

# Create tables if you are managing schema manually
Base.metadata.create_all(engine)

storage = SQLAlchemyStorage(session_factory=SessionLocal)
```

> **Important:** Always run your own migrations. The library does not modify your database automatically.

### Redis Storage (Production Ready)

The Redis backend offers high-performance storage and rate limiting. Make sure the `redis` Python package is installed.

```python
from redis import Redis

from magic_link.storage.redis import RedisStorage

client = Redis.from_url("redis://localhost:6379/0")
storage = RedisStorage(client)
```

The backend uses a per-token key with an automatic TTL matching the token expiration time. Rate limits use counter keys with the same namespace (`magic_link` by default).

#### Choosing a Backend

| Backend        | Recommended Use Case                            |
| -------------- | ------------------------------------------------ |
| In-Memory      | Local development, unit tests                    |
| SQLAlchemy     | Applications already using relational databases |
| Redis          | Production systems needing fast token lookups    |

Switch between backends by wiring the desired storage implementation into your authentication workflow. The rest of the library interacts only through the shared `StorageInterface`.

### Writing a Custom Storage Backend

Implement the `StorageInterface` for full control over persistence:

```python
from magic_link.interfaces import RateLimitRule, StorageInterface, TokenRecord


class DynamoStorage(StorageInterface):
    def create_token(self, record: TokenRecord) -> None:
        ...  # Persist to your datastore

    def get_token(self, token_hash: str) -> TokenRecord | None:
        ...

    def consume_token(self, token_hash: str, *, consumed_at=None) -> TokenRecord | None:
        ...

    def enforce_rate_limit(self, rule: RateLimitRule, *, at=None) -> bool:
        ...
```

Register your storage in application code and keep the rest of the integration unchanged.
