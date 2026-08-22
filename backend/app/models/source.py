from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin
from app.models.enums import ScanFrequency, SourceStatus, SourceType


class Source(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "sources"

    name: Mapped[str] = mapped_column(String(500), nullable=False)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    source_type: Mapped[SourceType] = mapped_column(default=SourceType.HTML, nullable=False)
    category: Mapped[str | None] = mapped_column(String(255), nullable=True)
    scan_frequency: Mapped[ScanFrequency] = mapped_column(default=ScanFrequency.DAILY, nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    status: Mapped[SourceStatus] = mapped_column(default=SourceStatus.PENDING, nullable=False)
    last_scan_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_success_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    result_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    config_json: Mapped[str | None] = mapped_column(Text, nullable=True)  # adapter-specific config (JSON)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    scan_runs = relationship("ScanRun", back_populates="source")
