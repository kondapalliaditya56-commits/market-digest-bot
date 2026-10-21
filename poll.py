"""Runs every ~10 minutes: reads new Telegram messages, answers the owner's questions/commands."""
import os
from datetime import datetime
from zoneinfo import ZoneInfo

import send

OWNER = os.environ.get("OWNER_CHAT_ID", "").strip()
MAX_PER_RUN = 5

HELP = ("/digest - PDF digest (arrives within ~10 min)\n/help - this list\n\n"
        "Anything else you type is answered with live web data. Replies come within about 10 minutes.")


def handle(chat_id: int, text: str):
    cmd = text.split()[0].split("@")[0].lower() if text else ""

    if cmd == "/start":
        if not OWNER:
            send.send_message(chat_id, f"Your chat ID is {chat_id}. Save it as the OWNER_CHAT_ID secret in GitHub, "
                                       "then this bot will answer only you.")
        elif str(chat_id) == OWNER:
            send.send_message(chat_id, "Ready. Digest arrives daily around 7:30 AM IST. /digest for one now, or ask a question.")
        return

    if not OWNER or str(chat_id) != OWNER:
        return  # strangers ignored

    if cmd == "/help":
        send.send_message(chat_id, HELP)
    elif cmd == "/digest":
        import digest  # lazy: heavy imports only when needed
        digest.make_digest_pdf("digest.pdf")
        day = datetime.now(ZoneInfo("Asia/Kolkata")).strftime("%d-%b-%Y")
        send.send_document(chat_id, "digest.pdf", f"Market_Digest_{day}.pdf", "Your market digest")
    elif cmd.startswith("/"):
        send.send_message(chat_id, "Unknown command. Try /help.")
    else:
        import digest
        send.send_message(chat_id, digest.ask_claude(text))


def main():
    updates = send.get_updates().get("result", [])
    if not updates:
        return
    # Confirm everything first so a crash never causes a reply loop.
    send.get_updates(offset=max(u["update_id"] for u in updates) + 1)

    handled = 0
    for u in updates:
        m = u.get("message")
        if not m or not m.get("text"):
            continue
        chat_id = m["chat"]["id"]
        if handled >= MAX_PER_RUN and str(chat_id) == OWNER:
            send.send_message(chat_id, "Too many messages at once; please resend the rest.")
            break
        try:
            handle(chat_id, m["text"].strip())
            handled += 1
        except Exception as e:  # noqa: BLE001
            if OWNER and str(chat_id) == OWNER:
                send.send_message(chat_id, f"Sorry, that failed: {e}")


if __name__ == "__main__":
    main()
