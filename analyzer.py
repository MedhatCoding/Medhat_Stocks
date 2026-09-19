import os
import requests
import pandas as pd
from google import genai

# المفاتيح من Secrets
OANOR_KEY = os.getenv("OANOR_API_KEY")
EODHD_KEY = os.getenv("EODHD_API_KEY")
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# عينة الأسهم الشرعية
SHARIAH_STOCKS = ["COPR.EGX", "AMOC.EGX", "SWDY.EGX", "TMGH.EGX"]

def fetch_stock_data(ticker):
    """جلب الأسعار وحساب المؤشرات الفنية"""
    url = f"https://eodhd.com/api/eod/{ticker}?api_token={EODHD_KEY}&fmt=json"
    try:
        res = requests.get(url)
        if res.status_code == 200:
            df = pd.DataFrame(res.json())
            if not df.empty:
                df['close'] = pd.to_numeric(df['close'])
                
                # حساب RSI (14)
                delta = df['close'].diff()
                gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                rs = gain / loss
                df['rsi'] = 100 - (100 / (1 + rs))
                
                latest_price = df['close'].iloc[-1]
                latest_rsi = df['rsi'].iloc[-1]
                return {"price": latest_price, "rsi": round(latest_rsi, 2)}
    except Exception as e:
        print(f"Error fetching {ticker}: {e}")
    return {"price": 0, "rsi": 50}

def analyze_with_gemini(ticker, tech_data):
    """التحليل الذكي بواسطة Gemini 2.5 Flash"""
    client = genai.Client(api_key=GEMINI_KEY)
    
    prompt = f"""
    أنت محلل مالي خبير في البورصة المصرية (EGX).
    حلل السهم وقدم توصية صريحة:
    - السهم: {ticker}
    - السعر: {tech_data['price']} EGP
    - RSI: {tech_data['rsi']}

    رد بصيغة JSON فقط بهذه البنية:
    {{
        "ticker": "{ticker}",
        "recommendation": "دخول / انتظار / خروج",
        "entry_price": {tech_data['price']},
        "target": 0.0,
        "stop_loss": 0.0,
        "reason": "سبب قصير جداً"
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
        print(f"Gemini error for {ticker}: {e}")
        return None

def send_telegram(text):
    """إرسال التقرير إلى التلجرام"""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "Markdown"
    }
    requests.post(url, json=payload)

if __name__ == "__main__":
    report = "📈 *توصيات الأسهم المصرية اليومية*\n\n"
    for stock in SHARIAH_STOCKS:
        data = fetch_stock_data(stock)
        analysis = analyze_with_gemini(stock, data)
        if analysis:
            report += f"🔹 *{stock}*\nالسعر: {data['price']} EGP | RSI: {data['rsi']}\nالنتيجة: `{analysis}`\n\n"
    
    send_telegram(report)
    print("Done!")
