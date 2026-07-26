# ADR 004 – Docker Compose Environment Separation

**Date**: 2026-07-26  
**Status**: Accepted

---

## Context

The application needs to run differently in local development vs. production:
- **Dev**: hot-reload, exposed DB/Redis ports, DEBUG=true, relaxed rate limits
- **Prod**: no source mounts, hidden ports, multiple workers, strict rate limits

## Decision

Use Docker Compose's **multi-file override pattern**:

```
docker-compose.yml           # Base service definitions (shared)
docker-compose.override.yml  # Auto-applied for local dev (hot-reload, etc.)
docker-compose.prod.yml      # Explicitly applied for production
```

### Development (automatic)
```bash
docker-compose up --build
# Automatically picks up docker-compose.override.yml
```

### Production (explicit)
```bash
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

## Environment Variables

Secrets are **never** committed. They are injected via:
- `.env` file locally (not in git — see `.gitignore`)
- CI/CD environment variables in staging/production

## Consequences

✅ Single source of truth for service topology (base file)  
✅ Dev ergonomics don't compromise production security  
✅ CI can choose which compose variant to target  
⚠️ Engineers must remember the `-f` flag for production deploys (document in README)
