"""Database operations for expense management and user settings"""
from datetime import datetime, timedelta
from config import get_database_connection
import pandas as pd


class ExpenseManager:
    def __init__(self):
        self.db = get_database_connection()
        self.user_id = "default_user"

    # ── User Settings ─────────────────────────────────────

    def get_user_settings(self):
        try:
            response = (
                self.db.table("user_settings")
                .select("*")
                .eq("user_id", self.user_id)
                .execute()
            )
            return response.data[0] if response.data else None
        except Exception:
            return None

    def save_user_settings(self, nickname: str, monthly_budget: float):
        try:
            existing = self.get_user_settings()
            payload = {
                "user_id": self.user_id,
                "nickname": nickname,
                "monthly_budget": round(float(monthly_budget), 2),
                "updated_at": datetime.utcnow().isoformat(),
            }
            if existing:
                self.db.table("user_settings").update(payload).eq(
                    "user_id", self.user_id
                ).execute()
            else:
                payload["created_at"] = datetime.utcnow().isoformat()
                self.db.table("user_settings").insert(payload).execute()
            return True, "Settings saved."
        except Exception as e:
            return False, str(e)

    # ── Expenses CRUD ─────────────────────────────────────

    def add_expense(self, description: str, amount: float, category: str,
                    bill_date: str, notes: str = "", brand: str = "",
                    store_name: str = "", payment_method: str = "Cash",
                    payment_method_other: str = ""):
        try:
            self.db.table("expenses").insert({
                "description": description,
                "amount": round(float(amount), 2),
                "category": category,
                "brand": brand,
                "store_name": store_name,
                "payment_method": payment_method,
                "payment_method_other": payment_method_other,
                "bill_date": bill_date,
                "notes": notes,
                "user_id": self.user_id,
            }).execute()
            return True, "Expense added."
        except Exception as e:
            return False, f"Error: {str(e)}"

    def get_monthly_expenses(self, year: int = None, month: int = None):
        if year is None or month is None:
            now = datetime.now()
            year, month = now.year, now.month

        first_day = datetime(year, month, 1)
        if month == 12:
            last_day = datetime(year + 1, 1, 1) - timedelta(days=1)
        else:
            last_day = datetime(year, month + 1, 1) - timedelta(days=1)

        try:
            response = (
                self.db.table("expenses")
                .select("*")
                .gte("bill_date", first_day.date().isoformat())
                .lte("bill_date", last_day.date().isoformat())
                .eq("user_id", self.user_id)
                .order("bill_date", desc=True)
                .execute()
            )
            return response.data or []
        except Exception:
            return []

    def get_all_expenses(self, limit: int = 5000):
        """Fetch all expenses for the user (for multi-month charts)."""
        try:
            response = (
                self.db.table("expenses")
                .select("*")
                .eq("user_id", self.user_id)
                .order("bill_date", desc=True)
                .limit(limit)
                .execute()
            )
            return response.data or []
        except Exception:
            return []

    def get_expense_summary(self, monthly_budget: float,
                            year: int = None, month: int = None):
        expenses = self.get_monthly_expenses(year, month)
        if not expenses:
            return {
                "total_spent": 0,
                "remaining_budget": monthly_budget,
                "by_category": {},
                "by_payment": {},
                "count": 0,
                "expenses_list": [],
            }

        df = pd.DataFrame(expenses)
        total_spent = float(df["amount"].sum())
        by_cat = df.groupby("category")["amount"].sum().to_dict()
        by_pay = df.groupby("payment_method")["amount"].sum().to_dict()

        return {
            "total_spent": total_spent,
            "remaining_budget": max(0, monthly_budget - total_spent),
            "by_category": by_cat,
            "by_payment": by_pay,
            "count": len(expenses),
            "expenses_list": expenses,
        }

    def delete_expense(self, expense_id: int):
        try:
            self.db.table("expenses").delete().eq("id", expense_id).execute()
            return True, "Expense deleted."
        except Exception as e:
            return False, str(e)