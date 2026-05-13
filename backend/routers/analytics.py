from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import extract, func
from datetime import datetime
from database.database import get_db, Transaction, User
from services.analytics import get_monthly_analytics
from routers.auth import require_auth

router = APIRouter(prefix="/analytics", tags=["analytics"])

@router.get("")
def analytics_endpoint(month: str = Query(default=None), user: User = Depends(require_auth), db: Session = Depends(get_db)):
    if not month:
        month = datetime.utcnow().strftime("%Y-%m")
    try:
        datetime.strptime(month, "%Y-%m")
    except ValueError:
        return {"error": "Invalid month format. Use YYYY-MM"}
    return get_monthly_analytics(db, month, user.id)

@router.get("/months")
def available_months(user: User = Depends(require_auth), db: Session = Depends(get_db)):
    rows = (db.query(func.strftime("%Y-%m", Transaction.received_at).label("month"),
        func.count(Transaction.id).label("count"))
        .filter(Transaction.user_id==user.id, Transaction.received_at.isnot(None))
        .group_by("month").order_by("month").all())
    return {"months": [{"month": r.month, "count": r.count} for r in rows]}

@router.get("/transactions")
def get_transactions(month: str = Query(default=None), category: str = Query(default=None),
    limit: int = Query(default=50), offset: int = Query(default=0),
    user: User = Depends(require_auth), db: Session = Depends(get_db)):
    query = db.query(Transaction).filter(Transaction.user_id==user.id)
    if month:
        try:
            year, mon = int(month.split("-")[0]), int(month.split("-")[1])
            query = query.filter(extract("year", Transaction.received_at)==year,
                extract("month", Transaction.received_at)==mon)
        except: pass
    if category:
        query = query.filter(Transaction.final_category==category)
    total = query.count()
    txns = query.order_by(Transaction.received_at.desc()).offset(offset).limit(limit).all()
    return {"total": total, "offset": offset, "limit": limit, "transactions": [
        {"id": t.id, "amount": t.amount, "merchant": t.merchant, "bank": t.bank,
         "transaction_type": t.transaction_type,
         "received_at": t.received_at.isoformat() if t.received_at else None,
         "final_category": t.final_category, "predicted_category": t.predicted_category,
         "confidence": t.ml_confidence, "is_corrected": t.is_corrected,
         "user_corrected_category": t.user_corrected_category} for t in txns]}
