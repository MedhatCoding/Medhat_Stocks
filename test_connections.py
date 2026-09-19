import os
import requests
from google import genai

OANOR_KEY = os.getenv("OANOR_API_KEY")
EODHD_KEY = os.getenv("EODHD_API_KEY")
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def test_telegram():
    print("--- 1. فحص بوت التلجرام ---")
    print(f"Chat ID المستلم: {TELEGRAM_CHAT_ID}")
    
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": "🚀 أهلاً مدحت! رسالة تجريبية من تطبيق الأسهم المصرية EGX."
    }
    try:
        response = requests.post(url, json=payload)
        res_json = response.json()
        print(f"استجابة التلجرام: {res_json}")
        if res_json.get("ok"):
            print("✅ Telegram: تم إرسال الرسالة بنجاح!")
        else:
            print(f"❌ Telegram: فشل بسبب - {res_json.get('description')}")
    except Exception as e:
        print(f"❌ Telegram: خطأ في الاتصال - {e}")

if __name__ == "__main__":
    test_telegram()
        
