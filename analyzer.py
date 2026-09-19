import os
import requests
import pandas as pd
from google import genai

# جلب المفاتيح من متغيرات البيئة
OANOR_KEY = os.getenv("OANOR_API_KEY")
EODHD_KEY = os.getenv("EODHD_API_KEY")
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# عينة تجريبية من الأسهم الشرعية للبدء بها
SHARIAH_STOCKS = ["COPR.EGX", "AMOC.EGX", "SWDY.EGX", "TMGH.EGX"]

def fetch_eodhd_data(ticker):
    """جلب البيانات التاريخية وحساب مؤشر RSI"""
    url = f"https://eodhd.com/api/eod/{ticker}?api_token={EODHD_KEY}&fmt=json"
    try:
        res = requests.get(url)
        if res.status_code == 200:
            df = pd.DataFrame(res.json())
            if not df.empty:
                df['close'] = pd.to_numeric(df['close'])
                
                # حساب مؤشر القوة النسبية RSI (14)
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
    """تحليل السهم بواسطة Gemini API للحصول على تقييم مركّب"""
    client = genai.Client(api_key=GEMINI_KEY)
    
    prompt = f"""
    أنت محلل مالي خبير في البورصة المصرية (EGX).
    قم بتحليل السهم التالي وقدم توصية استثمارية مباشرة:
    - السهم: {ticker}
    - السعر الحالي: {tech_data['price']} EGP
    - مؤشر القوة النسبية (RSI 14): {tech_data['rsi']}

    المطلوب رد بصيغة JSON خالية تماماً من أي تنسيق ماركداون وبدون أي نصوص جانبية بالهيكل التالي:
    {{
        "ticker": "{ticker}",
        "score": 85,
        "recommendation": "دخول قوي / شراء / انتظار",
        "entry_price": {tech_data['price']},
        "target_1": 0.0,
        "target_2": 0.0,
        "stop_loss": 0.0,
        "reasoning": "سبب التوصية باختصار شديد"
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

def send_telegram_msg(message):
    """إرسال التقرير النهائي للتلجرام"""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    requests.post(url, json=payload)

if __name__ == "__main__":
    print("=== بدء تحليل الأسهم وإرسال التقرير ===")
    summary_report = "📊 *تقرير التحليل اليومي للأسهم المصرية*\n\n"
    
    for stock in SHARIAH_STOCKS:
        tech = fetch_eodhd_data(stock)
        analysis_raw = analyze_with_gemini(stock, tech)
        
        if analysis_raw:
            summary_report += f"🔹 *السهم:* {stock}\n"
            summary_report += f"💵 *السعر:* {tech['price']} EGP | RSI: {tech['rsi']}\n"
            summary_report += f"📝 *التحليل:* {analysis_raw}\n"
            summary_report += "---------------------\n"
            
    send_telegram_msg(summary_report)
    print("✅ تم إرسال التقرير الكامل إلى التلجرام بنجاح!")
    
