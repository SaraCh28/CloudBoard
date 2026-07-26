# ADR 001 – Argon2 for Password Hashing

**Date**: 2026-07-26  
**Status**: Accepted  
**Deciders**: CloudBoard Engineering Team

---

## Context

CloudBoard stores user passwords. We need a hashing algorithm that is:
- Resistant to GPU/ASIC brute-force attacks
- Recommended by OWASP Password Storage Cheat Sheet (2024)
- Supported by Python's ecosystem

## Decision

Use **Argon2id** via `passlib[argon2]` + `argon2-cffi`.

Argon2 is the winner of the Password Hashing Competition (PHC) and is OWASP's top recommendation. The `id` variant combines Argon2i (side-channel resistance) and Argon2d (GPU resistance).

```python
# app/auth/security.py
from passlib.context import CryptContext
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")
```

Default parameters used (passlib's Argon2 defaults):
- Memory: 65 536 KiB (64 MB)
- Iterations: 3
- Parallelism: 4

## Consequences

✅ Industry-best resistance against offline dictionary attacks  
✅ Future-proof — parameters can be increased as hardware improves  
⚠️ Hashing is intentionally slow (~100–300ms) — acceptable for login; never hash in hot paths
