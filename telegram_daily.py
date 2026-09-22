import os
import html
import requests

from data_engine import data_engine


def money(value):
    if value is None:
        return "—"
    try:
        return f"{float(value):,.2f}"
    except Exception:
        return str(value)


def pct(value):
    if value is None:
        return "—"
    try:
        return f"{float(value):+.2f}%"
    except Exception:
        return str(value)


def main():
    result = data_engine.get_opportunities(limit=10)
    if not result.get("success"):
        message = "📊 <b>مدحت ستوكس AI</b>\nتعذر تشغيل فحص الفرص اليوم.\n" + html.escape(str(result.get("error", "خطأ غير معروف")))
    else:
        rows = result.get("data", [])
        lines = [
            "📊 <b>مدحت ستوكس AI — تقرير الفرص اليومي</b>",
            f"عدد الفرص المؤهلة: <b>{len(rows)}</b>",
        ]
        market = result.get("market", {})
        if market.get("success"):
            lines.append(f"السوق: EGX30 {money(market.get('close'))} • {html.escape(str(market.get('date','—')))}")
        if not rows:
            lines.append("\nلا توجد حاليًا فرصة تستوفي شروط الفحص.")
        for row in rows:
            symbol = str(row.get("symbol", "—"))
            name = data_engine.arabic_company_name(symbol, row.get("name", symbol))
            ml = row.get("ml_probability")
            ml_text = f" • ML: {float(ml):.1f}%" if ml is not None else ""
            lines.append(
                f"\n<b>{html.escape(name)}</b> ({html.escape(symbol)})"
                f"\nالسعر: {money(row.get('close'))} • التغير: {pct(row.get('change_pct'))}"
                f"\nالفرصة: <b>{row.get('opportunity_score','—')}/100</b> • المخاطر: {row.get('risk_score','—')}{ml_text}"
                f"\nالدخول: {money(row.get('entry_reference'))} • الهدف 1: {money(row.get('target1'))} • الإلغاء: {money(row.get('invalidation'))}"
            )
        message = "\n".join(lines)

    token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "")
    if not token or not chat_id:
        raise RuntimeError("Missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID")

    response = requests.post(
        f"https://api.telegram.org/bot{token}/sendMessage",
        json={"chat_id": chat_id, "text": message, "parse_mode": "HTML", "disable_web_page_preview": True},
        timeout=30,
    )
    response.raise_for_status()
    print("Telegram report sent successfully.")


if __name__ == "__main__":
    main()
