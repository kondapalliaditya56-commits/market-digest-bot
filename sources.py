"""Fetch recent public posts from Telegram channels and YouTube (no login needed)."""
import re
import xml.etree.ElementTree as ET

import requests
from bs4 import BeautifulSoup

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; DigestBot/1.0)"}

TELEGRAM_CHANNELS = ["moneypurseadv", "daytradertelugu"]
# Money Purse YouTube channel id (from the channel page)
YOUTUBE_CHANNEL_IDS = {"Money Purse": "UChBT5TlUeG68PKvJSg6MkqQ"}


def telegram_posts(channel: str, limit: int = 12) -> list[str]:
    """Latest posts from a PUBLIC channel via its web preview (t.me/s/<name>)."""
    try:
        r = requests.get(f"https://t.me/s/{channel}", headers=HEADERS, timeout=20)
        r.raise_for_status()
    except Exception as e:  # network or private channel
        return [f"(could not read {channel}: {e})"]
    soup = BeautifulSoup(r.text, "html.parser")
    posts = []
    for msg in soup.select(".tgme_widget_message"):
        text_el = msg.select_one(".tgme_widget_message_text")
        time_el = msg.select_one("time")
        if not text_el:
            continue
        text = re.sub(r"\s+", " ", text_el.get_text(" ", strip=True))[:500]
        when = time_el.get("datetime", "")[:16] if time_el else ""
        posts.append(f"[{when}] {text}")
    return posts[-limit:] or [f"(no readable posts in {channel})"]


def youtube_videos(channel_id: str, limit: int = 8) -> list[str]:
    try:
        r = requests.get(
            f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}",
            headers=HEADERS, timeout=20,
        )
        r.raise_for_status()
        root = ET.fromstring(r.text)
    except Exception as e:
        return [f"(could not read YouTube feed: {e})"]
    ns = {"a": "http://www.w3.org/2005/Atom"}
    out = []
    for entry in root.findall("a:entry", ns)[:limit]:
        title = entry.findtext("a:title", default="", namespaces=ns)
        date = entry.findtext("a:published", default="", namespaces=ns)[:10]
        out.append(f"[{date}] {title}")
    return out


def gather_source_text() -> str:
    parts = []
    for name, cid in YOUTUBE_CHANNEL_IDS.items():
        parts.append(f"## YouTube: {name} (latest uploads)\n" + "\n".join(youtube_videos(cid)))
    for ch in TELEGRAM_CHANNELS:
        parts.append(f"## Telegram: {ch} (latest posts)\n" + "\n".join(telegram_posts(ch)))
    return "\n\n".join(parts)
