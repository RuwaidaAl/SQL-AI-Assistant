# streamlit_app.py
import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
from sklearn.ensemble import IsolationForest
import warnings
warnings.filterwarnings('ignore')

st.set_page_config(page_title=" Velo Banking SQL Assistant", layout="centered")

st.markdown("""
<style>
    .stApp {
        background: linear-gradient(to bottom, #0a0e17, #121826);
        color: #e0e0e0;
        font-family: 'Segoe UI', sans-serif;
    }
    .main-container {
        max-width: 900px;
        margin: auto;
    }
    .title {
        font-size: 3.2rem;
        font-weight: 700;
        background: linear-gradient(90deg, #00d4ff, #7b68ee);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 0.01rem;
    }
    .subtitle {
        font-size: 1.3rem;
        color: #a0a0c0;
        text-align: center;
        margin-bottom: 1rem;
    }

    /* Text Input */
    .stTextInput > div > div > input {
        background: #252a3f !important;
        border: 2px solid #00d4ff !important;
        color: white !important;
        border-radius: 16px !important;
        font-size: 1.1rem !important;
        box-shadow: 0 4px 15px rgba(0, 212, 255, 0.2) !important;
    }

    /* Buttons */
    .stButton > button {
        background: linear-gradient(90deg, #00d4ff, #7b68ee);
        color: white;
        border: none;
        border-radius: 16px;
        height: 56px;
        font-size: 1.1rem;
        font-weight: 600;
        box-shadow: 0 4px 15px rgba(0,212,255,0.3);
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(0,212,255,0.4);
    }

    /* Result Card */
    .result-card {
        background: #1a1f2e;
        border-radius: 20px;
        border: 1px solid #333;
        box-shadow: 0 8px 32px rgba(0,0,0,0.4);
    }

    h3 {
        color: #ffffff !important;
        font-weight: 600 !important;
        font-size: 1.8rem !important;
    }

    /* REMOVE ALL Streamlit CODE BLOCK ARTIFACTS */
    div[data-testid="stCodeBlock"],
    div[data-testid="stCodeBlock"] *,
    pre, code {
        display: none !important;
        visibility: hidden !important;
        height: 0 !important;
        margin: 0 !important;
        padding: 0 !important;
    }

    /* Custom SQL Display Box */
    .sql-box {
        background-color: #f0f2f6;
        color: #1e1e1e;
        padding: 1.5rem;
        border-radius: 16px;
        border: 1px solid #cccccc;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        font-family: 'Courier New', monospace;
        font-size: 1rem;
        line-height: .9;
        white-space: pre-wrap;
        word-wrap: break-word;
        overflow-x: auto;
    }

    .stExpander {
        background: #1a1f2e;
        border-radius: 16px;
        border: 1px solid #333;
    }

    <style>

    /* =======================================================
       UNIVERSAL FIX: Remove red border from ALL buttons
       ======================================================= */
    html body .stButton > button,
    html body div[data-testid="stDownloadButton"] > button {
        border: 2px solid transparent !important;
        color: white !important;
        box-shadow: none !important;
        outline: none !important;
    }

    /* =======================================================
       BLUE FOCUS OUTLINE (normal + download buttons)
       ======================================================= */
    html body .stButton > button:focus,
    html body .stButton > button:focus-visible,
    html body div[data-testid="stDownloadButton"] > button:focus,
    html body div[data-testid="stDownloadButton"] > button:focus-visible {
        outline: 3px solid #0044ff !important;
        outline-offset: 4px !important;
        border: 2px solid #0044ff !important;
        box-shadow: none !important;
        color: white !important;
    }

    /* =======================================================
       ACTIVE / CLICKED STATE (never red)
       ======================================================= */
    html body .stButton > button:active,
    html body div[data-testid="stDownloadButton"] > button:active {
        border: 2px solid #0044ff !important;
        outline: none !important;
        box-shadow: none !important;
        color: white !important;
    }

</style>
""", unsafe_allow_html=True)


# ========================================
# DATABASE
# ========================================
@st.cache_resource
def create_database():
    conn = sqlite3.connect(":memory:", check_same_thread=False)
    for table, file in [
        ("customer", "customer.csv"),
        ("account", "account.csv"),
        ("loan", "loan.csv"),
        ("transactions", "transaction.csv")
    ]:
        pd.read_csv(file).to_sql(table, conn, index=False, if_exists="replace")
    return conn

conn = create_database()

from sql_ai import generate_sql

def run_sql(sql):
    try:
        return pd.read_sql_query(sql, conn)
    except Exception as e:
        return f"SQL Error: {e}"

def detect_anomalies():
    df = pd.read_sql_query("SELECT * FROM transactions", conn)
    if len(df) < 50:
        return None, df
    df['hour'] = pd.to_datetime(df['date']).dt.hour
    X = df[['amount', 'hour']].fillna(0)
    model = IsolationForest(contamination=0.1, random_state=42)
    df['anomaly'] = model.fit_predict(X)
    return df[df['anomaly'] == -1], df

# ========================================
# SESSION STATE
# ========================================
if 'history' not in st.session_state:
    st.session_state.history = []

# ========================================
# MAIN UI
# ========================================
st.markdown("<div class='main-container'>", unsafe_allow_html=True)

st.markdown("<h1 class='title'>Arura</h1>", unsafe_allow_html=True)
st.markdown("<p class='subtitle'>Your intelligent banking SQL assistant! Curious about something in your database? Ask me! I’ll look across all your tables and return the answer faster than you think.</p>", unsafe_allow_html=True)

question = st.text_input(
    "",
    placeholder="e.g. Show me all customers over 40 with active loans",
    label_visibility="collapsed",
    key="query"
)

col1, col2 = st.columns([1, 1])
with col1:
    run = st.button("Run Query", type="primary", use_container_width=True)
with col2:
    clear = st.button("Clear History", use_container_width=True)

if clear:
    st.session_state.history = []
    st.rerun()

# ========================================
# PROCESS QUERY
# ========================================
if run and question:
    with st.spinner("Generating SQL and fetching results..."):
        sql = generate_sql(question)
        result = run_sql(sql)

    st.session_state.history.insert(0, {
        "time": datetime.now().strftime("%H:%M"),
        "question": question,
        "sql": sql,
        "rows": len(result) if isinstance(result, pd.DataFrame) else 0
    })

    st.subheader("Generated SQL")
    st.markdown(f"<div class='sql-box'>{sql}</div>", unsafe_allow_html=True)

    st.subheader("Results")
    if isinstance(result, pd.DataFrame):
        if result.empty:
            st.info("No results found. Try adjusting your question.")
        else:
            st.dataframe(result, use_container_width=True)
            csv = result.to_csv(index=False)
            st.download_button(
                "Download Results",
                csv,
                f"freya_results_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                "text/csv",
                use_container_width=True
            )
    else:
        st.error(result)

    if "transaction" in question.lower() or "transaction" in sql.lower():
        st.markdown("---")
        st.subheader("🔍 Quick Anomaly Check")
        anomalies, _ = detect_anomalies()
        if anomalies is not None and len(anomalies) > 0:
            st.warning(f"Detected {len(anomalies)} unusual transactions")
            st.dataframe(anomalies[['amount', 'type', 'date']].head(10), use_container_width=True)
        else:
            st.success("No suspicious patterns found")

    st.markdown("</div>", unsafe_allow_html=True)

# ========================================
# RECENT QUERIES
# ========================================
if st.session_state.history:
    st.markdown("---")
    st.subheader("Recent Queries")
    for i, h in enumerate(st.session_state.history[:8]):
        with st.expander(f"{h['time']} — {h['question'][:60]}{'...' if len(h['question'])>60 else ''} ({h['rows']} rows)"):
            st.markdown(f"<div class='sql-box'>{h['sql']}</div>", unsafe_allow_html=True)
            if st.button("Run Again", key=f"rerun_{i}", use_container_width=True):
                st.session_state.query = h['question']
                st.rerun()

st.markdown("</div>", unsafe_allow_html=True)
