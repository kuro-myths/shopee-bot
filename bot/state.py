"""Per-chat alert preferences, persisted to a JSON file.

Lets users toggle drop notifications per chat without touching the
backend environment.
"""
import json
import os

STATE_FILE = os.getenv("BOT_STATE_FILE", "bot_state.json")


def _load():
    if not os.path.exists(STATE_FILE):
        return {}
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)


def alerts_enabled(chat_id: int) -> bool:
    return _load().get(str(chat_id), {}).get("alerts", True)


def set_alerts(chat_id: int, enabled: bool) -> bool:
    state = _load()
    entry = state.setdefault(str(chat_id), {})
    entry["alerts"] = enabled
    _save(state)
    return enabled
