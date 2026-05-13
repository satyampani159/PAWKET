# routers/auth.py
import random
import secrets
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from typing import Optional

from database.database import get_db, User, OTPRecord, Session as SessionModel
from models.auth_schemas import OTPRequest, OTPVerify, AuthResponse, UserProfile, SyncStatusUpdate

router = APIRouter(prefix="/auth", tags=["auth"])

OTP_EXPIRY_MINUTES = 10
SESSION_EXPIRY_DAYS = 30


def generate_otp() -> str:
    return str(random.randint(100000, 999999))


def send_otp_sms(phone: str, otp: str):
    # Prints to terminal for dev. Replace with MSG91/Twilio for production.
    print(f"\n{'='*40}")
    print(f"[OTP] Phone: {phone}  →  OTP: {otp}")
    print(f"{'='*40}\n")


def create_session(db: Session, user_id: int) -> str:
    token = secrets.token_urlsafe(32)
    session = SessionModel(
        user_id    = user_id,
        token      = token,
        created_at = datetime.utcnow(),
        expires_at = datetime.utcnow() + timedelta(days=SESSION_EXPIRY_DAYS),
        is_active  = True,
    )
    db.add(session)
    db.commit()
    return token


def get_user_from_token(token: str, db: Session) -> Optional[User]:
    session = db.query(SessionModel).filter(
        SessionModel.token     == token,
        SessionModel.is_active == True,
        SessionModel.expires_at > datetime.utcnow(),
    ).first()
    if not session:
        return None
    return db.query(User).filter(User.id == session.user_id).first()


def require_auth(
    authorization: str = Header(..., description="Bearer <token>"),
    db: Session = Depends(get_db),
) -> User:
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header.")
    token = authorization.split(" ", 1)[1]
    user  = get_user_from_token(token, db)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired session.")
    return user


@router.post("/request-otp", response_model=AuthResponse)
def request_otp(req: OTPRequest, db: Session = Depends(get_db)):
    phone = req.phone.strip()
    if not phone.startswith("+") or len(phone) < 10:
        raise HTTPException(status_code=400, detail="Phone must be in format +91XXXXXXXXXX")

    db.query(OTPRecord).filter(
        OTPRecord.phone   == phone,
        OTPRecord.is_used == False,
    ).update({"is_used": True})
    db.commit()

    otp = generate_otp()
    record = OTPRecord(
        phone      = phone,
        otp        = otp,
        created_at = datetime.utcnow(),
        expires_at = datetime.utcnow() + timedelta(minutes=OTP_EXPIRY_MINUTES),
        is_used    = False,
    )
    db.add(record)
    db.commit()
    send_otp_sms(phone, otp)

    return AuthResponse(success=True, message=f"OTP sent to {phone}. [DEV: {otp}]")


@router.post("/verify-otp", response_model=AuthResponse)
def verify_otp(req: OTPVerify, db: Session = Depends(get_db)):
    phone = req.phone.strip()
    record = db.query(OTPRecord).filter(
        OTPRecord.phone      == phone,
        OTPRecord.otp        == req.otp,
        OTPRecord.is_used    == False,
        OTPRecord.expires_at >  datetime.utcnow(),
    ).first()

    if not record:
        raise HTTPException(status_code=400, detail="Invalid or expired OTP.")

    record.is_used = True
    db.commit()

    user = db.query(User).filter(User.phone == phone).first()
    is_new = user is None
    if is_new:
        user = User(phone=phone, created_at=datetime.utcnow())
        db.add(user)
        db.commit()
        db.refresh(user)

    user.last_login = datetime.utcnow()
    db.commit()
    token = create_session(db, user.id)

    return AuthResponse(
        success=True, user_id=user.id, phone=user.phone,
        token=token, is_new_user=is_new, message="Login successful.",
    )


@router.get("/me", response_model=UserProfile)
def get_me(user: User = Depends(require_auth), db: Session = Depends(get_db)):
    from database.database import Transaction
    count = db.query(Transaction).filter(Transaction.user_id == user.id).count()
    return UserProfile(user_id=user.id, phone=user.phone,
        created_at=user.created_at, last_sync_at=user.last_sync_at,
        transaction_count=count)


@router.post("/sync-status")
def update_sync_status(req: SyncStatusUpdate, user: User = Depends(require_auth), db: Session = Depends(get_db)):
    user.last_sync_at = datetime.utcnow()
    db.commit()
    return {"success": True, "synced_count": req.synced_count}


@router.delete("/logout")
def logout(authorization: str = Header(...), db: Session = Depends(get_db)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid header.")
    token = authorization.split(" ", 1)[1]
    db.query(SessionModel).filter(SessionModel.token == token).update({"is_active": False})
    db.commit()
    return {"success": True}