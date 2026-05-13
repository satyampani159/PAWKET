# models/auth_schemas.py
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class OTPRequest(BaseModel):
    phone: str

class OTPVerify(BaseModel):
    phone: str
    otp:   str

class AuthResponse(BaseModel):
    success:     bool
    user_id:     Optional[int] = None
    phone:       Optional[str] = None
    token:       Optional[str] = None
    is_new_user: Optional[bool] = None
    message:     Optional[str] = None

class UserProfile(BaseModel):
    user_id:           int
    phone:             str
    created_at:        datetime
    last_sync_at:      Optional[datetime] = None
    transaction_count: int

class SyncStatusUpdate(BaseModel):
    user_id:      int
    synced_count: int