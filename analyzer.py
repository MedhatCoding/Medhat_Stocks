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

# القائمة الكاملة بـ 113 سهم مع تفادي مشاكل الاتجاهات
STOCKS_113 = [
    {"t": "CAED.EGX", "n": "القاهرة للخدمات التعليمية"},
    {"t": "CLHO.EGX", "n": "مستشفى كليوباترا"},
    {"t": "COPR.EGX", "n": "كوبر للاستثمار التجاري"},
    {"t": "COSG.EGX", "n": "القاهرة للزيوت والصابون"},
    {"t": "CPCI.EGX", "n": "القاهرة للأدوية"},
    {"t": "CRST.EGX", "n": "كريستمارك للمقاولات"},
    {"t": "DGTZ.EGX", "n": "ديجتايز للاستثمار والتقنية"},
    {"t": "EALR.EGX", "n": "العربية لاستصلاح الأراضي"},
    {"t": "EDFM.EGX", "n": "مطاحن شرق الدلتا"},
    {"t": "AALR.EGX", "n": "العامة لاستصلاح الأراضي"},
    {"t": "ACAMD.EGX", "n": "العربية لإدارة وتطوير الأصول"},
    {"t": "ADIB.EGX", "n": "مصرف أبو ظبي الإسلامي - مصر"},
    {"t": "ADRI.EGX", "n": "أراب للتنمية والاستثمار العقاري"},
    {"t": "AFMC.EGX", "n": "مطاحن ومخابز الإسكندرية"},
    {"t": "AIFI.EGX", "n": "أطلس للاستثمار والصناعات الغذائية"},
    {"t": "AJWA.EGX", "n": "أجواء للصناعات الغذائية"},
    {"t": "AMES.EGX", "n": "الإسكندرية للخدمات الطبية"},
    {"t": "AMOC.EGX", "n": "الإسكندرية للزيوت المعدنية (أموك)"},
    {"t": "AMPI.EGX", "n": "نوفيدا للإستثمار والتكنولوجيا"},
    {"t": "EFID.EGX", "n": "إيديتا للصناعات الغذائية"},
    {"t": "EGAL.EGX", "n": "مصر للألومنيوم"},
    {"t": "EGAS.EGX", "n": "غاز مصر"},
    {"t": "EHDR.EGX", "n": "المصريين للإسكان والتنمية"},
    {"t": "EITP.EGX", "n": "المصرية للمشروعات السياحية"},
    {"t": "ELNA.EGX", "n": "النصر لتصنيع الحاصلات الزراعية"},
    {"t": "FAITA.EGX", "n": "بنك فيصل الإسلامي - بالدولار"},
    {"t": "FCMD.EGX", "n": "فيوتشر كير للصناعات الطبية"},
    {"t": "FIRE.EGX", "n": "الأولى للاستثمار والتنمية العقارية"},
    {"t": "APPC.EGX", "n": "العبوات الدوائية المتطورة"},
    {"t": "APSW.EGX", "n": "العربية وبولفارا للغزل والنسيج"},
    {"t": "ARCC.EGX", "n": "العربية للإسمنت"},
    {"t": "ATLC.EGX", "n": "التوفيق للتأجير التمويلي"},
    {"t": "ATQA.EGX", "n": "مصر الوطنية للصلب - عتاقة"},
    {"t": "AXPH.EGX", "n": "الإسكندرية للأدوية"},
    {"t": "BIDI.EGX", "n": "بي إي دي للاستثمار والتنمية"},
    {"t": "BIGP.EGX", "n": "بي إي جي للتجارة والاستثمار"},
    {"t": "BIOC.EGX", "n": "جلاكسو سميث كلاين"},
    {"t": "FNAR.EGX", "n": "الفنار للمقاولات"},
    {"t": "GIHD.EGX", "n": "الغربية الإسلامية للتنمية العمرانية"},
    {"t": "GMCI.EGX", "n": "مجموعة جي أم سي"},
    {"t": "GPIM.EGX", "n": "جي بي آي للنمو العمراني"},
    {"t": "GTHE.EGX", "n": "جلوبال تليكوم القابضة"},
    {"t": "ICFC.EGX", "n": "الدولية للأسمدة والكيماويات"},
    {"t": "IEEC.EGX", "n": "المشروعات الصناعية والهندسية"},
    {"t": "IFAP.EGX", "n": "الدولية للمحاصيل الزراعية"},
    {"t": "INEG.EGX", "n": "المجموعة المتكاملة للأعمال الهندسية"},
    {"t": "SMFR.EGX", "n": "سماد مصر - إيجيفرت"},
    {"t": "SPIN.EGX", "n": "الإسكندرية للغزل والنسيج"},
    {"t": "SPMD.EGX", "n": "سبيد ميديكال"},
    {"t": "TANM.EGX", "n": "تنمية للاستثمار العقاري"},
    {"t": "UEFM.EGX", "n": "مطاحن مصر العليا"},
    {"t": "UPMS.EGX", "n": "الاتحاد الصيدلي"},
    {"t": "VERT.EGX", "n": "فرتيكا للصناعة والتجارة"},
    {"t": "WKOL.EGX", "n": "وادي كوم امبو"},
    {"t": "ZEOT.EGX", "n": "الزيوت المستخلصة ومنتجاتها"},
    {"t": "INFI.EGX", "n": "فوديكو"},
    {"t": "ISMA.EGX", "n": "الإسماعيلية مصر للدواجن"},
    {"t": "ISMQ.EGX", "n": "الحديد والصلب للمناجم والمحاجر"},
    {"t": "JUFO.EGX", "n": "جهينة للصناعات الغذائية"},
    {"t": "KABO.EGX", "n": "النصر للملابس والمنسوجات - كابو"},
    {"t": "MBSC.EGX", "n": "مصر بني سويف للإسمنت"},
    {"t": "MCQE.EGX", "n": "مصر للإسمنت - قنا"},
    {"t": "MCRO.EGX", "n": "ماكرو جروب"},
    {"t": "MFPC.EGX", "n": "موبكو - مصر لإنتاج السماد"},
    {"t": "MICH.EGX", "n": "مصر لصناعة الكيماويات"},
    {"t": "MILS.EGX", "n": "مطاحن ومخابز شمال القاهرة"},
    {"t": "MISR.EGX", "n": "مصر انتركونتننتال للجرانيت"},
    {"t": "MKIT.EGX", "n": "المصرية الكويتية للاستثمار"},
    {"t": "MMAT.EGX", "n": "مرسى مرسى علم"},
    {"t": "MOED.EGX", "n": "المصرية لنظم التعليم الحديثة"},
    {"t": "MOSC.EGX", "n": "مصر للزيوت والصابون"},
    {"t": "MPCI.EGX", "n": "ممفيس للأدوية"},
    {"ticker": "MPCO.EGX", "name": "المنصورة للدواجن"},
    {"t": "MTIE.EGX", "n": "ام ام جروب"},
    {"t": "NCCW.EGX", "n": "النصر للأعمال المدنية"},
    {"t": "NCGC.EGX", "n": "النيل لحليج الأقطان"},
    {"t": "NEDA.EGX", "n": "شمال الصعيد - نيوداب"},
    {"t": "NINH.EGX", "n": "مستشفى النزهة الدولي"},
    {"t": "OBRI.EGX", "n": "العبور للإستثمار العقاري"},
    {"t": "OCPH.EGX", "n": "أكتوبر فارما"},
    {"t": "PACH.EGX", "n": "باكين للبويات"},
    {"t": "PHGC.EGX", "n": "بريميم هيلثكير جروب"},
    {"t": "POUL.EGX", "n": "القاهرة للدواجن"},
    {"t": "PRCL.EGX", "n": "الشركة العامة للسيراميك"},
    {"t": "RREI.EGX", "n": "الاستثمار العقاري العربي - أليكو"},
    {"t": "RUBX.EGX", "n": "روبكس"},
    {"t": "SAUD.EGX", "n": "بنك البركة مصر"},
    {"t": "SCEM.EGX", "n": "أسمنت سيناء"},
    {"t": "SCFM.EGX", "n": "مطاحن جنوب القاهرة"},
    {"t": "SIPC.EGX", "n": "سبأ الدولية للأدوية"},
    {"t": "SKPC.EGX", "n": "سيدي كرير للبتروكيماويات"},
    {"t": "ETEL.EGX", "n": "المصرية للاتصالات"},
    {"t": "SWDY.EGX", "n": "السويدي إليكتريك"},
    {"t": "TMGH.EGX", "n": "طلعت مصطفى القابضة"},
    {"t": "PHDC.EGX", "n": "بالم هيلز للتعمير"},
    {"t": "OCDI.EGX", "n": "سوديك"},
    {"t": "AUTO.EGX", "n": "جي بي أوتو"},
    {"t": "FWRY.EGX", "n": "فوري"},
    {"t": "ISPH.EGX", "n": "ابن سينا فارما"},
    {"t": "ORWE.EGX", "n": "النساجون الشرقيون"},
    {"t": "MNHD.EGX", "n": "مدينة مصر للإسكان"},
    {"t": "ORAS.EGX", "n": "أوراسكوم للإنشاءات"},
    {"t": "ORHD.EGX", "n": "أوراسكوم للتنمية"},
    {"t": "EMFD.EGX", "n": "إعمار مصر"},
    {"t": "OLFI.EGX", "n": "عبور لاند"},
    {"t": "ABUK.EGX", "n": "أبو قير للأسمدة"},
    {"t": "RAYA.EGX", "n": "راية القابضة"},
    {"t": "RACC.EGX", "n": "راية لمراكز الاتصال"},
    {"t": "TAMD.EGX", "n": "تعليم لخدمات الإدارة"},
    {"t": "ETRS.EGX", "n": "إيجيترانس"},
    {"t": "ACGC.EGX", "n": "العربية لحليج الأقطان"},
    {"t": "ECAP.EGX", "n": "العز للسيراميك - الجوهرة"},
    {"t": "FAIT.EGX", "n": "بنك فيصل الإسلامي - بالجنيه"}
]

def fetch_stock_data(ticker):
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
                return {"price": round(df['close'].iloc[-1], 2), "rsi": round(df['rsi'].iloc[-1], 2)}
    except Exception as e:
        print(f"Error {ticker}: {e}")
    return None

def analyze_with_gemini(stock_name, ticker, tech_data):
    client = genai.Client(api_key=GEMINI_KEY)
    prompt = f"""
    حلل سهم "{stock_name}" ({ticker}):
    - السعر: {tech_data['price']} جنيه
    - RSI: {tech_data['rsi']}

    رد بـ JSON فقط:
    {{
        "rec": "دخول / شراء / انتظار / خروج",
        "target": 0.0,
        "stop": 0.0,
        "reason": "سبب فني مختصر جداً بالعربي"
    }}
    """
    try:
        res = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config={"response_mime_type": "application/json"}
        )
        return json.loads(res.text)
    except Exception as e:
        print(f"Gemini error {ticker}: {e}")
        return None

def send_telegram(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": text, "parse_mode": "HTML"})

if __name__ == "__main__":
    report = "📊 <b>تقرير الأسهم المصرية المعتمدة</b>\n━━━━━━━━━━━━━━━━━━━\n\n"
    
    for item in STOCKS_113:
        ticker = item.get("t") or item.get("ticker")
        name = item.get("n") or item.get("name")
        
        data = fetch_stock_data(ticker)
        if data:
            ans = analyze_with_gemini(name, ticker, data)
            if ans:
                card = f"📌 <b>{name}</b> ({ticker})\n"
                card += f"💵 <b>السعر:</b> {data['price']} ج.م\n"
                card += f"📊 <b>RSI:</b> {data['rsi']}\n"
                card += f"🎯 <b>التوصية:</b> {ans.get('rec', 'انتظار')}\n"
                card += f"🟢 <b>الهدف:</b> {ans.get('target', '-')} ج.م\n"
                card += f"🔴 <b>وقف الخسارة:</b> {ans.get('stop', '-')} ج.م\n"
                card += f"💡 <b>السبب:</b> {ans.get('reason', '-')}\n"
                card += "-----------------------------------\n\n"
                
                if len(report) + len(card) > 3800:
                    send_telegram(report)
                    report = card
                else:
                    report += card
                    
    if report:
        send_telegram(report)
