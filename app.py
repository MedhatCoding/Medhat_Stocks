import os
from datetime import datetime

import pandas as pd
import requests
import streamlit as st

from data_engine import data_engine
from sharia_universe import SHARIA_SYMBOLS, REFERENCE_DATE, REFERENCE_SOURCE, is_sharia_reference
from config import APP_NAME, APP_VERSION, STOCK_UNIVERSE_SIZE

# Optional live override: put SHARIA_SYMBOLS = "AAA,BBB,CCC" in Streamlit Secrets.
try:
    _sharia_override = st.secrets.get("SHARIA_SYMBOLS", "")
    if _sharia_override:
        SHARIA_SYMBOLS = [x.strip().upper().replace(".EGX", "") for x in str(_sharia_override).split(",") if x.strip()]
except Exception:
    pass


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
:root{--bg:#0b1020;--panel:#11182b;--panel2:#17213a;--line:#273451;--text:#f7f9ff;--muted:#98a5bb;--mint:#32d583;--mint2:#8af0b8;--violet:#8b7cff;--cyan:#4cc9f0;--red:#ff6675;--amber:#f5c451}
html,body,[class*="css"]{font-family:'Cairo',sans-serif}
.stApp{background:radial-gradient(circle at 78% -8%,rgba(139,124,255,.18),transparent 27%),radial-gradient(circle at 10% 8%,rgba(50,213,131,.08),transparent 24%),linear-gradient(135deg,#090e1b,#0d1425 55%,#0a1020);color:var(--text)}
.main .block-container{direction:rtl;text-align:right;max-width:1560px;padding:34px 46px 80px}
[data-testid="stSidebar"]{background:linear-gradient(180deg,#0f1628,#0a1020);border-left:1px solid #26324c;border-right:0}
[data-testid="stSidebar"]>div:first-child{padding:25px 18px}
[data-testid="stSidebar"] *{font-family:'Cairo',sans-serif}
.brand{padding:8px 10px 24px}.brand-title{font-size:27px;font-weight:800;color:#fff}.brand-sub{color:#7f8da7;font-size:12px;margin-top:5px}
[data-testid="stSidebar"] .stRadio>label{display:none}
[data-testid="stSidebar"] .stRadio [role="radiogroup"]{gap:10px}
[data-testid="stSidebar"] .stRadio [role="radio"]{background:rgba(255,255,255,.025);border:1px solid transparent;border-radius:15px;padding:15px 16px;min-height:54px;color:#aeb9cc;font-weight:800;font-size:14px;transition:.15s}
[data-testid="stSidebar"] .stRadio [role="radio"]:hover{background:#182238;color:#fff;border-color:#30405e}
[data-testid="stSidebar"] .stRadio [role="radio"][aria-checked="true"]{background:linear-gradient(90deg,rgba(50,213,131,.18),rgba(139,124,255,.10));color:#fff;border-color:rgba(50,213,131,.34);box-shadow:inset -4px 0 0 var(--mint),0 6px 20px rgba(0,0,0,.12)}
[data-testid="stSidebar"] .stRadio [role="radio"]>div:first-child{display:none}
.hero{background:linear-gradient(135deg,rgba(25,36,62,.96),rgba(16,24,43,.96));border:1px solid #2b3a5a;border-radius:26px;padding:34px 38px;margin-bottom:26px;box-shadow:0 22px 55px rgba(0,0,0,.25)}
.hero-title{font-size:34px;font-weight:800;letter-spacing:-1px;color:#fff}.hero-sub{color:#9ba8bd;font-size:15px;margin-top:8px}
.badge{display:inline-block;margin-top:19px;padding:9px 15px;border-radius:999px;background:rgba(50,213,131,.12);border:1px solid rgba(50,213,131,.3);color:#72e9aa;font-size:13px;font-weight:800}
.badge.gold{background:rgba(245,196,81,.12);border-color:rgba(245,196,81,.3);color:#f7d775}.badge.red{background:rgba(255,102,117,.11);border-color:rgba(255,102,117,.3);color:#ff9ca5}
.card{background:linear-gradient(145deg,#151f34,#11192b);border:1px solid #293856;border-radius:20px;padding:22px;min-height:124px;box-shadow:0 10px 30px rgba(0,0,0,.18)}
.card-label{color:#91a0b7;font-size:13px;font-weight:600}.card-value{color:#fff;font-size:29px;font-weight:800;margin-top:8px}.card-note{color:#718099;font-size:12px;margin-top:6px}
.section{font-size:21px;font-weight:800;color:#fff;margin:31px 0 13px}
.metric{background:#121b2d;border:1px solid #293956;border-radius:17px;padding:16px 18px;text-align:right;box-shadow:0 7px 22px rgba(0,0,0,.14)}
.metric-name{color:#91a0b7;font-size:12px}.metric-value{color:#fff;font-size:22px;font-weight:800;margin-top:4px}
.search-panel{background:linear-gradient(145deg,#141e33,#11192a);border:1px solid #2a3957;border-radius:21px;padding:22px;margin-bottom:22px;box-shadow:0 12px 35px rgba(0,0,0,.18)}
div[data-testid="stTextInput"] input,div[data-baseweb="select"]>div{background:#0d1525!important;border:1px solid #344565!important;color:#fff!important;border-radius:14px!important;min-height:54px;font-size:15px}
div[data-testid="stButton"]>button{min-height:52px;border-radius:14px;font-family:'Cairo',sans-serif;font-weight:800;border:1px solid #344565;background:#19243a;color:#f7f9ff;transition:.15s;font-size:15px}
div[data-testid="stButton"]>button:hover{border-color:var(--mint);color:#a9f5c9;background:#202e45}
div[data-testid="stButton"]>button[kind="primary"]{background:linear-gradient(135deg,#32d583,#20b96e);color:#07140d;border-color:#32d583;box-shadow:0 9px 25px rgba(50,213,131,.24)}
div[data-testid="stDownloadButton"]>button{min-height:52px;border-radius:14px;font-family:'Cairo',sans-serif;font-weight:800;font-size:15px}
div[data-testid="stMetric"]{background:#121b2d;border:1px solid #293956;padding:16px;border-radius:17px}
.stAlert{border-radius:15px}
[data-testid="stDataFrame"]{border:1px solid #293956;border-radius:17px;overflow:hidden}
hr{border-color:#24324b!important} footer{visibility:hidden}
.small-note{color:#78869d;font-size:12px;line-height:1.95}
.ai-box{background:linear-gradient(145deg,#172c27,#111b24);border:1px solid rgba(50,213,131,.27);border-right:5px solid #32d583;border-radius:20px;padding:23px;line-height:2.05;white-space:pre-wrap;color:#e3f5ec;font-size:14px}
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
            "⌂  لوحة التحكم",
            "◉  السوق",
            "✦  الفرص",
            "☆  قائمة المتابعة",
            "▣  المحفظة",
            "⌕  البحث والتحليل",
            "⚙  الإعدادات",
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
if page == "⌂  لوحة التحكم":
    st.markdown(
        '<div class="hero"><div class="hero-title">مدحت ستوكس AI</div>'
        '<div class="hero-sub">منصة EGX حديثة — بيانات فعلية، قراءة ذكية، وتجربة سريعة وواضحة بدون زحمة.</div>'
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
        st.info("قراءة كمية للبيانات المتاحة فقط — بدون أوامر شراء أو بيع.")
    else:
        st.info("لم يتم تشغيل تحليل بعد. افتح «البحث والتحليل» واكتب رمز سهم مثل SWDY أو EGAL.")

    st.markdown('<div class="section">كيف تعمل المنصة</div>', unsafe_allow_html=True)
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
elif page == "◉  السوق":
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
elif page == "✦  الفرص":
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
elif page == "☆  قائمة المتابعة":
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
elif page == "▣  المحفظة":
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
elif page == "⌕  البحث والتحليل":
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
        analyze = st.button("🔎  تشغيل التحليل", use_container_width=True, type="primary")
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
elif page == "⚙  الإعدادات":
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
