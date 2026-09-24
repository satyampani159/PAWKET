"""
services/ingest.py
------------------
Shared SMS ingestion used by:
  - POST /parse            (single message)
  - POST /parse/batch      (exported SMS batches)
  - POST /admin/load-batch (admin restore + store for auto-ingest)
  - startup bootstrap      (auto-ingest real batch / seed when DB is empty)
"""

import json
import os
from datetime import datetime
from pathlib import Path

from database.database import SessionLocal, Transaction, User

DEFAULT_REAL_PHONE = "+917377044562"


def _field(item, key, default=None):
    if isinstance(item, dict):
        return item.get(key, default)
    return getattr(item, key, default)


def _as_datetime(value):
    """Coerce ISO strings from raw JSON batches to datetime (HTTP path gets Pydantic coercion)."""
    if value is None or isinstance(value, datetime):
        return value
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except (ValueError, TypeError):
            return None
    return None


def process_one(text, sms_id, received_at, sender, user_id, db):
    """Parse + categorise one SMS into a Transaction. No commit — caller decides."""
    from ml.ml_loader import ml_models
    from services.parser import parse_sms
    from services.categorizer import categorize
    from services.deduplication import is_duplicate

    try:
        text = (text or "").strip()
        if not text:
            return "empty", None

        is_financial, _ = ml_models.predict_filter(text)
        if not is_financial:
            return "ignored", None

        parsed   = parse_sms(text)
        received = _as_datetime(received_at) or _as_datetime(parsed.get("received_at")) or datetime.utcnow()
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
            sender             = sender,
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
    except Exception as e:
        print(f"[PARSE] Error processing SMS: {e}")
        return "error", None


def ingest_entries(entries, user, db):
    """Ingest a list of SMS entries (dicts or ParseRequest objects) for a user.

    Commits once at the end. Returns counters:
    {"parsed", "ignored", "duplicates", "errors", "total"}
    """
    counts = {"parsed": 0, "ignored": 0, "duplicates": 0, "errors": 0, "total": len(entries)}
    for item in entries:
        status, _ = process_one(
            _field(item, "text"),
            _field(item, "sms_id"),
            _field(item, "received_at"),
            _field(item, "sender"),
            user.id,
            db,
        )
        if status == "parsed":
            counts["parsed"] += 1
        elif status in ("ignored", "empty"):
            counts["ignored"] += 1
        elif status == "duplicate":
            counts["duplicates"] += 1
        else:
            counts["errors"] += 1
    db.commit()
    return counts


def get_or_create_user(db, phone, **profile):
    user = db.query(User).filter(User.phone == phone).first()
    if not user:
        user = User(phone=phone, created_at=datetime.utcnow(), **profile)
        db.add(user)
        db.commit()
        db.refresh(user)
        print(f"[INGEST] Created user {phone}")
    return user


def store_batch_file(entries, path_str=None):
    """Persist the batch JSON so startup auto-ingest can replay it if the DB empties.

    Returns (stored: bool, path: str|None). Best-effort — never raises.
    """
    path_str = path_str or os.getenv("REAL_SMS_BATCH")
    if not path_str:
        return False, None
    try:
        path = Path(path_str)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(entries, ensure_ascii=False), encoding="utf-8")
        print(f"[INGEST] Stored batch ({len(entries)} entries) at {path}")
        return True, str(path)
    except Exception as e:
        print(f"[INGEST] Could not store batch at {path_str}: {e}")
        return False, path_str


def auto_seed_enabled():
    return os.getenv("AUTO_SEED", "true").strip().lower() in ("1", "true", "yes", "on")


def bootstrap_if_empty():
    """Called at startup when the DB might be empty (fresh volume / wiped container).

    Priority: existing data > REAL_SMS_BATCH auto-ingest > AUTO_SEED test data.
    """
    from ml.ml_loader import ml_models

    db = SessionLocal()
    try:
        existing = db.query(Transaction).count()
        if existing > 0:
            print(f"[BOOTSTRAP] DB already has {existing} transactions — nothing to do.")
            return "existing"

        batch_path = os.getenv("REAL_SMS_BATCH")
        if batch_path and Path(batch_path).exists():
            if not ml_models.loaded:
                print(f"[BOOTSTRAP] ML models not loaded — cannot ingest {batch_path}.")
            else:
                entries = json.loads(Path(batch_path).read_text(encoding="utf-8"))
                phone = os.getenv("REAL_PHONE", DEFAULT_REAL_PHONE)
                user = get_or_create_user(db, phone)
                counts = ingest_entries(entries, user, db)
                print(f"[BOOTSTRAP] Auto-ingested {batch_path} for {phone}: {counts}")
                return "ingested"

        if auto_seed_enabled():
            from services.auto_seed import auto_seed
            auto_seed()
            return "seeded"

        print("[BOOTSTRAP] DB empty; AUTO_SEED disabled and no REAL_SMS_BATCH found — left empty.")
        return "empty"
    finally:
        db.close()
