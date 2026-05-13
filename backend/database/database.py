from sqlalchemy import create_engine, Column, Integer, Float, String, DateTime, Boolean, Text, ForeignKey, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./finance.db")
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id           = Column(Integer, primary_key=True, index=True)
    phone        = Column(String, unique=True, nullable=False, index=True)
    created_at   = Column(DateTime, default=datetime.utcnow)
    last_login   = Column(DateTime, nullable=True)
    last_sync_at = Column(DateTime, nullable=True)
    is_active    = Column(Boolean, default=True)
    # Profile fields
    name         = Column(String, nullable=True)
    email        = Column(String, nullable=True)
    gender       = Column(String, nullable=True)   # male | female | other
    age          = Column(Integer, nullable=True)
    financial_goal = Column(String, nullable=True) # save_more | debt_free | invest | buy_home | retire_early | emergency_fund
    profile_photo  = Column(Text, nullable=True)   # base64 or URL
    monthly_income = Column(Float, nullable=True)

class OTPRecord(Base):
    __tablename__ = "otp_records"
    id         = Column(Integer, primary_key=True, index=True)
    phone      = Column(String, nullable=False, index=True)
    otp        = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    is_used    = Column(Boolean, default=False)

class Session(Base):
    __tablename__ = "sessions"
    id         = Column(Integer, primary_key=True, index=True)
    user_id    = Column(Integer, ForeignKey("users.id"), nullable=False)
    token      = Column(String, unique=True, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    is_active  = Column(Boolean, default=True)

class Transaction(Base):
    __tablename__ = "transactions"
    id                      = Column(Integer, primary_key=True, index=True)
    user_id                 = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    sms_id                  = Column(String, nullable=True)
    raw_text                = Column(Text, nullable=False)
    amount                  = Column(Float, nullable=True)
    merchant                = Column(String, nullable=True)
    bank                    = Column(String, nullable=True)
    transaction_type        = Column(String, nullable=True)
    received_at             = Column(DateTime, nullable=True)
    created_at              = Column(DateTime, default=datetime.utcnow)
    predicted_category      = Column(String, nullable=True)
    ml_confidence           = Column(Float, nullable=True)
    all_scores              = Column(Text, nullable=True)
    pattern_category        = Column(String, nullable=True)
    final_category          = Column(String, nullable=True)
    user_corrected_category = Column(String, nullable=True)
    corrected_at            = Column(DateTime, nullable=True)
    is_corrected            = Column(Boolean, default=False)
    is_recurring            = Column(Boolean, default=False)
    recurring_group_id      = Column(Integer, nullable=True)

class RecurringPattern(Base):
    __tablename__ = "recurring_patterns"
    id               = Column(Integer, primary_key=True, index=True)
    user_id          = Column(Integer, ForeignKey("users.id"), nullable=False)
    label            = Column(String)
    merchant         = Column(String, nullable=True)
    amount           = Column(Float)
    amount_variance  = Column(Float, default=0)
    category         = Column(String)
    frequency_days   = Column(Integer)
    first_seen       = Column(DateTime)
    last_seen        = Column(DateTime)
    occurrence_count = Column(Integer, default=1)

class MonthlySummary(Base):
    __tablename__ = "monthly_summaries"
    id                 = Column(Integer, primary_key=True, index=True)
    user_id            = Column(Integer, ForeignKey("users.id"), nullable=False)
    month              = Column(String)
    total_spend        = Column(Float, default=0)
    total_credit       = Column(Float, default=0)
    transaction_count  = Column(Integer, default=0)
    category_breakdown = Column(Text)
    updated_at         = Column(DateTime, default=datetime.utcnow)

Index("ix_txn_user_received",  Transaction.user_id, Transaction.received_at)
Index("ix_txn_user_sms",       Transaction.user_id, Transaction.sms_id)
Index("ix_txn_user_cat",       Transaction.user_id, Transaction.final_category)
Index("ix_monthly_user_month", MonthlySummary.user_id, MonthlySummary.month)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_tables():
    Base.metadata.create_all(bind=engine)
    print("[DB] Tables created / verified.")
