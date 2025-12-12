import pandas as pd
import sqlite3
from groq import Groq
from dotenv import dotenv_values
from datetime import datetime
from sklearn.ensemble import IsolationForest

env = dotenv_values("/Users/ruwaidaalharrasi/Desktop/Capstone/.env")
api_key = env.get("GROQ_API_KEY")
print("Loaded key:", api_key)

client = Groq(api_key=api_key)

customer = pd.read_csv("customer.csv")
account = pd.read_csv("account.csv")
loan = pd.read_csv("loan.csv")
transaction = pd.read_csv("transaction.csv")

# SQLite (in-memory)
conn = sqlite3.connect(":memory:")
customer.to_sql("customer", conn, index=False, if_exists="replace")
account.to_sql("account", conn, index=False, if_exists="replace")
loan.to_sql("loan", conn, index=False, if_exists="replace")
transaction.to_sql("transactions", conn, index=False, if_exists="replace")

print("\nAll tables loaded into SQLite!")

schema = {
    "customer": list(customer.columns),
    "account": list(account.columns),
    "loan": list(loan.columns),
    "transaction": list(transaction.columns),
}

SYSTEM_PROMPT = f"""
You are a strict SQL assistant for banking data stored in SQLite.
Your ONLY available tables are:

CUSTOMER({', '.join(schema['customer'])})
ACCOUNT({', '.join(schema['account'])})
LOAN({', '.join(schema['loan'])})
TRANSACTIONS({', '.join(schema['transaction'])})

RULES:
1. Only use these tables/columns.
2. No invented fields.
3. Follow relationships:
   - CUSTOMER.customer_id ↔ ACCOUNT.customer_id
   - ACCOUNT.account_id ↔ TRANSACTIONS.account_id
   - CUSTOMER.customer_id ↔ LOAN.customer_id
4. Return only SQL. No explanation.
5. If data is not available: respond with EXACT phrase:
   "Data not available in current banking tables"
"""

FORBIDDEN = [
    "omani", "non omani", "oman", "nationality", "citizen", "country",
    "international", "transfer", "credit card", "visa", "mastercard",
    "salary", "employer", "job", "income", "region", "city", "address",
    "passport", "work", "travel"
]


def get_available_data_examples():
    """What the user *can* ask."""
    return {
        "customer": ["customer names", "date of birth", "phone numbers"],
        "account": ["balances", "account types", "opening dates"],
        "loan": ["loan amounts", "loan status"],
        "transactions": ["transaction amounts", "dates", "types"],
        "combined": ["customers with balances", "loans + customer info"]
    }

def is_invalid_question(q):
    q = q.lower()

    # Check forbidden keywords
    for word in FORBIDDEN:
        if word in q:
            return word

    # Allow LLM errors to pass (we only check forbidden topics)
    return None

def generate_sql(question):
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": question}
        ]
    )

    sql = response.choices[0].message.content.strip()

    # Clean markdown fences
    sql = sql.replace("```sql", "").replace("```", "").strip()
    return sql

def run_sql(sql):
    try:
        return pd.read_sql_query(sql, conn)
    except Exception as e:
        return f"SQL Error: {e}"

def detect_simple_anomalies():
    df = pd.read_sql_query("SELECT * FROM transactions", conn)
    if len(df) < 50:
        print("Not enough data for anomaly detection.")
        return None

    df["hour"] = pd.to_datetime(df["date"]).dt.hour
    model = IsolationForest(contamination=0.1, random_state=42)
    df["is_anomaly"] = model.fit_predict(df[["amount", "hour"]])

    anomalies = df[df["is_anomaly"] == -1]
    print(f"Detected {len(anomalies)} unusual transactions.")
    return anomalies

def ask(question):
    print("\nUser Question:", question)

    invalid = is_invalid_question(question)

    if invalid:
        print(f"\nData not available for: '{invalid}'")

        examples = get_available_data_examples()
        print("\nYou CAN ask about:")
        for group, items in examples.items():
            print(f"  {group.upper()}:")
            for item in items:
                print(f"   • {item}")

        return pd.DataFrame({
            "Status": ["Data Not Available"],
            "Reason": [f"'{invalid}' is not part of the banking database"],
            "Try Asking About": ["customers, accounts, loans, transactions"]
        })

    sql = generate_sql(question)
    print("\nGenerated SQL:\n", sql)

    # If LLM says invalid schema → convert to our message
    if "data not available" in sql.lower():
        print("LLM says data unavailable. Redirecting…")
        return pd.DataFrame({
            "Status": ["Data Not Available"],
            "Reason": ["Query outside available schema"],
            "Try Asking About": ["customers, accounts, loans, transactions"]
        })

    result = run_sql(sql)

    # SQL ERROR
    if not isinstance(result, pd.DataFrame):
        print("\nSQL ERROR:", result)
        return pd.DataFrame({"Error": [result]})

    # EMPTY RESULT
    if result.empty:
        print("\n⚠ No matching rows.")
        return pd.DataFrame({"Message": ["No results found"]})

    # ----------------------------------------------------------
    # 4️⃣ Success → Save + return
    # ----------------------------------------------------------
    print(f"\nFound {len(result)} rows.")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"Bank_Query_{len(result)}rows_{timestamp}.xlsx"
    result.to_excel(filename, index=False)
    print("Saved:", filename)

    # Run anomaly detection when transactions are involved
    if "transaction" in question.lower():
        detect_simple_anomalies()

    return result


# =====================================================================
# OPTIONAL HELPERS
# =====================================================================
def get_dataframes():
    return {
        "customer": customer,
        "account": account,
        "loan": loan,
        "transactions": transaction,
    }


# TEST
print("\nTEST QUERY:")
print(ask("customers grouped by nationality"))
