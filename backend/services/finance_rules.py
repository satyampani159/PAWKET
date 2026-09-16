"""
services/finance_rules.py
-------------------------
Pure financial logic — no ML, no DB queries.
Takes analytics data as input, returns budgets, advice, and insights.

Rules implemented:
  - 50/30/20 budget rule
  - Per-category budget limits
  - Recurring payment detection
  - Spending pattern insights
  - Saving suggestions
"""

from typing import Optional
from collections import defaultdict
from datetime import datetime


# ---------------------------------------------------------------------------
# Category classification for 50/30/20
# "needs" = essential, "wants" = lifestyle, "savings" = investment/savings
# ---------------------------------------------------------------------------

NEEDS_CATEGORIES  = {"emi", "utilities", "health", "transport", "education", "transfer"}
WANTS_CATEGORIES  = {"food", "shopping"}
SAVING_CATEGORIES = {"investment"}


# ---------------------------------------------------------------------------
# Suggested budget limits — % of monthly income per category
# These are starting points; app can let user customise them
# ---------------------------------------------------------------------------

CATEGORY_BUDGET_PERCENT = {
    "food":          0.15,   # 15% of income
    "transport":     0.08,
    "shopping":      0.10,
    "health":        0.05,
    "emi":           0.35,   # EMIs typically cap at 35-40% (RBI guideline)
    "investment":    0.20,
    "utilities":     0.08,
    "education":     0.05,
    "transfer":      0.05,
    "others":        0.05,
}

# Absolute minimum monthly savings goal
MIN_SAVINGS_PERCENT = 0.10


# ---------------------------------------------------------------------------
# 50/30/20 analysis
# ---------------------------------------------------------------------------

def analyze_5030_20(
    category_totals: dict[str, float],
    estimated_income: float,
) -> dict:
    """
    Compares actual spending to the 50/30/20 rule.
    Returns actual vs target for needs / wants / savings.
    """
    needs_actual  = sum(category_totals.get(c, 0) for c in NEEDS_CATEGORIES)
    wants_actual  = sum(category_totals.get(c, 0) for c in WANTS_CATEGORIES)
    saving_actual = sum(category_totals.get(c, 0) for c in SAVING_CATEGORIES)

    needs_limit   = estimated_income * 0.50
    wants_limit   = estimated_income * 0.30
    saving_limit  = estimated_income * 0.20

    def status(actual, limit):
        if actual <= limit * 1.05:
            return "on_track"
        return "over"

    return {
        "rule_name":      "50/30/20",
        "needs_limit":    round(needs_limit, 2),
        "wants_limit":    round(wants_limit, 2),
        "savings_limit":  round(saving_limit, 2),
        "needs_actual":   round(needs_actual, 2),
        "wants_actual":   round(wants_actual, 2),
        "savings_actual": round(saving_actual, 2),
        "needs_status":   status(needs_actual, needs_limit),
        "wants_status":   status(wants_actual, wants_limit),
        "savings_status": status(saving_actual, saving_limit),
    }


# ---------------------------------------------------------------------------
# Per-category budget limits
# ---------------------------------------------------------------------------

def compute_category_budgets(
    category_totals: dict[str, float],
    estimated_income: float,
) -> list[dict]:
    budgets = []
    for category, percent in CATEGORY_BUDGET_PERCENT.items():
        limit  = round(estimated_income * percent, 2)
        actual = round(category_totals.get(category, 0), 2)
        over   = round(actual - limit, 2) if actual > limit else None

        budgets.append({
            "category":        category,
            "suggested_limit": limit,
            "actual_spend":    actual,
            "status":          "over" if actual > limit else "on_track",
            "over_by":         over,
        })

    return sorted(budgets, key=lambda x: x["actual_spend"], reverse=True)


# ---------------------------------------------------------------------------
# Recurring payment detection
# ---------------------------------------------------------------------------

def detect_recurring(transactions: list[dict]) -> list[dict]:
    """
    Groups transactions by (merchant or amount) and detects monthly patterns.
    Returns list of detected recurring payments with suggested category.
    """

    # Group by merchant first, then by rounded amount
    merchant_groups = defaultdict(list)
    amount_groups   = defaultdict(list)

    for txn in transactions:
        if txn.get("transaction_type") == "credit":
            continue
        if txn.get("merchant"):
            merchant_groups[txn["merchant"].lower()].append(txn)
        if txn.get("amount"):
            # Round to nearest 10 for grouping
            rounded = round(txn["amount"] / 10) * 10
            amount_groups[rounded].append(txn)

    recurring = []

    # Merchant-based recurring
    for merchant, txns in merchant_groups.items():
        if len(txns) >= 2:
            amounts = [t["amount"] for t in txns if t.get("amount")]
            if not amounts:
                continue
            avg_amount  = sum(amounts) / len(amounts)
            variance    = max(amounts) - min(amounts)

            # Low variance = likely fixed recurring payment
            if variance < avg_amount * 0.10:
                recurring.append({
                    "label":       merchant.title(),
                    "merchant":    merchant.title(),
                    "amount":      round(avg_amount, 2),
                    "occurrences": len(txns),
                    "type":        "merchant_recurring",
                    "category":    txns[0].get("final_category", "emi"),
                })

    # Amount-based recurring (no merchant name)
    for rounded_amt, txns in amount_groups.items():
        merchants = [t.get("merchant") for t in txns if t.get("merchant")]
        if len(txns) >= 2 and len(merchants) == 0:
            # No merchant name — likely a bank transfer / EMI
            recurring.append({
                "label":       f"Fixed payment of ₹{rounded_amt}",
                "merchant":    None,
                "amount":      float(rounded_amt),
                "occurrences": len(txns),
                "type":        "amount_recurring",
                "category":    "emi",
            })

    return recurring


# ---------------------------------------------------------------------------
# Insight generator
# ---------------------------------------------------------------------------

def generate_insights(
    category_totals: dict[str, float],
    estimated_income: float,
    transaction_count: int,
    recurring: list[dict],
    correction_rate: float,
    user_name: Optional[str] = None,
    user_goal: Optional[str] = None,
    transactions: Optional[list[dict]] = None,
    kpis: Optional[dict] = None,
    months_data: Optional[list[dict]] = None,
) -> list[dict]:
    insights = []

    if transactions is None:
        transactions = []
    if kpis is None:
        kpis = {}
    if months_data is None:
        months_data = []

    total_spend = sum(category_totals.values())

    # 1. Overspending warnings
    for category, percent in CATEGORY_BUDGET_PERCENT.items():
        actual = category_totals.get(category, 0)
        limit  = estimated_income * percent
        if actual > limit * 1.20:   # 20% over budget
            insights.append({
                "type":     "warning",
                "title":    f"High {category.title()} Spend",
                "message":  f"You spent ₹{actual:,.0f} on {category} this month — "
                            f"₹{actual - limit:,.0f} over your ₹{limit:,.0f} budget.",
                "category": category,
            })

    # 2. Savings check
    savings_actual  = category_totals.get("investment", 0)
    savings_target  = estimated_income * 0.20
    if savings_actual < savings_target * 0.50:
        insights.append({
            "type":     "warning",
            "title":    "Low Savings This Month",
            "message":  f"You invested ₹{savings_actual:,.0f} — aim for at least "
                        f"₹{savings_target:,.0f} (20% of income).",
            "category": "investment",
        })

    # 3. Food heavy
    food_pct = category_totals.get("food", 0) / max(total_spend, 1) * 100
    if food_pct > 25:
        insights.append({
            "type":     "tip",
            "title":    "Food Budget Running High",
            "message":  f"{food_pct:.0f}% of your spending is on food. "
                        "Cooking at home 2–3 days a week could save you "
                        f"₹{category_totals.get('food', 0) * 0.3:,.0f} next month.",
            "category": "food",
        })

    # 4. Recurring detected
    if recurring:
        total_recurring = sum(r["amount"] for r in recurring)
        insights.append({
            "type":     "tip",
            "title":    f"{len(recurring)} Recurring Payments Detected",
            "message":  f"₹{total_recurring:,.0f}/month in fixed payments. "
                        "Review if all subscriptions are still needed.",
            "category": None,
        })

    # 5. Achievement — low correction rate means model is accurate
    if correction_rate < 0.05 and transaction_count > 20:
        insights.append({
            "type":    "achievement",
            "title":   "Great Categorization Accuracy",
            "message": "Less than 5% of your transactions needed correction. "
                       "Your finance model is well tuned!",
            "category": None,
        })

    # 6. Many uncategorized
    others_pct = category_totals.get("others", 0) / max(total_spend, 1) * 100
    if others_pct > 20:
        insights.append({
            "type":    "tip",
            "title":   "Help Us Categorize Better",
            "message": f"{others_pct:.0f}% of transactions are uncategorized. "
                       "Tap any transaction to assign the right category — "
                       "it improves future predictions.",
            "category": None,
        })

    # 7. Month-over-month spending change
    if len(months_data) >= 2:
        current_total = kpis.get("total_spend", 0)
        prev_month = months_data[-2] if len(months_data) > 1 else None
        if prev_month and prev_month.get("kpis", {}).get("total_spend", 0) > 0:
            prev_total = prev_month["kpis"]["total_spend"]
            change_pct = ((current_total - prev_total) / prev_total) * 100
            if abs(change_pct) > 10:
                direction = "increased" if change_pct > 0 else "decreased"
                insights.append({
                    "type": "warning" if change_pct > 0 else "tip",
                    "title": f"Spending {direction.title()}",
                    "message": f"Your spending {direction} by {abs(change_pct):.0f}% compared to last month (₹{prev_total:,.0f} → ₹{current_total:,.0f}).",
                    "category": None,
                })

    # 8. Top merchant concentration
    if transactions:
        merchant_totals = defaultdict(float)
        for t in transactions:
            if t.get("transaction_type") == "debit" and t.get("merchant"):
                merchant_totals[t["merchant"]] += t.get("amount", 0)
        if merchant_totals:
            total_spend_kpi = kpis.get("total_spend", 1)
            top_3 = sorted(merchant_totals.items(), key=lambda x: -x[1])[:3]
            top_3_total = sum(amt for _, amt in top_3)
            top_3_pct = (top_3_total / total_spend_kpi * 100) if total_spend_kpi else 0
            if top_3_pct > 40:
                names = ", ".join(m for m, _ in top_3)
                insights.append({
                    "type": "tip",
                    "title": "High Merchant Concentration",
                    "message": f"Your top 3 merchants ({names}) account for {top_3_pct:.0f}% of your spending. Consider diversifying.",
                    "category": None,
                })

    # 9. Weekend vs weekday spending
    weekday_spend = 0
    weekend_spend = 0
    weekday_count = 0
    weekend_count = 0
    for t in transactions:
        if t.get("transaction_type") == "debit" and t.get("received_at"):
            try:
                dt = datetime.fromisoformat(t["received_at"])
                if dt.weekday() >= 5:  # Saturday or Sunday
                    weekend_spend += t.get("amount", 0)
                    weekend_count += 1
                else:
                    weekday_spend += t.get("amount", 0)
                    weekday_count += 1
            except (ValueError, TypeError):
                pass
    if weekday_count > 0 and weekend_count > 0:
        weekday_avg = weekday_spend / weekday_count
        weekend_avg = weekend_spend / weekend_count
        if weekend_avg > weekday_avg * 1.3:
            insights.append({
                "type": "tip",
                "title": "Weekend Spending Spike",
                "message": f"You spend ₹{weekend_avg:,.0f} per transaction on weekends vs ₹{weekday_avg:,.0f} on weekdays. That's {((weekend_avg/weekday_avg - 1)*100):.0f}% more.",
                "category": None,
            })

    # 10. Savings rate based on income
    if estimated_income and estimated_income > 0:
        spend = kpis.get("total_spend", 0)
        savings = estimated_income - spend
        savings_rate = (savings / estimated_income) * 100
        if savings_rate < 10 and spend > 0:
            insights.append({
                "type": "warning",
                "title": "Low Savings Rate",
                "message": f"You're saving only {savings_rate:.0f}% of your income (₹{savings:,.0f} of ₹{estimated_income:,.0f}). Aim for at least 20%.",
                "category": None,
            })
        elif savings_rate >= 20:
            insights.append({
                "type": "achievement",
                "title": "Great Savings Rate",
                "message": f"You're saving {savings_rate:.0f}% of your income this month. Keep it up!",
                "category": None,
            })

    # 11. Single category dominance
    if category_totals:
        total_spend_main = kpis.get("total_spend", 1) or sum(category_totals.values()) or 1
        for cat, amt in category_totals.items():
            pct = (amt / total_spend_main * 100) if total_spend_main else 0
            if pct > 40 and cat != "emi":  # EMI is expected to be large
                cat_label = cat.replace("_", " ").title()
                insights.append({
                    "type": "warning",
                    "title": f"High {cat_label} Spending",
                    "message": f"{cat_label} accounts for {pct:.0f}% of your total spend (₹{amt:,.0f}). Consider setting a budget for this category.",
                    "category": cat,
                })
                break  # Only show one dominance warning

    return insights


# ---------------------------------------------------------------------------
# Income estimator
# ---------------------------------------------------------------------------

def estimate_income(transactions: list[dict]) -> float:
    """
    Estimates monthly income from credit transactions.
    Looks for a large, regular credit — likely salary.
    Falls back to 3x total spend if no salary detected.
    """
    credits = [
        t["amount"] for t in transactions
        if t.get("transaction_type") == "credit"
        and t.get("amount", 0) > 5000
    ]

    if credits:
        # Largest credit is probably salary
        return max(credits)

    # Fallback: assume total spend is ~60% of income (saving 40%)
    total_spend = sum(
        t.get("amount", 0) for t in transactions
        if t.get("transaction_type") == "debit"
    )
    return total_spend / 0.60 if total_spend > 0 else 30000  # default 30k
