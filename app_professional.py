import streamlit as st
from data_engine import data_engine

st.set_page_config(page_title="Medhat Stocks AI", page_icon="📊", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;500;600;700;800&display=swap');
html, body, [class*="css"] { font-family: 'Cairo', sans-serif; }
.stApp { background:#0b0f14; color:#e8edf3; }
.main .block-container { direction:rtl; text-align:right; max-width:1500px; padding:28px 36px 50px; }
[data-testid="stSidebar"] { background:#0f141b; border-left:1px solid #202833; border-right:none; }
[data-testid="stSidebar"] * { text-align:right; }
[data-testid="stSidebar"] .stRadio label { color:#b9c3cf; font-weight:600; }
.hero { background:linear-gradient(135deg,#121923 0%,#0d131b 100%); border:1px solid #26313d; border-radius:22px; padding:30px; margin-bottom:24px; }
.hero-title { font-size:32px; font-weight:800; margin:0; color:#f3f6f9; }
.hero-subtitle { color:#8e9baa; margin-top:6px; font-size:14px; }
.section-title { font-size:20px; font-weight:800; margin:25px 0 14px; }
.card { background:#111821; border:1px solid #242f3b; border-radius:18px; padding:20px; min-height:125px; }
.card-label { color:#8996a5; font-size:13px; margin-bottom:8px; }
.card-value { color:#f1f5f8; font-size:27px; font-weight:800; }
.card-note { color:#6f7c8b; font-size:12px; margin-top:4px; }
.status { display:inline-block; padding:5px 11px; border-radius:20px; background:#17241e; color:#70d69a; font-size:12px; font-weight:700; }
.search-box { background:#111821; border:1px solid #26313d; border-radius:18px; padding:22px; margin-bottom:20px; }
.metric-panel { background:#111821; border:1px solid #242f3b; border-radius:18px; padding:18px; text-align:center; }
.metric-name { color:#8794a3; font-size:12px; }
.metric-number { color:#f2f5f8; font-size:24px; font-weight:800; margin-top:4px; }
div[data-testid="stButton"] > button { border-radius:12px; min-height:44px; font-family:'Cairo',sans-serif; font-weight:700; }
div[data-testid="stTextInput"] input { background:#0d131a; border:1px solid #2b3744; border-radius:12px; color:#fff; direction:rtl; text-align:right; }
.stAlert { border-radius:14px; }
footer { visibility:hidden; }
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("## 📊 مدحت ستوكس AI")
    st.caption("تحليل EGX • الأسهم المتوافقة مع الشريعة")
    st.divider()
    page = st.radio("NAVIGATION", ["لوحة التحكم","السوق","الفرص","قائمة المتابعة","المحفظة","البحث والتحليل","الإعدادات"], label_visibility="collapsed")
    st.divider()
    st.caption("محرك التحليل يعمل في الخلفية")
    st.caption("Version 1.0")

if page == "لوحة التحكم":
    st.markdown('<div class="hero"><div class="hero-title">لوحة التحكم</div><div class="hero-subtitle">مركز التحليل الذكي للبورصة المصرية والأسهم المتوافقة مع الشريعة</div><br><span class="status">● النظام متصل</span></div>', unsafe_allow_html=True)
    cards=[("حالة السوق","—","في انتظار محرك السوق"),("الأسهم محل التحليل","113","الكون الشرعي"),("فرص اليوم","—","بعد اكتمال التحليل"),("جودة البيانات","—","لم يتم الفحص الكامل")]
    for col,(label,value,note) in zip(st.columns(4),cards):
        with col: st.markdown(f'<div class="card"><div class="card-label">{label}</div><div class="card-value">{value}</div><div class="card-note">{note}</div></div>',unsafe_allow_html=True)
    st.markdown('<div class="section-title">نظرة السوق</div>',unsafe_allow_html=True)
    for col,name in zip(st.columns(3),["الاتجاه العام","اتساع السوق","التذبذب"]):
        with col: st.markdown(f'<div class="metric-panel"><div class="metric-name">{name}</div><div class="metric-number">—</div></div>',unsafe_allow_html=True)
    st.markdown('<div class="section-title">آخر حالة للنظام</div>',unsafe_allow_html=True)
    st.info("سيتم هنا عرض ملخص التحليل اليومي بعد تشغيل محركات البيانات والتحليل.")

elif page == "السوق":
    st.markdown('<div class="hero"><div class="hero-title">السوق المصري</div><div class="hero-subtitle">نظرة عامة على حالة EGX</div></div>',unsafe_allow_html=True)
    for col,label in zip(st.columns(4),["EGX30","الاتجاه","التذبذب","السيولة"]):
        with col: st.markdown(f'<div class="metric-panel"><div class="metric-name">{label}</div><div class="metric-number">—</div></div>',unsafe_allow_html=True)
    st.markdown('<div class="section-title">خريطة السوق</div>',unsafe_allow_html=True)
    st.info("ستظهر خريطة القطاعات والأسهم بعد اكتمال محرك السوق.")

elif page == "الفرص":
    st.markdown('<div class="hero"><div class="hero-title">الفرص</div><div class="hero-subtitle">الأسهم التي اجتازت مراحل الفحص والتحليل</div></div>',unsafe_allow_html=True)
    st.info("لا يتم عرض فرصة قبل اكتمال شروط التحليل والتأكيد وإدارة المخاطر.")
    st.dataframe({"السهم":[],"الشركة":[],"درجة الفرصة":[],"القرار":[],"المخاطر":[]},use_container_width=True,hide_index=True)

elif page == "قائمة المتابعة":
    st.markdown('<div class="hero"><div class="hero-title">قائمة المتابعة</div><div class="hero-subtitle">الأسهم التي تراقبها</div></div>',unsafe_allow_html=True)
    st.info("يمكن إضافة الأسهم إلى قائمة المتابعة من صفحة البحث والتحليل.")

elif page == "المحفظة":
    st.markdown('<div class="hero"><div class="hero-title">المحفظة</div><div class="hero-subtitle">متابعة المراكز والأداء والمخاطر</div></div>',unsafe_allow_html=True)
    st.info("وحدة المحفظة سيتم تفعيلها بعد اكتمال محرك التحليل والتتبع.")

elif page == "البحث والتحليل":
    st.markdown('<div class="hero"><div class="hero-title">البحث والتحليل</div><div class="hero-subtitle">ابحث عن سهم أو رمز شركة للحصول على بيانات السوق والتحليل</div></div>',unsafe_allow_html=True)
    st.markdown('<div class="search-box">',unsafe_allow_html=True)
    symbol=st.text_input("ابحث عن السهم",placeholder="مثال: COMI",label_visibility="visible")
    analyze=st.button("🔎 تحليل السهم",use_container_width=True)
    st.markdown('</div>',unsafe_allow_html=True)
    if analyze:
        clean_symbol=symbol.strip().upper()
        if not clean_symbol: st.warning("اكتب رمز السهم أولاً.")
        else:
            with st.spinner("جاري جلب بيانات السهم..."):
                result=data_engine.get_latest_price(clean_symbol)
            if result.get("success"):
                st.markdown(f'<div class="hero"><div class="hero-title">{result.get("symbol",clean_symbol)}</div><div class="hero-subtitle">آخر بيانات سعرية متاحة</div></div>',unsafe_allow_html=True)
                values=[("آخر إغلاق",result.get("close","—")),("الافتتاح",result.get("open","—")),("أعلى سعر",result.get("high","—")),("أقل سعر",result.get("low","—"))]
                for col,(label,value) in zip(st.columns(4),values):
                    with col: st.markdown(f'<div class="metric-panel"><div class="metric-name">{label}</div><div class="metric-number">{value}</div></div>',unsafe_allow_html=True)
                st.markdown('<div class="section-title">تفاصيل البيانات</div>',unsafe_allow_html=True)
                d1,d2=st.columns(2)
                with d1: st.write(f"**التاريخ:** {result.get('date','—')}")
                with d2: st.write(f"**حجم التداول:** {result.get('volume','—')}")
                st.markdown('<div class="section-title">التحليل الذكي</div>',unsafe_allow_html=True)
                st.info("سيظهر هنا التحليل الفني والأساسي والفرصة والمخاطر بعد تشغيل محركات التحليل الكاملة.")
            else: st.error("تعذر جلب بيانات السهم. "+str(result.get("error","خطأ غير معروف")))

elif page == "الإعدادات":
    st.markdown('<div class="hero"><div class="hero-title">الإعدادات</div><div class="hero-subtitle">حالة الاتصال ومكونات النظام</div></div>',unsafe_allow_html=True)
    health=data_engine.health_check()
    for col,(label,key,note) in zip(st.columns(2),[("EODHD","eodhd_configured","مصدر بيانات السوق"),("OANOR","oanor_configured","مصدر بيانات إضافي")]):
        with col: st.markdown(f'<div class="card"><div class="card-label">{label}</div><div class="card-value">{"متصل" if health[key] else "غير متصل"}</div><div class="card-note">{note}</div></div>',unsafe_allow_html=True)
    st.markdown('<div class="section-title">حالة النظام</div>',unsafe_allow_html=True)
    st.json(health)
