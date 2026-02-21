from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from app.core.config import settings
from app.api.routes import bills

os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

app = FastAPI(
    title=settings.APP_NAME,
    description="AI-powered hospital bill verification using Gemini 1.5 Flash",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    print(f"✅ {settings.APP_NAME} started!")

app.include_router(bills.router)

@app.get("/", tags=["Health"])
def health():
    return {"status": "running", "app": settings.APP_NAME, "docs": "/docs"}
