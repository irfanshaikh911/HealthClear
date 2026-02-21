"""HealthClear Backend — FastAPI application entry point."""

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.bills import router as bills_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown events."""
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    print(f"✅ {settings.APP_NAME} started!")
    yield
    print(f"⏹  {settings.APP_NAME} stopped.")


app = FastAPI(
    title=settings.APP_NAME,
    description="AI-powered hospital bill verification using Gemini 2.0 Flash",
    version="1.0.0",
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


@app.get("/", tags=["Health"])
def health_check():
    return {
        "status": "running",
        "app": settings.APP_NAME,
        "docs": "/docs",
    }
