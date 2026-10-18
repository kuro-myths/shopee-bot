"""Unit tests for the Telegram notifier.

The notifier returns False silently when credentials are missing, so
these tests run without a real bot token.
"""
from app.config import settings
from app.services.notifier import send_telegram


def test_send_returns_false_without_token():
    token, chat = settings.telegram_bot_token, settings.telegram_chat_id
    settings.telegram_bot_token = ""
    settings.telegram_chat_id = ""
    try:
        assert send_telegram("test") is False
    finally:
        settings.telegram_bot_token = token
        settings.telegram_chat_id = chat


def test_send_returns_false_without_chat_id():
    token, chat = settings.telegram_bot_token, settings.telegram_chat_id
    settings.telegram_bot_token = "fake-token"
    settings.telegram_chat_id = ""
    try:
        assert send_telegram("test") is False
    finally:
        settings.telegram_bot_token = token
        settings.telegram_chat_id = chat
