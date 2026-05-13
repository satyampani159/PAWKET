from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from database.database import get_db, User, Transaction
from routers.auth import require_auth

router = APIRouter(prefix="/profile", tags=["profile"])

VALID_GOALS = {
    "save_more":      "Save More Money",
    "debt_free":      "Become Debt Free",
    "invest":         "Grow Investments",
    "buy_home":       "Buy a Home",
    "retire_early":   "Retire Early",
    "emergency_fund": "Build Emergency Fund",
}

GOAL_ADVICE = {
    "save_more": {
        "tip": "Try saving at least 20% of your income every month.",
        "focus": "Cut wants spending — aim for 50/30/20 rule.",
    },
    "debt_free": {
        "tip": "Pay more than the minimum on your EMIs to clear debt faster.",
        "focus": "Prioritise EMI payments before discretionary spending.",
    },
    "invest": {
        "tip": "Start a SIP of at least ₹500/month — consistency beats timing.",
        "focus": "Redirect shopping and food savings into mutual funds.",
    },
    "buy_home": {
        "tip": "Save at least 20% of property value as down payment.",
        "focus": "Reduce lifestyle inflation and build a dedicated home fund.",
    },
    "retire_early": {
        "tip": "Invest 30%+ of income — the earlier you start, the better.",
        "focus": "Maximise NPS and ELSS investments for tax-efficient growth.",
    },
    "emergency_fund": {
        "tip": "Build 6 months of expenses as emergency fund before investing.",
        "focus": "Park money in liquid funds or high-interest savings accounts.",
    },
}

class ProfileUpdate(BaseModel):
    name:           Optional[str]   = None
    email:          Optional[str]   = None
    gender:         Optional[str]   = None
    age:            Optional[int]   = None
    financial_goal: Optional[str]   = None
    profile_photo:  Optional[str]   = None
    monthly_income: Optional[float] = None

class ProfileResponse(BaseModel):
    user_id:        int
    phone:          str
    name:           Optional[str]
    email:          Optional[str]
    gender:         Optional[str]
    age:            Optional[int]
    financial_goal: Optional[str]
    financial_goal_label: Optional[str]
    profile_photo:  Optional[str]
    monthly_income: Optional[float]
    transaction_count: int
    member_since:   str
    goal_advice:    Optional[dict]

@router.get("", response_model=ProfileResponse)
def get_profile(user: User = Depends(require_auth), db: Session = Depends(get_db)):
    count = db.query(Transaction).filter(Transaction.user_id == user.id).count()
    goal_advice = GOAL_ADVICE.get(user.financial_goal) if user.financial_goal else None
    return ProfileResponse(
        user_id        = user.id,
        phone          = user.phone,
        name           = user.name,
        email          = user.email,
        gender         = user.gender,
        age            = user.age,
        financial_goal = user.financial_goal,
        financial_goal_label = VALID_GOALS.get(user.financial_goal) if user.financial_goal else None,
        profile_photo  = user.profile_photo,
        monthly_income = user.monthly_income,
        transaction_count = count,
        member_since   = user.created_at.strftime("%b %Y"),
        goal_advice    = goal_advice,
    )

@router.patch("")
def update_profile(req: ProfileUpdate, user: User = Depends(require_auth), db: Session = Depends(get_db)):
    if req.name           is not None: user.name           = req.name.strip()
    if req.email          is not None: user.email          = req.email.strip()
    if req.gender         is not None: user.gender         = req.gender
    if req.age            is not None: user.age            = req.age
    if req.financial_goal is not None:
        if req.financial_goal not in VALID_GOALS:
            raise HTTPException(status_code=400, detail=f"Invalid goal. Choose from: {list(VALID_GOALS.keys())}")
        user.financial_goal = req.financial_goal
    if req.profile_photo  is not None: user.profile_photo  = req.profile_photo
    if req.monthly_income is not None: user.monthly_income = req.monthly_income
    db.commit()
    return {"success": True, "message": "Profile updated."}

@router.get("/goals")
def list_goals():
    return {"goals": [{"key": k, "label": v} for k, v in VALID_GOALS.items()]}
