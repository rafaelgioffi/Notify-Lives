from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy import DateTime, Integer, String, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

from .config import ROOT_DIR, settings


class Base(DeclarativeBase):
    pass


class PublicationAttempt(Base):
    __tablename__ = "publication_attempts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    campaign_id: Mapped[str] = mapped_column(String(100), index=True)
    channel: Mapped[str] = mapped_column(String(40), index=True)
    destination: Mapped[str] = mapped_column(String(500))
    status: Mapped[str] = mapped_column(String(30), index=True)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    external_id: Mapped[str | None] = mapped_column(String(500), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


def _ensure_sqlite_directory(database_url: str) -> None:
    if not database_url.startswith("sqlite:///"):
        return
    database_path = Path(database_url.removeprefix("sqlite:///"))
    if not database_path.is_absolute():
        database_path = ROOT_DIR / database_path
    database_path.parent.mkdir(parents=True, exist_ok=True)


_ensure_sqlite_directory(settings.database_url)
engine = create_engine(settings.database_url, future=True)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


def initialize_database() -> None:
    Base.metadata.create_all(engine)


def record_attempt(**values: Any) -> PublicationAttempt:
    with SessionLocal.begin() as session:
        attempt = PublicationAttempt(**values)
        session.add(attempt)
        session.flush()
        session.refresh(attempt)
        return attempt


def update_attempt(attempt_id: int, **values: Any) -> None:
    with SessionLocal.begin() as session:
        attempt = session.get(PublicationAttempt, attempt_id)
        if attempt is None:
            raise ValueError(f"Tentativa {attempt_id} não encontrada")
        for key, value in values.items():
            setattr(attempt, key, value)

