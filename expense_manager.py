# ============================================================
# Smart Household Finance Agent — Database / Expense Manager
# ============================================================

from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from config import supabase


# ── Data Helpers ──────────────────────────────────────────

def _today() -> str:
    return date.today().isoformat()


def _now() -> str:
    return datetime.utcnow().isoformat()


# ── Expense Manager ───────────────────────────────────────

class ExpenseManager:
    """
    Handles all CRUD operations against the Supabase `expenses` table.

    Expected table schema (create in Supabase SQL editor):

        CREATE TABLE expenses (
            id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            store_name    TEXT,
            date          DATE NOT NULL DEFAULT CURRENT_DATE,
            total_amount  NUMERIC(10, 2) NOT NULL,
            currency      TEXT DEFAULT 'USD',
            category      TEXT NOT NULL DEFAULT 'Other',
            items         JSONB,
            payment_method TEXT,
            notes         TEXT,
            image_url     TEXT,
            created_at    TIMESTAMPTZ DEFAULT NOW(),
            updated_at    TIMESTAMPTZ DEFAULT NOW()
        );
    """

    def __init__(self):
        self._db = supabase
        self._table = "expenses"

    # ── Create ────────────────────────────────────────────

    def add_expense(
        self,
        *,
        total_amount: float,
        category: str,
        store_name: Optional[str] = None,
        expense_date: Optional[str] = None,
        currency: str = "USD",
        items: Optional[list[dict]] = None,
        payment_method: Optional[str] = None,
        notes: Optional[str] = None,
        image_url: Optional[str] = None,
    ) -> dict:
        """Insert a new expense record and return the created row."""
        payload = {
            "store_name": store_name,
            "date": expense_date or _today(),
            "total_amount": round(float(total_amount), 2),
            "currency": currency,
            "category": category,
            "items": items or [],
            "payment_method": payment_method,
            "notes": notes,
            "image_url": image_url,
            "created_at": _now(),
            "updated_at": _now(),
        }

        response = (
            self._db.table(self._table)
            .insert(payload)
            .execute()
        )
        return response.data[0] if response.data else {}

    # ── Read ──────────────────────────────────────────────

    def get_all_expenses(
        self,
        limit: int = 200,
        order_by: str = "date",
        ascending: bool = False,
    ) -> list[dict]:
        """Return expenses ordered by date (newest first by default)."""
        response = (
            self._db.table(self._table)
            .select("*")
            .order(order_by, desc=not ascending)
            .limit(limit)
            .execute()
        )
        return response.data or []

    def get_expenses_by_category(self, category: str) -> list[dict]:
        """Return all expenses for a given category."""
        response = (
            self._db.table(self._table)
            .select("*")
            .eq("category", category)
            .order("date", desc=True)
            .execute()
        )
        return response.data or []

    def get_expenses_by_date_range(
        self,
        start_date: str,
        end_date: str,
    ) -> list[dict]:
        """Return expenses between two ISO-format dates (inclusive)."""
        response = (
            self._db.table(self._table)
            .select("*")
            .gte("date", start_date)
            .lte("date", end_date)
            .order("date", desc=True)
            .execute()
        )
        return response.data or []

    def get_expense_by_id(self, expense_id: str) -> Optional[dict]:
        """Return a single expense by its UUID, or None if not found."""
        response = (
            self._db.table(self._table)
            .select("*")
            .eq("id", expense_id)
            .single()
            .execute()
        )
        return response.data

    # ── Update ────────────────────────────────────────────

    def update_expense(self, expense_id: str, updates: dict) -> dict:
        """
        Partially update an expense record.

        Args:
            expense_id: UUID of the expense to update.
            updates: Dict of fields to change.

        Returns:
            The updated row.
        """
        updates["updated_at"] = _now()
        response = (
            self._db.table(self._table)
            .update(updates)
            .eq("id", expense_id)
            .execute()
        )
        return response.data[0] if response.data else {}

    # ── Delete ────────────────────────────────────────────

    def delete_expense(self, expense_id: str) -> bool:
        """Delete an expense by UUID. Returns True on success."""
        response = (
            self._db.table(self._table)
            .delete()
            .eq("id", expense_id)
            .execute()
        )
        return bool(response.data)

    # ── Aggregations ──────────────────────────────────────

    def get_total_by_category(self) -> dict[str, float]:
        """Return a mapping of {category: total_amount} across all expenses."""
        expenses = self.get_all_expenses(limit=10_000)
        totals: dict[str, float] = {}
        for exp in expenses:
            cat = exp.get("category", "Other")
            totals[cat] = totals.get(cat, 0.0) + float(exp.get("total_amount", 0))
        return totals

    def get_monthly_totals(self) -> dict[str, float]:
        """Return a mapping of {YYYY-MM: total_amount} for the last 12 months."""
        expenses = self.get_all_expenses(limit=10_000)
        monthly: dict[str, float] = {}
        for exp in expenses:
            raw_date = exp.get("date", "")
            month_key = raw_date[:7] if raw_date else "Unknown"
            monthly[month_key] = monthly.get(month_key, 0.0) + float(exp.get("total_amount", 0))
        # Sort chronologically
        return dict(sorted(monthly.items()))


# ── Module-level singleton ─────────────────────────────────
expense_manager = ExpenseManager()
