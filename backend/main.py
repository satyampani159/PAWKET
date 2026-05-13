import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

from database.database import create_tables
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
    ml_models.load(os.getenv("ML_MODELS_DIR", "ml/models"))
    print("[startup] Ready.\n")
    yield

app = FastAPI(title="Finance App API", version="1.0.0", lifespan=lifespan)

app.add_middleware(CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "*").split(","),
    allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

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
    return {"status": "ok", "ml_loaded": ml_models.loaded}
