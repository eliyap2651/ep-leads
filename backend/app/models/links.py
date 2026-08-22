import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin
from app.models.enums import Confidence


class LeadSource(Base, UUIDMixin, TimestampMixin):
    """Source-tracking: which source(s) a lead was found/confirmed in (spec section 17)."""

    __tablename__ = "lead_sources"

    lead_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("leads.id", ondelete="CASCADE"), nullable=False, index=True
    )
    source_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sources.id", ondelete="SET NULL"), nullable=True
    )
    source_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    date_found: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_checked: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    still_exists: Mapped[bool | None] = mapped_column(nullable=True)
    confidence: Mapped[Confidence] = mapped_column(default=Confidence.MEDIUM, nullable=False)

    lead = relationship("Lead", back_populates="lead_sources")


class LeadContact(Base, UUIDMixin, TimestampMixin):
    """Links a lead to one or more contacts."""

    __tablename__ = "lead_contacts"

    lead_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("leads.id", ondelete="CASCADE"), nullable=False, index=True
    )
    contact_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("contacts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    is_primary: Mapped[bool] = mapped_column(default=False, nullable=False)

    lead = relationship("Lead", back_populates="lead_contacts")
    contact = relationship("Contact", back_populates="lead_links")
