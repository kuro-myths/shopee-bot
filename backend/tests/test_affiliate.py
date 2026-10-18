"""Unit tests for the affiliate service.

These tests run without real credentials, so they verify the fallback
behaviour plus the URL-parsing helpers.
"""
from app.config import settings
from app.services.affiliate import get_affiliate_url


def test_fallback_returns_original_url_when_no_credentials():
    original_secret = settings.shopee_app_secret
    settings.shopee_app_secret = ""
    try:
        product = {
            "url": "https://shopee.co.id/item-i.1.2",
            "marketplace": "shopee",
        }
        result = get_affiliate_url(product)
        assert result["source"] == "original"
        assert result["url"] == product["url"]
    finally:
        settings.shopee_app_secret = original_secret


def test_fallback_for_tiktok_without_credentials():
    original = settings.tiktok_app_secret
    settings.tiktok_app_secret = ""
    try:
        product = {"url": "https://tiktok.com/shop/item", "marketplace": "tiktok"}
        result = get_affiliate_url(product)
        assert result["source"] == "original"
    finally:
        settings.tiktok_app_secret = original


def test_fallback_returns_note():
    settings.shopee_app_secret = ""
    product = {"url": "https://shopee.co.id/x", "marketplace": "shopee"}
    result = get_affiliate_url(product)
    assert "note" in result
    assert result["note"] != ""
