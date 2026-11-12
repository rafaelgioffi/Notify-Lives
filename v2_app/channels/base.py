from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class PublicationResult:
    success: bool
    external_id: str | None = None
    error_message: str | None = None


class ChannelAdapter(Protocol):
    channel_name: str

    def publish(
        self,
        *,
        destination: str,
        caption: str,
        media_url: str | None = None,
        campaign_id: str = "manual",
    ) -> PublicationResult:
        ...

