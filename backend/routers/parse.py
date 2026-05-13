import json
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database.database import get_db, Transaction, User
from models.schemas import ParseRequest, ParseResponse
from services.parser import parse_sms
from services.categorizer import categorize
from services.deduplication import is_duplicate
from ml.ml_loader import ml_models
from routers.auth import require_auth

router = APIRouter(prefix="/parse", tags=["parse"])


def _process_one(text, sms_id, received_at, user_id, db):
    """Shared logic for single and batch parse."""
    text = text.strip()
    if not text:
        return "empty", None

    is_financial, _ = ml_models.predict_filter(text)
    if not is_financial:
        return "ignored", None

    parsed   = parse_sms(text)
    received = received_at or parsed.get("received_at") or datetime.utcnow()
    amount   = parsed.get("amount")
    txn_type = parsed.get("transaction_type", "debit")

    # Smart deduplication — catches UPI app + bank SMS duplicates
    if is_duplicate(db, user_id, amount, txn_type, received, sms_id, text):
        return "duplicate", None

    cat = categorize(
        text=text, amount=amount,
        received_at=received, merchant=parsed.get("merchant"),
    )

    txn = Transaction(
        user_id            = user_id,
        sms_id             = sms_id,
        raw_text           = text,
        amount             = amount,
        merchant           = parsed.get("merchant"),
        bank               = parsed.get("bank"),
        transaction_type   = txn_type,
        received_at        = received,
        predicted_category = cat["predicted_category"],
        ml_confidence      = cat["confidence"],
        all_scores         = json.dumps(cat["all_scores"]),
        pattern_category   = cat["pattern_category"],
        final_category     = cat["final_category"],
        is_corrected       = False,
    )
    db.add(txn)
    return "parsed", txn


@router.post("", response_model=ParseResponse)
def parse_endpoint(req: ParseRequest, user: User = Depends(require_auth), db: Session = Depends(get_db)):
    if not ml_models.loaded:
        raise HTTPException(status_code=503, detail="ML models not loaded.")

    status, txn = _process_one(
        req.text, req.sms_id, req.received_at, user.id, db
    )

    if status == "empty":
        raise HTTPException(status_code=400, detail="SMS text is empty.")

    if status in ("ignored", "duplicate"):
        return ParseResponse(
            status=status,
            message="Not a financial SMS." if status == "ignored" else "Duplicate transaction skipped.",
            sms_id=req.sms_id, transaction_id=None,
            amount=None, merchant=None, transaction_type=None,
            received_at=None, bank=None, predicted_category=None,
            confidence=None, confidence_tier=None, all_scores=None,
            pattern_category=None, final_category=None,
        )

    db.commit()
    db.refresh(txn)

    parsed = parse_sms(req.text)
    cat    = categorize(text=req.text, amount=txn.amount, received_at=txn.received_at, merchant=txn.merchant)

    return ParseResponse(
        status="parsed", sms_id=req.sms_id, transaction_id=txn.id,
        amount=txn.amount, merchant=txn.merchant,
        transaction_type=txn.transaction_type, received_at=txn.received_at,
        bank=txn.bank, predicted_category=cat["predicted_category"],
        confidence=cat["confidence"], confidence_tier=cat["confidence_tier"],
        all_scores=cat["all_scores"], pattern_category=cat["pattern_category"],
        final_category=cat["final_category"], message=None,
    )


@router.post("/batch")
def parse_batch(req: list[ParseRequest], user: User = Depends(require_auth), db: Session = Depends(get_db)):
    if len(req) > 500:
        raise HTTPException(status_code=400, detail="Max 500 messages per batch.")

    parsed_count = ignored_count = duplicate_count = 0

    for item in req:
        status, _ = _process_one(
            item.text, item.sms_id, item.received_at, user.id, db
        )
        if status == "parsed":
            parsed_count += 1
        elif status == "ignored" or status == "empty":
            ignored_count += 1
        elif status == "duplicate":
            duplicate_count += 1

    db.commit()

    return {
        "parsed":     parsed_count,
        "ignored":    ignored_count,
        "duplicates": duplicate_count,
        "total":      len(req),
    }


@router.get("/dedup-scan")
def dedup_scan(user: User = Depends(require_auth), db: Session = Depends(get_db)):
    """
    Scans existing transactions and returns potential duplicate groups.
    Call this to clean up data imported before deduplication was active.
    """
    from services.deduplication import find_duplicate_groups
    groups = find_duplicate_groups(db, user.id)
    return {
        "duplicate_groups": len(groups),
        "total_to_delete":  sum(len(g["delete_ids"]) for g in groups),
        "groups":           groups[:20],  # return first 20 for review
    }


@router.delete("/dedup-clean")
def dedup_clean(user: User = Depends(require_auth), db: Session = Depends(get_db)):
    """
    Automatically removes detected duplicates, keeping the first occurrence.
    """
    from services.deduplication import find_duplicate_groups
    groups = find_duplicate_groups(db, user.id)
    total_deleted = 0
    for group in groups:
        for del_id in group["delete_ids"]:
            db.query(Transaction).filter(
                Transaction.id == del_id,
                Transaction.user_id == user.id,
            ).delete()
            total_deleted += 1
    db.commit()
    return {"deleted": total_deleted, "groups_cleaned": len(groups)}
