"""Tests for the HMAC signature helpers used by affiliate APIs."""
import hashlib
import hmac

from app.services.affiliate import _shopee_sign, _tiktok_sign


def test_shopee_sign_is_deterministic():
    s1 = _shopee_sign("1001", "/api/v2/shortlink/generate", 1700000000)
    s2 = _shopee_sign("1001", "/api/v2/shortlink/generate", 1700000000)
    assert s1 == s2
    assert len(s1) == 64  # sha256 hex


def test_shopee_sign_changes_with_partner():
    a = _shopee_sign("1001", "/api/v2/shortlink/generate", 1700000000)
    b = _shopee_sign("1002", "/api/v2/shortlink/generate", 1700000000)
    assert a != b


def test_tiktok_sign_is_sha256_hex():
    s = _tiktok_sign("secret", 1700000000)
    expected = hmac.new(b"secret", b"1700000000", hashlib.sha256).hexdigest()
    assert s == expected
