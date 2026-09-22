from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime
from database.database import get_db, User
from services.analytics import get_monthly_analytics
from services.chat_engine import get_chat_reply
from routers.auth import require_auth

router = APIRouter(prefix="/chat", tags=["chat"])


class ChatRequest(BaseModel):
    message: str
    month: str | None = None
    history: list[dict] | None = None


@router.post("")
async def chat_endpoint(
    req: ChatRequest,
    user: User = Depends(require_auth),
    db: Session = Depends(get_db),
):
    month = req.month or datetime.utcnow().strftime("%Y-%m")

    analytics = get_monthly_analytics(db, month, user.id)

    user_profile = {
        "name": user.name,
        "gender": user.gender,
        "age": user.age,
        "financial_goal": user.financial_goal,
    }

    reply = await get_chat_reply(
        message=req.message,
        analytics=analytics,
        month=month,
        history=req.history or [],
        user_profile=user_profile,
    )

    return {"reply": reply}
