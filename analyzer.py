import os
import requests
import pandas as pd
from google import genai

# المفاتيح
OANOR_KEY = os.getenv("OANOR_API_KEY")
EODHD_KEY = os.getenv("EODHD_API_KEY")
GEMINI_KEY = os.getenv("GEMINI_API_KEY")

# قائمة مصغرة للاختبار من الأسهم الشرعية الـ 113
SHARIAH_STOCKS = ["COPR.EGX", "AMOC.EGX", "SWDY.EGX", "TMGH.EGX"]

def fetch_eodhd_data(ticker):
    """جلب البيانات التاريخية لحساب المؤشرات الفنية"""
    url = f"https://eodhd.com/api/eod/{ticker}?api_token={EODHD_KEY}&fmt=json"
    try:
        res = requests.get(url)
        if res.status_code == 200:
            df = pd.DataFrame(res.json())
            if not df.empty:
                df['close'] = pd.to_numeric(df['close'])
                # حساب مؤشر القوة النسبية RSI مبسط
                delta = df['close'].diff()
                gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                rs = gain / loss
                df['rsi'] = 100 - (100 / (1 + rs))
                
                latest_price = df['close'].iloc[-1]
                latest_rsi = df['rsi'].iloc[-1]
                return {"price": latest_price, "rsi": round(latest_rsi, 2)}
    except Exception as e:
        print(f"خطأ في جلب بيانات {ticker}: {e}")
    return {"price": 0, "rsi": 50}

def analyze_with_gemini(ticker, tech_data):
    """تحليل السهم بواسطة Gemini API للدمج بين الفني والأخبار"""
    client = genai.Client(api_key=GEMINI_KEY)
    
    prompt = f"""
    أنت محلل مالي خبير في Borsa Egypt (EGX).
    قم بتحليل السهم التالي بناءً على البيانات الفنية المتاحة وقدم توصية استثمارية محددة:
    - السهم: {ticker}
    - السعر الحالي: {tech_data['price']} EGP
    - مؤشر القوة النسبية (RSI 14): {tech_data['rsi']}

    المطلوب رد بصيغة JSON خالية من أي نصوص إضافية بالهيكل التالي:
    {{
        "ticker": "{ticker}",
        "score": 85,
        "recommendation": "دخول قوي / شراء / انتظار",
        "entry_price": {tech_data['price']},
        "target_1": 0.0,
        "target_2": 0.0,
        "stop_loss": 0.0,
        "risk_reward_ratio": "1:2",
        "reasoning": "سبب التوصية باختصار"
    }}
    """
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config={"response_mime_type": "application/json"}
        )
        return response.text
    except Exception as e:
        print(f"خطأ في تحليل Gemini للسهم {ticker}: {e}")
        return None

if __name__ == "__main__":
    print("=== بدء عملية التحليل الذكي للأسهم ===")
    for stock in SHARIAH_STOCKS:
        tech = fetch_eodhd_data(stock)
        print(f"\n[+] جاري تحليل {stock}...")
        analysis = analyze_with_gemini(stock, tech)
        print(analysis)
              
