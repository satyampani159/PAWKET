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


# ---------------------------------------------------------------------------
# Category classification for 50/30/20
# "needs" = essential, "wants" = lifestyle, "savings" = investment/savings
# ---------------------------------------------------------------------------

NEEDS_CATEGORIES  = {"emi", "utilities", "health", "transport", "education"}
WANTS_CATEGORIES  = {"food", "shopping", "daily_expense", "transfer"}
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
    "daily_expense": 0.05,
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
    from collections import defaultdict
    import math

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
) -> list[dict]:
    insights = []

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
