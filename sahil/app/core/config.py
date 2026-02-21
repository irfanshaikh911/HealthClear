from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    SUPABASE_URL: str = "https://lejegaygvmjqekkamcrg.supabase.co"
    SUPABASE_KEY: str = "sb_publishable_z2he4SSrmXexTRxzioixEg_KdMPWtaH"
    GEMINI_API_KEY: str = "AIzaSyDy8FbP7PouKTNpd8RRG0xYCjgGSKnkQuI"

    UPLOAD_DIR: str = "uploads"
    MAX_FILE_SIZE_MB: int = 10
    ALLOWED_EXTENSIONS: str = "jpg,jpeg,pdf"
    APP_NAME: str = "Bill Verification System"
    DEBUG: bool = True

    @property
    def allowed_extensions_list(self) -> list[str]:
        return [ext.strip() for ext in self.ALLOWED_EXTENSIONS.split(",")]

    class Config:
        env_file = ".env"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
