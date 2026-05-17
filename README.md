# 💰 Smart Household Finance Agent

> An AI-powered household expense tracker that reads receipts using Claude's vision API and stores data in Supabase.

---

## ✨ Features

| Feature | Description |
|---|---|
| 📸 **Receipt Scanning** | Upload a photo — Claude extracts store, date, items & total automatically |
| 💾 **Cloud Storage** | All expenses stored in Supabase (PostgreSQL) |
| 📊 **Visual Dashboard** | Interactive charts: spending by category & monthly trends |
| 📋 **Expense History** | Filter by date range & category, delete entries |
| 🤖 **AI Insights** | Claude summarises your spending and suggests savings tips |

---

## 🗂️ Project Structure

```
smart-household-finance-agent/
├── .env                   # API keys (DO NOT COMMIT)
├── .gitignore
├── requirements.txt       # Python dependencies
├── README.md
├── app.py                 # Main Streamlit app (4 pages)
├── config.py              # Config & Supabase client singleton
├── vision_agent.py        # Claude vision integration
├── expense_manager.py     # CRUD database operations
└── screenshots/           # Documentation screenshots
```

---

## 🚀 Quick Start

### 1. Clone & Install

```bash
git clone https://github.com/your-username/smart-household-finance-agent.git
cd smart-household-finance-agent
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env .env.local    # optional — edit .env directly
```

Fill in `.env`:

```env
ANTHROPIC_API_KEY=sk-ant-...
SUPABASE_URL=https://xxxx.supabase.co
SUPABASE_ANON_KEY=eyJ...
```

### 3. Set Up Supabase Table

Run this SQL in your Supabase SQL editor:

```sql
CREATE TABLE expenses (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    store_name      TEXT,
    date            DATE NOT NULL DEFAULT CURRENT_DATE,
    total_amount    NUMERIC(10, 2) NOT NULL,
    currency        TEXT DEFAULT 'USD',
    category        TEXT NOT NULL DEFAULT 'Other',
    items           JSONB,
    payment_method  TEXT,
    notes           TEXT,
    image_url       TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);
```

### 4. Run the App

```bash
streamlit run app.py
```

Open [http://localhost:8501](http://localhost:8501) in your browser.

---

## 🛠️ Tech Stack

- **Frontend**: [Streamlit](https://streamlit.io/)
- **AI Vision**: [Anthropic Claude](https://www.anthropic.com/) (`claude-opus-4-5`)
- **Database**: [Supabase](https://supabase.com/) (PostgreSQL)
- **Charts**: [Plotly](https://plotly.com/python/)

---

## ⚠️ Security

- Never commit your `.env` file — it is listed in `.gitignore`
- Use Supabase Row Level Security (RLS) in production
- Rotate API keys regularly

---

## 📄 License

MIT — free to use and modify.
