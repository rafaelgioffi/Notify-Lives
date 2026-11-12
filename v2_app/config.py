from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent.parent


def _env(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip()


@dataclass(frozen=True)
class Settings:
    database_url: str = _env("DATABASE_URL", f"sqlite:///{ROOT_DIR / 'data' / 'notify_lives.db'}")
    cloudinary_cloud_name: str = _env("CLOUDINARY_CLOUD_NAME")
    cloudinary_api_key: str = _env("CLOUDINARY_API_KEY")
    cloudinary_api_secret: str = _env("CLOUDINARY_API_SECRET")
    whatsapp_initial_delay: float = float(_env("WHATSAPP_INITIAL_DELAY", "2"))
    whatsapp_retry_delay: float = float(_env("WHATSAPP_RETRY_DELAY", "6"))
    whatsapp_max_retries: int = int(_env("WHATSAPP_MAX_RETRIES", "2"))
    whatsapp_manual_confirmation: bool = _env("WHATSAPP_MANUAL_CONFIRMATION", "true").lower() in {
        "1",
        "true",
        "yes",
    }


settings = Settings()

