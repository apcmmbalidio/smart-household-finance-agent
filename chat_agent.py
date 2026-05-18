"""
Finance AI Chat Agent (Rule-Based)
Multi-step reasoning agent that retrieves expense data and provides
personalized financial insights using decision logic and templates.
No LLM API calls — Gemini is reserved for receipt scanning only.

Agent Flow:
  User question -> Classify intent (keywords) -> Retrieve data (Supabase) -> Apply rules -> Generate response
"""
import json
from datetime import datetime
from collections import Counter

# Intent keywords for local classification
INTENT_KEYWORDS = {
    "budget_check": [
        "budget", "over budget", "under budget", "remaining", "left",
        "how much left", "budget status", "afford", "limit",
    ],
    "category_analysis": [
        "food", "groceries", "utilities", "transportation", "entertainment",
        "healthcare", "education", "tuition", "shopping", "dining",
        "toiletries", "beverages", "frozen", "household", "category",
    ],
    "monthly_comparison": [
        "compare", "comparison", "vs", "versus", "last month",
        "previous month", "month over month", "trend",
    ],
    "top_expenses": [
        "top", "biggest", "largest", "most expensive", "highest",
        "rank", "expensive",
    ],
    "payment_analysis": [
        "payment", "pay method", "cash", "credit card", "gcash",
        "maya", "debit", "bank transfer", "how do i pay",
    ],
    "savings_tips": [
        "save", "saving", "cut", "reduce", "tips", "advice",
        "suggest", "recommendation", "cheaper", "optimize",
    ],
    "item_price": [
        "price", "how much does", "how much is",
        "price of", "cost of", "price history",
    ],
    "yearly_overview": [
        "all months", "yearly", "annual", "every month",
        "each month", "month by month", "entire year", "whole year",
        "all time", "this year", "per month",
    ],
}


class FinanceChatAgent:
    """
    Rule-based finance assistant. No LLM API calls.

    Agentic capabilities:
    1. Goal-oriented: answers financial questions with real data
    2. Multi-step reasoning: classify -> retrieve -> apply rules -> respond
    3. Tool usage: queries Supabase via ExpenseManager
    4. Memory: retains conversation history within session
    5. Decision-making: picks data retrieval + response strategy based on intent
    6. Autonomy: completes full pipeline without human intervention
    """

    def __init__(self, expense_manager, monthly_budget: float):
        self.em = expense_manager
        self.budget = monthly_budget
        self.conversation_history = []

    # -- Step 1: Classify Intent (keyword matching) --------

    def _classify_intent(self, user_message: str) -> str:
        """Classify intent using keyword matching with smart overrides."""
        import re
        msg = user_message.lower()
        scores = {}
        for intent, keywords in INTENT_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in msg)
            if score > 0:
                scores[intent] = score

        if not scores:
            return "general_query"

        best = max(scores, key=scores.get)

        # Smart override: if yearly_overview or monthly_comparison but user
        # also mentions a specific item/brand/store, prefer general_query
        if best in ("yearly_overview", "monthly_comparison"):
            skip = {
                "how", "much", "did", "spend", "spent", "buying", "buy", "bought",
                "what", "the", "for", "and", "are", "was", "were", "have", "had",
                "has", "does", "this", "that", "with", "from", "about", "been",
                "total", "many", "often", "where", "when", "which", "who",
                "tell", "show", "give", "list", "all", "any", "some", "most",
                "month", "months", "today", "yesterday", "last", "can", "you",
                "your", "my", "ive", "its", "got", "get", "year", "yearly",
                "annual", "every", "each", "entire", "whole", "time",
                "items", "always", "monthly", "overall",
                "expense", "expenses", "spending", "finances", "finance",
                "money", "budget", "summary", "report", "breakdown",
                "compare", "comparison", "versus", "previous", "trend",
                "billing", "bill",
            }
            words = re.findall(r'[a-zA-Z0-9]+', msg)
            specific = [w for w in words if len(w) > 2 and w not in skip]
            if specific:
                return "general_query"  # User wants to search, not see overview

        return best

    # -- Step 2: Retrieve Data (Tool Usage) ----------------

    def _retrieve_data(self, intent: str) -> dict:
        """Decision-making: select and execute the right data retrieval strategy."""
        now = datetime.now()
        context = {"intent": intent, "budget": self.budget}

        if intent == "budget_check":
            summary = self.em.get_expense_summary(self.budget)
            context["summary"] = summary
            context["percent_used"] = round(
                summary["total_spent"] / self.budget * 100, 1
            ) if self.budget > 0 else 0

        elif intent == "category_analysis":
            summary = self.em.get_expense_summary(self.budget)
            context["summary"] = summary

        elif intent == "monthly_comparison":
            cur = self.em.get_expense_summary(self.budget, now.year, now.month)
            prev_month = now.month - 1 if now.month > 1 else 12
            prev_year = now.year if now.month > 1 else now.year - 1
            prev = self.em.get_expense_summary(self.budget, prev_year, prev_month)
            context["current"] = {
                "period": now.strftime("%B %Y"), "data": cur,
            }
            context["previous"] = {
                "period": datetime(prev_year, prev_month, 1).strftime("%B %Y"),
                "data": prev,
            }

        elif intent == "top_expenses":
            all_exp = self.em.get_all_expenses(limit=50)
            context["top"] = sorted(
                all_exp, key=lambda x: float(x.get("amount", 0)), reverse=True
            )[:10]

        elif intent == "payment_analysis":
            summary = self.em.get_expense_summary(self.budget)
            context["summary"] = summary

        elif intent == "savings_tips":
            summary = self.em.get_expense_summary(self.budget)
            all_exp = self.em.get_all_expenses(limit=100)
            context["summary"] = summary
            item_totals = Counter()
            for e in all_exp:
                brand = e.get("brand", "").strip()
                desc = e.get("description", "")
                key = f"{brand} {desc}".strip() if brand else desc
                item_totals[key] += float(e.get("amount", 0))
            context["top_items"] = item_totals.most_common(5)

        elif intent == "item_price":
            all_exp = self.em.get_all_expenses(limit=200)
            items = {}
            for e in all_exp:
                key = f"{e.get('brand', '')} {e['description']}".strip()
                if key not in items:
                    items[key] = []
                items[key].append({
                    "price": float(e["amount"]), "date": e["bill_date"]
                })
            context["items"] = {k: v for k, v in items.items()}

        elif intent == "yearly_overview":
            all_exp = self.em.get_all_expenses(limit=500)
            # Group by month
            monthly = {}
            for e in all_exp:
                date_str = e.get("bill_date", "")
                if date_str:
                    month_key = date_str[:7]  # "YYYY-MM"
                    if month_key not in monthly:
                        monthly[month_key] = {"total": 0, "count": 0, "categories": Counter()}
                    monthly[month_key]["total"] += float(e.get("amount", 0))
                    monthly[month_key]["count"] += 1
                    monthly[month_key]["categories"][e.get("category", "Other")] += float(e.get("amount", 0))
            context["monthly"] = monthly
            context["all_expenses"] = all_exp

        else:
            # General query: load EVERYTHING so we can answer any question
            summary = self.em.get_expense_summary(self.budget)
            all_exp = self.em.get_all_expenses(limit=500)
            context["summary"] = summary
            context["all_expenses"] = all_exp
            # Top items by total spend
            item_totals = Counter()
            for e in all_exp:
                key = f"{e.get('brand', '')} {e['description']}"  .strip()
                item_totals[key] += float(e.get("amount", 0))
            context["top_items"] = item_totals.most_common(10)
            # Stores
            store_totals = Counter()
            for e in all_exp:
                store = e.get("store_name", "").strip()
                if store:
                    store_totals[store] += float(e.get("amount", 0))
            context["stores"] = store_totals.most_common(5)

        return context

    # -- Step 3: Generate Response (Rule-Based Logic) ------

    def _generate_response(self, intent: str, context: dict, user_message: str) -> str:
        """Apply decision rules and templates to generate a data-driven response."""
        # Check for suggestive affordability checks first
        msg_lower = user_message.lower()
        
        # We check for a price OR keywords indicating an affordability question
        has_price_mention = False
        clean_msg = msg_lower.replace(",", "") # Remove commas for easy parsing
        import re
        prices_found = re.findall(r'\b\d+(?:\.\d{1,2})?\b', clean_msg)
        if prices_found:
            if len(prices_found) == 1:
                has_price_mention = True
            else:
                for p in prices_found:
                    val = float(p)
                    if val > 0 and abs(val - self.budget) > 1.0: # not the budget itself
                        has_price_mention = True
                        break

        is_affordability_query = has_price_mention and any(w in msg_lower for w in ["can i", "should i", "safe to", "is it safe", "budget", "afford"])
        is_affordability_query = is_affordability_query or any(w in msg_lower for w in ["everyday", "every day", "daily", "pickup", "starbucks", "grab", "netflix", "spotify", "smirnoff", "mule", "electricity bill", "electric bill", "water bill", "rent"])

        if is_affordability_query:
            # Default values
            item_name = "habit/purchase"
            unit_price = 100.0
            frequency = "daily"
            category = "Other"
            
            # 1. Determine Frequency
            if any(w in msg_lower for w in ["electricity", "electric", "meralco", "water", "bill", "rent", "subscription", "netflix", "spotify", "tuition", "internet", "monthly", "per month"]):
                frequency = "monthly"
            
            # 2. Extract Price
            clean_msg = msg_lower.replace(",", "")
            prices_found = re.findall(r'\b\d+(?:\.\d{1,2})?\b', clean_msg)
            extracted_price = None
            if prices_found:
                if len(prices_found) == 1:
                    extracted_price = float(prices_found[0])
                else:
                    for p in prices_found:
                        val = float(p)
                        if val > 0 and abs(val - self.budget) > 1.0:
                            extracted_price = val
                            break
                    if extracted_price is None:
                        extracted_price = float(prices_found[0])
            
            # 3. Dynamic Item Name Extraction
            item_match = re.search(r'(?:can\s+i\s+(?:drink|buy|have|eat|get|enjoy|purchase|consume|pay|order|have)|safe\s+to\s+have)\s+([a-zA-Z0-9\s\-\'\’]+?)(?:\s+(?:everyday|every\s+day|daily|with|for|per|my|monthly|this))', msg_lower)
            if item_match:
                extracted_item = item_match.group(1).strip()
                # Clean up leading numbers
                extracted_item = re.sub(r'^\d+\s*', '', extracted_item)
                # Clean up leading articles/filler words
                extracted_item = re.sub(r'^(?:a|an|the|some|any|in|for)\s+', '', extracted_item)
                if extracted_item:
                    item_name = extracted_item.title()
            
            # Simple keyword overrides for common terms
            if "electricity" in msg_lower or "electric" in msg_lower or "meralco" in msg_lower:
                item_name = "Electricity Bill"
                category = "Utilities"
                frequency = "monthly"
                if extracted_price is None:
                    extracted_price = 10000.0 # default Meralco average
            elif "water" in msg_lower:
                item_name = "Water Bill"
                category = "Utilities"
                frequency = "monthly"
            elif "rent" in msg_lower:
                item_name = "Rent"
                category = "Utilities"
                frequency = "monthly"
            elif "pickup" in msg_lower:
                item_name = "Pickup Coffee"
                category = "Beverages"
            elif "starbucks" in item_name.lower() or "starbucks" in msg_lower:
                item_name = "Starbucks Coffee"
                category = "Beverages"
            elif "smirnoff" in msg_lower or "mule" in msg_lower:
                item_name = "Smirnoff Mule"
                category = "Beverages"
                
            # If price was extracted, use it
            if extracted_price is not None:
                unit_price = extracted_price
            else:
                if "coffee" in item_name.lower():
                    unit_price = 85.0 if "pickup" in item_name.lower() else 120.0
                elif "netflix" in item_name.lower():
                    unit_price = 399.0
                elif "spotify" in item_name.lower():
                    unit_price = 149.0
                    
            # 4. Map Item to Category
            item_name_lower = item_name.lower()
            if any(w in item_name_lower for w in ["electricity", "electric", "meralco", "water", "rent", "utility", "utilities", "internet", "phone"]):
                category = "Utilities"
            elif any(w in item_name_lower for w in ["coffee", "pickup", "starbucks", "smirnoff", "mule", "coke", "soda", "drink", "beer"]):
                category = "Beverages"
            elif any(w in item_name_lower for w in ["food", "eat", "dining", "jollibee", "mcdonald", "mcdo", "kfc", "restaurant"]):
                category = "Dining Out"
            elif any(w in item_name_lower for w in ["grab", "taxi", "angkas", "joyride", "gas", "fuel", "ride"]):
                category = "Transportation"
            elif any(w in item_name_lower for w in ["netflix", "spotify", "hbo", "show", "entertainment"]):
                category = "Entertainment"
                
            # 5. Determine Cost
            # Large expenses are naturally treated as one-time/monthly totals, not daily recurring habits
            if unit_price >= 1000.0:
                frequency = "monthly"
                
            if frequency == "monthly":
                monthly_cost = unit_price
                freq_desc = f"P {unit_price:,.2f} per month"
            else:
                monthly_cost = unit_price * 30
                freq_desc = f"P {unit_price:,.2f} daily"
                
            s = context.get("summary", self.em.get_expense_summary(self.budget))
            remaining = s.get("remaining_budget", self.budget - s.get("total_spent", 0))
            spent = s.get("total_spent", 0)
            
            cost_pct = (monthly_cost / self.budget * 100) if self.budget > 0 else 0
            
            lines = [
                f"### Affordability & Planning Analysis: {item_name}\n",
                f"Let's look at the financial impact of this {frequency} purchase:\n",
                f"- Cost per item: {freq_desc}",
                f"- Projected monthly total cost: **P {monthly_cost:,.2f}** ({cost_pct:.1f}% of your P {self.budget:,.2f} monthly budget)\n",
            ]
            
            if remaining >= monthly_cost:
                lines.append(f"Affordability Status: Yes, you can safely afford this!")
                lines.append(f"Even after adding this {frequency} {item_name} habit, you would still have **P {remaining - monthly_cost:,.2f}** remaining in your budget for this month.")
                
                lines.append("\n**Actionable Plan & Suggestions:**")
                cat_spent = s.get("by_category", {}).get(category, 0)
                lines.append(f"1. **{category} Spending Context**: You have spent **P {cat_spent:,.2f}** on {category} this month. Adding **P {monthly_cost:,.2f}** would bring your monthly {category} total to **P {cat_spent + monthly_cost:,.2f}**.")
                
                if category == "Beverages":
                    if "pickup" in item_name_lower:
                        lines.append(f"2. **Savings Optimization**: To enjoy your Pickup Coffee even more efficiently, download the Pickup App to buy discounted vouchers or earn loyalty rewards.")
                    else:
                        lines.append(f"2. **Savings Optimization**: Consider buying in bulk or checking if there are membership or bundle discounts for {item_name}.")
                    lines.append(f"3. **Category Safeguard**: Set a mental cap of **P 3,000.00** for the Beverages category to ensure you don't overspend while maintaining this daily routine.")
                elif category == "Utilities":
                    lines.append(f"2. **Savings Optimization**: Look for ways to improve household efficiency (e.g., switching to inverter appliances, scheduling aircon usage, or unplugging phantom loads).")
                    lines.append(f"3. **Category Safeguard**: Your Utilities budget can be highly seasonal (higher electricity bill in summer months). Keep a buffer of **P 5,000.00** in your savings for peak utility bills.")
                elif category == "Entertainment":
                    lines.append(f"2. **Savings Optimization**: Look for annual billing plans or family plans which can save you up to 30-50% off individual monthly pricing.")
                    lines.append(f"3. **Category Safeguard**: Audit your active subscriptions quarterly to prune any services you don't watch or use frequently.")
                else:
                    lines.append(f"2. **Savings Optimization**: Search for digital coupons, loyalty cards, or promos to discount this purchase.")
                    lines.append(f"3. **Category Safeguard**: Log every transaction in the app to maintain visibility and prevent minor purchases from snowballing.")
            else:
                lines.append(f"Affordability Status: Warning: This will put a heavy strain on your budget!")
                lines.append(f"Your remaining budget is **P {remaining:,.2f}**, which is less than the projected monthly cost of **P {monthly_cost:,.2f}**.")
                lines.append("\n**Alternate Plan & Suggestions:**")
                lines.append(f"1. **Reduce Frequency/Usage**: Try to reduce electricity usage by 15-20% to fit this bill within your budget, or find areas to cut back on discretionary categories.")
                lines.append(f"2. **Lower Cost Alternatives**: Look for cheaper options or optimize existing appliances to protect your monthly savings rate.")
                
            return "\n".join(lines)

        if intent == "budget_check":
            s = context["summary"]
            spent = s["total_spent"]
            remaining = s["remaining_budget"]
            pct = context["percent_used"]

            if spent == 0:
                return (
                    f"You haven't recorded any expenses this month yet. "
                    f"Your full budget of P {self.budget:,.2f} is available."
                )

            status = ""
            if pct >= 100:
                over = spent - self.budget
                status = f"You are OVER budget by P {over:,.2f}."
            elif pct >= 80:
                status = f"Warning: You've used {pct}% of your budget. Only P {remaining:,.2f} remaining."
            else:
                status = f"You're on track. You've used {pct}% of your budget."

            lines = [
                f"**Budget Status for {datetime.now().strftime('%B %Y')}**\n",
                f"- Monthly budget: P {self.budget:,.2f}",
                f"- Total spent: P {spent:,.2f}",
                f"- Remaining: P {remaining:,.2f}",
                f"- Usage: {pct}%\n",
                status,
            ]

            # Top categories
            if s["by_category"]:
                lines.append("\n**Breakdown by category:**")
                for cat, amt in sorted(s["by_category"].items(), key=lambda x: x[1], reverse=True):
                    pct_cat = round(amt / spent * 100, 1)
                    lines.append(f"- {cat}: P {amt:,.2f} ({pct_cat}%)")

            return "\n".join(lines)

        elif intent == "category_analysis":
            s = context["summary"]
            if not s["by_category"]:
                return "No expenses recorded this month to analyze by category."

            lines = [f"**Category Breakdown for {datetime.now().strftime('%B %Y')}**\n"]
            total = s["total_spent"]
            for cat, amt in sorted(s["by_category"].items(), key=lambda x: x[1], reverse=True):
                pct = round(amt / total * 100, 1) if total > 0 else 0
                lines.append(f"- **{cat}**: P {amt:,.2f} ({pct}%)")

            lines.append(f"\nTotal: P {total:,.2f} across {s['count']} transactions.")

            # Find which category the user asked about
            msg_lower = user_message.lower()
            for cat, amt in s["by_category"].items():
                if cat.lower() in msg_lower or any(w in msg_lower for w in cat.lower().split()):
                    lines.append(f"\nYou specifically asked about **{cat}**: you spent P {amt:,.2f} on it this month.")
                    break

            return "\n".join(lines)

        elif intent == "monthly_comparison":
            cur = context["current"]["data"]
            prev = context["previous"]["data"]
            cur_p = context["current"]["period"]
            prev_p = context["previous"]["period"]

            diff = cur["total_spent"] - prev["total_spent"]
            direction = "more" if diff > 0 else "less"

            lines = [
                f"**Monthly Comparison**\n",
                f"| | {prev_p} | {cur_p} |",
                f"|---|---|---|",
                f"| Total Spent | P {prev['total_spent']:,.2f} | P {cur['total_spent']:,.2f} |",
                f"| Transactions | {prev['count']} | {cur['count']} |",
                f"\nYou spent P {abs(diff):,.2f} **{direction}** this month compared to last month.",
            ]

            # Category comparison
            all_cats = set(list(cur["by_category"].keys()) + list(prev["by_category"].keys()))
            if all_cats:
                lines.append("\n**By category:**")
                for cat in sorted(all_cats):
                    c_amt = cur["by_category"].get(cat, 0)
                    p_amt = prev["by_category"].get(cat, 0)
                    change = c_amt - p_amt
                    arrow = "(+)" if change > 0 else "(-)" if change < 0 else "(=)"
                    lines.append(f"- {cat}: P {p_amt:,.0f} -> P {c_amt:,.0f} {arrow}")

            return "\n".join(lines)

        elif intent == "top_expenses":
            top = context.get("top", [])
            if not top:
                return "No expenses found to rank."

            lines = [f"**Top {len(top)} Biggest Expenses**\n"]
            for i, e in enumerate(top, 1):
                brand = e.get("brand", "")
                desc = f"{brand} {e['description']}".strip() if brand else e["description"]
                lines.append(
                    f"{i}. **{desc}** - P {float(e['amount']):,.2f} "
                    f"({e['category']}, {e['bill_date']})"
                )

            total_top = sum(float(e["amount"]) for e in top)
            lines.append(f"\nThese {len(top)} items total P {total_top:,.2f}.")
            return "\n".join(lines)

        elif intent == "payment_analysis":
            s = context["summary"]
            by_pay = s.get("by_payment", {})
            if not by_pay:
                return "No payment method data available yet."

            lines = [f"**Payment Method Breakdown**\n"]
            total = s["total_spent"]
            for method, amt in sorted(by_pay.items(), key=lambda x: x[1], reverse=True):
                pct = round(amt / total * 100, 1) if total > 0 else 0
                lines.append(f"- **{method}**: P {amt:,.2f} ({pct}%)")

            most_used = max(by_pay, key=by_pay.get)
            lines.append(f"\nYou use **{most_used}** the most, accounting for the largest share of your spending.")
            return "\n".join(lines)

        elif intent == "savings_tips":
            s = context["summary"]
            top_items = context.get("top_items", [])
            spent = s["total_spent"]

            if spent == 0:
                return "No spending data to analyze yet. Start adding expenses to get savings tips."

            lines = [f"**Savings Analysis**\n"]

            # Identify largest category
            if s["by_category"]:
                largest_cat = max(s["by_category"], key=s["by_category"].get)
                largest_amt = s["by_category"][largest_cat]
                pct = round(largest_amt / spent * 100, 1)
                lines.append(
                    f"Your biggest spending category is **{largest_cat}** "
                    f"at P {largest_amt:,.2f} ({pct}% of total). "
                    f"Consider reviewing these expenses for potential cuts."
                )

            # Top recurring items
            if top_items:
                lines.append("\n**Your most frequent purchases:**")
                for item, total in top_items:
                    lines.append(f"- {item}: P {total:,.2f} total")

            # Budget comparison
            if spent > self.budget:
                over = spent - self.budget
                lines.append(
                    f"\nYou are over budget by P {over:,.2f}. "
                    f"To get back on track, look at reducing spending in your top category."
                )
            elif spent > self.budget * 0.8:
                lines.append(
                    f"\nYou've used {round(spent/self.budget*100)}% of your budget. "
                    f"Be cautious with remaining purchases this month."
                )
            else:
                remaining = self.budget - spent
                lines.append(f"\nYou have P {remaining:,.2f} remaining in your budget. Keep it up.")

            return "\n".join(lines)

        elif intent == "item_price":
            items = context.get("items", {})
            if not items:
                return "No item price data available yet."

            # Extract user's search words, then find items matching them
            import re as _re
            _skip = {"price", "cost", "how", "much", "does", "the", "for", "of", "is"}
            user_words = [w for w in _re.findall(r'[a-zA-Z0-9]+', user_message.lower()) if len(w) > 2 and w not in _skip]
            matched = None
            for name, prices in items.items():
                name_lower = name.lower()
                if any(w in name_lower for w in user_words):
                    matched = (name, prices)
                    break

            if matched:
                name, prices = matched
                lines = [f"**Price History for {name}**\n"]
                for p in sorted(prices, key=lambda x: x["date"]):
                    lines.append(f"- {p['date']}: P {p['price']:,.2f}")
                if len(prices) > 1:
                    avg = sum(p["price"] for p in prices) / len(prices)
                    lines.append(f"\nAverage price: P {avg:,.2f} across {len(prices)} purchases.")
                return "\n".join(lines)
            else:
                lines = [f"**All Tracked Items** ({len(items)} unique items)\n"]
                for name, prices in sorted(items.items(), key=lambda x: -max(p["price"] for p in x[1]))[:10]:
                    latest = max(prices, key=lambda x: x["date"])
                    lines.append(f"- **{name}**: P {latest['price']:,.2f} (latest)")
                return "\n".join(lines)

        elif intent == "yearly_overview":
            monthly = context.get("monthly", {})
            if not monthly:
                return "No expense data found."

            grand_total = sum(m["total"] for m in monthly.values())
            grand_count = sum(m["count"] for m in monthly.values())

            lines = ["**Yearly Spending Overview**\n"]
            lines.append("| Month | Transactions | Total Spent | Top Category |")
            lines.append("|---|---|---|---|")

            for month_key in sorted(monthly.keys()):
                m = monthly[month_key]
                try:
                    month_label = datetime.strptime(month_key, "%Y-%m").strftime("%B %Y")
                except Exception:
                    month_label = month_key
                top_cat = max(m["categories"], key=m["categories"].get) if m["categories"] else "N/A"
                top_cat_amt = m["categories"].get(top_cat, 0)
                lines.append(
                    f"| {month_label} | {m['count']} | P {m['total']:,.2f} | "
                    f"{top_cat} (P {top_cat_amt:,.2f}) |"
                )

            lines.append(f"| **TOTAL** | **{grand_count}** | **P {grand_total:,.2f}** | |")
            lines.append(f"\nMonthly average: **P {grand_total / len(monthly):,.2f}**")
            lines.append(f"Monthly budget: **P {self.budget:,.2f}**")

            return "\n".join(lines)

        else:  # general_query — smart search + comprehensive data
            s = context.get("summary", {})
            all_exp = context.get("all_expenses", [])
            spent = s.get("total_spent", 0)
            remaining = s.get("remaining_budget", self.budget)
            count = s.get("count", 0)
            msg = user_message.lower()

            lines = []

            # Smart search: find ALL matching transactions first
            # Extract search words (skip common filler words, strip punctuation)
            import re
            skip_words = {
                "how", "much", "did", "spend", "spent", "buying", "buy", "bought",
                "what", "the", "for", "and", "are", "was", "were", "have", "had",
                "has", "does", "this", "that", "with", "from", "about", "been",
                "total", "many", "often", "where", "when", "which", "who", "whom",
                "tell", "show", "give", "list", "all", "any", "some", "most",
                "month", "months", "today", "yesterday", "last", "can", "you", "your", "my",
                "ive", "its", "got", "get", "been", "being", "don", "dont",
                "didnt", "isnt", "wasnt", "wont", "cant", "could", "would",
                "should", "shall", "will", "may", "might", "must", "need",
                "also", "just", "like", "know", "think", "want", "see",
                "year", "yearly", "annual", "every", "each", "entire", "whole",
                "items", "always", "monthly", "overall", "time",
            }
            words_raw = re.findall(r'[a-zA-Z0-9]+', msg)
            search_words = [w for w in words_raw if len(w) > 3 and w not in skip_words]
            # Fallback: if all words were filtered, try with length > 2
            if not search_words:
                search_words = [w for w in words_raw if len(w) > 2 and w not in skip_words]
            # Number aliases (e.g. 711 -> 7-eleven, 7eleven)
            aliases = {"711": "7-eleven", "7eleven": "7-eleven"}
            search_words = [aliases.get(w, w) for w in search_words]

            if search_words:
                matches = []
                for e in all_exp:
                    desc = e.get("description", "").lower()
                    brand = e.get("brand", "").lower()
                    store = e.get("store_name", "").lower()
                    category = e.get("category", "").lower()
                    searchable = f"{desc} {brand} {store} {category}"
                    if any(w in searchable for w in search_words):
                        matches.append(e)

                if matches:
                    match_total = sum(float(e["amount"]) for e in matches)
                    match_qty = sum(int(e.get("quantity", 1)) for e in matches)
                    search_term = " ".join(search_words)
                    lines.append(f"**Results for \"{search_term}\"**\n")

                    # Adapt summary based on question type
                    orig_msg = user_message.lower()
                    if "how many" in orig_msg or "count" in orig_msg or "number" in orig_msg:
                        lines.append(f"You bought **{match_qty} item(s)** across **{len(matches)} transaction(s)**, totaling P {match_total:,.2f}\n")
                    elif "how much" in orig_msg or "total" in orig_msg or "cost" in orig_msg:
                        lines.append(f"You spent **P {match_total:,.2f}** across **{len(matches)} transaction(s)**\n")
                    else:
                        lines.append(f"Found **{len(matches)} transaction(s)** -- {match_qty} item(s), totaling **P {match_total:,.2f}**\n")

                    for e in matches:
                        brand = e.get("brand", "")
                        desc = f"{brand} {e['description']}".strip() if brand else e["description"]
                        pay = e.get("payment_method", "")
                        store = e.get("store_name", "")
                        qty = int(e.get("quantity", 1))
                        store_text = f" at {store}" if store else ""
                        qty_text = f" x{qty}" if qty > 1 else ""
                        lines.append(
                            f"- {e['bill_date']}: **{desc}**{qty_text} - P {float(e['amount']):,.2f} "
                            f"({e['category']}{store_text}{', ' + pay if pay else ''})"
                        )

                    lines.append("")
                    return "\n".join(lines)

            # No search matches or no search terms — show full summary
            lines.append(f"**Finance Summary for {datetime.now().strftime('%B %Y')}**\n")
            lines.append(f"- Budget: P {self.budget:,.2f}")
            lines.append(f"- Total spent: P {spent:,.2f}")
            lines.append(f"- Remaining: P {remaining:,.2f}")
            lines.append(f"- Transactions: {count}")

            if s.get("by_category"):
                lines.append("\n**Spending by category:**")
                for cat, amt in sorted(s["by_category"].items(), key=lambda x: x[1], reverse=True):
                    pct = round(amt / spent * 100, 1) if spent > 0 else 0
                    lines.append(f"- {cat}: P {amt:,.2f} ({pct}%)")

            if s.get("by_payment"):
                lines.append("\n**By payment method:**")
                for method, amt in sorted(s["by_payment"].items(), key=lambda x: x[1], reverse=True):
                    lines.append(f"- {method}: P {amt:,.2f}")

            top_items = context.get("top_items", [])
            if top_items:
                lines.append("\n**Most purchased items:**")
                for item, total in top_items[:5]:
                    lines.append(f"- {item}: P {total:,.2f}")

            stores = context.get("stores", [])
            if stores:
                lines.append("\n**Top stores:**")
                for store, total in stores:
                    lines.append(f"- {store}: P {total:,.2f}")

            if all_exp:
                lines.append("\n**Last 5 transactions:**")
                for e in all_exp[:5]:
                    brand = e.get("brand", "")
                    desc = f"{brand} {e['description']}".strip() if brand else e["description"]
                    lines.append(f"- {e['bill_date']}: {desc} - P {float(e['amount']):,.2f} ({e['category']})")

            return "\n".join(lines)

    # -- Main Entry Point ----------------------------------

    def chat(self, user_message: str) -> dict:
        """
        Main agent entry point. Executes the full agentic pipeline:
        1. Classify intent (keyword matching)
        2. Retrieve relevant data from Supabase (tool usage)
        3. Apply decision rules to generate response
        4. Store in conversation history (memory)

        Returns dict with intent, data_retrieved flag, and response text.
        """
        # Step 1: Classify
        intent = self._classify_intent(user_message)

        # Step 2: Retrieve data (tool usage)
        context = self._retrieve_data(intent)

        # Step 3: Generate response (rule-based logic)
        response = self._generate_response(intent, context, user_message)

        # Step 4: Store in memory
        self.conversation_history.append({"role": "user", "content": user_message})
        self.conversation_history.append({"role": "assistant", "content": response})

        return {
            "intent": intent,
            "data_retrieved": bool(context),
            "response": response,
            "steps": [
                f"1. Classified intent: {intent} (keyword matching)",
                f"2. Retrieved data from Supabase ({len(json.dumps(context, default=str))} chars)",
                f"3. Applied decision rules for '{intent}' response template",
                f"4. Stored in memory ({len(self.conversation_history)//2} exchanges)",
            ],
        }

    def get_history(self):
        """Return conversation history."""
        return self.conversation_history

    def clear_history(self):
        """Clear conversation memory."""
        self.conversation_history = []
