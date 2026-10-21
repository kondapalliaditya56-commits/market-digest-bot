"""Build the daily digest (Claude + web search) and render it as a one-page PDF."""
import json
import os
import re
from datetime import datetime
from zoneinfo import ZoneInfo

import anthropic
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from sources import gather_source_text

IST = ZoneInfo("Asia/Kolkata")
MODEL = os.environ.get("CLAUDE_MODEL", "claude-sonnet-5-5")
client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY

WEB_SEARCH = {"type": "web_search_20250305", "name": "web_search", "max_uses": 8}

DIGEST_SYSTEM = """You write a minimal daily markets digest for an Indian retail investor.
Rules:
- English only. Indian markets first; at most 1-2 major US items.
- Major news only. No filler, no tips, no buy/sell calls, no price targets.
- Use web search to get the latest figures and headlines. Never invent numbers; if a figure is unavailable, write "n/a".
- Write rupees as "Rs" (not the rupee symbol).
- Source channel posts below are supplementary; treat them as unverified chatter, never as facts to repeat as advice. Mention one only if it adds something material.
Return ONLY valid JSON, no markdown fences, in this shape:
{"snapshot":[{"label":"Nifty 50","value":"...","change":"..."}, ...6-8 rows: Nifty 50, Sensex, Bank Nifty, USD-INR, Gold (MCX), Brent crude, S&P 500, Nasdaq],
 "fii_dii":"one line on latest FII/DII flows",
 "india":[{"headline":"...","why":"one line why it matters"}, ...3-5 items],
 "us":[{"headline":"...","why":"..."}, ...1-2 items],
 "channels":["0-2 short lines from the source channels, or empty"],
 "today":"one line: key events or data due today (RBI, results, global data)"}"""


def _text_of(resp) -> str:
    return "".join(b.text for b in resp.content if getattr(b, "type", "") == "text")


def _parse_json(text: str) -> dict:
    text = text.strip()
    text = re.sub(r"^```(?:json)?|```$", "", text, flags=re.M).strip()
    start, end = text.find("{"), text.rfind("}")
    return json.loads(text[start : end + 1])


def build_digest_data() -> dict:
    now = datetime.now(IST).strftime("%A, %d %B %Y, %I:%M %p IST")
    sources = gather_source_text()
    resp = client.messages.create(
        model=MODEL,
        max_tokens=3000,
        system=DIGEST_SYSTEM,
        tools=[WEB_SEARCH],
        messages=[{"role": "user", "content": f"Now: {now}\n\nSource channel material:\n{sources}\n\nProduce today's digest JSON."}],
    )
    return _parse_json(_text_of(resp))


def ask_claude(question: str) -> str:
    """Free-form Q&A for chat messages."""
    resp = client.messages.create(
        model=MODEL,
        max_tokens=1500,
        system=(
            "You are a concise markets assistant inside a Telegram chat for an Indian retail investor. "
            "English only. Use web search for anything current. Keep answers short (under 150 words), plain text, "
            "no markdown tables. Give facts and context, never buy/sell recommendations; remind briefly that you are "
            "not a SEBI-registered advisor only when the question is about what to buy or sell."
        ),
        tools=[WEB_SEARCH],
        messages=[{"role": "user", "content": question}],
    )
    return _text_of(resp).strip() or "I could not find an answer. Try rephrasing."


def _clean(s) -> str:
    s = str(s).replace("₹", "Rs ").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return s.encode("latin-1", "replace").decode("latin-1")


def render_pdf(data: dict, path: str) -> str:
    navy = colors.HexColor("#14213d")
    grey = colors.HexColor("#555555")
    h = ParagraphStyle("h", fontName="Helvetica-Bold", fontSize=20, textColor=navy, leading=24)
    sub = ParagraphStyle("sub", fontName="Helvetica", fontSize=10, textColor=grey, leading=13)
    sec = ParagraphStyle("sec", fontName="Helvetica-Bold", fontSize=12, textColor=navy, spaceBefore=10, spaceAfter=4)
    body = ParagraphStyle("b", fontName="Helvetica", fontSize=11, leading=15)
    why = ParagraphStyle("w", fontName="Helvetica", fontSize=10, leading=13, textColor=grey, leftIndent=10)
    foot = ParagraphStyle("f", fontName="Helvetica-Oblique", fontSize=8, textColor=grey, leading=10)

    doc = SimpleDocTemplate(path, pagesize=A4, leftMargin=18 * mm, rightMargin=16 * mm, topMargin=14 * mm, bottomMargin=14 * mm,
                            title="Daily Market Digest", author="Digest Bot")
    story = [Paragraph("Daily Market Digest", h),
             Paragraph(datetime.now(IST).strftime("%A, %d %B %Y") + " | 7:30 AM IST", sub), Spacer(1, 6)]

    rows = [["Market", "Level", "Change"]] + [[_clean(r.get("label", "")), _clean(r.get("value", "n/a")), _clean(r.get("change", ""))] for r in data.get("snapshot", [])]
    t = Table(rows, colWidths=[60 * mm, 55 * mm, 45 * mm], repeatRows=1)
    t.setStyle(TableStyle([
        ("FONT", (0, 0), (-1, 0), "Helvetica-Bold", 10), ("BACKGROUND", (0, 0), (-1, 0), navy), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONT", (0, 1), (-1, -1), "Helvetica", 10), ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f2f4f8")]),
        ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3), ("LINEBELOW", (0, -1), (-1, -1), 0.5, grey),
    ]))
    story += [t]
    if data.get("fii_dii"):
        story += [Spacer(1, 4), Paragraph("<b>FII/DII:</b> " + _clean(data["fii_dii"]), body)]

    story.append(Paragraph("India - top stories", sec))
    for i in data.get("india", []):
        story += [Paragraph("&bull; <b>" + _clean(i.get("headline", "")) + "</b>", body), Paragraph(_clean(i.get("why", "")), why), Spacer(1, 3)]
    if data.get("us"):
        story.append(Paragraph("US - what matters", sec))
        for i in data["us"]:
            story += [Paragraph("&bull; <b>" + _clean(i.get("headline", "")) + "</b>", body), Paragraph(_clean(i.get("why", "")), why), Spacer(1, 3)]
    if data.get("channels"):
        story.append(Paragraph("From your channels", sec))
        for c in data["channels"]:
            story.append(Paragraph("&bull; " + _clean(c), body))
    if data.get("today"):
        story += [Paragraph("Today", sec), Paragraph(_clean(data["today"]), body)]
    story += [Spacer(1, 10), Paragraph("For information only. Not investment advice. Figures from web sources at generation time; verify before acting.", foot)]
    doc.build(story)
    return path


def make_digest_pdf(path: str = "digest.pdf") -> str:
    return render_pdf(build_digest_data(), path)
