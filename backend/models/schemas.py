"""
models/schemas.py
-----------------
All Pydantic request/response models.
The mobile app sends and receives these shapes exactly.
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


# ---------------------------------------------------------------------------
# Confidence tier — used by the app for color coding
# ---------------------------------------------------------------------------

class ConfidenceTier:
    HIGH   = "high"    # >= 85%  → green
    MEDIUM = "medium"  # 60-85%  → yellow
    LOW    = "low"     # < 60%   → red


def get_confidence_tier(confidence: float) -> str:
    if confidence >= 0.85:
        return ConfidenceTier.HIGH
    elif confidence >= 0.60:
        return ConfidenceTier.MEDIUM
    return ConfidenceTier.LOW


# ---------------------------------------------------------------------------
# Parse endpoint  POST /parse
# ---------------------------------------------------------------------------

class ParseRequest(BaseModel):
    text: str = Field(..., description="Raw SMS text from the phone")
    sms_id: Optional[str] = Field(None, description="Unique SMS ID from phone")
    received_at: Optional[datetime] = Field(None, description="When SMS was received")


class ParseResponse(BaseModel):
    status: str                         # "parsed" | "ignored"
    sms_id: Optional[str]
    transaction_id: Optional[int]       # DB row id — used for corrections

    # Extracted fields
    amount: Optional[float]
    merchant: Optional[str]
    transaction_type: Optional[str]     # "debit" | "credit"
    received_at: Optional[datetime]
    bank: Optional[str]

    # ML output
    predicted_category: Optional[str]
    confidence: Optional[float]         # 0.0 – 1.0
    confidence_tier: Optional[str]      # "high" | "medium" | "low"
    all_scores: Optional[dict]          # {category: score} — all probabilities

    # Pattern engine output (may override ML)
    pattern_category: Optional[str]     # category from amount/pattern logic
    final_category: Optional[str]       # what the app actually displays

    message: Optional[str]             # reason if status == "ignored"


# ---------------------------------------------------------------------------
# Correct endpoint  PATCH /correct
# ---------------------------------------------------------------------------

class CorrectRequest(BaseModel):
    transaction_id: int
    correct_category: str


class CorrectResponse(BaseModel):
    success: bool
    transaction_id: int
    old_category: str
    new_category: str


# ---------------------------------------------------------------------------
# Analytics endpoint  GET /analytics?month=2024-05
# ---------------------------------------------------------------------------

class CategoryBreakdown(BaseModel):
    category: str
    total: float
    count: int
    percentage: float
    avg_transaction: float


class SpendingTrend(BaseModel):
    date: str           # "2024-05-01"
    amount: float
    category: str


class KPIs(BaseModel):
    total_spend: float
    total_credit: float
    net: float
    transaction_count: int
    avg_transaction: float
    largest_transaction: float
    smallest_transaction: float
    median_transaction: float
    most_spent_category: str
    most_spent_amount: float
    repeat_merchants: int
    uncategorized_count: int     # how many are still "others"
    correction_rate: float       # % user has manually corrected


class AnalyticsResponse(BaseModel):
    month: str
    kpis: KPIs
    category_breakdown: list[CategoryBreakdown]
    daily_trend: list[SpendingTrend]
    top_merchants: list[dict]


# ---------------------------------------------------------------------------
# Advice endpoint  GET /advice?month=2024-05
# ---------------------------------------------------------------------------

class BudgetRule(BaseModel):
    rule_name: str          # "50/30/20"
    needs_limit: float      # 50% of income
    wants_limit: float      # 30%
    savings_limit: float    # 20%
    needs_actual: float
    wants_actual: float
    savings_actual: float
    needs_status: str       # "on_track" | "over" | "under"
    wants_status: str
    savings_status: str


class CategoryBudget(BaseModel):
    category: str
    suggested_limit: float
    actual_spend: float
    status: str             # "on_track" | "over" | "under"
    over_by: Optional[float]


class Insight(BaseModel):
    type: str               # "warning" | "tip" | "achievement"
    title: str
    message: str
    category: Optional[str]


class AdviceResponse(BaseModel):
    month: str
    estimated_income: float
    budget_rule: BudgetRule
    category_budgets: list[CategoryBudget]
    insights: list[Insight]
    recurring_detected: list[dict]  # detected EMIs, subscriptions, rent
