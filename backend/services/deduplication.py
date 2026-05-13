"""
services/deduplication.py
--------------------------
Smart deduplication for Indian financial SMS.

Problem: UPI transactions generate 2 SMS — one from the UPI app
(PhonePe, GPay) and one from the bank. Same transaction, two messages.

Solution: If a transaction with the same amount (±₹1), same type
(debit/credit), and within 5 minutes already exists for this user
→ it's a duplicate. Skip it.

Also handles: same SMS text arriving twice (exact duplicate).
"""

from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from database.database import Transaction

AMOUNT_TOLERANCE   = 1.0    # ₹1 tolerance for rounding differences
TIME_WINDOW_MINS   = 5      # minutes — UPI + bank SMS arrive within seconds


def is_duplicate(
    db:       Session,
    user_id:  int,
    amount:   float,
    txn_type: str,
    received_at: datetime,
    sms_id:   str = None,
    raw_text: str = None,
) -> bool:
    """
    Returns True if this transaction already exists in the database.

    Checks in order:
    1. Exact SMS ID match (fastest)
    2. Exact text match (same SMS delivered twice)
    3. Amount + type + time window match (UPI app vs bank SMS)
    """

    # 1. Exact SMS ID
    if sms_id:
        exists = db.query(Transaction.id).filter(
            Transaction.user_id == user_id,
            Transaction.sms_id  == sms_id,
        ).first()
        if exists:
            return True

    # 2. Exact text match
    if raw_text:
        exists = db.query(Transaction.id).filter(
            Transaction.user_id  == user_id,
            Transaction.raw_text == raw_text,
        ).first()
        if exists:
            return True

    # 3. Amount + type + time window
    if amount is not None and received_at is not None:
        window_start = received_at - timedelta(minutes=TIME_WINDOW_MINS)
        window_end   = received_at + timedelta(minutes=TIME_WINDOW_MINS)

        similar = db.query(Transaction.id).filter(
            Transaction.user_id        == user_id,
            Transaction.transaction_type == txn_type,
            Transaction.amount.between(amount - AMOUNT_TOLERANCE, amount + AMOUNT_TOLERANCE),
            Transaction.received_at.between(window_start, window_end),
        ).first()

        if similar:
            return True

    return False


def find_duplicate_groups(db: Session, user_id: int) -> list[dict]:
    """
    Scans existing transactions and finds potential duplicate groups.
    Returns list of groups for admin review.
    Used for cleaning up existing data.
    """
    txns = db.query(Transaction).filter(
        Transaction.user_id == user_id,
        Transaction.amount.isnot(None),
    ).order_by(Transaction.received_at).all()

    groups = []
    used_ids = set()

    for i, t1 in enumerate(txns):
        if t1.id in used_ids:
            continue
        group = [t1]
        for t2 in txns[i+1:]:
            if t2.id in used_ids:
                continue
            if t2.transaction_type != t1.transaction_type:
                continue
            if abs((t2.amount or 0) - (t1.amount or 0)) > AMOUNT_TOLERANCE:
                continue
            if t1.received_at and t2.received_at:
                diff = abs((t2.received_at - t1.received_at).total_seconds())
                if diff > TIME_WINDOW_MINS * 60:
                    break  # sorted by time, no point continuing
                group.append(t2)
                used_ids.add(t2.id)
        if len(group) > 1:
            used_ids.add(t1.id)
            groups.append({
                "amount":      t1.amount,
                "type":        t1.transaction_type,
                "received_at": t1.received_at.isoformat() if t1.received_at else None,
                "count":       len(group),
                "ids":         [t.id for t in group],
                "keep_id":     group[0].id,  # keep the first one
                "delete_ids":  [t.id for t in group[1:]],
            })

    return groups
