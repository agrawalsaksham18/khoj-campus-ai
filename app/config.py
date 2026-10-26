import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    SARVAM_API_KEY: str = ""
    PORT: int = 8000
    HOST: str = "127.0.0.1"
    DEBUG: bool = True
    COLLEGE_NAME: str = "IIT Kanpur"
    COLLEGE_TAG: str = "IITK"
    DATABASE_URL: str = "sqlite:///./khoj.db"
    MAX_IMAGE_UPLOAD_MB: int = 5
    UPLOAD_DIR: Path = BASE_DIR / "app" / "static" / "uploads"

    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @property
    def has_sarvam_key(self) -> bool:
        return bool(self.SARVAM_API_KEY and self.SARVAM_API_KEY.strip())

settings = Settings()
settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
