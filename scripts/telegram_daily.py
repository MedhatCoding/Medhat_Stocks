import html
import os
import sys
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo

import requests

# The script lives in scripts/, while the application modules live at repo root.
# Add the repository root to Python's import path for GitHub Actions and local runs.
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from data_engine import DataEngine
from recommendation_journal import evaluate_open, record_opportunity

TZ = ZoneInfo("Africa/Cairo")
SEND_HOUR = 9
MIN_SCORE = 55
MIN_REBOUND = 45
MAX_RISK = 65


def load_portfolio_from_supabase():
    url = os.getenv("SUPABASE_URL", "").rstrip("/")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
    owner = os.getenv("PORTFOLIO_OWNER_ID", "medhat")
    if not url or not key:
        return []
    try:
        r = requests.get(url + "/rest/v1/portfolio_positions",
            headers={"apikey": key, "Authorization": "Bearer " + key},
            params={"owner_id": "eq." + owner, "select": "symbol,qty,avg", "order": "symbol.asc"}, timeout=20)
        r.raise_for_status()
        return r.json()
    except Exception as exc:
        print("Portfolio storage unavailable:", exc)
        return []


def build_portfolio_report(engine, market):
    positions = load_portfolio_from_supabase()
    if not positions:
        return ["💼 <b>توصيات المحفظة</b>", "لا توجد مراكز محفوظة حاليًا."]
    total_value = 0.0
    priced = []
    for pos in positions:
        price_result = engine.get_latest_price(pos.get("symbol"))
        price = price_result.get("close") if price_result.get("success") else None
        qty = float(pos.get("qty") or 0)
        value = qty * float(price) if price is not None else 0
        total_value += value
        priced.append((pos, price, value))
    lines = ["💼 <b>توصيات المحفظة</b>"]
    for pos, price, value in priced:
        try:
            advice = __import__("portfolio_advisor").advise(pos, market=market, portfolio_value=total_value)
        except Exception as exc:
            print("Portfolio advice failed:", exc)
            continue
        action = advice.get("action", "بيانات غير كافية")
        emoji = {"زيادة":"🟢", "احتفاظ":"🟡", "بيع":"🔴"}.get(action, "⚪")
        pnl = advice.get("pnl_pct")
        pnl_text = "—" if pnl is None else f"{float(pnl):+.2f}%"
        lines.append(f'{emoji} <b>{html.escape(str(advice.get("name") or advice.get("symbol")))}</b> ({html.escape(str(advice.get("symbol")))})')
        lines.append(f"↳ <b>{action}</b> • ر/خ {pnl_text} • وزن {float(advice.get("weight_pct") or 0):.1f}%")
        lines.append(f'↳ {html.escape(str(advice.get("reason") or "—"))}')
    return lines

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
        # EGX regular trading week is Sunday through Thursday.
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
    report = engine.get_premarket_report(limit=12)
    if not report.get("success"):
        raise RuntimeError(
            f"Pre-market report unavailable: {report.get('error', 'unknown error')}"
        )

    indices_board = engine.get_market_indices()
    market = dict(report.get("market", {}) or {})
    seasonality = engine.get_market_seasonality(min_years=3)
    market["seasonality_score"] = seasonality.get("score")

    rows = [
        row for row in report.get("opportunities", [])
        if row.get("sharia_compliant") is True
        and float(row.get("opportunity_score") or 0) >= MIN_SCORE
        and float(row.get("rebound_score") or 0) >= MIN_REBOUND
        and float(row.get("risk_score") or 100) <= MAX_RISK
    ]
    rows.sort(key=lambda row: float(row.get("opportunity_score") or 0), reverse=True)

    # Close matured recommendations first, then journal today's qualifying setups.
    evaluate_open(lambda symbol, days: engine.get_stock_history(symbol, days=max(30, days)))
    for row in rows[:12]:
        record_opportunity(row)

    lines = [
        "📊 <b>مدحت ستوكس — تقرير صباح السوق</b>",
        f"📅 {html.escape(now.strftime('%Y-%m-%d'))} — {html.escape(now.strftime('%H:%M'))} القاهرة",
        f"📚 آخر جلسة مكتملة: <b>{html.escape(str(report.get('latest_session_date', 'غير متاح')))}</b>",
        f"📈 حالة السوق: <b>{html.escape(str(market.get('regime', 'غير متاح')))}</b>",
    ]

    index_rows = (indices_board or {}).get("indices", [])
    if index_rows:
        lines += ["", "📌 <b>المؤشرات</b>"]
        # EGX33 first because it is the Sharia benchmark for this app.
        index_rows = sorted(index_rows, key=lambda x: 0 if x.get("symbol") == "EGX33" else 1)
        for idx in index_rows:
            change = idx.get("change_pct")
            change_text = "—" if change is None else f"{float(change):+.2f}%"
            prefix = "☪️ " if idx.get("symbol") == "EGX33" else "• "
            lines.append(
                f"{prefix}{html.escape(str(idx.get('name', '—')))}: "
                f"<b>{idx.get('close', '—')}</b> ({change_text})"
            )

    lines += ["", f"🎯 <b>الفرص المؤهلة: {len(rows)}</b>"]

    lines += [""] + build_portfolio_report(engine, market) + [""]

    for index, row in enumerate(rows[:5], 1):
        symbol = html.escape(str(row.get("symbol", "—")))
        name = html.escape(str(row.get("name") or symbol))
        score = row.get("opportunity_score", "—")
        rebound = row.get("rebound_score", "—")
        risk = row.get("risk_score", "—")
        rsi = row.get("rsi14", "—")
        news = row.get("news_score")
        news_text = "غير متاح" if news is None else f"{float(news):+.2f}"
        setup = html.escape(str(row.get("setup", "—")))
        lines.append(
            f"<b>{index}. {name} ({symbol})</b> — فرصة {score}/100\n"
            f"ارتداد {rebound}/100 • مخاطر {risk}/100 • RSI {rsi}\n"
            f"الأخبار {news_text} • {setup}"
        )
        lines.append("")

    if not rows:
        lines.append("ℹ️ لا توجد حاليًا فرصة شرعية تستوفي شروط الدخول؛ لم يتم اختلاق أي فرصة.")

    lines.append(
        "⚠️ <i>تقرير تحليلي شخصي قبل الافتتاح، وليس أمرًا بالشراء أو البيع. "
        "يتم إرساله تلقائيًا في أيام السوق دون الحاجة لتشغيل التطبيق.</i>"
    )

    send_telegram(token, chat_id, "\n".join(lines))
    print(f"Telegram sent successfully: {len(rows[:5])} opportunities.")


if __name__ == "__main__":
    main()
