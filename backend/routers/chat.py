from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from datetime import datetime
from database.database import get_db, User
from services.analytics import get_monthly_analytics
from services.chat_engine import get_chat_reply_with_meta, AI_DISCLOSURE_SHORT, PERSONA_NAME
from routers.auth import require_auth

router = APIRouter(prefix="/chat", tags=["chat"])


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=500)
    month: str | None = None
    history: list[dict] | None = None


def _prev_month(month: str) -> str:
    y, m = int(month[:4]), int(month[5:7])
    return f"{y - 1:04d}-12" if m == 1 else f"{y:04d}-{m - 1:02d}"


@router.post("")
async def chat_endpoint(
    req: ChatRequest,
    user: User = Depends(require_auth),
    db: Session = Depends(get_db),
):
    month = req.month or datetime.utcnow().strftime("%Y-%m")
    message = (req.message or "").strip()[:500]

    try:
        analytics = get_monthly_analytics(db, month, user.id)
    except Exception:
        analytics = {}

    try:
        prev_analytics = get_monthly_analytics(db, _prev_month(month), user.id)
    except Exception:
        prev_analytics = {}

    user_profile = {
        "name": user.name,
        "gender": user.gender,
        "age": user.age,
        "financial_goal": user.financial_goal,
    }

    reply, meta = await get_chat_reply_with_meta(
        message=message,
        analytics=analytics,
        month=month,
        history=req.history or [],
        user_profile=user_profile,
        prev_analytics=prev_analytics,
    )

    # Backwards-compatible: mobile reads `reply`. Meta documents the 7 behaviours.
    return {
        "reply": reply,
        "meta": {
            **meta,
            "disclosure": AI_DISCLOSURE_SHORT,
            "persona": PERSONA_NAME,
        },
    }
