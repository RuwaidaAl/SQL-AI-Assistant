# 🏦 Banking SQL Assistant

Ask questions about banking data in plain English and get SQL results instantly.


### 1. Get Your Free API Key
- Go to [console.groq.com](https://console.groq.com)
- Sign up (free tier available)
- Create API key → Copy it

### 2. Set Up
```bash
# Clone & install
git clone [your-repo-url]
cd banking-sql-assistant
pip install pandas groq python-dotenv

# Add your API key
echo "GROQ_API_KEY=your_key_here" > .env

# Add your CSV files:
# customer.csv, account.csv, loan.csv, transaction.csv
