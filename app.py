import streamlit as st

st.set_page_config(
    page_title="Medhat Stocks AI",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 1400px;
    }

    .main-title {
        font-size: 34px;
        font-weight: 700;
        margin-bottom: 4px;
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
    """,
    unsafe_allow_html=True,
)

# -------------------------
# Sidebar
# -------------------------

with st.sidebar:
    st.markdown("## 📈 Medhat Stocks AI")
    st.caption("EGX • Sharia-compliant stocks")

    st.divider()

    page = st.radio(
        "Navigation",
        [
            "Dashboard",
            "Market",
            "Opportunities",
            "Watchlist",
            "Portfolio",
            "Research",
            "Settings",
        ],
    )

    st.divider()

    st.caption("AI analysis runs in the background.")
    st.caption("Version 1.0")

# -------------------------
# Dashboard
# -------------------------

if page == "Dashboard":

    st.markdown(
        '<div class="main-title">Egyptian Stock Market AI</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="subtitle">'
        "AI-assisted analysis of Sharia-compliant EGX stocks"
        "</div>",
        unsafe_allow_html=True,
    )

    # Market overview
    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.markdown(
            '<div class="card">'
            '<div class="muted">Market Status</div>'
            '<div class="score">—</div>'
            '<div class="muted">Waiting for data</div>'
            "</div>",
            unsafe_allow_html=True,
        )

    with c2:
        st.markdown(
            '<div class="card">'
            '<div class="muted">Stocks Analyzed</div>'
            '<div class="score">113</div>'
            '<div class="muted">Sharia universe</div>'
            "</div>",
            unsafe_allow_html=True,
        )

    with c3:
        st.markdown(
            '<div class="card">'
            '<div class="muted">Opportunities</div>'
            '<div class="score">—</div>'
            '<div class="muted">Analysis pending</div>'
            "</div>",
            unsafe_allow_html=True,
        )

    with c4:
        st.markdown(
            '<div class="card">'
            '<div class="muted">Data Health</div>'
            '<div class="score">—</div>'
            '<div class="muted">Not connected</div>'
            "</div>",
            unsafe_allow_html=True,
        )

    st.subheader("Today's Analysis")

    st.info(
        "The analysis engine is not connected yet. "
        "The next steps will connect market data, technical analysis, "
        "fundamentals, AI interpretation, risk analysis and Telegram reports."
    )

    st.subheader("Decision Engine")

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric("Entry Opportunity", "—")

    with col2:
        st.metric("Oversold", "—")

    with col3:
        st.metric("Watchlist", "—")

    with col4:
        st.metric("No Trade", "—")

    with col5:
        st.metric("Rejected", "—")

    st.subheader("Top Opportunities")

    st.dataframe(
        {
            "Symbol": [],
            "Company": [],
            "Sector": [],
            "Opportunity Score": [],
            "Decision": [],
            "Risk": [],
        },
        use_container_width=True,
        hide_index=True,
    )

# -------------------------
# Market
# -------------------------

elif page == "Market":

    st.title("Market")

    st.info(
        "Market data will appear here after connecting the EGX data engine."
    )

    st.subheader("Market Regime")

    c1, c2, c3 = st.columns(3)

    with c1:
        st.metric("Trend", "—")

    with c2:
        st.metric("Breadth", "—")

    with c3:
        st.metric("Volatility", "—")

# -------------------------
# Opportunities
# -------------------------

elif page == "Opportunities":

    st.title("Opportunities")

    st.info(
        "Stocks will be listed here after the analysis engine evaluates "
        "price action, liquidity, fundamentals, news, risk and confirmation."
    )

    st.dataframe(
        {
            "Symbol": [],
            "Company": [],
            "Score": [],
            "Decision": [],
            "Why Now": [],
            "Risk": [],
        },
        use_container_width=True,
        hide_index=True,
    )

# -------------------------
# Watchlist
# -------------------------

elif page == "Watchlist":

    st.title("Watchlist")

    st.info(
        "Your tracked stocks will appear here."
    )

# -------------------------
# Portfolio
# -------------------------

elif page == "Portfolio":

    st.title("Portfolio")

    st.info(
        "Portfolio tracking will be connected after the core analysis engine."
    )

# -------------------------
# Research
# -------------------------

elif page == "Research":

    st.title("Research")

    st.markdown(
        """
        ### Research Mode

        Search and investigate an individual EGX stock.

        The research engine will combine:

        - Market data
        - Technical analysis
        - Fundamentals
        - Liquidity
        - Relative strength
        - News
        - Gemini AI interpretation
        - Risk analysis
        - Confirmation signals
        """
    )

    symbol = st.text_input(
        "Stock symbol",
        placeholder="Example: COMI",
    )

    if st.button("Analyze Stock"):
        if symbol.strip():
            st.info(
                f"Research request created for **{symbol.upper()}**. "
                "The data engine will be connected in the next stage."
            )
        else:
            st.warning("Enter a stock symbol first.")

# -------------------------
# Settings
# -------------------------

elif page == "Settings":

    st.title("Settings")

    st.subheader("Analysis")

    st.checkbox(
        "Show technical indicators",
        value=False,
    )

    st.checkbox(
        "Show detailed AI reasoning",
        value=False,
    )

    st.checkbox(
        "Enable Telegram daily report",
        value=True,
    )

    st.divider()

    st.subheader("System")

    st.write("Data provider: Not connected")
    st.write("AI provider: Gemini")
    st.write("Database: Not connected")
    st.write("Telegram: Not connected")

    st.success("Application interface is ready.")
