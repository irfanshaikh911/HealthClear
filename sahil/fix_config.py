import os

config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app", "core", "config.py")

content = '''from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://postgres:password@localhost:5432/bill_verification"
    GEMINI_API_KEY: str = ""
    SECRET_KEY: str = "changeme_in_production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
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
'''

with open(config_path, "w", encoding="utf-8") as f:
    f.write(content)

print(f"✅ Fixed: {config_path}")
print("\nNow run: uvicorn app.main:app --reload")
