from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database.database import get_db, Transaction, User
from models.schemas import CorrectRequest, CorrectResponse
from routers.auth import require_auth

router = APIRouter(prefix="/correct", tags=["correct"])
VALID_CATEGORIES = {"food","transport","shopping","health","emi","investment","transfer","utilities","education","daily_expense","others"}

@router.patch("", response_model=CorrectResponse)
def correct_category(req: CorrectRequest, user: User = Depends(require_auth), db: Session = Depends(get_db)):
    txn = db.query(Transaction).filter(Transaction.id==req.transaction_id, Transaction.user_id==user.id).first()
    if not txn:
        raise HTTPException(status_code=404, detail="Transaction not found.")
    if req.correct_category not in VALID_CATEGORIES:
        raise HTTPException(status_code=400, detail="Invalid category.")
    old = txn.final_category or txn.predicted_category
    txn.user_corrected_category = req.correct_category
    txn.final_category = req.correct_category
    txn.is_corrected = True
    txn.corrected_at = datetime.utcnow()
    db.commit()
    return CorrectResponse(success=True, transaction_id=txn.id, old_category=old, new_category=req.correct_category)

@router.get("/categories")
def list_categories():
    return {"categories": sorted(VALID_CATEGORIES), "display_names": {
        "food":"🍕 Food & Dining","transport":"🚗 Transport","shopping":"🛒 Shopping",
        "health":"🏥 Health","emi":"🏦 EMI & Loans","investment":"📈 Investment",
        "transfer":"👥 Transfers","utilities":"💡 Utilities & Bills",
        "education":"📚 Education","daily_expense":"☕ Daily Expenses","others":"📦 Others"}}
