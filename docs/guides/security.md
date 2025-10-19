# Security & Production Considerations

`magic_link` ships with secure defaults, but production deployments require thoughtful configuration.

## Secret Management

- Set a strong `MAGIC_LINK_SECRET_KEY` (at least 32 random bytes). Rotate it using your secrets management platform.
- Never commit secrets to version control; load them via environment variables or a secrets manager.

## Storage Backends

- **SQLAlchemy**: Suitable when latency is less critical and persistence is required. Ensure indexes are in place (`token_hash`, `identifier`). Configure connection pooling and run against PostgreSQL or another production-grade RDBMS.
- **Redis**: Ideal for high-throughput scenarios and rate limiting. Configure persistence as needed and secure the instance (AUTH/password, TLS, network whitelisting).

## Rate Limiting

Tune `MAGIC_LINK_RATE_LIMIT_WINDOW_SECONDS` and `MAGIC_LINK_RATE_LIMIT_MAX_REQUESTS` to balance usability and abuse prevention. Monitor metrics to adjust thresholds.

## Logging

Use structured logging in production. Example:

```python
import json
import logging

from magic_link.logging import get_logger

logger = get_logger()
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter(json.dumps({"msg": "%(message)s", "level": "%(levelname)s"})))
logger.addHandler(handler)
```

Emit security-related events (token issued, token consumed, rate limit exceeded) to your observability platform.

## TLS and Email Delivery

- Use TLS (`SMTP_USE_TLS=true`) when connecting to SMTP relays.
- Consider DKIM, SPF, and DMARC policies for high deliverability.

## Monitoring and Alerts

- Track token issuance and verification success rates.
- Alert on repeated rate-limit violations or spikes in invalid token attempts.

## Incident Response

- If a secret is compromised, rotate `MAGIC_LINK_SECRET_KEY` and invalidate outstanding tokens (e.g., delete rows or flush Redis namespace).
- Maintain audit logs via your storage backend or an application-level logging service.
