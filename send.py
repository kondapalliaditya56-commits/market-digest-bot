"""Tiny Telegram Bot API helpers (no framework needed)."""
import os

import requests

API = f"https://api.telegram.org/bot{os.environ['TELEGRAM_BOT_TOKEN']}"


def send_message(chat_id, text: str):
    for i in range(0, max(len(text), 1), 4000):
        r = requests.post(f"{API}/sendMessage", data={"chat_id": chat_id, "text": text[i : i + 4000]}, timeout=30)
        r.raise_for_status()


def send_document(chat_id, path: str, filename: str, caption: str = ""):
    with open(path, "rb") as f:
        r = requests.post(f"{API}/sendDocument", data={"chat_id": chat_id, "caption": caption},
                          files={"document": (filename, f)}, timeout=90)
    r.raise_for_status()


def get_updates(offset=None) -> dict:
    params = {"timeout": 0, "allowed_updates": '["message"]'}
    if offset is not None:
        params["offset"] = offset
    r = requests.get(f"{API}/getUpdates", params=params, timeout=30)
    r.raise_for_status()
    return r.json()
