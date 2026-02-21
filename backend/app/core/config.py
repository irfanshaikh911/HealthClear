"""Application settings loaded from environment variables."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """All configuration is read from environment / .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ── Supabase ──────────────────────────────────────────────
    PUBLIC_SUPABASE_URL: str
    PUBLIC_SUPABASE_PUBLISHABLE_DEFAULT_KEY: str

    # ── Groq ──────────────────────────────────────────────────
    GROQ_API_KEY: str

    # ── Tesseract OCR path (Windows) ──────────────────────────
    TESSERACT_CMD: str = r"D:\Tesseract-OCR\tesseract.exe"

    # ── File uploads ──────────────────────────────────────────
    UPLOAD_DIR: str = "uploads"
    MAX_FILE_SIZE_MB: int = 10
    ALLOWED_EXTENSIONS: str = "jpg,jpeg,png,pdf,bmp,tiff"

    # ── App metadata ──────────────────────────────────────────
    APP_NAME: str = "HealthClear Bill Verification"
    DEBUG: bool = False

    @property
    def allowed_extensions_list(self) -> list[str]:
        return [ext.strip() for ext in self.ALLOWED_EXTENSIONS.split(",")]


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
