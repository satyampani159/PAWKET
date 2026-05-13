from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from datetime import datetime
from database.database import get_db, User
from services.analytics import get_monthly_analytics
from services.finance_rules import analyze_5030_20, compute_category_budgets, detect_recurring, generate_insights, estimate_income
from routers.auth import require_auth

router = APIRouter(prefix="/advice", tags=["advice"])

GOAL_TIPS = {
    "save_more":      "Since your goal is to save more, focus on cutting want-based spending.",
    "debt_free":      "Your goal is to be debt free — every extra rupee on EMI saves you interest.",
    "invest":         "To grow your investments, redirect food and shopping savings into SIPs.",
    "buy_home":       "For your home buying goal, build a dedicated savings bucket this month.",
    "retire_early":   "Early retirement needs aggressive saving — aim for 30%+ savings rate.",
    "emergency_fund": "Build 6 months of expenses as emergency fund before other investments.",
}

@router.get("")
def advice_endpoint(month: str = Query(default=None), income: float = Query(default=None),
    user: User = Depends(require_auth), db: Session = Depends(get_db)):

    if not month:
        month = datetime.utcnow().strftime("%Y-%m")

    analytics = get_monthly_analytics(db, month, user.id)
    if not analytics.get("transactions"):
        return {"month": month, "message": "No transactions found for this month."}

    transactions    = analytics["transactions"]
    category_totals = analytics.get("category_totals", {})
    kpis            = analytics.get("kpis", {})

    # Use profile income if available, else estimate
    estimated_income = income or user.monthly_income or estimate_income(transactions)

    # Build personalised greeting
    name   = user.name or "there"
    gender = user.gender or ""
    pronoun = "his" if gender == "male" else "her" if gender == "female" else "their"
    greeting = f"Hi {name}! Here's {pronoun} financial summary for {month}."

    # Goal-based tip
    goal_tip = GOAL_TIPS.get(user.financial_goal, "") if user.financial_goal else ""

    # Generate insights with user context
    insights = generate_insights(
        category_totals   = category_totals,
        estimated_income  = estimated_income,
        transaction_count = kpis.get("transaction_count", 0),
        recurring         = detect_recurring(transactions),
        correction_rate   = kpis.get("correction_rate", 0),
        user_name         = name,
        user_goal         = user.financial_goal,
    )

    # Add goal-specific insight at the top
    if goal_tip:
        insights.insert(0, {
            "type":     "tip",
            "title":    f"Your Goal: {user.financial_goal.replace('_', ' ').title()}",
            "message":  goal_tip,
            "category": None,
        })

    return {
        "month":            month,
        "greeting":         greeting,
        "estimated_income": round(estimated_income, 2),
        "budget_rule":      analyze_5030_20(category_totals, estimated_income),
        "category_budgets": compute_category_budgets(category_totals, estimated_income),
        "insights":         insights,
        "recurring_detected": detect_recurring(transactions),
        "user_profile": {
            "name":           user.name,
            "gender":         user.gender,
            "age":            user.age,
            "financial_goal": user.financial_goal,
        }
    }
