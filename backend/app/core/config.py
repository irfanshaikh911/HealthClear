"""Application settings loaded from environment variables."""

"""Application settings loaded from environment variables."""

import os
from dotenv import load_dotenv

from pathlib import Path

# Load environment variables from backend/.env file
env_path = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(env_path, override=True)

class Settings:
    """All configuration is read from environment / .env file using python-dotenv."""
    
    # ── Supabase ──────────────────────────────────────────────
    PUBLIC_SUPABASE_URL: str = os.getenv("PUBLIC_SUPABASE_URL", "")
    PUBLIC_SUPABASE_PUBLISHABLE_DEFAULT_KEY: str = os.getenv("PUBLIC_SUPABASE_PUBLISHABLE_DEFAULT_KEY", "")

    # ── Groq ──────────────────────────────────────────────────
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")

    # ── File uploads ──────────────────────────────────────────
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "uploads")
    MAX_FILE_SIZE_MB: int = int(os.getenv("MAX_FILE_SIZE_MB", "10"))
    ALLOWED_EXTENSIONS: str = os.getenv("ALLOWED_EXTENSIONS", "jpg,jpeg,png,pdf,bmp,tiff")

    # ── App metadata ──────────────────────────────────────────
    APP_NAME: str = os.getenv("APP_NAME", "HealthClear Bill Verification")
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"

    @property
    def allowed_extensions_list(self) -> list[str]:
        return [ext.strip() for ext in self.ALLOWED_EXTENSIONS.split(",")]


settings = Settings()
