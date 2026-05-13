"""
services/categorizer.py
-----------------------
Two-stage categorization:
  Stage 1 — ML model predicts category + confidence
  Stage 2 — Pattern engine overrides "others" using amount + time signals

Final category priority:
  user_corrected_category  (always wins — user is the ground truth)
  > pattern_category       (amount/time heuristics)
  > predicted_category     (ML model)
"""

import re
from datetime import datetime
from typing import Optional
from ml.ml_loader import ml_models
from models.schemas import get_confidence_tier


# ---------------------------------------------------------------------------
# Stage 2 — Pattern engine
# Runs only when ML says "others" OR confidence is below 0.60
# ---------------------------------------------------------------------------

# Amount brackets → likely categories
AMOUNT_RULES = [
    # (min, max, hour_start, hour_end, category, reason)
    # Small morning spend → transport (auto/metro/bus)
    (5,    80,   5,  10, "transport",     "small morning payment"),
    # Small midday spend → food (chai/lunch)
    (10,   200,  11, 15, "food",          "midday small payment"),
    # Small evening spend → food (tea/snacks/dinner)
    (10,   300,  18, 23, "food",          "evening small payment"),
    # Very small any time → daily expense (cigarette, biscuit, etc.)
    (1,    99,   0,  23, "daily_expense", "micro transaction"),
    # Medium any time → shopping
    (100,  500,  0,  23, "shopping",      "medium transaction"),
    # Large → likely EMI or rent
    (5000, 999999, 0, 23, "emi",          "large recurring amount"),
]

# Sender ID patterns → bank category signals
SENDER_CATEGORY_MAP = {
    r"swiggy|zomato|blinkit|zepto": "food",
    r"uber|ola|rapido|irctc":       "transport",
    r"amazon|flipkart|myntra":      "shopping",
    r"apollo|netmeds|pharmeasy":    "health",
    r"zerodha|groww|upstox":        "investment",
    r"netflix|hotstar|spotify":     "utilities",
    r"airtel|jio|vi|bsnl":         "utilities",
}


def pattern_engine(
    text: str,
    amount: Optional[float],
    received_at: Optional[datetime],
    merchant: Optional[str],
) -> Optional[str]:
    """
    Returns a category string if pattern logic can determine one,
    otherwise returns None (let ML prediction stand).
    """
    t = text.lower()

    # 1. Sender/merchant keyword match (fast path)
    for pattern, category in SENDER_CATEGORY_MAP.items():
        if re.search(pattern, t):
            return category

    # 2. Amount + time-of-day rules
    if amount is not None:
        hour = received_at.hour if received_at else 13  # default midday

        for min_amt, max_amt, h_start, h_end, category, _ in AMOUNT_RULES:
            if min_amt <= amount <= max_amt and h_start <= hour <= h_end:
                return category

    return None


# ---------------------------------------------------------------------------
# Recurring detection helper
# ---------------------------------------------------------------------------

def is_likely_recurring(amount: float, existing_amounts: list[float]) -> bool:
    """
    Returns True if this amount matches a pattern in recent transactions.
    Used to flag EMI / rent / subscriptions.
    """
    if not existing_amounts or amount is None:
        return False
    matches = [a for a in existing_amounts if abs(a - amount) / max(a, 1) < 0.05]
    return len(matches) >= 2  # same amount seen 2+ times before


# ---------------------------------------------------------------------------
# Main categorize function
# ---------------------------------------------------------------------------

def categorize(
    text: str,
    amount: Optional[float] = None,
    received_at: Optional[datetime] = None,
    merchant: Optional[str] = None,
    user_corrected_category: Optional[str] = None,
) -> dict:
    """
    Full two-stage categorization.

    Returns:
        predicted_category  — ML output
        confidence          — ML confidence (0-1)
        confidence_tier     — high / medium / low
        all_scores          — all category probabilities
        pattern_category    — pattern engine output (may be None)
        final_category      — what the app displays
    """

    # --- Stage 1: ML model ---
    ml_category, confidence, all_scores = ml_models.predict_category(text)
    confidence_tier = get_confidence_tier(confidence)

    # --- Stage 2: Pattern engine ---
    # Run if ML said "others" OR confidence is low
    pattern_cat = None
    if ml_category == "others" or confidence < 0.60:
        pattern_cat = pattern_engine(text, amount, received_at, merchant)

    # --- Final category resolution ---
    # Priority: user correction > pattern engine > ML
    if user_corrected_category:
        final = user_corrected_category
    elif pattern_cat:
        final = pattern_cat
    else:
        final = ml_category

    return {
        "predicted_category": ml_category,
        "confidence":         round(confidence, 4),
        "confidence_tier":    confidence_tier,
        "all_scores":         all_scores,
        "pattern_category":   pattern_cat,
        "final_category":     final,
    }
