import os
from datetime import datetime

import pandas as pd
import requests
import streamlit as st

from data_engine import data_engine
from sharia_universe import SHARIA_SYMBOLS, REFERENCE_DATE, REFERENCE_SOURCE, is_sharia_reference
from config import APP_NAME, APP_VERSION, STOCK_UNIVERSE_SIZE


st.set_page_config(
    page_title=APP_NAME,
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# -----------------------------
# Session state
# -----------------------------
if "watchlist" not in st.session_state:
    st.session_state.watchlist = []
if "portfolio" not in st.session_state:
    st.session_state.portfolio = []
if "last_analysis" not in st.session_state:
    st.session_state.last_analysis = None
if "last_ai" not in st.session_state:
    st.session_state.last_ai = None
if "last_fundamentals" not in st.session_state:
    st.session_state.last_fundamentals = None


# -----------------------------
# Helpers
# -----------------------------
def money(value, digits=2):
    if value is None or value == "":
        return "—"
    try:
        return f"{float(value):,.{digits}f}"
    except (TypeError, ValueError):
        return str(value)


def pct(value):
    if value is None:
        return "—"
    try:
        return f"{float(value):+.2f}%"
    except (TypeError, ValueError):
        return str(value)


def integer(value):
    if value is None or value == "":
        return "—"
    try:
        return f"{int(float(value)):,}"
    except (TypeError, ValueError):
        return str(value)


def sharia_status(symbol):
    return is_sharia_reference(symbol)


def add_watchlist(symbol):
    symbol = data_engine.display_symbol(symbol)
    if symbol and symbol not in st.session_state.watchlist:
        st.session_state.watchlist.append(symbol)


def remove_watchlist(symbol):
    if symbol in st.session_state.watchlist:
        st.session_state.watchlist.remove(symbol)


def send_telegram(message):
    token = data_engine.get_secret("TELEGRAM_BOT_TOKEN")
    chat_id = data_engine.get_secret("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        return False, "TELEGRAM_BOT_TOKEN أو TELEGRAM_CHAT_ID غير موجود"
    try:
        response = requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={"chat_id": chat_id, "text": message, "parse_mode": "HTML"},
            timeout=20,
        )
        response.raise_for_status()
        return True, "تم إرسال الرسالة"
    except requests.RequestException as exc:
        return False, str(exc)


# -----------------------------
# Professional dark UI
# -----------------------------
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;500;600;700;800&display=swap');

:root {
  --bg:#080d13;
  --panel:#0f1721;
  --panel2:#121d29;
  --border:#233142;
  --text:#eef3f7;
  --muted:#8b9aaa;
  --gold:#d6b35a;
  --gold2:#f0d58a;
  --green:#35c98a;
  --red:#ef6b73;
  --blue:#62a7ff;
}

html, body, [class*="css"] { font-family:'Cairo',sans-serif; }
.stApp { background:radial-gradient(circle at 80% -10%, #182433 0, var(--bg) 38%); color:var(--text); }
.main .block-container { direction:rtl; text-align:right; max-width:1540px; padding:30px 34px 60px; }
[data-testid="stSidebar"] {
  background:#0b1118;
  border-left:1px solid var(--border);
  border-right:0;
}
[data-testid="stSidebar"] * { font-family:'Cairo',sans-serif; }
[data-testid="stSidebar"] .stRadio label { color:#bdc8d3; font-weight:700; }
[data-testid="stSidebar"] .stRadio label:hover { color:var(--gold2); }

.brand { padding:8px 2px 14px; }
.brand-title { font-size:23px; font-weight:800; color:#fff; }
.brand-sub { color:var(--muted); font-size:12px; margin-top:3px; }

.hero {
  background:linear-gradient(145deg,rgba(20,31,44,.98),rgba(10,16,23,.98));
  border:1px solid var(--border); border-radius:24px; padding:28px 30px;
  margin-bottom:22px; box-shadow:0 18px 55px rgba(0,0,0,.18);
}
.hero-title { font-size:31px; font-weight:800; letter-spacing:-.4px; color:#fff; }
.hero-sub { color:var(--muted); font-size:13px; margin-top:4px; }
.badge { display:inline-block; margin-top:16px; padding:6px 12px; border-radius:999px;
  background:rgba(53,201,138,.10); border:1px solid rgba(53,201,138,.24);
  color:#6de0aa; font-size:12px; font-weight:700; }
.badge.gold { background:rgba(214,179,90,.10); border-color:rgba(214,179,90,.25); color:var(--gold2); }
.badge.red { background:rgba(239,107,115,.10); border-color:rgba(239,107,115,.25); color:#ff9aa0; }

.card {
  background:linear-gradient(145deg,#111b27,#0d151e);
  border:1px solid var(--border); border-radius:18px; padding:20px; min-height:128px;
}
.card-label { color:var(--muted); font-size:12px; }
.card-value { color:#fff; font-size:26px; font-weight:800; margin-top:6px; }
.card-note { color:#68798a; font-size:11px; margin-top:5px; }

.section { font-size:19px; font-weight:800; color:#f7f9fb; margin:26px 0 13px; }
.metric {
  background:#0e1721; border:1px solid var(--border); border-radius:16px;
  padding:16px; text-align:right;
}
.metric-name { color:var(--muted); font-size:11px; }
.metric-value { color:#fff; font-size:21px; font-weight:800; margin-top:3px; }

.search-panel {
  background:#0e1721; border:1px solid var(--border); border-radius:20px;
  padding:20px; margin-bottom:18px;
}
div[data-testid="stTextInput"] input, div[data-baseweb="select"] > div {
  background:#0a1118 !important; border-color:#2b3a4a !important;
  color:#fff !important; border-radius:12px !important;
}
div[data-testid="stButton"] > button {
  min-height:43px; border-radius:12px; font-family:'Cairo',sans-serif; font-weight:800;
  border:1px solid #334252; background:#121d29; color:#eef3f7;
}
div[data-testid="stButton"] > button:hover { border-color:var(--gold); color:var(--gold2); }
div[data-testid="stDownloadButton"] > button {
  min-height:43px; border-radius:12px; font-family:'Cairo',sans-serif; font-weight:800;
}
div[data-testid="stMetric"] { background:#0e1721; border:1px solid var(--border); padding:12px; border-radius:14px; }
.stAlert { border-radius:14px; }
[data-testid="stDataFrame"] { border:1px solid var(--border); border-radius:14px; overflow:hidden; }
hr { border-color:var(--border) !important; }
footer { visibility:hidden; }
.small-note { color:#748495; font-size:11px; line-height:1.8; }
.ai-box {
  background:linear-gradient(145deg,rgba(31,42,57,.75),rgba(14,21,29,.95));
  border:1px solid rgba(214,179,90,.25); border-radius:18px; padding:22px;
  line-height:2; white-space:pre-wrap;
}
</style>
""",
    unsafe_allow_html=True,
)


# -----------------------------
# Sidebar
# -----------------------------
with st.sidebar:
    st.markdown(
        '<div class="brand"><div class="brand-title">📊 مدحت ستوكس AI</div>'
        '<div class="brand-sub">تحليل EGX • فلترة شرعية • بيانات فعلية</div></div>',
        unsafe_allow_html=True,
    )
    st.divider()

    page = st.radio(
        "NAV",
        [
            "لوحة التحكم",
            "السوق",
            "الفرص",
            "قائمة المتابعة",
            "المحفظة",
            "البحث والتحليل",
            "الإعدادات",
        ],
        label_visibility="collapsed",
    )

    st.divider()
    health = data_engine.health_check()
    if health["eodhd_configured"]:
        st.markdown('<span class="badge">● EODHD متصل</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="badge red">● EODHD غير متصل</span>', unsafe_allow_html=True)
    st.caption(f"الإصدار {APP_VERSION} • الهدف: {STOCK_UNIVERSE_SIZE} سهم")


# -----------------------------
# Dashboard
# -----------------------------
if page == "لوحة التحكم":
    st.markdown(
        '<div class="hero"><div class="hero-title">مركز التحليل الذكي</div>'
        '<div class="hero-sub">منصة مدحت ستوكس AI لمتابعة الأسهم المصرية مع فصل البيانات عن التحليل والفلترة الشرعية.</div>'
        '<span class="badge">● النظام جاهز للتحليل</span></div>',
        unsafe_allow_html=True,
    )

    last = st.session_state.last_analysis
    if last:
        market_state = last["status"]
        market_note = f"آخر سهم محلل: {last['symbol']}"
        score = last["opportunity_score"]
        risk = last["risk_score"]
    else:
        market_state, market_note, score, risk = "—", "ابدأ من البحث والتحليل", "—", "—"

    cards = [
        ("حالة آخر تحليل", market_state, market_note),
        ("الكون المستهدف", str(STOCK_UNIVERSE_SIZE), "هدف المنصة"),
        ("المرجع الشرعي", str(len(SHARIA_SYMBOLS)), f"قائمة مرجعية حتى {REFERENCE_DATE}"),
        ("آخر درجة فرصة", score, "حساب آلي وصفي، ليست توصية"),
    ]
    for col, (label, value, note) in zip(st.columns(4), cards):
        with col:
            st.markdown(
                f'<div class="card"><div class="card-label">{label}</div>'
                f'<div class="card-value">{value}</div><div class="card-note">{note}</div></div>',
                unsafe_allow_html=True,
            )

    st.markdown('<div class="section">آخر قراءة تحليلية</div>', unsafe_allow_html=True)
    if last:
        cols = st.columns(6)
        metrics = [
            ("السعر", money(last["close"])),
            ("التغير", pct(last["change_pct"])),
            ("RSI 14", money(last["rsi14"])),
            ("SMA 20", money(last["sma20"])),
            ("الدعم", money(last["support"])),
            ("المقاومة", money(last["resistance"])),
        ]
        for col, (label, value) in zip(cols, metrics):
            with col:
                st.markdown(
                    f'<div class="metric"><div class="metric-name">{label}</div>'
                    f'<div class="metric-value">{value}</div></div>',
                    unsafe_allow_html=True,
                )
        st.info("هذه قراءة كمية للبيانات المتاحة، وليست توصية شراء أو بيع.")
    else:
        st.info("لم يتم تشغيل تحليل بعد. افتح «البحث والتحليل» واكتب رمز سهم مثل SWDY أو EGAL.")

    st.markdown('<div class="section">منهجية المنصة</div>', unsafe_allow_html=True)
    a, b, c = st.columns(3)
    for col, title, text in [
        (a, "01 • البيانات", "بيانات الإغلاق والحجم والتاريخ من EODHD مع معالجة أخطاء واضحة."),
        (b, "02 • التحليل", "اتجاهات SMA وRSI وATR والتذبذب والحجم والدعم والمقاومة."),
        (c, "03 • الذكاء", "Gemini يشرح الإشارات المتاحة دون اختراع أرقام أو إصدار أمر شراء/بيع."),
    ]:
        with col:
            st.markdown(
                f'<div class="card"><div class="card-label">{title}</div>'
                f'<div style="font-size:14px;color:#dce4eb;line-height:1.9;margin-top:8px">{text}</div></div>',
                unsafe_allow_html=True,
            )


# -----------------------------
# Market
# -----------------------------
elif page == "السوق":
    st.markdown(
        '<div class="hero"><div class="hero-title">السوق المصري</div>'
        '<div class="hero-sub">قراءة السوق هنا مبنية على آخر تحليل تم تشغيله فعلياً، بدون أرقام وهمية.</div></div>',
        unsafe_allow_html=True,
    )
    last = st.session_state.last_analysis
    if not last:
        st.info("ابدأ بتحليل سهم من صفحة «البحث والتحليل» لتكوين أول قراءة فعلية.")
    else:
        st.markdown('<div class="section">آخر حالة مقاسة</div>', unsafe_allow_html=True)
        cols = st.columns(4)
        items = [
            ("الاتجاه", last["status"]),
            ("درجة الفرصة", last["opportunity_score"]),
            ("درجة المخاطر", last["risk_score"]),
            ("جلسات البيانات", last["history_rows"]),
        ]
        for col, (label, value) in zip(cols, items):
            with col:
                st.metric(label, value)
        st.markdown('<div class="section">حركة السعر والمتوسطات</div>', unsafe_allow_html=True)
        chart = last["chart"].copy()
        chart["date"] = pd.to_datetime(chart["date"])
        chart = chart.set_index("date")
        chart.columns = ["الإغلاق", "SMA 20", "SMA 50", "SMA 200"]
        st.line_chart(chart, height=380)
        st.caption("المؤشرات الفنية مفيدة لوصف السلوك التاريخي ولا تضمن نتيجة مستقبلية.")


# -----------------------------
# Opportunities
# -----------------------------
elif page == "الفرص":
    st.markdown(
        '<div class="hero"><div class="hero-title">الفرص</div>'
        '<div class="hero-sub">لا نعرض «أفضل سهم» أو ترتيباً إجبارياً. هذه الصفحة تعرض فقط الأسهم التي طلبت تحليلها واحتفظت بها.</div></div>',
        unsafe_allow_html=True,
    )
    if not st.session_state.watchlist:
        st.info("قائمة المتابعة فارغة. أضف الأسهم من صفحة البحث والتحليل.")
    else:
        rows = []
        for symbol in st.session_state.watchlist:
            result = data_engine.analyze_stock(symbol)
            if result["success"]:
                rows.append({
                    "السهم": result["symbol"].replace(".EGX", ""),
                    "الحالة": result["status"],
                    "درجة الفرصة": result["opportunity_score"],
                    "المخاطر": result["risk_score"],
                    "RSI": round(result["rsi14"], 2) if result["rsi14"] is not None else None,
                    "التغير 20ج": pct(result["return20"]),
                    "آخر إغلاق": money(result["close"]),
                })
        if rows:
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        else:
            st.warning("تعذر تحديث عناصر قائمة المتابعة حالياً.")


# -----------------------------
# Watchlist
# -----------------------------
elif page == "قائمة المتابعة":
    st.markdown(
        '<div class="hero"><div class="hero-title">قائمة المتابعة</div>'
        '<div class="hero-sub">قائمة محلية داخل جلسة التطبيق. لا تحتاج قاعدة بيانات لتجربة النسخة الحالية.</div></div>',
        unsafe_allow_html=True,
    )
    if not st.session_state.watchlist:
        st.info("لا توجد أسهم بعد.")
    else:
        for symbol in list(st.session_state.watchlist):
            col1, col2, col3 = st.columns([2, 5, 1])
            with col1:
                st.markdown(f"### {symbol}")
            with col2:
                result = data_engine.get_latest_price(symbol)
                if result["success"]:
                    st.write(
                        f"**{money(result['close'])}**  •  {pct(result['change_pct'])}  •  {result['date']}"
                    )
                else:
                    st.write("تعذر تحديث السعر.")
            with col3:
                if st.button("حذف", key=f"remove_{symbol}"):
                    remove_watchlist(symbol)
                    st.rerun()


# -----------------------------
# Portfolio
# -----------------------------
elif page == "المحفظة":
    st.markdown(
        '<div class="hero"><div class="hero-title">المحفظة</div>'
        '<div class="hero-sub">تتبع المراكز داخل الجلسة الحالية مع حساب القيمة والتغير بناءً على آخر بيانات EOD.</div></div>',
        unsafe_allow_html=True,
    )
    with st.form("portfolio_form"):
        c1, c2, c3 = st.columns(3)
        with c1:
            p_symbol = st.text_input("رمز السهم", placeholder="SWDY")
        with c2:
            p_qty = st.number_input("الكمية", min_value=0.0, step=1.0)
        with c3:
            p_avg = st.number_input("متوسط التكلفة", min_value=0.0, step=0.01)
        submitted = st.form_submit_button("إضافة مركز", use_container_width=True)
        if submitted:
            symbol = data_engine.display_symbol(p_symbol)
            if symbol and p_qty > 0 and p_avg > 0:
                st.session_state.portfolio.append({"symbol": symbol, "qty": p_qty, "avg": p_avg})
                st.success("تمت إضافة المركز.")
            else:
                st.warning("أدخل الرمز والكمية ومتوسط التكلفة.")

    if st.session_state.portfolio:
        rows = []
        for pos in st.session_state.portfolio:
            latest = data_engine.get_latest_price(pos["symbol"])
            price = latest.get("close") if latest.get("success") else None
            value = price * pos["qty"] if price is not None else None
            cost = pos["avg"] * pos["qty"]
            pnl = value - cost if value is not None else None
            rows.append({
                "السهم": pos["symbol"],
                "الكمية": pos["qty"],
                "متوسط التكلفة": money(pos["avg"]),
                "السعر": money(price),
                "القيمة": money(value),
                "الربح/الخسارة": money(pnl),
            })
        frame = pd.DataFrame(rows)
        st.dataframe(frame, use_container_width=True, hide_index=True)
        st.download_button(
            "⬇️ تنزيل المحفظة CSV",
            frame.to_csv(index=False).encode("utf-8-sig"),
            file_name="medhat_stocks_portfolio.csv",
            mime="text/csv",
            use_container_width=True,
        )
    else:
        st.info("لم تضف أي مركز بعد.")


# -----------------------------
# Research / analysis
# -----------------------------
elif page == "البحث والتحليل":
    st.markdown(
        '<div class="hero"><div class="hero-title">البحث والتحليل</div>'
        '<div class="hero-sub">ابحث بالرمز أو اسم الشركة. البيانات من السوق أولاً، ثم التحليل الكمي، ثم شرح AI عند الطلب.</div></div>',
        unsafe_allow_html=True,
    )

    st.markdown('<div class="search-panel">', unsafe_allow_html=True)
    query = st.text_input("ابحث عن السهم", placeholder="مثال: SWDY أو EGAL", label_visibility="visible")
    suggestions = data_engine.search_symbols(query) if query else []
    if suggestions:
        st.caption("اقتراحات من قائمة EGX:")
        labels = [f"{x['symbol']} — {x['name']}" for x in suggestions[:6]]
        picked = st.selectbox("اختر من النتائج", labels, label_visibility="collapsed")
        selected_symbol = picked.split(" — ")[0]
    else:
        selected_symbol = query.strip().upper()

    c1, c2, c3 = st.columns(3)
    with c1:
        analyze = st.button("🔎 تشغيل التحليل", use_container_width=True)
    with c2:
        ai_enabled = st.checkbox("تشغيل شرح Gemini", value=True)
    with c3:
        technical_visible = st.checkbox("إظهار التفاصيل الفنية", value=False)
    st.markdown("</div>", unsafe_allow_html=True)

    if analyze:
        if not selected_symbol:
            st.warning("اكتب رمز السهم أولاً.")
        else:
            with st.spinner("جاري جلب البيانات وتحليل آخر 365 جلسة..."):
                result = data_engine.analyze_stock(selected_symbol)
            if not result["success"]:
                st.error(result["error"])
            else:
                st.session_state.last_analysis = result
                st.session_state.last_ai = None
                symbol = result["symbol"].replace(".EGX", "")
                sharia_ok = sharia_status(symbol)

                status_class = "gold" if sharia_ok else "red"
                status_text = "✓ موجود في القائمة الشرعية المرجعية" if sharia_ok else "⚠ غير موجود في القائمة الشرعية المرجعية"

                st.markdown(
                    f'<div class="hero"><div class="hero-title">{symbol}</div>'
                    f'<div class="hero-sub">آخر جلسة متاحة: {result["date"]}</div>'
                    f'<span class="badge {status_class}">{status_text}</span></div>',
                    unsafe_allow_html=True,
                )

                cols = st.columns(4)
                for col, label, value in [
                    (cols[0], "آخر إغلاق", money(result["close"])),
                    (cols[1], "التغير", pct(result["change_pct"])),
                    (cols[2], "أعلى سعر", money(result["high"])),
                    (cols[3], "أقل سعر", money(result["low"])),
                ]:
                    with col:
                        st.markdown(
                            f'<div class="metric"><div class="metric-name">{label}</div>'
                            f'<div class="metric-value">{value}</div></div>',
                            unsafe_allow_html=True,
                        )

                st.markdown('<div class="section">ملخص التحليل</div>', unsafe_allow_html=True)
                cols = st.columns(5)
                for col, label, value in [
                    (cols[0], "الحالة", result["status"]),
                    (cols[1], "درجة الفرصة", result["opportunity_score"]),
                    (cols[2], "درجة المخاطر", result["risk_score"]),
                    (cols[3], "الدعم", money(result["support"])),
                    (cols[4], "المقاومة", money(result["resistance"])),
                ]:
                    with col:
                        st.metric(label, value)

                if sharia_ok:
                    st.success("السهم موجود في قائمة الشرعية المرجعية المدمجة. راجع تاريخ المرجع قبل اتخاذ أي قرار.")
                else:
                    st.warning("السهم غير موجود في القائمة الشرعية المرجعية الحالية داخل التطبيق؛ لذلك لا يتم اعتباره فرصة شرعية مؤكدة.")

                b1, b2 = st.columns(2)
                with b1:
                    if symbol in st.session_state.watchlist:
                        st.info("السهم موجود بالفعل في قائمة المتابعة.")
                    elif st.button("⭐ إضافة لقائمة المتابعة", use_container_width=True):
                        add_watchlist(symbol)
                        st.success("تمت الإضافة.")
                with b2:
                    if ai_enabled:
                        with st.spinner("جاري صياغة شرح AI..."):
                            fundamentals = data_engine.get_company_snapshot(symbol)
                            st.session_state.last_fundamentals = fundamentals if fundamentals["success"] else None
                            ai = data_engine.ai_analysis(
                                symbol,
                                result,
                                fundamentals if fundamentals.get("success") else {},
                            )
                            st.session_state.last_ai = ai
                    else:
                        st.info("شرح Gemini متوقف لهذه العملية.")

                st.markdown('<div class="section">الشارت</div>', unsafe_allow_html=True)
                chart = result["chart"].copy()
                chart["date"] = pd.to_datetime(chart["date"])
                chart = chart.set_index("date")
                chart.columns = ["الإغلاق", "SMA 20", "SMA 50", "SMA 200"]
                st.line_chart(chart, height=390)

                if technical_visible:
                    st.markdown('<div class="section">التفاصيل الفنية</div>', unsafe_allow_html=True)
                    technical = pd.DataFrame([
                        ["RSI 14", money(result["rsi14"]), "قياس زخم"],
                        ["SMA 20", money(result["sma20"]), "متوسط قصير"],
                        ["SMA 50", money(result["sma50"]), "متوسط متوسط"],
                        ["SMA 200", money(result["sma200"]), "متوسط طويل"],
                        ["ATR 14", money(result["atr14"]), "نطاق حركة"],
                        ["العائد 20 جلسة", pct(result["return20"]), "أداء تاريخي"],
                        ["العائد 60 جلسة", pct(result["return60"]), "أداء تاريخي"],
                        ["التذبذب", pct(result["volatility20"]), "سنوي تقريبي"],
                        ["نسبة الحجم", money(result["volume_ratio"]), "مقابل متوسط 20 جلسة"],
                    ], columns=["المؤشر", "القيمة", "المعنى"])
                    st.dataframe(technical, use_container_width=True, hide_index=True)

                if st.session_state.last_fundamentals:
                    f = st.session_state.last_fundamentals
                    st.markdown('<div class="section">لقطة أساسية</div>', unsafe_allow_html=True)
                    cols = st.columns(5)
                    for col, label, value in [
                        (cols[0], "الشركة", f.get("name", "—")),
                        (cols[1], "القطاع", f.get("sector", "—")),
                        (cols[2], "القيمة السوقية", integer(f.get("market_cap"))),
                        (cols[3], "P/E", money(f.get("pe"))),
                        (cols[4], "عائد التوزيعات", pct(f.get("dividend_yield"))),
                    ]:
                        with col:
                            st.markdown(
                                f'<div class="metric"><div class="metric-name">{label}</div>'
                                f'<div class="metric-value" style="font-size:17px">{value}</div></div>',
                                unsafe_allow_html=True,
                            )

                if st.session_state.last_ai and st.session_state.last_ai.get("success"):
                    st.markdown('<div class="section">التحليل الذكي</div>', unsafe_allow_html=True)
                    st.markdown(
                        f'<div class="ai-box">{st.session_state.last_ai["text"]}</div>',
                        unsafe_allow_html=True,
                    )
                    st.caption("التحليل الذكي يشرح البيانات المتاحة ولا يمثل توصية استثمارية أو حكماً شرعياً.")

                st.markdown(
                    '<div class="small-note">مصدر الأسعار: EODHD. قد تتأخر بيانات الإغلاق بحسب خطة مزود البيانات. '
                    'الفلترة الشرعية مرجعية وليست فتوى؛ يرجى الرجوع إلى المرجع الشرعي المناسب عند الحاجة.</div>',
                    unsafe_allow_html=True,
                )


# -----------------------------
# Settings
# -----------------------------
elif page == "الإعدادات":
    st.markdown(
        '<div class="hero"><div class="hero-title">الإعدادات وحالة النظام</div>'
        '<div class="hero-sub">كل الأسرار تُقرأ من Streamlit Secrets ولا يتم عرض قيمها داخل التطبيق.</div></div>',
        unsafe_allow_html=True,
    )

    health = data_engine.health_check()
    cols = st.columns(3)
    for col, label, key in [
        (cols[0], "EODHD", "eodhd_configured"),
        (cols[1], "Gemini AI", "gemini_configured"),
        (cols[2], "OANOR", "oanor_configured"),
    ]:
        with col:
            state = "متصل" if health[key] else "غير مهيأ"
            st.metric(label, state)

    st.markdown('<div class="section">المرجعية الشرعية</div>', unsafe_allow_html=True)
    st.write(f"المصدر: {REFERENCE_SOURCE}")
    st.write(f"تاريخ المرجع: {REFERENCE_DATE}")
    st.write(f"عدد الرموز المرجعية المدمجة: {len(SHARIA_SYMBOLS)}")
    st.caption(f"هدف المنصة الحالي: {STOCK_UNIVERSE_SIZE} سهم. يمكن تحديث القائمة من الكود/Secret عند صدور نسخة أحدث.")

    st.markdown('<div class="section">Telegram</div>', unsafe_allow_html=True)
    if st.button("📨 اختبار إرسال Telegram", use_container_width=True):
        ok, message = send_telegram("📊 <b>مدحت ستوكس AI</b>\nاختبار اتصال Telegram ناجح.")
        if ok:
            st.success(message)
        else:
            st.error(message)

    st.markdown('<div class="section">ملاحظات تشغيلية</div>', unsafe_allow_html=True)
    st.info(
        "المحفظة وقائمة المتابعة في هذه النسخة محفوظتان داخل جلسة Streamlit الحالية. "
        "للحفظ الدائم بين الأجهزة نحتاج قاعدة بيانات وحسابات مستخدمين في مرحلة لاحقة."
    )

    st.json({
        "version": APP_VERSION,
        "market": "EGX",
        "target_universe": STOCK_UNIVERSE_SIZE,
        "reference_sharia_symbols": len(SHARIA_SYMBOLS),
        "checked_at": health["checked_at"],
    })
