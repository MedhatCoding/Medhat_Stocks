import streamlit as st
import pandas as pd
import os
import requests
from google import genai

# إعدادات الصفحة
st.set_page_config(
    page_page_title="EGX Shariah Stock Analyzer",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# تصميم الداكن المخصص
st.markdown("""
<style>
    .main { background-color: #0e1117; color: #ffffff; }
    .stMetric { background-color: #1f2937; padding: 15px; border-radius: 10px; }
    .stButton>button { background-color: #f59e0b; color: #000000; font-weight: bold; border-radius: 8px; }
</style>
""", unsafe_allow_html=True)

st.title("📊 محلل الأسهم المصرية الشرعية (EGX)")
st.caption("تحليل فني وذكاء اصطناعي مدمج للأسهم الشرعية الـ 113")

# جلب المفاتيح
EODHD_KEY = os.getenv("EODHD_API_KEY") or st.secrets.get("EODHD_API_KEY", "")
GEMINI_KEY = os.getenv("GEMINI_API_KEY") or st.secrets.get("GEMINI_API_KEY", "")

# قائمة الأسهم الشرعية
SHARIAH_STOCKS = ["COPR.EGX", "AMOC.EGX", "SWDY.EGX", "TMGH.EGX"]

selected_stock = st.sidebar.selectbox("اختر السهم للتحليل المباشر:", SHARIAH_STOCKS)

def fetch_data(ticker):
    url = f"https://eodhd.com/api/eod/{ticker}?api_token={EODHD_KEY}&fmt=json"
    try:
        res = requests.get(url)
        if res.status_code == 200:
            df = pd.DataFrame(res.json())
            if not df.empty:
                df['close'] = pd.to_numeric(df['close'])
                delta = df['close'].diff()
                gain = (delta.where(delta > 0, 0)).rolling(14).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
                rs = gain / loss
                df['rsi'] = 100 - (100 / (1 + rs))
                return df
    except Exception as e:
        st.error(f"خطأ في جلب البيانات: {e}")
    return pd.DataFrame()

if st.sidebar.button("تشغيل التحليل الآن"):
    with st.spinner("جاري جلب البيانات وتحليلها بواسطة Gemini..."):
        df = fetch_data(selected_stock)
        if not df.empty:
            latest_price = df['close'].iloc[-1]
            latest_rsi = round(df['rsi'].iloc[-1], 2)
            
            col1, col2 = st.columns(2)
            col1.metric("السعر الحالي", f"{latest_price} EGP")
            col2.metric("مؤشر القوة النسبية (RSI)", latest_rsi)
            
            # رسم بياني للسعر
            st.line_chart(df.set_index('date')['close'].tail(30))
            
            # تحليل Gemini
            if GEMINI_KEY:
                client = genai.Client(api_key=GEMINI_KEY)
                prompt = f"حلل سهم {selected_stock} بسعر {latest_price} وRSI {latest_rsi} وقدم توصية دخول/انتظار وقاط حاسمة باختصار."
                res = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
                st.subheader("💡 توصية الذكاء الاصطناعي")
                st.info(res.text)
        else:
            st.warning("تعذر جلب البيانات لهذا السهم.")
