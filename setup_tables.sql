-- ============================================================
-- Smart Household Finance Agent — Database Setup v2
-- Run this in Supabase SQL Editor
-- ============================================================

-- 1. Drop old tables (removes all existing data)
DROP TABLE IF EXISTS expenses;
DROP TABLE IF EXISTS user_settings;

-- 2. User Settings
CREATE TABLE user_settings (
    id SERIAL PRIMARY KEY,
    user_id TEXT UNIQUE NOT NULL DEFAULT 'default_user',
    nickname TEXT NOT NULL DEFAULT 'User',
    monthly_budget NUMERIC(10, 2) NOT NULL DEFAULT 5000.00,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3. Expenses (supports itemized receipts, brands, payment methods)
CREATE TABLE expenses (
    id SERIAL PRIMARY KEY,
    description TEXT NOT NULL,
    amount NUMERIC(10, 2) NOT NULL,
    category TEXT NOT NULL DEFAULT 'Other',
    brand TEXT DEFAULT '',
    store_name TEXT DEFAULT '',
    payment_method TEXT DEFAULT 'Cash',
    payment_method_other TEXT DEFAULT '',
    bill_date DATE NOT NULL DEFAULT CURRENT_DATE,
    notes TEXT DEFAULT '',
    user_id TEXT NOT NULL DEFAULT 'default_user',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 4. Row Level Security
ALTER TABLE user_settings ENABLE ROW LEVEL SECURITY;
ALTER TABLE expenses ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Allow all on user_settings" ON user_settings
    FOR ALL USING (true) WITH CHECK (true);

CREATE POLICY "Allow all on expenses" ON expenses
    FOR ALL USING (true) WITH CHECK (true);
