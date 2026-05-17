"""Quick diagnostic to check what's in Supabase"""
from config import get_database_connection
from datetime import datetime

db = get_database_connection()

print("=== ALL EXPENSES ===")
res = db.table("expenses").select("*").execute()
for r in res.data:
    print("  id=%s | date=%s | user_id=%s | desc=%s | amt=%s | cat=%s" % (
        r.get("id"), r.get("bill_date"), r.get("user_id"),
        r.get("description"), r.get("amount"), r.get("category")
    ))
print("Total rows:", len(res.data))

print("\n=== CURRENT MONTH FILTER ===")
now = datetime.now()
first = "%d-%02d-01" % (now.year, now.month)
last = "%d-%02d-31" % (now.year, now.month)
print("Filtering: bill_date between", first, "and", last, "AND user_id = default_user")

res2 = db.table("expenses").select("*").gte("bill_date", first).lte("bill_date", last).eq("user_id", "default_user").execute()
print("Filtered rows:", len(res2.data))

print("\n=== USER SETTINGS ===")
res3 = db.table("user_settings").select("*").execute()
for r in res3.data:
    print("  user_id=%s | nick=%s | budget=%s" % (
        r.get("user_id"), r.get("nickname"), r.get("monthly_budget")
    ))
