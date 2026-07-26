# ADR 002 – JWT Access + Refresh Token Strategy

**Date**: 2026-07-26  
**Status**: Accepted

---

## Context

CloudBoard needs stateless authentication that:
- Supports short-lived sessions (security)
- Allows "remember me" via long-lived refresh (UX)
- Avoids database lookups on every API call (performance)

## Decision

Use a **dual-token JWT strategy**:

| Token | Expiry | Scope |
|-------|--------|-------|
| Access token | 30 minutes | Carried in `Authorization: Bearer` header |
| Refresh token | 7 days | Sent only to `POST /api/v1/auth/refresh` |

Both tokens are signed with **HS256** and include a `"type"` claim (`"access"` or `"refresh"`) to prevent type confusion attacks.

```python
# Refresh endpoint validates type claim
if payload.get("type") != "refresh":
    raise HTTPException(401, "Invalid refresh token")
```

## Future: Redis Token Blacklist

The logout endpoint is structured to support token invalidation:
```python
# TODO: Add token to Redis blacklist (Module 13)
```
On logout, the access token's JTI (JWT ID) will be stored in Redis with TTL equal to the token's remaining lifetime.

## Consequences

✅ Stateless — no DB lookup on each request  
✅ Short access token window limits blast radius of token theft  
⚠️ Until Redis blacklist is implemented, logout does not revoke tokens server-side
