import streamlit as st

st.set_page_config(
    page_title="مدحت ستوكس AI",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
.main-title {
    font-size: 34px;
    font-weight: 700;
    margin-bottom: 5px;
}

.subtitle {
    color: #888;
    font-size: 15px;
    margin-bottom: 25px;
}

.card {
    padding: 20px;
    border-radius: 14px;
    border: 1px solid rgba(128,128,128,.25);
    margin-bottom: 15px;
}

.score {
    font-size: 32px;
    font-weight: 700;
}

.muted {
    color: #888;
    font-size: 13px;
}

/* محتوى التطبيق بالعربي */
.main .block-container {
    direction: rtl;
    text-align: right;
}

/* القائمة الجانبية */
[data-testid="stSidebar"] {
    direction: rtl;
}

[data-testid="stSidebar"] * {
    text-align: right;
}

/* نخلي أزرار الاختيار واضحة */
[data-testid="stSidebar"] [role="radiogroup"] {
    direction: rtl;
}
</style>
""", unsafe_allow_html=True)


# =========================
# القائمة الجانبية
# =========================

with st.sidebar:
    st.markdown("## 📈 مدحت ستوكس AI")
    st.caption("البورصة المصرية • الأسهم المتوافقة مع الشريعة")

    st.divider()

    page = st.radio(
        "القائمة الرئيسية",
        [
            "لوحة التحكم",
            "السوق",
            "الفرص",
            "قائمة المتابعة",
            "المحفظة",
            "البحث والتحليل",
            "الإعدادات",
        ],
    )

    st.divider()

    st.caption("التحليل بالذكاء الاصطناعي يعمل في الخلفية.")
    st.caption("الإصدار 1.0")


# =========================
# لوحة التحكم
# =========================

if page == "لوحة التحكم":

    st.markdown(
        '<div class="main-title">التحليل الذكي للبورصة المصرية</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="subtitle">'
        "منصة مساعدة لتحليل الأسهم المصرية المتوافقة مع الشريعة الإسلامية"
        "</div>",
        unsafe_allow_html=True,
    )

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.markdown("""
        <div class="card">
            <div class="muted">حالة السوق</div>
            <div class="score">—</div>
            <div class="muted">في انتظار البيانات</div>
        </div>
        """, unsafe_allow_html=True)

    with c2:
        st.markdown("""
        <div class="card">
            <div class="muted">الأسهم محل التحليل</div>
            <div class="score">113</div>
            <div class="muted">قائمة الأسهم الشرعية</div>
        </div>
        """, unsafe_allow_html=True)

    with c3:
        st.markdown("""
        <div class="card">
            <div class="muted">الفرص الحالية</div>
            <div class="score">—</div>
            <div class="muted">في انتظار التحليل</div>
        </div>
        """, unsafe_allow_html=True)

    with c4:
        st.markdown("""
        <div class="card">
            <div class="muted">سلامة البيانات</div>
            <div class="score">—</div>
            <div class="muted">لم يتم الاتصال بعد</div>
        </div>
        """, unsafe_allow_html=True)

    st.subheader("تحليل اليوم")

    st.info(
        "محرك التحليل لم يتم ربطه بالبيانات الحقيقية بعد. "
        "سيتم لاحقًا ربط بيانات السوق والتحليل الفني والأساسي "
        "والأخبار والذكاء الاصطناعي وإدارة المخاطر."
    )

    st.subheader("محرك القرارات")

    a, b, c, d, e = st.columns(5)

    with a:
        st.metric("فرصة دخول", "—")

    with b:
        st.metric("تشبع بيعي", "—")

    with c:
        st.metric("قائمة متابعة", "—")

    with d:
        st.metric("لا توجد صفقة", "—")

    with e:
        st.metric("مرفوض", "—")

    st.subheader("أهم الفرص")

    st.dataframe(
        {
            "السهم": [],
            "الشركة": [],
            "القطاع": [],
            "درجة الفرصة": [],
            "القرار": [],
            "المخاطر": [],
        },
        use_container_width=True,
        hide_index=True,
    )


# =========================
# السوق
# =========================

elif page == "السوق":

    st.title("السوق")

    st.info("ستظهر بيانات السوق هنا بعد ربط محرك بيانات البورصة المصرية.")

    a, b, c = st.columns(3)

    with a:
        st.metric("الاتجاه", "—")

    with b:
        st.metric("اتساع السوق", "—")

    with c:
        st.metric("التذبذب", "—")


# =========================
# الفرص
# =========================

elif page == "الفرص":

    st.title("الفرص")

    st.info(
        "سيتم عرض الأسهم التي تجتاز محرك التحليل "
        "بعد فحص السعر والسيولة والأساسيات والأخبار والمخاطر."
    )

    st.dataframe(
        {
            "السهم": [],
            "الشركة": [],
            "الدرجة": [],
            "القرار": [],
            "لماذا الآن؟": [],
            "المخاطر": [],
        },
        use_container_width=True,
        hide_index=True,
    )


# =========================
# قائمة المتابعة
# =========================

elif page == "قائمة المتابعة":

    st.title("قائمة المتابعة")
    st.info("ستظهر هنا الأسهم التي تريد متابعتها.")


# =========================
# المحفظة
# =========================

elif page == "المحفظة":

    st.title("المحفظة")
    st.info("سيتم ربط متابعة المحفظة بعد الانتهاء من محرك التحليل الأساسي.")


# =========================
# البحث والتحليل
# =========================

elif page == "البحث والتحليل":

    st.title("البحث والتحليل")

    st.markdown("""
    ### وضع البحث

    ابحث عن سهم مصري لتحليله.

    سيجمع المحرك بين:

    - بيانات السوق
    - التحليل الفني
    - التحليل الأساسي
    - السيولة
    - القوة النسبية
    - الأخبار
    - تحليل Gemini
    - إدارة المخاطر
    - إشارات التأكيد
    """)

    symbol = st.text_input(
        "رمز السهم",
        placeholder="مثال: COMI",
    )

    if st.button("تحليل السهم"):
        if symbol.strip():
            st.info(
                f"تم إنشاء طلب تحليل للسهم **{symbol.upper()}**."
            )
        else:
            st.warning("اكتب رمز السهم أولًا.")


# =========================
# الإعدادات
# =========================

elif page == "الإعدادات":

    st.title("الإعدادات")

    st.subheader("التحليل")

    st.checkbox("إظهار المؤشرات الفنية", value=False)
    st.checkbox("إظهار تفاصيل تحليل الذكاء الاصطناعي", value=False)
    st.checkbox("تفعيل التقرير اليومي على Telegram", value=True)

    st.divider()

    st.subheader("النظام")

    st.write("مصدر البيانات: لم يتم الاتصال")
    st.write("الذكاء الاصطناعي: Gemini")
    st.write("قاعدة البيانات: لم يتم الاتصال")
    st.write("Telegram: لم يتم الاتصال")

    st.success("واجهة التطبيق جاهزة.")
