"""Configuration and database connection setup"""
import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

# Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Supabase URL and Key are required. Check your .env file.")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Defaults
DEFAULT_BUDGET = float(os.getenv("MONTHLY_BUDGET", 5000))

EXPENSE_CATEGORIES = [
    "Utilities",
    "Food & Groceries",
    "Beverages",
    "Frozen Goods",
    "Toiletries",
    "Household Supplies",
    "Transportation",
    "Entertainment",
    "Healthcare",
    "Education",
    "Tuition",
    "Shopping",
    "Dining Out",
    "Other",
]

PAYMENT_METHODS = [
    "Cash",
    "Credit Card",
    "Debit Card",
    "GCash",
    "Maya",
    "Bank Transfer",
    "Other",
]


def get_database_connection():
    """Returns active Supabase connection"""
    return supabase
