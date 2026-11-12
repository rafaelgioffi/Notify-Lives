from __future__ import annotations

import hashlib
import time
from pathlib import Path

import requests

from ..config import settings


class CloudinaryMediaStore:
    """Uploads media only when a channel requires a public HTTPS URL."""

    def upload(self, file_path: str | Path, *, resource_type: str = "auto") -> str:
        if not all(
            (
                settings.cloudinary_cloud_name,
                settings.cloudinary_api_key,
                settings.cloudinary_api_secret,
            )
        ):
            raise RuntimeError("Cloudinary não configurado. Preencha as variáveis CLOUDINARY_*.")

        path = Path(file_path)
        timestamp = str(int(time.time()))
        signature_payload = f"timestamp={timestamp}{settings.cloudinary_api_secret}"
        signature = hashlib.sha1(signature_payload.encode("utf-8")).hexdigest()
        endpoint = (
            f"https://api.cloudinary.com/v1_1/{settings.cloudinary_cloud_name}/"
            f"{resource_type}/upload"
        )
        with path.open("rb") as media:
            response = requests.post(
                endpoint,
                data={
                    "api_key": settings.cloudinary_api_key,
                    "timestamp": timestamp,
                    "signature": signature,
                },
                files={"file": (path.name, media)},
                timeout=120,
            )
        response.raise_for_status()
        return response.json()["secure_url"]

