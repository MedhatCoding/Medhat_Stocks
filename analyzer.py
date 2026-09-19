import os
import requests
import json
import pandas as pd
from google import genai

# المفاتيح من Secrets
EODHD_KEY = os.getenv("EODHD_API_KEY")
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# القائمة الكاملة للـ 113 سهم المعتمدة
STOCKS_113 = [
    {"ticker": "CAED.EGX", "name": "القاهرة للخدمات التعليمية"},
    {"ticker": "CLHO.EGX", "name": "مستشفى كليوباترا"},
    {"ticker": "COPR.EGX", "name": "كوبر للاستثمار التجاري"},
    {"ticker": "COSG.EGX", "name": "القاهرة للزيوت والصابون"},
    {"ticker": "CPCI.EGX", "name": "القاهرة للأدوية"},
    {"ticker": "CRST.EGX", "name": "كريستمارك للمقاولات"},
    {"ticker": "DGTZ.EGX", "name": "ديجتايز للاستثمار والتقنية"},
    {"ticker": "EALR.EGX", "name": "العربية لاستصلاح الأراضي"},
    {"ticker": "EDFM.EGX", "name": "مطاحن شرق الدلتا"},
    {"ticker": "AALR.EGX", "name": "العامة لاستصلاح الأراضي"},
    {"ticker": "ACAMD.EGX", "name": "العربية لدارة وتطوير الأصول"},
    {"ticker": "ADIB.EGX", "name": "مصرف أبو ظبي الإسلامي - مصر"},
    {"ticker": "ADRI.EGX", "name": "أراب للتنمية والاستثمار العقاري"},
    {"ticker": "AFMC.EGX", "name": "مطاحن ومخابز الإسكندرية"},
    {"ticker": "AIFI.EGX", "name": "أطلس للاستثمار والصناعات الغذائية"},
    {"ticker": "AJWA.EGX", "name": "أجواء للصناعات الغذائية"},
    {"ticker": "AMES.EGX", "name": "الإسكندرية للخدمات الطبية"},
    {"ticker": "AMOC.EGX", "name": "الإسكندرية للزيوت المعدنية (أموك)"},
    {"ticker": "AMPI.EGX", "name": "نوفيدا للإستثمار والتكنولوجيا"},
    {"ticker": "EFID.EGX", "name": "إيديتا للصناعات الغذائية"},
    {"ticker": "EGAL.EGX", "name": "مصر للألومنيوم"},
    {"ticker": "EGAS.EGX", "name": "غاز مصر"},
    {"ticker": "EHDR.EGX", "name": "المصريين للإسكان والتنمية"},
    {"ticker": "EITP.EGX", "name": "المصرية للمشروعات السياحية"},
    {"ticker": "ELNA.EGX", "name": "النصر لتصنيع الحاصلات الزراعية"},
    {"ticker": "FAITA.EGX", "name": "بنك فيصل الإسلامي - بالدولار"},
    {"ticker": "FCMD.EGX", "name": "فيوتشر كير للصناعات الطبية"},
    {"ticker": "FIRE.EGX", "name": "الأولى للاستثمار والتنمية العقارية"},
    {"ticker": "APPC.EGX", "name": "العبوات الدوائية المتطورة"},
    {"ticker": "APSW.EGX", "name": "العربية وبولفارا للغزل والنسيج"},
    {"ticker": "ARCC.EGX", "name": "العربية للإسمنت"},
    {"ticker": "ATLC.EGX", "name": "التوفيق للتأجير التمويلي"},
    {"ticker": "ATQA.EGX", "name": "مصر الوطنية للصلب - عتاقة"},
    {"ticker": "AXPH.EGX", "name": "الإسكندرية للأدوية"},
    {"ticker": "BIDI.EGX", "name": "بي إي دي للاستثمار والتنمية"},
    {"ticker": "BIGP.EGX", "name": "بي إي جي للتجارة والاستثمار"},
    {"ticker": "BIOC.EGX", "name": "جلاكسو سميث كلاين"},
    {"ticker": "FNAR.EGX", "name": "الفنار للمقاولات"},
    {"ticker": "GIHD.EGX", "name": "الغربية الإسلامية للتنمية العمرانية"},
    {"ticker": "GMCI.EGX", "name": "مجموعة جي أم سي"},
    {"ticker": "GPIM.EGX", "name": "جي بي آي للنمو العمراني"},
    {"ticker": "GTHE.EGX", "name": "جلوبال تليكوم القابضة"},
    {"ticker": "ICFC.EGX", "name": "الدولية للأسمدة والكيماويات"},
    {"ticker": "IEEC.EGX", "name": "المشروعات الصناعية والهندسية"},
    {"ticker": "IFAP.EGX", "name": "الدولية للمحاصيل الزراعية"},
    {"ticker": "INEG.EGX", "name": "المجموعة المتكاملة للأعمال الهندسية"},
    {"ticker": "SMFR.EGX", "name": "سماد مصر - إيجيفرت"},
    {"ticker": "SPIN.EGX", "name": "الإسكندرية للغزل والنسيج"},
    {"ticker": "SPMD.EGX", "name": "سبيد ميديكال"},
    {"ticker": "TANM.EGX", "name": "تنمية للاستثمار العقاري"},
    {"ticker": "UEFM.EGX", "name": "مطاحن مصر العليا"},
    {"ticker": "UPMS.EGX", "name": "الاتحاد الصيدلي"},
    {"ticker": "VERT.EGX", "name": "فرتيكا للصناعة والتجارة"},
    {"ticker": "WKOL.EGX", "name": "وادي كوم امبو"},
    {"ticker": "ZEOT.EGX", "name": "الزيوت المستخلصة ومنتجاتها"},
    {"ticker": "INFI.EGX", "name": "فوديكو"},
    {"ticker": "ISMA.EGX", "name": "الإسماعيلية مصر للدواجن"},
    {"ticker": "ISMQ.EGX", "name": "الحديد والصلب للمناجم والمحاجر"},
    {"ticker": "JUFO.EGX", "name": "جهينة للصناعات الغذائية"},
    {"ticker": "KABO.EGX", "name": "النصر للملابس والمنسوجات - كابو"},
    {"ticker": "MBSC.EGX", "name": "مصر بني سويف للإسمنت"},
    {"ticker": "MCQE.EGX", "name": "مصر للإسمنت - قنا"},
    {"ticker": "MCRO.EGX", "name": "ماكرو جروب"},
    {"ticker": "MFPC.EGX", "name": "موبكو - مصر لإنتاج السماد"},
    {"ticker": "MICH.EGX", "name": "مصر لصناعة الكيماويات"},
    {"ticker": "MILS.EGX", "name": "مطاحن ومخابز شمال القاهرة"},
    {"ticker": "MISR.EGX", "name": "مصر انتركونتننتال للجرانيت"},
    {"ticker": "MKIT.EGX", "name": "المصرية الكويتية للاستثمار"},
    {"ticker": "MMAT.EGX", "name": "مرسى مرسى علم"},
    {"ticker": "MOED.EGX", "name": "المصرية لنظم التعليم الحديثة"},
    {"ticker": "MOSC.EGX", "name": "مصر للزيوت والصابون"},
    {"ticker": "MPCI.EGX", "name": "ممفيس للأدوية"},
    {"ticker": "MPCO.EGX", "name": "المنصورة للدواجن"},
    {"ticker": "MTIE.EGX", "name": "ام ام جروب"},
    {"ticker": "NCCW.EGX", "name": "النصر للأعمال المدنية"},
    {"ticker": "NCGC.EGX", "name": "النيل لحليج الأقطان"},
    {"ticker": "NEDA.EGX", "name": "شمال الصعيد - نيوداب"},
    {"ticker": "NINH.EGX", "name": "مستشفى النزهة الدولي"},
    {"ticker": "OBRI.EGX", "name": "العبور للإستثمار العقاري"},
    {"ticker": "OCPH.EGX", "name": "أكتوبر فارما"},
    {"ticker": "PACH.EGX", "name": "باكين للبويات"},
    {"ticker": "PHGC.EGX", "name": "بريميم هيلثكير جروب"},
    {"ticker": "POUL.EGX", "name": "القاهرة للدواجن"},
    {"ticker": "PRCL.EGX", "name": "الشركة العامة للسيراميك"},
    {"ticker": "RREI.EGX", "name": "الاستثمار العقاري العربي - أليكو"},
    {"ticker": "RUBX.EGX", "name": "روبكس"},
    {"ticker": "SAUD.EGX", "name": "بنك البركة مصر"},
    {"ticker": "SCEM.EGX", "name": "أسمنت سيناء"},
    {"ticker": "SCFM.EGX", "name": "مطاحن جنوب القاهرة"},
    {"ticker": "SIPC.EGX", "name": "سبأ الدولية للأدوية"},
    {"ticker": "SKPC.EGX", "name": "سيدي كرير للبتروكيماويات"},
    {"ticker": "ETEL.EGX", "name": "المصرية للاتصالات"},
    {"ticker": "SWDY.EGX", "name": "السويدي إليكتريك"},
    {"ticker": "TMGH.EGX", "name": "طلعت مصطفى القابضة"},
    {"ticker": "PHDC.EGX", "name": "بالم هيلز للتعمير"},
    {"ticker": "OCDI.EGX", "name": "سوديك"},
    {"ticker": "AUTO.EGX", "name": "جي بي أوتو"},
    {"ticker": "FWRY.EGX", "name": "فوري"},
    {"ticker": "ISPH.EGX", "name": "ابن سينا فارما"},
    {"ticker": "ORWE.EGX", "name": "النساجون الشرقيون"},
    {"ticker": "MNHD.EGX", "name": "مدينة مصر للإسكان (مدينة نصر)"},
    {"ticker": "ORAS.EGX", "name": "أوراسكوم للإنشاءات"},
    {"ticker": "ORHD.EGX", "name": "أوراسكوم للتنمية"},
    {"ticker": "EMFD.EGX", "name": "إعمار مصر"},
    {"ticker": "OLFI.EGX", "name": "عبور لاند"},
    {"ticker": "ABUK.EGX", "name": "أبو قير للأسمدة"},
    {"ticker": "RAYA.EGX", "name": "راية القابضة"},
    {"ticker": "RACC.EGX", "name": "راية لمراكز الاتصال"},
    {"ticker": "TAMD.EGX", "name": "تعليم لخدمات الإدارة"},
    {"ticker": "ETRS.EGX", "name": "إيجيترانس"},
    {"ticker": "ACGC.EGX", "name": "العربية لحليج الأقطان"},
    {"ticker": "ECAP.EGX", "name": "العز للسيراميك - الجوهرة"},
    {"ticker": "FAIT.EGX", "name": "بنك فيصل الإسلامي - بالجنيه"}
]

def fetch_stock_data(ticker):
    """جلب البيانات الفنية وحساب RSI"""
    url = f"https://eodhd.com/api/eod/{ticker}?api_token={EODHD_KEY}&fmt=json"
    try:
        res = requests.get(url, timeout=10)
        if res.status_code == 200:
            df = pd.DataFrame(res.json())
            if not df.empty and 'close' in df.columns:
                df['close'] = pd.to_numeric(df['close'])
                delta = df['close'].diff()
                gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                rs = gain / loss
                df['rsi'] = 100 - (100 / (1 + rs))
                
                latest_price = df['close'].iloc[-1]
                latest_rsi = df['rsi'].iloc[-1]
                return {"price": round(latest_price, 2), "rsi": round(latest_rsi, 2)}
    except Exception as e:
        print(f"خطأ في جلب {ticker}: {e}")
    return None

def analyze_with_gemini(stock_name, ticker, tech_data):
    """تحليل Gemini والصياغة بالعربي"""
    client = genai.Client(api_key=GEMINI_KEY)
    
    prompt = f"""
    أنت محلل مالي خبير في البورصة المصرية.
    قم بتحليل سهم "{stock_name}" ({ticker}):
    - السعر الحالي: {tech_data['price']} جنيه
    - RSI (14): {tech_data['rsi']}

    رد بـ JSON فقط بهذه الحقول المحددة دون زيادة:
    {{
        "recommendation": "دخول قوي / شراء / انتظار / خروج",
        "target": 0.0,
        "stop_loss": 0.0,
        "reason": "سبب فني مختصر جداً بالعربي"
    }}
    """
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config={"response_mime_type": "application/json"}
        )
        return json.loads(response.text)
    except Exception as e:
        print(f"خطأ Gemini لـ {ticker}: {e}")
        return None

def send_telegram(text):
    """إرسال التقرير للتلجرام"""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "HTML"
    }
    requests.post(url, json=payload)

if __name__ == "__main__":
    current_report = "📊 <b>تقرير توصيات أسهم البورصة المصرية المعتمدة</b>\n"
    current_report += "━━━━━━━━━━━━━━━━━━━\n\n"
    
    for item in STOCKS_113:
        data = fetch_stock_data(item["ticker"])
        if data:
            analysis = analyze_with_gemini(item["name"], item["ticker"], data)
            if analysis:
                card = f"📌 <b>{item['name']}</b> ({item['ticker']})\n"
                card += f"💵 <b>السعر:</b> {data['price']} ج.م\n"
                card += f"📊 <b>RSI:</b> {data['rsi']}\n"
                card += f"🎯 <b>التوصية:</b> {analysis.get('recommendation', 'انتظار')}\n"
                card += f"🟢 <b>الهدف:</b> {analysis.get('target', '-')} ج.م\n"
                card += f"🔴 <b>وقف الخسارة:</b> {analysis.get('stop_loss', '-')} ج.م\n"
                card += f"💡 <b>السبب:</b> {analysis.get('reason', '-')}\n"
                card += "-----------------------------------\n\n"
                
                # تقطيع الرسالة إذا تجاوزت حد التلجرام (4000 حرف)
                if len(current_report) + len(card) > 3800:
                    send_telegram(current_report)
                    current_report = card
                else:
                    current_report += card
                    
    if current_report:
        send_telegram(current_report)
        
    print("تم تحليل قائمة الـ 113 سهم وإرسال التقرير العربي المنسق بنجاح!")
