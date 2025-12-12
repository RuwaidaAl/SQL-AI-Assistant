Banking SQL Assistant
A simple tool that lets you ask questions about banking data in plain English, and it automatically writes and runs the SQL queries for you.

What It Does
Uploads banking data (customers, accounts, loans, transactions)

Lets you ask questions like: "Show me customers with high balances"

Automatically converts your question to SQL code

Runs the query and shows you the results

Built-in safety features to protect your data

Quick Setup
1. Get Your API Key
Go to console.groq.com

Sign up for a free account

Go to "API Keys" and click "Create API Key"

Copy your new key

2. Set Up the Project
bash
# Create project folder
mkdir banking-assistant
cd banking-assistant

# Download the Python file
# (Get banking_assistant.py from this repository)

# Create your .env file
echo "GROQ_API_KEY=your_key_here" > .env
3. Add Your Data Files
Place these CSV files in the same folder:

customer.csv - Your customer information

account.csv - Account balances and details

loan.csv - Loan records

transaction.csv - Transaction history

4. Install & Run
bash
# Install required packages
pip install pandas groq python-dotenv

# Run the assistant
python banking_assistant.py
Example Questions You Can Ask
text
"Show total balance for each customer"
"Find customers from California"
"List accounts with balance over $10,000"
"Show customers with overdue loans"
"How many transactions last month?"
