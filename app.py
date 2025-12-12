# streamlit_app.py
import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

st.set_page_config(page_title="Arura Banking SQL Assistant", layout="centered")


st.markdown("""
<style>
    .stApp {
        background: linear-gradient(to bottom, #0a0e17, #121826);
        color: #e0e0e0;
        font-family: 'Segoe UI', sans-serif;
    }

    section[data-testid="stSidebar"] {
        width: 350px !important;
        background-color: #101522;
        border-right: 1px solid #1b2335;
    }

    .sidebar-title {
        color: #7b9cff;
        font-size: 1.4rem;
        font-weight: 600;
        margin-bottom: 8px;
    }

    .sidebar-text {
        color: #c8c8d6;
        font-size: 0.95rem;
        margin-bottom: 14px;
    }

    .title {
        font-size: 3.2rem;
        font-weight: 700;
        background: linear-gradient(90deg, #00d4ff, #7b68ee);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
    }

    .subtitle {
        font-size: 1.3rem;
        color: #a0a0c0;
        text-align: center;
        margin-bottom: 1.4rem;
    }

    .stTextInput > div > div > input {
        background: #252a3f !important;
        border: 2px solid #00d4ff !important;
        color: white !important;
        border-radius: 16px !important;
    }

    .stButton > button {
        background: linear-gradient(90deg, #00d4ff, #7b68ee);
        color: white;
        border: none;
        border-radius: 16px;
        height: 56px;
        font-size: 1.1rem;
        font-weight: 600;
    }

    h3, .stSubheader {
        color: white !important;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_resource
def create_database():
    conn = sqlite3.connect(":memory:", check_same_thread=False)
    for table, file in [
        ("customer", "customer.csv"),
        ("account", "account.csv"),
        ("loan", "loan.csv"),
        ("transactions", "transaction.csv"),
    ]:
        pd.read_csv(file).to_sql(table, conn, index=False, if_exists="replace")
    return conn

conn = create_database()

from sql_ai import generate_sql   # your LLM SQL engine

def run_sql(sql):
    try:
        return pd.read_sql_query(sql, conn)
    except Exception as e:
        return f"SQL Error: {e}"

if "uploaded_ids" not in st.session_state:
    st.session_state.uploaded_ids = None

if "history" not in st.session_state:
    st.session_state.history = []


st.sidebar.markdown("<div class='sidebar-title'>Upload Customer List</div>", unsafe_allow_html=True)
st.sidebar.markdown(
    "<p class='sidebar-text'>Upload a CSV containing only <b>customer_id</b>. "
    "Arura will restrict query results to these customers.</p>",
    unsafe_allow_html=True
)

uploaded_file = st.sidebar.file_uploader("Upload CSV", type=["csv"])

# Process upload
if uploaded_file:
    df_ids = pd.read_csv(uploaded_file)

    if "customer_id" not in df_ids.columns:
        st.sidebar.error("❌ File must contain a column named 'customer_id'")
    else:
        st.session_state.uploaded_ids = df_ids["customer_id"].dropna().astype(int).tolist()
        st.sidebar.success(f"Uploaded {len(st.session_state.uploaded_ids)} customer IDs")

# Clear upload safely
if st.sidebar.button("Clear Upload"):
    st.session_state.uploaded_ids = None
    st.sidebar.success("Upload cleared.")
    st.rerun()

############################################
# MAIN UI
############################################
st.markdown("<h1 class='title'>Arura</h1>", unsafe_allow_html=True)
st.markdown("<p class='subtitle'>AYour intelligent banking SQL assistant! Curious about something in your database? Ask me! I’ll look across all your tables and return the answer faster than you think.</p>", unsafe_allow_html=True)

question = st.text_input("", placeholder="e.g. Get phone numbers for uploaded customers")

col1, col2 = st.columns([1, 1])
run = col1.button("Run Query", use_container_width=True)
clear = col2.button("Clear History", use_container_width=True)

if clear:
    st.session_state.history = []
    st.rerun()

############################################
# SQL EXECUTION
############################################
if run and question:

    with st.spinner("Generating SQL..."):

        extra_context = ""
        if st.session_state.uploaded_ids:
            extra_context = (
                f"\nUser uploaded customer IDs: {st.session_state.uploaded_ids}. "
                "Always filter queries using customer_id IN (these values)."
            )

        sql = generate_sql(question + extra_context)

        # Auto-Inject WHERE Filter
        if st.session_state.uploaded_ids:
            id_list = ",".join(str(i) for i in st.session_state.uploaded_ids)
            if "customer_id in" not in sql.lower():
                if "where" in sql.lower():
                    sql += f" AND customer_id IN ({id_list})"
                else:
                    sql += f" WHERE customer_id IN ({id_list})"

        result = run_sql(sql)

    # Display SQL
    st.subheader("Generated SQL")
    st.code(sql, language="sql")

    # Display Results
    st.subheader("Results")

    if isinstance(result, pd.DataFrame):
        if result.empty:
            st.info("No matching results found.")
        else:
            st.dataframe(result)

            # Download button
            csv = result.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="⬇️ Download Results as CSV",
                data=csv,
                file_name=f"arura_results_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv",
                use_container_width=True
            )
    else:
        st.error(result)

if st.session_state.history:
    st.subheader("Recent Queries")
    for h in st.session_state.history[:5]:
        with st.expander(h["question"]):
            st.code(h["sql"], language="sql")
