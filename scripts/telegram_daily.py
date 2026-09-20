import html
import os
from datetime import datetime
from zoneinfo import ZoneInfo

import requests

from data_engine import DataEngine

TZ = ZoneInfo("Africa/Cairo")
SEND_HOUR = 15
MIN_SCORE = 55
MIN_REBOUND = 45
MAX_RISK = 65


def send_telegram(token, chat_id, message):
    response = requests.post(
        f"https://api.telegram.org/bot{token}/sendMessage",
        json={
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
        },
        timeout=30,
    )
    response.raise_for_status()
    data = response.json()
    if not data.get("ok"):
        raise RuntimeError(data.get("description", "Telegram rejected the message"))


def main():
    now = datetime.now(TZ)
    force = os.getenv("FORCE_TELEGRAM", "").lower() == "true"

    if not force:
        # EGX trading days are Sunday through Thursday.
        if now.weekday() not in (6, 0, 1, 2, 3):
            print("Weekend/non-trading day. No Telegram message.")
            return
        if now.hour != SEND_HOUR:
            print(f"Outside the {SEND_HOUR}:00 Cairo send window. No Telegram message.")
            return

    token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "")
    if not token or not chat_id:
        raise RuntimeError("TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID are required.")

    engine = DataEngine()
    market = engine.get_market_context()
    if not market.get("success"):
        print("Market context unavailable. No message.")
        return

    # If the latest market date is not today in Cairo, EGX was not open today
    # (holiday, closure, or data not published yet), so do not send stale signals.
    if str(market.get("date", "")) != now.date().isoformat() and not force:
        print("No completed EGX session for today. No message.")
        return

    result = engine.get_opportunities(limit=12)
    if not result.get("success"):
        raise RuntimeError(result.get("error", "Opportunity scan failed"))

    rows = [
        row for row in result.get("data", [])
        if row.get("sharia_compliant") is True
        and float(row.get("opportunity_score") or 0) >= MIN_SCORE
        and float(row.get("rebound_score") or 0) >= MIN_REBOUND
        and float(row.get("risk_score") or 100) <= MAX_RISK
    ]
    rows.sort(key=lambda row: float(row.get("opportunity_score") or 0), reverse=True)

    if not rows:
        print("No qualifying Sharia-compliant opportunity today. No message sent.")
        return

    lines = [
        "📊 <b>مدحت ستوكس — فرص EGX اليوم</b>",
        f"📅 {html.escape(now.strftime('%Y-%m-%d'))} — {html.escape(now.strftime('%H:%M'))} القاهرة",
        f"📈 حالة السوق: <b>{html.escape(str(market.get('regime', 'غير متاح')))}</b>",
        "",
    ]

    for index, row in enumerate(rows[:5], 1):
        symbol = html.escape(str(row.get("symbol", "—")))
        score = row.get("opportunity_score", "—")
        rebound = row.get("rebound_score", "—")
        risk = row.get("risk_score", "—")
        rsi = row.get("rsi14", "—")
        news = row.get("news_score")
        news_text = "غير متاح" if news is None else f"{float(news):+.2f}"
        setup = html.escape(str(row.get("setup", "—")))
        lines.append(
            f"<b>{index}. {symbol}</b> — فرصة {score}/100\n"
            f"ارتداد {rebound}/100 • مخاطر {risk}/100 • RSI {rsi}\n"
            f"الأخبار {news_text} • {setup}" 
        )
        lines.append("")

    lines.append("⚠️ <i>هذه مرشحات تحليلية وليست أمراً بالشراء أو البيع. البيانات الفعلية فقط، ولا تُرسل رسالة عند عدم وجود فرصة مؤهلة.</i>")
    send_telegram(token, chat_id, "\n".join(lines))
    print(f"Telegram sent: {len(rows[:5])} opportunities.")


if __name__ == "__main__":
    main()
