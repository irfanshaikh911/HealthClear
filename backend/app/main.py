"""HealthClear Backend — FastAPI application entry point."""

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.bills import router as bills_router
from app.api.assistant import router as assistant_router
from app.api.auth import router as auth_router
from app.db.supabase import get_supabase
from app.services.seed_service import seed


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown events."""
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

    # Seed cost-estimation reference data (hospitals, procedures, risk_conditions)
    try:
        client = get_supabase()
        seed(client)
    except Exception as e:
        print(f"⚠️  Seed skipped: {e}")

    print(f"✅ {settings.APP_NAME} started!")
    yield
    print(f"⏹  {settings.APP_NAME} stopped.")


app = FastAPI(
    title=settings.APP_NAME,
    description="AI-powered hospital bill verification & healthcare cost estimation",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(bills_router)
app.include_router(assistant_router)
app.include_router(auth_router)


@app.get("/", tags=["Health"])
def health_check():
    return {
        "status": "running",
        "app": settings.APP_NAME,
        "docs": "/docs",
    }
