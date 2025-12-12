import pandas as pd
import sqlite3
from groq import Groq
from dotenv import dotenv_values
import os

env = dotenv_values("/Users/ruwaidaalharrasi/Desktop/Capstone/.env")
api_key = env.get("GROQ_API_KEY")
print("Loaded key:", api_key)

client = Groq(api_key=api_key)
customer = pd.read_csv("customer.csv")
account = pd.read_csv("account.csv")
loan = pd.read_csv("loan.csv")
transaction = pd.read_csv("transaction.csv")


conn = sqlite3.connect(":memory:")

customer.to_sql("customer", conn, index=False, if_exists="replace")
account.to_sql("account", conn, index=False, if_exists="replace")
loan.to_sql("loan", conn, index=False, if_exists="replace")
transaction.to_sql("transaction", conn, index=False, if_exists="replace")

print("All tables loaded into SQLite!\n")

# ----------------------------------
# Build dynamic schema prompt
# ----------------------------------
schema = {
    "customer": list(customer.columns),
    "account": list(account.columns),
    "loan": list(loan.columns),
    "transaction": list(transaction.columns),
}

SYSTEM_PROMPT = f"""You are a specialized SQL assistant for National Banking Corporation's Data Analysis Team. You have access to 4 core banking tables that can be joined for financial analysis.

DATABASE SCHEMA - NATIONAL BANKING CORPORATION:

1. CUSTOMER({', '.join(schema['customer'])})
   - Core customer demographic and contact information
   
2. ACCOUNT({', '.join(schema['account'])})
   - All banking accounts with balances and status
   
3. LOAN({', '.join(schema['loan'])})
   - Customer loan records including amounts and terms
   
4. TRANSACTION({', '.join(schema['transaction'])})
   - All financial transactions across accounts

RELATIONSHIP MAP:
• CUSTOMER ↔ ACCOUNT: Join on customer_id
• ACCOUNT ↔ TRANSACTION: Join on account_id  
• CUSTOMER ↔ LOAN: Join on customer_id
• ACCOUNT ↔ LOAN: Join on account_id (if applicable)

CRITICAL BUSINESS RULES:
1. Use STRICT SQLite syntax - all queries must execute in SQLite
2. Use ONLY exact column names from the schema above
3. Never invent or assume columns that don't exist
4. All joins MUST use the relationship keys specified above
5. Handle NULL values appropriately in aggregations

QUERY RESPONSE PROTOCOL:
• If question requires data/columns not in schema → Return: "Data not available in current banking tables"
• If question requires joining tables without matching keys → Return: "No direct relationship between [Table1] and [Table2] for this analysis"
• If question is clear and answerable → Return ONLY the SQL query with no explanations
• Format queries cleanly with proper indentation for readability

EXAMPLE QUESTIONS YOU CAN HANDLE:
✓ "Show total account balance for each customer"
✓ "Find customers with overdue loans"
✓ "Calculate monthly transaction volume by account type"
✓ "Identify high-value customers with multiple accounts"

YOUR MISSION: Convert banking business questions into precise, executable SQL queries that follow banking data governance standards."""

def generate_sql(question):
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",  # Changed to a free model
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": question}
        ]
    )
    # FIXED: Removed the early return statement
    sql = response.choices[0].message.content.strip()
    
    # Remove markdown code blocks if present
    if sql.startswith("```sql"):
        sql = sql[6:] 
    if sql.startswith("```"):
        sql = sql[3:] 
    if sql.endswith("```"):
        sql = sql[:-3]  
    
    return sql.strip()

def run_sql(sql):
    try:
        return pd.read_sql_query(sql, conn)
    except Exception as e:
        return f"SQL Error: {e}"


def ask(question):
    print("\nUser Question:", question)

    sql = generate_sql(question)
    print("\nGenerated SQL:\n", sql)

    result = run_sql(sql)
        # Check if result is an empty DataFrame
    if isinstance(result, pd.DataFrame):
        if result.empty:
            print("\nSQL Result: No records match the query criteria")
        else:
            print(f"\nSQL Result ({len(result)} records found):")
            print(result)
    else:
        # Handle SQL errors
        print("\nSQL Result:", result)
    
    return result

ask("show me a new table with category of balance summayr how many in each category i want 100-600 600-1000 1000-2000 more thn 2000")