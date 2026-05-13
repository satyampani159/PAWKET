"""
services/analytics.py
---------------------
Computes all analytics from the database.
Called by the /analytics router.
"""

from sqlalchemy.orm import Session
from sqlalchemy import extract, func
from datetime import datetime, date
from collections import defaultdict
import json

from database.database import Transaction


def get_monthly_analytics(db: Session, month: str) -> dict:
    """
    month: "2024-05"
    Returns full analytics dict for that month.
    """
    year, mon = int(month.split("-")[0]), int(month.split("-")[1])

    # Fetch all transactions for the month
    txns = db.query(Transaction).filter(
        extract("year",  Transaction.received_at) == year,
        extract("month", Transaction.received_at) == mon,
    ).all()

    if not txns:
        return {"month": month, "kpis": {}, "category_breakdown": [],
                "daily_trend": [], "top_merchants": [], "transactions": []}

    debits  = [t for t in txns if t.transaction_type == "debit"  and t.amount]
    credits = [t for t in txns if t.transaction_type == "credit" and t.amount]

    debit_amounts = [t.amount for t in debits]
    total_spend   = sum(debit_amounts)
    total_credit  = sum(t.amount for t in credits)

    # KPIs
    sorted_amounts = sorted(debit_amounts)
    n = len(sorted_amounts)
    median = (
        (sorted_amounts[n//2 - 1] + sorted_amounts[n//2]) / 2
        if n % 2 == 0 and n > 0
        else sorted_amounts[n//2] if n > 0 else 0
    )

    corrected_count = sum(1 for t in txns if t.is_corrected)
    correction_rate = corrected_count / len(txns) if txns else 0

    category_totals = defaultdict(float)
    category_counts = defaultdict(int)
    for t in debits:
        cat = t.final_category or "others"
        category_totals[cat] += t.amount
        category_counts[cat] += 1

    top_category     = max(category_totals, key=category_totals.get) if category_totals else ""
    top_category_amt = category_totals.get(top_category, 0)

    merchant_counts = defaultdict(int)
    for t in debits:
        if t.merchant:
            merchant_counts[t.merchant] += 1
    repeat_merchants = sum(1 for c in merchant_counts.values() if c > 1)

    kpis = {
        "total_spend":        round(total_spend, 2),
        "total_credit":       round(total_credit, 2),
        "net":                round(total_credit - total_spend, 2),
        "transaction_count":  len(txns),
        "avg_transaction":    round(total_spend / len(debits), 2) if debits else 0,
        "largest_transaction":round(max(debit_amounts), 2) if debit_amounts else 0,
        "smallest_transaction":round(min(debit_amounts), 2) if debit_amounts else 0,
        "median_transaction": round(median, 2),
        "most_spent_category":top_category,
        "most_spent_amount":  round(top_category_amt, 2),
        "repeat_merchants":   repeat_merchants,
        "uncategorized_count":category_counts.get("others", 0),
        "correction_rate":    round(correction_rate, 4),
    }

    # Category breakdown
    category_breakdown = []
    for cat, total in sorted(category_totals.items(), key=lambda x: -x[1]):
        category_breakdown.append({
            "category":        cat,
            "total":           round(total, 2),
            "count":           category_counts[cat],
            "percentage":      round(total / total_spend * 100, 1) if total_spend else 0,
            "avg_transaction": round(total / category_counts[cat], 2) if category_counts[cat] else 0,
        })

    # Daily trend
    daily = defaultdict(float)
    daily_cat = defaultdict(str)
    for t in debits:
        if t.received_at:
            day = t.received_at.strftime("%Y-%m-%d")
            daily[day] += t.amount
            daily_cat[day] = t.final_category or "others"

    daily_trend = [
        {"date": d, "amount": round(amt, 2), "category": daily_cat[d]}
        for d, amt in sorted(daily.items())
    ]

    # Top merchants
    merchant_spend = defaultdict(float)
    for t in debits:
        if t.merchant:
            merchant_spend[t.merchant] += t.amount

    top_merchants = [
        {"merchant": m, "total": round(amt, 2), "count": merchant_counts[m]}
        for m, amt in sorted(merchant_spend.items(), key=lambda x: -x[1])[:10]
    ]

    # Raw transactions for advice engine
    txn_list = [
        {
            "id":               t.id,
            "amount":           t.amount,
            "merchant":         t.merchant,
            "transaction_type": t.transaction_type,
            "final_category":   t.final_category,
            "received_at":      t.received_at.isoformat() if t.received_at else None,
        }
        for t in txns
    ]

    return {
        "month":              month,
        "kpis":               kpis,
        "category_breakdown": category_breakdown,
        "daily_trend":        daily_trend,
        "top_merchants":      top_merchants,
        "category_totals":    dict(category_totals),
        "transactions":       txn_list,
    }
