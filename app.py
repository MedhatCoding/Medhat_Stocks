import os
import json
from pathlib import Path
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
# Personal persistence
# -----------------------------
# Personal-use only: no accounts or database.
PERSONAL_DATA_FILE = Path(__file__).with_name("personal_data.json")

def load_personal_data():
    try:
        if PERSONAL_DATA_FILE.exists():
            data = json.loads(PERSONAL_DATA_FILE.read_text(encoding="utf-8"))
            return {
                "watchlist": list(data.get("watchlist", [])),
                "portfolio": list(data.get("portfolio", [])),
            }
    except (OSError, ValueError, TypeError):
        pass
    return {"watchlist": [], "portfolio": []}

def save_personal_data():
    data = {
        "watchlist": st.session_state.get("watchlist", []),
        "portfolio": st.session_state.get("portfolio", []),
    }
    try:
        PERSONAL_DATA_FILE.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    except OSError:
        pass

_initial_personal_data = load_personal_data()

# -----------------------------
# Session state
# -----------------------------
if "watchlist" not in st.session_state:
    st.session_state.watchlist = _initial_personal_data["watchlist"]
if "portfolio" not in st.session_state:
    st.session_state.portfolio = _initial_personal_data["portfolio"]
if "last_analysis" not in st.session_state:
    st.session_state.last_analysis = None
if "last_ai" not in st.session_state:
    st.session_state.last_ai = None
if "last_fundamentals" not in st.session_state:
    st.session_state.last_fundamentals = None
if "mobile_page" not in st.session_state:
    st.session_state.mobile_page = "⌂  الرئيسية"
if "analysis_nav_symbol" not in st.session_state:
    st.session_state.analysis_nav_symbol = None
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
        save_personal_data()


def remove_watchlist(symbol):
    if symbol in st.session_state.watchlist:
        st.session_state.watchlist.remove(symbol)
        save_personal_data()


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
 .main .block-container{padding-bottom:110px!important}
 /* Real mobile app dock: fixed to the bottom of the viewport. */
 div[data-testid="stRadio"]{
   position:fixed!important;left:0!important;right:0!important;bottom:0!important;
   z-index:999999!important;width:100vw!important;height:82px!important;
   margin:0!important;padding:6px 7px 8px!important;
   background:#081321!important;border-top:1px solid #29415c!important;
   box-shadow:0 -14px 35px rgba(0,0,0,.55)!important;
   direction:rtl!important;
 }
 div[data-testid="stRadio"]>label{display:none!important}
 div[data-testid="stRadio"]>div{width:100%!important;margin:0!important;padding:0!important}
 div[data-testid="stRadio"] [role="radiogroup"]{
   display:grid!important;grid-template-columns:repeat(7,minmax(0,1fr))!important;
   gap:2px!important;width:100%!important;height:68px!important;
   margin:0!important;padding:0!important;
 }
 div[data-testid="stRadio"] [role="radio"]{
   display:flex!important;align-items:center!important;justify-content:center!important;
   width:100%!important;height:66px!important;min-height:66px!important;
   padding:5px 1px!important;margin:0!important;border-radius:13px!important;
   border:1px solid transparent!important;background:transparent!important;
   color:#71869b!important;font-size:8px!important;font-weight:800!important;
   line-height:1.25!important;text-align:center!important;white-space:normal!important;
 }
 div[data-testid="stRadio"] [role="radio"]>div{display:flex!important;align-items:center!important;justify-content:center!important}
 div[data-testid="stRadio"] [role="radio"]>div:first-child{display:none!important}
 div[data-testid="stRadio"] [role="radio"][aria-checked="true"]{
   background:#102b21!important;color:#83f2b5!important;
   border-color:#24583f!important;
 }
 /* Streamlit versions that render options as labels instead of role=radio. */
 div[data-testid="stRadio"] label{
   display:flex!important;align-items:center!important;justify-content:center!important;
   text-align:center!important;
 }
}
@media(max-width:390px){
 div[data-testid="stRadio"] [role="radio"]{font-size:7px!important}
}

.m-shell{direction:rtl}
.m-card-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:9px;margin:0 0 15px}
.m-card{background:linear-gradient(145deg,#0f2135,#0b1726);border:1px solid #213c56;border-radius:17px;padding:14px 13px;min-height:94px;box-shadow:0 8px 22px rgba(0,0,0,.18)}
.m-label{font-size:10px;color:#8095aa;font-weight:800}
.m-value{font-size:20px;color:#f7fbff;font-weight:900;margin-top:5px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.m-value.up,.price-change.up{color:var(--green)!important}.m-value.down,.price-change.down{color:var(--red)!important}.price-change.flat{color:#91a4b9!important;font-size:11px}.m-value.flat{color:#f7fbff}
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
.scenario-mini{background:#0a1624;border:1px solid #203750;border-radius:14px;padding:11px 13px;margin:8px 0 12px;color:#c8d6e5;font-size:11px;line-height:1.9}.scenario-mini b{color:#fff}
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
<style>
/* AUTHORITATIVE APP NAVIGATION — no radio, no sidebar */
[data-testid="stSidebar"]{display:none!important}
.st-key-bottom_nav{
  position:relative!important;
  width:100%!important;
  margin:0 0 14px!important;
  z-index:50!important;
}
.st-key-bottom_nav button{
  min-height:48px!important;
  border-radius:12px!important;
  background:#0d1b2c!important;
  border:1px solid #203750!important;
  color:#91a4b9!important;
  font-family:'Cairo',sans-serif!important;
  font-size:10px!important;
  font-weight:900!important;
  line-height:1.2!important;
  white-space:pre-line!important;
}
@media(max-width:700px){
  .main .block-container{padding-bottom:105px!important}
  .st-key-bottom_nav{
    position:fixed!important;
    left:0!important;
    right:0!important;
    bottom:0!important;
    width:100vw!important;
    margin:0!important;
    padding:7px 6px 8px!important;
    background:#081321!important;
    border-top:1px solid #29415c!important;
    box-shadow:0 -14px 35px rgba(0,0,0,.55)!important;
    z-index:999999!important;
    direction:rtl!important;
  }
  .st-key-bottom_nav>div{
    width:100%!important;
    margin:0!important;
  }
  .st-key-bottom_nav [data-testid="stHorizontalBlock"]{
    display:grid!important;
    grid-template-columns:repeat(7,minmax(0,1fr))!important;
    gap:3px!important;
    width:100%!important;
    margin:0!important;
  }
  .st-key-bottom_nav [data-testid="column"]{
    width:auto!important;
    min-width:0!important;
    flex:1 1 0!important;
  }
  .st-key-bottom_nav button{
    width:100%!important;
    height:68px!important;
    min-height:68px!important;
    padding:4px 1px!important;
    border-radius:13px!important;
    border:1px solid transparent!important;
    background:transparent!important;
    color:#71869b!important;
    font-size:8px!important;
  }
  .st-key-bottom_nav button:hover{
    border-color:#24583f!important;
    color:#83f2b5!important;
  }
}
@media(min-width:701px){
  .st-key-bottom_nav{
    display:flex!important;
    justify-content:flex-start!important;
  }
  .st-key-bottom_nav [data-testid="stHorizontalBlock"]{gap:6px!important}
}
</style>

""",
    unsafe_allow_html=True,
)


# -----------------------------
# Mobile app shell helpers
# -----------------------------
def value_class(value):
    try:
        n = float(value)
        return "up" if n > 0 else ("down" if n < 0 else "flat")
    except (TypeError, ValueError):
        return "flat"

def app_card(label, value, note="", tone="flat"):
    return (
        f'<div class="m-card"><div class="m-label">{label}</div>'
        f'<div class="m-value {tone}">{value}</div>'
        f'<div class="m-note">{note}</div></div>'
    )

def price_card(label, price, change=None, note=""):
    tone = value_class(change)
    change_text = f" • {pct(change)}" if change is not None else ""
    return (
        f'<div class="m-card"><div class="m-label">{label}</div>'
        f'<div class="m-value">{money(price)} <span class="price-change {tone}">{change_text}</span></div>'
        f'<div class="m-note">{note}</div></div>'
    )

def company_display_name(result, fallback="الشركة"):
    fundamentals = result.get("fundamentals") or {}
    name = fundamentals.get("name")
    if name and str(name).strip():
        return str(name).strip()
    return fallback

def friendly_error(message):
    text = str(message or "")
    if "404" in text or "Trigger Not Found" in text:
        return "تعذر جلب بيانات السوق الآن. جرّب تحديث الصفحة بعد قليل؛ المشكلة من مصدر البيانات وليست من تصميم التطبيق."
    return text

def app_action(icon, title, subtitle):
    return (
        f'<div class="action-card"><div class="action-icon">{icon}</div>'
        f'<div><div class="action-title">{title}</div>'
        f'<div class="action-sub">{subtitle}</div></div></div>'
    )

# -----------------------------
# App navigation
# -----------------------------
# Real app navigation: seven actual buttons in a fixed bottom dock on mobile.
NAV_ITEMS = [
    ("⌂", "الرئيسية"),
    ("◉", "السوق"),
    ("⌕", "تحليل"),
    ("☆", "المتابعة"),
    ("▣", "المحفظة"),
    ("✦", "الفرص"),
    ("⚙", "الإعدادات"),
]
with st.container(key="bottom_nav"):
    nav_cols = st.columns(7, gap="small")
    for nav_col, (icon, label) in zip(nav_cols, NAV_ITEMS):
        with nav_col:
            if st.button(f"{icon}\n{label}", key=f"nav_{label}", use_container_width=True):
                st.session_state.mobile_page = f"{icon}  {label}"
                st.rerun()

page = st.session_state.mobile_page

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
    st.markdown(
        '<div class="hero"><div class="hero-title">صباح السوق 👋</div>'
        '<div class="hero-sub">شاشة EGX قبل الافتتاح: حالة السوق، آخر جلسة مكتملة، والفرص المؤهلة في مكان واحد.</div>'
        '<span class="badge">● التحليل قبل افتتاح السوق</span></div>',
        unsafe_allow_html=True,
    )

    with st.spinner("جاري تجهيز تقرير ما قبل الافتتاح..."):
        premarket = data_engine.get_premarket_report(limit=5)

    if premarket.get("success"):
        market = premarket["market"]
        market_regime = market.get("regime", "غير متاح")
        st.markdown(
            f'<div class="premarket"><div class="premarket-title">تقرير ما قبل الافتتاح</div>'
            f'<div class="premarket-time">آخر جلسة مكتملة: {premarket.get("latest_session_date","—")} • '
            f'وقت القاهرة: {premarket.get("time","—")}</div>'
            f'<div class="premarket-body">حالة EGX30: <b>{market_regime}</b> • '
            f'قيمة المؤشر: <b>{money(market.get("close"))}</b> • '
            f'تغير 20 جلسة: <b>{pct(market.get("return20"))}</b><br>'
            f'الفرص المؤهلة في الفحص: <b>{len(premarket.get("opportunities", []))}</b> • '
            f'المرجع الشرعي: <b>{premarket.get("sharia_universe_count", len(SHARIA_SYMBOLS))}</b> سهم.</div></div>',
            unsafe_allow_html=True,
        )
        if premarket.get("opportunities"):
            st.markdown('<div class="section">الفرص المؤهلة الآن</div>', unsafe_allow_html=True)
            for row in premarket["opportunities"][:5]:
                st.markdown(
                    '<div class="m-card-grid">'
                    f'{app_card("الشركة", data_engine.arabic_company_name(row.get("symbol","—"), row.get("name","اسم الشركة غير متاح")), "رمز التداول: " + row.get("symbol","—"))}'
                    f'{app_card("الفرصة", row.get("opportunity_score","—"), "من 100")}'
                    f'{app_card("الارتداد", row.get("rebound_score","—"), row.get("setup",""))}'
                    f'{app_card("المخاطر", row.get("risk_score","—"), "من 100")}'
                    '</div>',
                    unsafe_allow_html=True,
                )
                if st.button(f'🔎 تحليل السهم', key=f'home_analyze_{row.get("symbol","")}', use_container_width=True, type="primary"):
                    st.session_state.mobile_page = "⌕  تحليل"
                    st.session_state.prefill_symbol = row.get("symbol","")
                    st.session_state.analysis_nav_symbol = row.get("symbol","")
                    st.session_state.analysis_autorun = True
                    st.rerun()
        else:
            st.info("لا توجد حالياً فرصة تستوفي شروط الفحص؛ التطبيق لا يعرض فرصة مصطنعة.")
    else:
        st.error(friendly_error(premarket.get("error", "تعذر تجهيز تقرير ما قبل الافتتاح.")))

    last = st.session_state.last_analysis
    cards = [
        ("الأسهم المستهدفة", STOCK_UNIVERSE_SIZE, "هدف المنصة"),
        ("المرجع الشرعي", len(SHARIA_SYMBOLS), f"حتى {REFERENCE_DATE}"),
        ("قائمة المتابعة", len(st.session_state.watchlist), "محفوظة تلقائيًا"),
        ("المحفظة", len(st.session_state.portfolio), "مراكز محفوظة"),
    ]
    if last:
        cards = [
            ("آخر إغلاق", money(last.get("close")), last.get("symbol","").replace(".EGX","")),
            ("التغير", pct(last.get("change_pct")), "الجلسة الأخيرة"),
            ("RSI 14", money(last.get("rsi14")), "الزخم"),
            ("درجة الفرصة", last.get("final_opportunity_score", last.get("opportunity_score","—")), "السيناريو الحالي"),
        ]

    st.markdown('<div class="m-shell"><div class="m-card-grid">', unsafe_allow_html=True)
    for label, value, note in cards:
        st.markdown(app_card(label, value, note), unsafe_allow_html=True)
    st.markdown('</div></div>', unsafe_allow_html=True)

    st.markdown('<div class="section">اختصارات</div>', unsafe_allow_html=True)
    q1, q2 = st.columns(2)
    with q1:
        if st.button("⌕ فتح التحليل", use_container_width=True, type="primary"):
            st.session_state.mobile_page = "⌕  تحليل"
            st.rerun()
    with q2:
        if st.button("✦ فتح الفرص", use_container_width=True):
            st.session_state.mobile_page = "✦  الفرص"
            st.rerun()

    if last:
        st.markdown('<div class="section">آخر قراءة</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="m-card-grid">'
            f'{app_card("الدعم", money(last.get("support")), "مستوى")}'
            f'{app_card("المقاومة", money(last.get("resistance")), "مستوى")}'
            f'{app_card("هدف 1", money(last.get("target1")), "ATR")}'
            f'{app_card("إلغاء", money(last.get("invalidation")), "السيناريو")}'
            '</div>',
            unsafe_allow_html=True,
        )


# -----------------------------
# Market
# -----------------------------
elif page == "◉  السوق":
    st.markdown(
        '<div class="hero"><div class="hero-title">السوق المصري</div>'
        '<div class="hero-sub">حالة EGX30 مستقلة عن تحليل سهم بعينه، مع آخر جلسة مكتملة واتجاه متوسطات السوق.</div></div>',
        unsafe_allow_html=True,
    )
    with st.spinner("جاري قراءة حالة EGX30..."):
        market = data_engine.get_market_context()
    if not market.get("success"):
        st.error(market.get("error", "تعذر قراءة السوق."))
    else:
        st.markdown(
            f'<div class="premarket"><div class="premarket-title">حالة السوق</div>'
            f'<div class="premarket-time">آخر جلسة مكتملة: {market.get("date","—")}</div>'
            f'<div class="premarket-body">EGX30: <b>{money(market.get("close"))}</b> • '
            f'SMA20: <b>{money(market.get("sma20"))}</b> • SMA50: <b>{money(market.get("sma50"))}</b> • '
            f'العائد 20 جلسة: <b>{pct(market.get("return20"))}</b> • '
            f'النظام: <b>{market.get("regime","—")}</b></div></div>',
            unsafe_allow_html=True,
        )
        last = st.session_state.last_analysis
        if last:
            st.markdown('<div class="section">آخر سهم تم تحليله</div>', unsafe_allow_html=True)
            st.markdown(
                '<div class="m-card-grid">'
                f'{app_card("الشركة", data_engine.arabic_company_name(last.get("symbol","—"), last.get("symbol","—")), "رمز التداول: " + last.get("symbol","—"))}'
                f'{app_card("RSI", money(last.get("rsi14")), "14 جلسة")}'
                f'{app_card("الفرصة", last.get("final_opportunity_score",last.get("opportunity_score","—")), "من 100")}'
                f'{app_card("المخاطر", last.get("risk_score","—"), "من 100")}'
                '</div>',
                unsafe_allow_html=True,
            )


# -----------------------------
# Opportunities
# -----------------------------
elif page == "✦  الفرص":
    st.markdown(
        '<div class="hero"><div class="hero-title">الفرص والتوصيات التحليلية</div>'
        '<div class="hero-sub">فحص آلي لأسهم EGX من القائمة الشرعية المرجعية، مع درجة فرصة، ارتداد، مخاطر، وسيناريو سعري محسوب من ATR. ليست أمراً بالشراء أو البيع.</div></div>',
        unsafe_allow_html=True,
    )

    with st.spinner("جاري فحص الأسهم المرشحة وتحليل السوق والأخبار..."):
        opportunities = data_engine.get_opportunities(limit=20)

    if not opportunities.get("success"):
        st.error(opportunities.get("error", "تعذر تشغيل فحص الفرص."))
    elif not opportunities.get("data"):
        st.info("لا توجد حالياً فرصة تستوفي شروط الفحص. هذا أفضل من عرض سهم بلا إشارة كافية.")
    else:
        market = opportunities.get("market", {})
        if market.get("success"):
            st.markdown(
                f'<div class="premarket"><div class="premarket-title">حالة السوق قبل الافتتاح</div>'
                f'<div class="premarket-time">آخر جلسة مكتملة: {market.get("date","—")} • EGX30: {money(market.get("close"))}</div>'
                f'<div class="premarket-body">النظام يدمج حالة السوق مع التحليل الفني والأخبار والفلترة الشرعية.</div></div>',
                unsafe_allow_html=True,
            )

        st.markdown('<div class="section">المرشحون اليوم</div>', unsafe_allow_html=True)
        for i, row in enumerate(opportunities["data"][:10], 1):
            symbol = row.get("symbol", "—")
            sharia = row.get("sharia_compliant") is True
            st.markdown(
                f'<div class="m-card-grid">'
                f'{app_card("الشركة", data_engine.arabic_company_name(symbol, row.get("name","اسم الشركة غير متاح")), "رمز التداول: " + symbol)}'
                f'{price_card("السعر الحالي", row.get("close"), row.get("change_pct"), "آخر سعر متاح")}'
                f'{app_card("نسبة التغير", pct(row.get("change_pct")), "الجلسة الأخيرة", value_class(row.get("change_pct")))}'
                f'{app_card("الفرصة", row.get("opportunity_score","—"), "من 100")}'
                f'{app_card("المخاطر", row.get("risk_score","—"), "من 100")}'
                f'</div>',
                unsafe_allow_html=True,
            )
            c1, c2, c3 = st.columns(3)
            with c1:
                st.metric("مرجع الدخول", money(row.get("entry_reference")))
            with c2:
                st.metric("هدف 1 ATR", money(row.get("target1")))
            with c3:
                st.metric("إلغاء السيناريو", money(row.get("invalidation")))
            st.markdown(
                f'<div class="m-card-grid">'
                f'{app_card("الدخول", money(row.get("entry_reference")), "مرجع")}'
                f'{app_card("هدف 1", money(row.get("target1")), "ATR")}'
                f'{app_card("هدف 2", money(row.get("target2")), "ATR")}'
                f'{app_card("وقف الخسارة", money(row.get("stop")), "حماية")}'
                f'</div>',
                unsafe_allow_html=True,
            )
            st.caption(
                f"رمز التداول: {symbol} • RSI {money(row.get('rsi14'))} • تغير 20 جلسة {pct(row.get('return20'))} • "
                f"نسبة الحجم {money(row.get('volume_ratio'))} • الأخبار {money(row.get('news_score'))}"
            )
            a1, a2 = st.columns(2)
            with a1:
                if st.button("🔎 تحليل السهم", key=f"opp_analyze_{symbol}_{i}", use_container_width=True, type="primary"):
                    st.session_state.analysis_nav_symbol = symbol
                    st.session_state.analysis_autorun = True
                    st.session_state.mobile_page = "⌕  تحليل"
                    st.rerun()
            with a2:
                if st.button("⭐ إضافة للمتابعة", key=f"opp_watch_{symbol}_{i}", use_container_width=True):
                    add_watchlist(symbol)
                    st.success(f"تمت إضافة {data_engine.arabic_company_name(symbol, symbol)} لقائمة المتابعة.")
            st.markdown("---")

        ml_rows = [x for x in opportunities.get("data", []) if x.get("ml_probability") is not None]
        if ml_rows:
            avg_ml = sum(float(x["ml_probability"]) for x in ml_rows) / len(ml_rows)
            st.markdown(
                f'<div class="premarket"><div class="premarket-title">🧠 التعلم الآلي</div>'
                f'<div class="premarket-body">النموذج يتعلم من السلوك التاريخي لكل سهم ويؤثر تدريجيًا في درجة الفرصة. '
                f'متوسط الاحتمال التاريخي في المرشحين الحاليين: <b>{avg_ml:.1f}%</b>.</div></div>',
                unsafe_allow_html=True,
            )

        if st.button("📨 إرسال فرص اليوم إلى Telegram", use_container_width=True):
            lines = ["📊 <b>مدحت ستوكس AI — فرص اليوم</b>", f"عدد الفرص: {len(opportunities.get('data', []))}"]
            for row in opportunities.get("data", [])[:10]:
                name = data_engine.arabic_company_name(row.get("symbol",""), row.get("name",""))
                ml = row.get("ml_probability")
                ml_text = f" • ML: {ml:.1f}%" if ml is not None else ""
                lines.append(
                    f"\n<b>{name}</b> ({row.get('symbol','—')})\n"
                    f"السعر: {money(row.get('close'))} • التغير: {pct(row.get('change_pct'))}\n"
                    f"الفرصة: {row.get('opportunity_score','—')}/100 • المخاطر: {row.get('risk_score','—')}{ml_text}\n"
                    f"الدخول المرجعي: {money(row.get('entry_reference'))} • الهدف 1: {money(row.get('target1'))} • الإلغاء: {money(row.get('invalidation'))}"
                )
            ok, msg = send_telegram("\n".join(lines))
            st.success(msg) if ok else st.error(msg)

        st.markdown('<div class="section">لماذا ظهر هذا السهم؟</div>', unsafe_allow_html=True)
        st.info(
            "المرشح يُبنى من الاتجاه الفني، مؤشرات الارتداد، المخاطر، حالة EGX30، "
            "والمشاعر الخبرية عند توفرها. لا يتم اعتبار السهم فرصة مؤهلة إلا بعد اجتياز شروط الفحص."
        )

        st.markdown('<div class="section">كل نتائج الفحص</div>', unsafe_allow_html=True)
        table = pd.DataFrame(opportunities["data"])
        if "symbol" in table.columns:
            table["اسم الشركة"] = table["symbol"].apply(
                lambda s: data_engine.arabic_company_name(s, str(s))
            )
        cols = [c for c in [
            "اسم الشركة", "opportunity_score", "rebound_score", "risk_score",
            "rsi14", "return20", "volume_ratio", "news_score", "setup"
        ] if c in table.columns]
        st.dataframe(table[cols], use_container_width=True, hide_index=True)


# -----------------------------
# Watchlist
# -----------------------------
elif page == "☆  المتابعة":
    st.markdown(
        '<div class="hero"><div class="hero-title">قائمة المتابعة</div>'
        '<div class="hero-sub">تابع السعر، التغير، RSI، الفرصة والمخاطر لكل سهم أضفته.</div></div>',
        unsafe_allow_html=True,
    )
    if not st.session_state.watchlist:
        st.info("لا توجد أسهم بعد. أضف سهماً من صفحة التحليل أو الفرص.")
    else:
        for i, symbol in enumerate(list(st.session_state.watchlist)):
            result = data_engine.get_full_analysis(symbol)
            if result.get("success"):
                st.markdown(
                    '<div class="m-card-grid">'
                    f'{app_card("الشركة", data_engine.arabic_company_name(symbol, symbol), "رمز التداول: " + symbol)}'
                    f'{app_card("السعر", money(result.get("close")), "آخر إغلاق")}'
                    f'{app_card("التغير", pct(result.get("change_pct")), "الجلسة الأخيرة")}'
                    f'{app_card("الفرصة", result.get("final_opportunity_score","—"), "من 100")}'
                    f'{app_card("RSI", money(result.get("rsi14")), "14")}'
                    f'{app_card("المخاطر", result.get("risk_score","—"), "من 100")}'
                    '</div>',
                    unsafe_allow_html=True,
                )
            else:
                st.warning(f"{symbol}: {friendly_error(result.get('error','تعذر التحليل'))}")
            if st.button(f"✕ إزالة {symbol}", key=f"watch_remove_{symbol}_{i}", use_container_width=True):
                remove_watchlist(symbol)
                st.rerun()


# -----------------------------
# Portfolio
# -----------------------------
elif page == "▣  المحفظة":
    st.markdown(
        '<div class="hero"><div class="hero-title">المحفظة</div>'
        '<div class="hero-sub">أدخل مراكزك، وسنحسب القيمة الحالية والربح/الخسارة باستخدام آخر سعر متاح.</div></div>',
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
        submitted = st.form_submit_button("إضافة / تحديث مركز", use_container_width=True)
        if submitted:
            symbol = data_engine.display_symbol(p_symbol)
            if symbol and p_qty > 0 and p_avg > 0:
                existing = next((x for x in st.session_state.portfolio if x["symbol"] == symbol), None)
                if existing:
                    existing["qty"] = p_qty
                    existing["avg"] = p_avg
                else:
                    st.session_state.portfolio.append({"symbol": symbol, "qty": p_qty, "avg": p_avg})
                st.success("تم حفظ المركز.")
            else:
                st.warning("أدخل الرمز والكمية ومتوسط التكلفة.")

    if st.session_state.portfolio:
        rows = []
        total_cost = 0.0
        total_value = 0.0
        for i, pos in enumerate(st.session_state.portfolio):
            latest = data_engine.get_latest_price(pos["symbol"])
            price = latest.get("close") if latest.get("success") else None
            value = price * pos["qty"] if price is not None else None
            cost = pos["avg"] * pos["qty"]
            pnl = value - cost if value is not None else None
            total_cost += cost
            if value is not None:
                total_value += value
            rows.append({
                "الشركة": data_engine.arabic_company_name(pos["symbol"], pos["symbol"]), "الرمز": pos["symbol"], "الكمية": pos["qty"], "متوسط الدخول": money(pos["avg"]),
                "السعر الحالي": money(price), "التغير %": pct(latest.get("change_pct")) if latest.get("success") else "—",
                "القيمة الحالية": money(value), "الربح/الخسارة": money(pnl),
            })
            if st.button(f"✕ إزالة {pos['symbol']}", key=f"portfolio_remove_{pos['symbol']}_{i}", use_container_width=True):
                st.session_state.portfolio.pop(i)
                save_personal_data()
                st.rerun()
        pnl_total = total_value - total_cost if total_value else None
        st.markdown('<div class="m-card-grid">'
                    f'{app_card("التكلفة", money(total_cost), "إجمالي التكلفة")}'
                    f'{app_card("القيمة", money(total_value), "القيمة الحالية")}'
                    f'{app_card("الربح/الخسارة", money(pnl_total), "غير محقق")}'
                    f'{app_card("عدد المراكز", len(st.session_state.portfolio), "مركز")}'
                    '</div>', unsafe_allow_html=True)
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
    nav_symbol = st.session_state.pop("analysis_nav_symbol", None)
    if nav_symbol:
        st.session_state.analysis_query = nav_symbol
    elif "analysis_query" not in st.session_state:
        st.session_state.analysis_query = st.session_state.get("prefill_symbol", "")
    query = st.text_input("ابحث عن السهم", key="analysis_query", placeholder="مثال: SWDY أو EGAL", label_visibility="visible")
    suggestions = data_engine.search_symbols(query) if query else []
    if suggestions:
        st.caption("اقتراحات من قائمة EGX:")
        labels = [f"{x['symbol']} — {data_engine.arabic_company_name(x['symbol'], x['name'])}" for x in suggestions[:6]]
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

    if analyze or st.session_state.get("analysis_autorun"):
        st.session_state.analysis_autorun = False
        st.session_state.prefill_symbol = selected_symbol or st.session_state.get("prefill_symbol", "")
        if not selected_symbol:
            selected_symbol = st.session_state.prefill_symbol
        if not selected_symbol:
            st.warning("اكتب رمز السهم أولاً.")
        else:
            with st.spinner("جاري جلب البيانات وتحليل آخر 365 جلسة..."):
                result = data_engine.get_full_analysis(selected_symbol)
            if not result["success"]:
                st.error(friendly_error(result["error"]))
            else:
                st.session_state.last_analysis = result
                st.session_state.last_ai = None
                # IMPORTANT: analysis_query belongs to st.text_input and must never be
                # assigned after that widget has been created. Keep navigation state separate.
                symbol = result["symbol"].replace(".EGX", "")
                sharia_ok = sharia_status(symbol)

                status_class = "gold" if sharia_ok else "red"
                status_text = "✓ موجود في القائمة الشرعية المرجعية" if sharia_ok else "⚠ غير موجود في القائمة الشرعية المرجعية"

                st.markdown(
                    f'<div class="hero"><div class="hero-title">{company_display_name(result, "اسم الشركة غير متاح")}</div>'
                    f'<div class="hero-sub">رمز التداول: {symbol} • آخر جلسة متاحة: {result["date"]}</div>'
                    f'<span class="badge {status_class}">{status_text}</span></div>',
                    unsafe_allow_html=True,
                )

                st.markdown(
                    '<div class="m-card-grid">'
                    f'{price_card("السعر الحالي", result["close"], result.get("change_pct"), "آخر سعر/إغلاق متاح")}'
                    f'{app_card("نسبة التغير", pct(result["change_pct"]), "الجلسة الأخيرة", value_class(result.get("change_pct")))}'
                    f'{app_card("أعلى سعر", money(result["high"]), "الجلسة")}'
                    f'{app_card("أقل سعر", money(result["low"]), "الجلسة")}'
                    '</div>',
                    unsafe_allow_html=True,
                )

                st.markdown('<div class="section">السيناريو التحليلي</div>', unsafe_allow_html=True)
                st.markdown(
                    '<div class="premarket">'
                    f'<div class="premarket-title">{result.get("setup","لا توجد إشارة كافية")}</div>'
                    f'<div class="premarket-body">درجة الفرصة <b>{result.get("final_opportunity_score","—")}/100</b> • '
                    f'الارتداد <b>{result.get("rebound_score","—")}/100</b> • المخاطر <b>{result.get("risk_score","—")}/100</b><br>'
                    f'السعر الحالي: <b>{money(result.get("close"))}</b> • مرجع الدخول: <b>{money(result.get("entry_reference"))}</b><br>'
                    f'المستهدف 1: <b>{money(result.get("target1"))}</b> • المستهدف 2: <b>{money(result.get("target2"))}</b><br>'
                    f'وقف الخسارة: <b>{money(result.get("stop"))}</b> • إلغاء السيناريو: <b>{money(result.get("invalidation"))}</b> • '
                    f'R:R: <b>{money(result.get("risk_reward"))}</b></div>'
                    '</div>', unsafe_allow_html=True,
                )

                ml = result.get("ml", {})
                if ml.get("success"):
                    st.markdown(
                        '<div class="section">🧠 التعلم الآلي</div>'
                        f'<div class="premarket"><div class="premarket-title">احتمال تاريخي محسوب بالنموذج</div>'
                        f'<div class="premarket-body">احتمال تحقق سيناريو +{ml.get("target_pct",3)}% خلال {ml.get("horizon_days",10)} جلسات قبل وقف {ml.get("stop_pct",4)}%: '
                        f'<b>{ml.get("probability","—")}%</b><br>'
                        f'عينات التدريب: <b>{ml.get("samples","—")}</b> • دقة اختبار تاريخي: <b>{ml.get("validation_accuracy","—")}%</b></div></div>',
                        unsafe_allow_html=True,
                    )

                st.markdown('<div class="section">الأخبار</div>', unsafe_allow_html=True)
                news_rows = result.get("news", [])
                if news_rows:
                    for news in news_rows[:5]:
                        title = str(news.get("title") or "بدون عنوان").replace("<","&lt;").replace(">","&gt;")
                        source = str(news.get("source") or "—").replace("<","&lt;").replace(">","&gt;")
                        link = news.get("link") or ""
                        if link:
                            st.markdown(f'**{title}**  \n{source} • {news.get("date","—")} • [فتح الخبر]({link})')
                        else:
                            st.markdown(f'**{title}**  \n{source} • {news.get("date","—")}')
                else:
                    st.info("لا توجد أخبار متاحة لهذا السهم من مزودي البيانات الحاليين.")

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
                            fundamentals = result.get("fundamentals", {})
                            st.session_state.last_fundamentals = fundamentals if fundamentals.get("success") else None
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
        '<div class="hero"><div class="hero-title">الإعدادات وقياس الأداء</div>'
        '<div class="hero-sub">سجل داخلي للتوصيات ونتائجها، مع مؤشرات أداء تاريخية للمعايرة فقط.</div></div>',
        unsafe_allow_html=True,
    )
    try:
        from recommendation_journal import summary, evaluate_open, backtest
        evaluate_open(data_engine.get_stock_history, horizon=10)
        s = summary()
        c1,c2,c3,c4 = st.columns(4)
        c1.metric("إجمالي الإشارات", s["total"])
        c2.metric("المغلقة", s["closed"])
        c3.metric("نسبة النجاح", f'{s["win_rate"]}%' if s["win_rate"] is not None else "—")
        c4.metric("متوسط العائد", f'{s["avg_return"]}%' if s["avg_return"] is not None else "—")
        st.caption(f'المفتوحة: {s["open"]} • Profit Factor: {s["profit_factor"] if s["profit_factor"] is not None else "—"}')
        if st.button("📊 تشغيل Backtest", use_container_width=True):
            with st.spinner("جاري اختبار القواعد التاريخية..."):
                bt = backtest(data_engine.get_stock_history, SHARIA_SYMBOLS)
            if bt.get("success"):
                st.success(f'العينات: {bt["samples"]} • النجاح: {bt["win_rate"]}% • متوسط العائد: {bt["avg_return"]}% • Profit Factor: {bt["profit_factor"] or "—"}')
            else:
                st.warning(bt.get("reason", "تعذر تشغيل الاختبار."))
        st.info("نتائج الـBacktest وسجل الأداء أدوات قياس تاريخية وليست ضمانًا للنتائج المستقبلية.")
    except Exception as exc:
        st.warning(f"تعذر قراءة سجل الأداء حاليًا: {exc}")

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
        "المحفظة وقائمة المتابعة للاستخدام الشخصي وتُحفظ في ملف personal_data.json داخل بيئة التطبيق. "
        "لا توجد حسابات مستخدمين أو قاعدة بيانات تجارية."
    )

    st.json({
        "version": APP_VERSION,
        "market": "EGX",
        "target_universe": STOCK_UNIVERSE_SIZE,
        "reference_sharia_symbols": len(SHARIA_SYMBOLS),
        "checked_at": health["checked_at"],
    })

