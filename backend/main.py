import os
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from sqlalchemy import text

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent

from database.database import create_tables, SessionLocal
from ml.ml_loader import ml_models
from routers.auth import router as auth_router
from routers.parse import router as parse_router
from routers.analytics import router as analytics_router
from routers.correct import router as correct_router
from routers.advice import router as advice_router
from routers.profile import router as profile_router

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
    print("[startup] Ready.\n")
    yield

app = FastAPI(title="Finance App API", version="1.0.0", lifespan=lifespan)

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
