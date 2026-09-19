import os
import requests
from google import genai

# 1. جلب المفاتيح من متغيرات البيئة (GitHub Secrets)
OANOR_KEY = os.getenv("OANOR_API_KEY")
EODHD_KEY = os.getenv("EODHD_API_KEY")
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def test_telegram():
    print("--- 1. فحص بوت التلجرام ---")
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": "🚀 أهلاً مدحت! تم اختبار الاتصال بنجاح. مشروع تحليل الأسهم المصرية جاهز للربط والتحليل."
    }
    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            print("✅ Telegram: شغّال وتم إرسال الرسالة بنجاح!")
        else:
            print(f"❌ Telegram: خطأ ({response.status_code}) - {response.text}")
    except Exception as e:
        print(f"❌ Telegram: فشل الاتصال - {e}")

def test_gemini():
    print("\n--- 2. فحص ذكاء Gemini API ---")
    try:
        client = genai.Client(api_key=GEMINI_KEY)
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents="رد بكلمة واحدة فقط: ممتاز",
        )
        print(f"✅ Gemini API: شغّال والاستجابة: {response.text.strip()}")
    except Exception as e:
        print(f"❌ Gemini API: فيه مشكلة - {e}")

def test_eodhd():
    print("\n--- 3. فحص EODHD API ---")
    # اختبار جلب أسعار سهم مثل TMGH
    url = f"https://eodhd.com/api/eod/TMGH.EGX?api_token={EODHD_KEY}&fmt=json"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            print("✅ EODHD API: شغّال وجلب بيانات الأسهم بنجاح!")
        else:
            print(f"❌ EODHD API: خطأ ({response.status_code})")
    except Exception as e:
        print(f"❌ EODHD API: فشل الاتصال - {e}")

if __name__ == "__main__":
    print("=== بدء اختبار كل المفاتيح والخدمات ===\n")
    test_telegram()
    test_gemini()
    test_eodhd()
    print("\n=== اكتمل الفحص ===")
