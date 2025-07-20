import os
import json

HINTS_PATH = "/app/data/files212/bot/hint/user_hint.json"

def load_user_hints():
    if not os.path.exists(HINTS_PATH):
        return {}
    with open(HINTS_PATH, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except Exception:
            return {}

def save_user_hint(user_id, field, value):
    user_id = str(user_id)
    hints = load_user_hints()
    if user_id not in hints:
        hints[user_id] = {}
    hints[user_id][field] = value
    os.makedirs(os.path.dirname(HINTS_PATH), exist_ok=True)
    with open(HINTS_PATH, "w", encoding="utf-8") as f:
        json.dump(hints, f, ensure_ascii=False, indent=2)

def get_last_hint(user_id, field):
    user_id = str(user_id)
    hints = load_user_hints()
    return hints.get(user_id, {}).get(field)

from telegram import InlineKeyboardMarkup, InlineKeyboardButton

def make_hint_keyboard(field, user_id, back_btn):
    last_hint = get_last_hint(user_id, field)
    buttons = [[back_btn]]
    if last_hint:
        buttons.append([InlineKeyboardButton(last_hint, callback_data=f"hint_{field}")])
    return InlineKeyboardMarkup(buttons)