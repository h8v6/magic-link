# Database Migrations In Depth

The `SQLAlchemyStorage` backend ships with ready-to-use models. You remain responsible for integrating them into your migration workflow.

## Alembic Configuration

1. Import the models in `alembic/env.py` so Alembic’s autogenerate can detect them:

```python
# alembic/env.py
from alembic import context
from sqlalchemy import engine_from_config, pool

from magic_link.storage.sqlalchemy import Base as MagicLinkBase
from myapp.database import Base as MyAppBase

config = context.config

target_metadata = [MyAppBase.metadata, MagicLinkBase.metadata]
```

2. When running `alembic revision --autogenerate`, Alembic will create tables similar to:

```python
op.create_table(
    "magic_link_tokens",
    sa.Column("id", sa.Integer(), nullable=False),
    sa.Column("token_hash", sa.String(length=128), nullable=False),
    sa.Column("subject", sa.String(length=255), nullable=False),
    sa.Column("signature", sa.String(length=128), nullable=False),
    sa.Column("issued_at", sa.DateTime(timezone=True), nullable=False),
    sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
    sa.Column("consumed_at", sa.DateTime(timezone=True), nullable=True),
    sa.Column("payload", sa.JSON(), nullable=False, server_default="{}"),
    sa.PrimaryKeyConstraint("id"),
    sa.UniqueConstraint("token_hash")
)
```

3. Apply migrations using your standard workflow (`alembic upgrade head`).

## Manual SQL

If you prefer to manage your schema manually, the minimal SQLite-compatible schema is:

```sql
CREATE TABLE magic_link_tokens (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    token_hash VARCHAR(128) UNIQUE NOT NULL,
    subject VARCHAR(255) NOT NULL,
    signature VARCHAR(128) NOT NULL,
    issued_at TIMESTAMP WITH TIME ZONE NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    consumed_at TIMESTAMP WITH TIME ZONE,
    payload JSON NOT NULL DEFAULT '{}'
);

CREATE TABLE magic_link_rate_limits (
    identifier VARCHAR(255) PRIMARY KEY,
    window_start TIMESTAMP WITH TIME ZONE NOT NULL,
    request_count INTEGER NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL
);
```

Always create indexes consistent with your database vendor if you expect high volume.

## Testing Migrations

Run the integration test suite (`pytest tests/integration/test_storage_sqlalchemy_postgres.py`) against your database provider to confirm migrations match the expected schema.
