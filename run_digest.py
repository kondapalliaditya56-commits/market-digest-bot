"""Generate today's digest PDF and send it to the owner chat."""
import os
from datetime import datetime
from zoneinfo import ZoneInfo

import digest
import send

chat = int(os.environ["OWNER_CHAT_ID"])
path = "digest.pdf"

last_err = None
for attempt in range(2):  # one retry in case the model returns malformed JSON
    try:
        digest.make_digest_pdf(path)
        break
    except Exception as e:  # noqa: BLE001
        last_err = e
else:
    send.send_message(chat, f"Digest failed today: {last_err}")
    raise SystemExit(1)

day = datetime.now(ZoneInfo("Asia/Kolkata")).strftime("%d-%b-%Y")
send.send_document(chat, path, f"Market_Digest_{day}.pdf", "Your daily market digest")
