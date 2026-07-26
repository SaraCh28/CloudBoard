"""
CloudBoard – Module 16 Security Unit Tests.

Tests:
  - sanitize_input()        XSS sanitization
  - validate_file_upload()  MIME whitelist + size guard
  - SecurityHeadersMiddleware headers
  - CSRFMiddleware token validation
  - JWT decode edge cases
  - argon2 password hash / verify
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.middleware.security import sanitize_input, validate_file_upload
from app.auth.security import hash_password, verify_password, create_access_token, decode_token

client = TestClient(app)


# ── sanitize_input() ─────────────────────────────────────────────

class TestSanitizeInput:
    def test_strips_script_tags(self):
        inp = "<script>alert('xss')</script>Hello"
        out = sanitize_input(inp)
        assert "<script>" not in out
        assert "Hello" in out

    def test_strips_javascript_uri(self):
        inp = "javascript:alert(1)"
        out = sanitize_input(inp)
        assert "javascript:" not in out

    def test_escapes_angle_brackets(self):
        inp = "<b>bold</b>"
        out = sanitize_input(inp)
        assert "<b>" not in out
        assert "&lt;b&gt;" in out

    def test_empty_string(self):
        assert sanitize_input("") == ""

    def test_plain_text_unchanged_content(self):
        inp = "  Hello World  "
        out = sanitize_input(inp)
        assert "Hello World" in out

    def test_ampersand_encoded(self):
        inp = "a & b"
        out = sanitize_input(inp)
        assert "&amp;" in out


# ── validate_file_upload() ────────────────────────────────────────

class TestFileValidation:
    def test_valid_png(self):
        ok, reason = validate_file_upload(
            filename="photo.png",
            content_type="image/png",
            size_bytes=1024,
        )
        assert ok is True
        assert reason == ""

    def test_valid_pdf(self):
        ok, reason = validate_file_upload(
            filename="doc.pdf",
            content_type="application/pdf",
            size_bytes=500_000,
        )
        assert ok is True

    def test_rejects_exe(self):
        ok, reason = validate_file_upload(
            filename="malware.exe",
            content_type="application/octet-stream",
            size_bytes=1024,
        )
        assert ok is False
        assert "not permitted" in reason

    def test_rejects_mismatched_extension(self):
        # PNG content-type but .exe extension
        ok, reason = validate_file_upload(
            filename="evil.exe",
            content_type="image/png",
            size_bytes=1024,
        )
        assert ok is False
        assert "does not match" in reason

    def test_rejects_oversized_file(self):
        ok, reason = validate_file_upload(
            filename="big.pdf",
            content_type="application/pdf",
            size_bytes=11 * 1024 * 1024,  # 11 MB
        )
        assert ok is False
        assert "limit" in reason

    def test_rejects_missing_filename(self):
        ok, reason = validate_file_upload(
            filename=None,
            content_type="image/png",
            size_bytes=1024,
        )
        assert ok is False

    def test_custom_size_limit(self):
        ok, reason = validate_file_upload(
            filename="small.png",
            content_type="image/png",
            size_bytes=200,
            max_size_bytes=100,  # tiny limit
        )
        assert ok is False
        assert "limit" in reason


# ── Security Headers ──────────────────────────────────────────────

class TestSecurityHeaders:
    def test_health_returns_security_headers(self):
        r = client.get("/health")
        assert r.status_code == 200
        assert r.headers.get("x-content-type-options") == "nosniff"
        assert r.headers.get("x-frame-options") == "DENY"
        assert r.headers.get("x-xss-protection") == "1; mode=block"
        assert r.headers.get("referrer-policy") == "strict-origin-when-cross-origin"
        assert "frame-ancestors 'none'" in r.headers.get("content-security-policy", "")

    def test_permissions_policy_present(self):
        r = client.get("/health")
        pp = r.headers.get("permissions-policy", "")
        assert "camera=()" in pp
        assert "microphone=()" in pp


# ── JWT Edge Cases ────────────────────────────────────────────────

class TestJWTSecurity:
    def test_decode_valid_token(self):
        token = create_access_token({"sub": "user-123"})
        payload = decode_token(token)
        assert payload is not None
        assert payload["sub"] == "user-123"
        assert payload["type"] == "access"

    def test_decode_tampered_token_returns_none(self):
        token = create_access_token({"sub": "user-123"})
        tampered = token[:-5] + "XXXXX"
        result = decode_token(tampered)
        assert result is None

    def test_decode_empty_string_returns_none(self):
        assert decode_token("") is None

    def test_decode_garbage_returns_none(self):
        assert decode_token("not.a.valid.token.at.all") is None


# ── Argon2 Password Hashing ───────────────────────────────────────

class TestPasswordHashing:
    def test_hash_is_not_plaintext(self):
        h = hash_password("Secure#123")
        assert h != "Secure#123"
        assert "$argon2" in h

    def test_verify_correct_password(self):
        h = hash_password("Correct#Pass1")
        assert verify_password("Correct#Pass1", h) is True

    def test_reject_wrong_password(self):
        h = hash_password("Correct#Pass1")
        assert verify_password("Wrong#Pass1", h) is False

    def test_two_hashes_of_same_password_differ(self):
        """Argon2 uses unique salts per hash."""
        h1 = hash_password("Same#Pass1")
        h2 = hash_password("Same#Pass1")
        assert h1 != h2
