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
if "mobile_page" not in st.session_state:
    st.session_state.mobile_page = "⌂  الرئيسية"
if "jump_page" not in st.session_state:
    st.session_state.jump_page = None
if st.session_state.jump_page:
    st.session_state.mobile_page = st.session_state.jump_page
    st.session_state.jump_page = None


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
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;500;600;700;800;900&display=swap');
:root{--bg:#07111f;--surface:#0d1a2b;--surface2:#12243a;--line:#20344d;--text:#f7fbff;--muted:#91a4b9;--green:#22d47a;--gold:#f4c95d;--red:#ff6677}
html,body,[class*="css"]{font-family:'Cairo',sans-serif}
.stApp{background:#07111f;color:var(--text)}
.main .block-container{direction:rtl;text-align:right;max-width:1180px;padding:18px 28px 100px}
[data-testid="stSidebar"]{display:none!important}
[data-testid="stSidebar"]>div:first-child{padding:18px 12px}
[data-testid="stSidebar"] *{font-family:'Cairo',sans-serif}
.brand{padding:8px 10px 20px}.brand-title{font-size:24px;font-weight:900}.brand-sub{color:var(--muted);font-size:11px}
[data-testid="stSidebar"] .stRadio>label{display:none}
[data-testid="stSidebar"] .stRadio [role="radiogroup"]{gap:6px}
[data-testid="stSidebar"] .stRadio [role="radio"]{background:transparent;border:1px solid transparent;border-radius:14px;padding:12px 13px;min-height:48px;color:#8fa2b7;font-weight:800}
[data-testid="stSidebar"] .stRadio [role="radio"][aria-checked="true"]{background:#102b21;color:#8df5bd;border-color:#24573e;box-shadow:inset -4px 0 0 var(--green)}
[data-testid="stSidebar"] .stRadio [role="radio"]>div:first-child{display:none}
.app-topbar{display:flex;align-items:center;justify-content:space-between;margin:0 0 16px;padding:3px 2px}
.app-name{font-size:21px;font-weight:900}.app-context{font-size:10px;color:#73869b}
.market-pill{padding:7px 12px;border-radius:999px;background:#10291f;border:1px solid #24543d;color:#7df0af;font-size:10px;font-weight:900}
.hero{background:linear-gradient(145deg,#102842,#0b1726);border:1px solid #27435f;border-radius:25px;padding:25px;margin-bottom:17px;box-shadow:0 15px 35px rgba(0,0,0,.25)}
.hero-title{font-size:29px;font-weight:900}.hero-sub{color:#9aadc1;font-size:13px;margin-top:6px;line-height:1.9}
.badge{display:inline-block;margin-top:13px;padding:6px 11px;border-radius:999px;background:#102b20;border:1px solid #25583e;color:#81efb1;font-size:11px;font-weight:900}.badge.gold{background:#302818;border-color:#665224;color:#f5d57a}.badge.red{background:#30171c;border-color:#672b34;color:#ff9da6}
.card{background:#0d1b2c;border:1px solid #203750;border-radius:18px;padding:17px;min-height:108px;box-shadow:0 8px 25px rgba(0,0,0,.16)}
.card-label{color:#91a5ba;font-size:11px;font-weight:700}.card-value{color:#fff;font-size:24px;font-weight:900;margin-top:5px}.card-note{color:#6f8399;font-size:10px;margin-top:4px}
.section{font-size:19px;font-weight:900;color:#fff;margin:24px 0 10px}
.metric{background:#0d1b2c;border:1px solid #203750;border-radius:15px;padding:13px 15px}.metric-name{color:#8499ae;font-size:10px}.metric-value{color:#fff;font-size:19px;font-weight:900;margin-top:3px}
.search-panel{background:#0d1b2c;border:1px solid #24405c;border-radius:19px;padding:16px;margin-bottom:16px}
div[data-testid="stTextInput"] input,div[data-baseweb="select"]>div{background:#081321!important;border:1px solid #2b4560!important;color:#fff!important;border-radius:13px!important;min-height:52px;font-size:15px}
div[data-testid="stButton"]>button{min-height:50px;border-radius:13px;font-family:'Cairo',sans-serif;font-weight:900;border:1px solid #2b4560;background:#12243a;color:#fff;font-size:13px}
div[data-testid="stButton"]>button[kind="primary"]{background:linear-gradient(135deg,#28df84,#19b96b);color:#04130b;border-color:#28df84}
div[data-testid="stDownloadButton"]>button{min-height:50px;border-radius:13px;font-family:'Cairo',sans-serif;font-weight:900}
div[data-testid="stMetric"]{background:#0d1b2c;border:1px solid #203750;padding:13px;border-radius:15px}
[data-testid="stDataFrame"]{border:1px solid #203750;border-radius:15px;overflow:hidden}
.stAlert{border-radius:14px}footer{visibility:hidden}hr{border-color:#1b3047!important}
.small-note{color:#71869b;font-size:10px;line-height:1.9}
.ai-box{background:#0d2a20;border:1px solid #276046;border-right:4px solid var(--green);border-radius:17px;padding:18px;line-height:2;color:#e6f8ee;font-size:13px}
.nav-status{text-align:center;color:#6f8398;font-size:10px;padding:9px;border-top:1px solid #1b3047;margin-top:10px}
@media(max-width:700px){
.stApp{background:linear-gradient(180deg,#07111f 0%,#081321 100%)}
.main .block-container{padding:8px 10px 92px;max-width:100%}
[data-testid="stSidebar"]{position:fixed!important;z-index:999999;bottom:0;top:auto!important;left:0;right:0;width:100vw!important;height:72px!important;background:#081321;border:0;border-top:1px solid #203750;box-shadow:0 -8px 25px rgba(0,0,0,.45)}
[data-testid="stSidebar"]>div:first-child{padding:4px 5px!important;height:72px}
[data-testid="stSidebar"] .brand,[data-testid="stSidebar"] hr,[data-testid="stSidebar"] .stCaption,.nav-status{display:none!important}
[data-testid="stSidebar"] .stRadio [role="radiogroup"]{display:flex!important;flex-direction:row!important;gap:2px!important;width:100%!important}
[data-testid="stSidebar"] .stRadio [role="radio"]{flex:1!important;height:62px!important;min-height:62px!important;padding:4px 1px!important;border-radius:12px!important;display:flex!important;align-items:center!important;justify-content:center!important;text-align:center!important;font-size:9px!important;line-height:1.25!important}
[data-testid="stSidebar"] .stRadio [role="radio"][aria-checked="true"]{box-shadow:inset 0 2px 0 var(--green)!important}
.app-topbar{margin:2px 2px 12px}.app-name{font-size:18px}.market-pill{font-size:9px;padding:6px 9px}
.hero{border-radius:20px;padding:19px 16px;margin-bottom:12px}.hero-title{font-size:23px}.hero-sub{font-size:11px}
.section{font-size:17px;margin:19px 0 8px}
.card{min-height:0;padding:14px;border-radius:15px}.card-value{font-size:20px}
.metric{padding:10px;border-radius:13px}.metric-value{font-size:16px}
.search-panel{padding:12px;border-radius:16px}
div[data-testid="stButton"]>button,div[data-testid="stDownloadButton"]>button{min-height:50px}
div[data-testid="stTextInput"] input,div[data-baseweb="select"]>div{min-height:52px;font-size:16px}
[data-testid="stHorizontalBlock"]{gap:7px!important}
}
@media(max-width:430px){.hero-title{font-size:21px}.section{font-size:16px}.card-value{font-size:19px}}
</style>
<style>
/* MOBILE APP OVERRIDE */
@media (max-width:700px){
/* remove the web-dashboard feel */
header[data-testid="stHeader"]{height:0!important;background:transparent!important}
[data-testid="stToolbar"],[data-testid="stDecoration"],footer{display:none!important}
.main .block-container{padding:0 12px 105px!important;max-width:none!important}
.stApp{background:#07111f!important}
[data-testid="stSidebar"]{
 display:block!important;position:fixed!important;z-index:100000!important;
 left:0!important;right:0!important;bottom:0!important;top:auto!important;
 width:100%!important;height:78px!important;max-height:78px!important;
 background:rgba(8,19,33,.98)!important;border:0!important;
 border-top:1px solid #29415c!important;box-shadow:0 -12px 35px rgba(0,0,0,.5)!important;
}
[data-testid="stSidebar"]>div:first-child{padding:3px 6px!important;height:78px!important;overflow:hidden!important}
[data-testid="stSidebar"] .brand,
[data-testid="stSidebar"] hr,
[data-testid="stSidebar"] .nav-status,
[data-testid="stSidebar"] [data-testid="stButton"]{display:none!important}
[data-testid="stSidebar"] .stRadio{margin:0!important;padding:0!important}
[data-testid="stSidebar"] .stRadio [role="radiogroup"]{
 display:grid!important;grid-template-columns:repeat(7,1fr)!important;
 gap:3px!important;width:100%!important;height:70px!important;
}
[data-testid="stSidebar"] .stRadio [role="radio"]{
 display:flex!important;align-items:center!important;justify-content:center!important;
 width:auto!important;height:64px!important;min-height:64px!important;
 padding:5px 1px!important;margin:0!important;border-radius:13px!important;
 border:1px solid transparent!important;background:transparent!important;
 color:#71869b!important;font-size:9px!important;font-weight:800!important;
 line-height:1.25!important;text-align:center!important;
}
[data-testid="stSidebar"] .stRadio [role="radio"][aria-checked="true"]{
 background:#102b21!important;color:#83f2b5!important;
 border-color:#24583f!important;box-shadow:none!important;
}
[data-testid="stSidebar"] .stRadio [role="radio"]>div:first-child{display:none!important}

/* app header */
.app-topbar{margin:0 -2px 12px!important;padding:12px 3px 4px!important}
.app-name{font-size:19px!important;font-weight:900!important}
.app-context{font-size:9px!important;color:#71869b!important}
.market-pill{font-size:9px!important;padding:6px 9px!important}

/* hero becomes app dashboard card */
.hero{
 margin:0 0 12px!important;padding:19px 17px!important;
 border-radius:22px!important;border:1px solid #294764!important;
 background:linear-gradient(145deg,#102b46,#0c1828)!important;
 box-shadow:0 10px 28px rgba(0,0,0,.25)!important;
}
.hero-title{font-size:23px!important;line-height:1.35!important}
.hero-sub{font-size:11px!important;line-height:1.8!important}
.badge{font-size:9px!important;margin-top:11px!important}

/* compact app cards */
.section{font-size:16px!important;margin:18px 1px 8px!important}
.card{min-height:0!important;padding:14px!important;border-radius:16px!important}
.card-label{font-size:10px!important}
.card-value{font-size:20px!important;margin-top:3px!important}
.card-note{font-size:9px!important}
.metric{padding:10px!important;border-radius:13px!important}
.metric-name{font-size:9px!important}
.metric-value{font-size:16px!important}

/* controls */
.search-panel{padding:12px!important;border-radius:17px!important}
div[data-testid="stTextInput"] input,
div[data-baseweb="select"]>div{min-height:52px!important;border-radius:14px!important;font-size:16px!important}
div[data-testid="stButton"]>button{min-height:50px!important;border-radius:14px!important}
[data-testid="stHorizontalBlock"]{gap:7px!important}

/* charts/data should fit phone */
[data-testid="stDataFrame"]{max-width:100%!important;overflow:hidden!important}
}

/* extra small phones */
@media (max-width:390px){
 .main .block-container{padding-left:9px!important;padding-right:9px!important}
 .hero{padding:17px 14px!important}
 .hero-title{font-size:21px!important}
 .app-name{font-size:18px!important}
 [data-testid="stSidebar"] .stRadio [role="radio"]{font-size:8px!important}
}
</style>
<style>
/* STRUCTURAL MOBILE APP SHELL */
.app-bottom-nav{display:none}
@media(max-width:700px){
 .main .block-container{padding-bottom:105px!important}
 /* The navigation radio is now part of the page, not a sidebar. */
 div[data-testid="stRadio"]{
   position:fixed!important;left:0!important;right:0!important;bottom:0!important;
   z-index:100000!important;margin:0!important;padding:5px 6px 7px!important;
   background:rgba(8,19,33,.98)!important;border-top:1px solid #29415c!important;
   box-shadow:0 -12px 35px rgba(0,0,0,.5)!important;
   direction:rtl!important;
 }
 div[data-testid="stRadio"]>label{display:none!important}
 div[data-testid="stRadio"] [role="radiogroup"]{
   display:grid!important;grid-template-columns:repeat(7,1fr)!important;
   gap:3px!important;width:100%!important;
 }
 div[data-testid="stRadio"] [role="radio"]{
   display:flex!important;align-items:center!important;justify-content:center!important;
   height:62px!important;min-height:62px!important;padding:4px 1px!important;
   margin:0!important;border-radius:13px!important;border:1px solid transparent!important;
   background:transparent!important;color:#71869b!important;font-size:8px!important;
   font-weight:800!important;line-height:1.25!important;text-align:center!important;
 }
 div[data-testid="stRadio"] [role="radio"][aria-checked="true"]{
   background:#102b21!important;color:#83f2b5!important;border-color:#24583f!important;
 }
 div[data-testid="stRadio"] [role="radio"]>div:first-child{display:none!important}
}
@media(max-width:390px){
 div[data-testid="stRadio"] [role="radio"]{font-size:7px!important}
}

.m-shell{direction:rtl}
.m-card-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:9px;margin:0 0 15px}
.m-card{background:linear-gradient(145deg,#0f2135,#0b1726);border:1px solid #213c56;border-radius:17px;padding:14px 13px;min-height:94px;box-shadow:0 8px 22px rgba(0,0,0,.18)}
.m-label{font-size:10px;color:#8095aa;font-weight:800}
.m-value{font-size:20px;color:#f7fbff;font-weight:900;margin-top:5px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.m-note{font-size:9px;color:#60778d;margin-top:4px;line-height:1.6}
.action-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:9px;margin-bottom:15px}
.action-card{display:flex;align-items:center;gap:10px;background:#0d1b2c;border:1px solid #203750;border-radius:17px;padding:13px;min-height:67px}
.action-icon{width:36px;height:36px;display:flex;align-items:center;justify-content:center;border-radius:12px;background:#102b21;color:#6feaa8;font-size:17px;font-weight:900;flex:0 0 36px}
.action-title{font-size:12px;font-weight:900;color:#fff}
.action-sub{font-size:9px;color:#70869b;margin-top:2px}
.app-strip{display:flex;gap:7px;overflow:hidden;margin:0 0 14px}
.strip-chip{background:#0d1b2c;border:1px solid #203750;border-radius:13px;padding:9px 11px;min-width:92px}
.strip-symbol{font-size:11px;font-weight:900;color:#fff}
.strip-value{font-size:10px;color:#7eeeb0;margin-top:2px}
.premarket{background:linear-gradient(135deg,#0d2a20,#0b1d19);border:1px solid #276046;border-right:4px solid #22d47a;border-radius:19px;padding:15px;margin:0 0 15px}
.premarket-title{font-size:13px;font-weight:900;color:#eafff3}
.premarket-time{font-size:10px;color:#82b69c;margin-top:3px}
.premarket-body{font-size:11px;color:#cde7d9;line-height:1.8;margin-top:8px}
@media(max-width:700px){
 .m-card-grid{gap:8px}
 .m-card{padding:12px;min-height:88px}
 .m-value{font-size:18px}
 .action-card{min-height:63px;padding:11px}
 .action-title{font-size:11px}
 .action-sub{font-size:8px}
 .action-icon{width:33px;height:33px;flex-basis:33px}
 .app-strip{overflow-x:auto;scrollbar-width:none}
 .app-strip::-webkit-scrollbar{display:none}
 [data-testid="stSidebar"]{height:84px!important;max-height:84px!important}
 [data-testid="stSidebar"]>div:first-child{height:84px!important}
 [data-testid="stSidebar"] .stRadio [role="radiogroup"]{height:76px!important;align-items:center!important}
 [data-testid="stSidebar"] .stRadio [role="radio"]{height:68px!important;min-height:68px!important;font-size:8px!important}
}
@media(max-width:390px){
 .m-card{min-height:84px;padding:11px}
 .m-value{font-size:17px}
 .action-title{font-size:10px}
}
</style>
""",
    unsafe_allow_html=True,
)


# -----------------------------
# Mobile app shell helpers
# -----------------------------
def app_card(label, value, note=""):
    return (
        f'<div class="m-card"><div class="m-label">{label}</div>'
        f'<div class="m-value">{value}</div>'
        f'<div class="m-note">{note}</div></div>'
    )

def app_action(icon, title, subtitle):
    return (
        f'<div class="action-card"><div class="action-icon">{icon}</div>'
        f'<div><div class="action-title">{title}</div>'
        f'<div class="action-sub">{subtitle}</div></div></div>'
    )

# -----------------------------
# App navigation
# -----------------------------
# -----------------------------
# In-app navigation dock
# -----------------------------
page = st.radio(
    "NAV",
    ["⌂  الرئيسية","◉  السوق","⌕  تحليل","☆  المتابعة","▣  المحفظة","✦  الفرص","⚙  الإعدادات"],
    key="mobile_page",
    label_visibility="collapsed",
)

st.markdown(
    '<div class="app-topbar"><div><div class="app-name">مدحت ستوكس <span style="color:#22d47a">•</span></div>'
    '<div class="app-context">EGX • تحليل ذكي</div></div>'
    '<div class="market-pill">● السوق</div></div>',
    unsafe_allow_html=True,
)



# -----------------------------
# Dashboard
# -----------------------------
if page == "⌂  الرئيسية":
    last = st.session_state.last_analysis

    st.markdown(
        '<div class="hero"><div class="hero-title">صباح السوق 👋</div>'
        '<div class="hero-sub">مدحت ستوكس — شاشة متابعة EGX قبل القرار، في مكان واحد وبشكل سريع.</div>'
        '<span class="badge">● التحليل قبل افتتاح السوق</span></div>',
        unsafe_allow_html=True,
    )

    if last:
        st.markdown(
            f'<div class="premarket"><div class="premarket-title">تحليل ما قبل الافتتاح</div>'
            f'<div class="premarket-time">آخر جلسة: {last["date"]} • آخر سهم: {last["symbol"].replace(".EGX","")}</div>'
            f'<div class="premarket-body">الحالة <b>{last["status"]}</b> • درجة الفرصة '
            f'<b>{last["opportunity_score"]}</b> • المخاطر <b>{last["risk_score"]}</b>. '
            f'هذه قراءة كمية وصفية وليست توصية شراء أو بيع.</div></div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<div class="premarket"><div class="premarket-title">تحليل ما قبل الافتتاح</div>'
            '<div class="premarket-time">جاهز — لم يتم تشغيل تحليل لسهم بعد</div>'
            '<div class="premarket-body">ابدأ بتحليل سهم من شاشة «تحليل» لتظهر هنا آخر قراءة فعلية.</div></div>',
            unsafe_allow_html=True,
        )

    if last:
        cards = [
            ("السعر", money(last["close"]), "آخر إغلاق"),
            ("التغير", pct(last["change_pct"]), "الجلسة الأخيرة"),
            ("RSI 14", money(last["rsi14"]), "الزخم"),
            ("الفرصة", last["opportunity_score"], "درجة وصفية"),
        ]
    else:
        cards = [
            ("الأسهم المستهدفة", STOCK_UNIVERSE_SIZE, "هدف المنصة"),
            ("المرجع الشرعي", len(SHARIA_SYMBOLS), f"حتى {REFERENCE_DATE}"),
            ("قائمة المتابعة", len(st.session_state.watchlist), "جلسة حالية"),
            ("المحفظة", len(st.session_state.portfolio), "مراكز حالية"),
        ]

    st.markdown('<div class="m-shell"><div class="m-card-grid">', unsafe_allow_html=True)
    for label, value, note in cards:
        st.markdown(app_card(label, value, note), unsafe_allow_html=True)
    st.markdown('</div></div>', unsafe_allow_html=True)

    st.markdown('<div class="section">اختصارات</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="action-grid">'
        + app_action("⌕", "تحليل سهم", "بيانات + مؤشرات + AI")
        + app_action("✦", "الفرص", "الأسهم التي تتابعها")
        + app_action("☆", "قائمة المتابعة", "مراقبة سريعة")
        + app_action("▣", "المحفظة", "مراكزك وقيمتها")
        + '</div>',
        unsafe_allow_html=True,
    )
    q1, q2 = st.columns(2)
    with q1:
        if st.button("⌕ فتح التحليل", use_container_width=True, type="primary"):
            st.session_state.jump_page = "⌕  تحليل"
            st.rerun()
    with q2:
        if st.button("✦ فتح الفرص", use_container_width=True):
            st.session_state.jump_page = "✦  الفرص"
            st.rerun()

    st.markdown('<div class="section">آخر قراءة</div>', unsafe_allow_html=True)
    if last:
        st.markdown(
            f'<div class="m-card-grid">'
            f'{app_card("الدعم", money(last["support"]), "مستوى مقاس")}'
            f'{app_card("المقاومة", money(last["resistance"]), "مستوى مقاس")}'
            f'{app_card("SMA 20", money(last["sma20"]), "متوسط")}'
            f'{app_card("SMA 50", money(last["sma50"]), "متوسط")}'
            f'</div>',
            unsafe_allow_html=True,
        )
    else:
        st.info("لا توجد قراءة أخيرة بعد. استخدم زر «فتح التحليل» للبدء.")

    st.markdown('<div class="section">ماذا يفعل التطبيق؟</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="m-card"><div class="m-label">01 • بيانات</div>'
        '<div class="m-note" style="font-size:12px;color:#dbe6ef">يستقبل بيانات EGX المتاحة ويعرض آخر جلسة مكتملة.</div></div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="m-card" style="margin-top:8px"><div class="m-label">02 • تحليل كمي</div>'
        '<div class="m-note" style="font-size:12px;color:#dbe6ef">SMA وRSI وATR والحجم والدعم والمقاومة والعوائد التاريخية.</div></div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="m-card" style="margin-top:8px"><div class="m-label">03 • شرح ذكي</div>'
        '<div class="m-note" style="font-size:12px;color:#dbe6ef">Gemini يشرح الأرقام والإشارات المتاحة دون اختلاق بيانات أو إصدار أمر تداول.</div></div>',
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
elif page == "☆  المتابعة":
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
elif page == "⌕  تحليل":
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

                st.markdown(
                    '<div class="m-card-grid">'
                    f'{app_card("آخر إغلاق", money(result["close"]), "السعر")}'
                    f'{app_card("التغير", pct(result["change_pct"]), "الجلسة الأخيرة")}'
                    f'{app_card("أعلى سعر", money(result["high"]), "الجلسة")}'
                    f'{app_card("أقل سعر", money(result["low"]), "الجلسة")}'
                    '</div>',
                    unsafe_allow_html=True,
                )

                st.markdown('<div class="section">ملخص التحليل</div>', unsafe_allow_html=True)
                st.markdown(
                    '<div class="m-card-grid">'
                    f'{app_card("الحالة", result["status"], "الوضع الفني")}'
                    f'{app_card("درجة الفرصة", result["opportunity_score"], "وصفية")}'
                    f'{app_card("درجة المخاطر", result["risk_score"], "وصفية")}'
                    f'{app_card("الدعم", money(result["support"]), "مستوى")}'
                    f'{app_card("المقاومة", money(result["resistance"]), "مستوى")}'
                    '</div>',
                    unsafe_allow_html=True,
                )

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
                    st.markdown(
                        '<div class="m-card-grid">'
                        f'{app_card("الشركة", f.get("name", "—"), "الاسم")}'
                        f'{app_card("القطاع", f.get("sector", "—"), "التصنيف")}'
                        f'{app_card("القيمة السوقية", integer(f.get("market_cap")), "Market Cap")}'
                        f'{app_card("P/E", money(f.get("pe")), "مضاعف")}'
                        f'{app_card("عائد التوزيعات", pct(f.get("dividend_yield")), "Dividend Yield")}'
                        '</div>',
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

<style>
@media(min-width:701px){
 div[data-testid="stRadio"]{margin:0 0 14px!important}
 div[data-testid="stRadio"]>label{display:none!important}
 div[data-testid="stRadio"] [role="radiogroup"]{display:flex!important;gap:6px!important;direction:rtl!important}
 div[data-testid="stRadio"] [role="radio"]{padding:8px 12px!important;border-radius:12px!important;background:#0d1b2c!important;border:1px solid #203750!important;color:#91a4b9!important;font-size:11px!important;font-weight:800!important}
 div[data-testid="stRadio"] [role="radio"][aria-checked="true"]{background:#102b21!important;color:#83f2b5!important;border-color:#24583f!important}
 div[data-testid="stRadio"] [role="radio"]>div:first-child{display:none!important}
</style>
