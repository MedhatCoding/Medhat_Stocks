import streamlit as st
from data_engine import data_engine

st.set_page_config(
    page_title="مدحت ستوكس AI",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
.main .block-container {
    direction: rtl;
    text-align: right;
    padding-top: 2rem;
    padding-bottom: 2rem;
    max-width: 1400px;
}

[data-testid="stSidebar"] {
    direction: rtl;
}

[data-testid="stSidebar"] * {
    text-align: right;
}

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
            <div class="muted">لم يتم الفحص</div>
        </div>
        """, unsafe_allow_html=True)

    st.subheader("تحليل اليوم")

    st.info(
        "بعد تشغيل محرك البيانات سيتم هنا عرض حالة السوق "
        "والفرص التي اجتازت شروط التحليل."
    )


# =========================
# السوق
# =========================

elif page == "السوق":

    st.title("السوق")

    st.info(
        "بيانات السوق الحية سيتم عرضها هنا بعد اكتمال محرك السوق."
    )

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
        "ستظهر هنا الأسهم التي تجتاز محرك التحليل الكامل."
    )

    st.dataframe(
        {
            "السهم": [],
            "الشركة": [],
            "درجة الفرصة": [],
            "القرار": [],
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
    st.info("متابعة المحفظة سيتم تفعيلها في مرحلة لاحقة.")


# =========================
# البحث
