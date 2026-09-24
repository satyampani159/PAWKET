import os
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from pydantic import BaseModel
from sqlalchemy import text

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent

from database.database import create_tables, SessionLocal, Base, engine
from ml.ml_loader import ml_models
from routers.auth import router as auth_router
from routers.parse import router as parse_router
from routers.analytics import router as analytics_router
from routers.correct import router as correct_router
from routers.advice import router as advice_router
from routers.profile import router as profile_router
from routers.chat import router as chat_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("\n[startup] Creating database tables...")
    create_tables()
    print("[startup] Loading ML models...")
    try:
        ml_models.load(os.getenv("ML_MODELS_DIR", str(BASE_DIR / "ml" / "models")))
    except Exception as e:
        print(f"[startup] WARNING: ML models failed to load: {e}")
        print("[startup] Running without ML — parse endpoints will return 503.")
    print("[startup] Bootstrapping data if DB is empty...")
    try:
        from services.ingest import bootstrap_if_empty
        bootstrap_if_empty()
    except Exception as e:
        print(f"[startup] Data bootstrap skipped: {e}")
    print("[startup] Ready.\n")
    yield

app = FastAPI(title="PAWKET API", version="1.1.2", lifespan=lifespan)

cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:8081").split(",")
allow_creds = cors_origins != ["*"]
app.add_middleware(CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=allow_creds, allow_methods=["*"], allow_headers=["*"])

app.include_router(auth_router)
app.include_router(profile_router)
app.include_router(parse_router)
app.include_router(analytics_router)
app.include_router(correct_router)
app.include_router(advice_router)
app.include_router(chat_router)

@app.get("/", tags=["health"])
def root():
    return {"status": "ok", "ml_loaded": ml_models.loaded, "docs": "/docs"}

@app.get("/health", tags=["health"])
def health():
    db_ok = False
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        db_ok = True
    except Exception:
        pass
    return {"status": "ok", "ml_loaded": ml_models.loaded, "db_ok": db_ok}


def require_admin(x_admin_key: str = Header(None)):
    expected = os.getenv("ADMIN_KEY")
    if not expected or x_admin_key != expected:
        raise HTTPException(status_code=401, detail="Invalid or missing admin key.")


@app.post("/admin/reset", tags=["admin"])
def admin_reset(seed: bool = True, _admin: None = Depends(require_admin)):
    """Drop all tables, recreate them. Optionally re-seed with auto_seed data."""
    print("[ADMIN] Dropping all tables...")
    Base.metadata.drop_all(bind=engine)
    print("[ADMIN] Recreating tables...")
    Base.metadata.create_all(bind=engine)
    if seed:
        print("[ADMIN] Re-seeding test data...")
        from services.auto_seed import auto_seed
        auto_seed()
        return {"status": "reset", "message": "All data cleared. 68 transactions seeded for +917377044562."}
    return {"status": "reset", "message": "All data cleared. No seed data added."}


@app.post("/admin/drop", tags=["admin"])
def admin_drop(_admin: None = Depends(require_admin)):
    """Drop all tables and recreate empty — no seed data. For use with test_seed.py."""
    print("[ADMIN] Dropping all tables...")
    Base.metadata.drop_all(bind=engine)
    print("[ADMIN] Recreating empty tables...")
    Base.metadata.create_all(bind=engine)
    return {"status": "dropped", "message": "All data cleared. Empty DB ready for test_seed.py."}


class LoadBatchRequest(BaseModel):
    phone: str
    entries: list = []
    store_only: bool = False


@app.post("/admin/load-batch", tags="admin")
def admin_load_batch(req: LoadBatchRequest, _admin: None = Depends(require_admin)):
    """Ingest a real SMS batch for a phone number and/or store it for startup auto-ingest.

    - Normal mode: runs entries through the ML pipeline (dedup-safe) into that user's DB.
    - store_only=true: only persists entries to REAL_SMS_BATCH (no ingest).
    """
    from services.ingest import get_or_create_user, ingest_entries, store_batch_file

    phone = req.phone.strip()
    if not phone.startswith("+") or len(phone) < 10:
        raise HTTPException(status_code=400, detail="phone must be international format, e.g. +911234567890")
    if not req.entries:
        raise HTTPException(status_code=400, detail="entries is empty.")

    if req.store_only:
        stored, path = store_batch_file(req.entries)
        return {"status": "stored", "phone": phone, "stored": stored, "path": path,
                "entries": len(req.entries)}

    if not ml_models.loaded:
        raise HTTPException(status_code=503, detail="ML models not loaded.")

    db = SessionLocal()
    try:
        user = get_or_create_user(db, phone)
        counts = ingest_entries(req.entries, user, db)
    finally:
        db.close()

    stored, path = store_batch_file(req.entries)
    print(f"[ADMIN] load-batch for {phone}: {counts} stored={stored}")
    return {"status": "ok", "phone": phone, "stored": stored, "path": path, **counts}
