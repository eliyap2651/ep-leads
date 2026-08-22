import uuid
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin
from app.models.enums import Domain, LeadStatus, LeadTier, RecordType, Region


class Lead(Base, UUIDMixin, TimestampMixin):
    """The central entity: one lead = one business opportunity (tender or early-stage project)."""

    __tablename__ = "leads"

    company_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id", ondelete="SET NULL"), nullable=True, index=True
    )
    assigned_to_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )

    title: Mapped[str] = mapped_column(String(1000), nullable=False)
    record_type: Mapped[RecordType] = mapped_column(nullable=False)
    domain: Mapped[Domain | None] = mapped_column(nullable=True)
    city: Mapped[str | None] = mapped_column(String(255), nullable=True)
    region: Mapped[Region] = mapped_column(default=Region.UNKNOWN, nullable=False)
    address: Mapped[str | None] = mapped_column(String(500), nullable=True)

    estimated_value: Mapped[float | None] = mapped_column(Numeric(14, 2), nullable=True)
    deadline: Mapped[date | None] = mapped_column(Date, nullable=True)  # submission deadline if a tender

    score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    tier: Mapped[LeadTier] = mapped_column(default=LeadTier.LOW, nullable=False)
    score_breakdown_json: Mapped[str | None] = mapped_column(Text, nullable=True)

    status: Mapped[LeadStatus] = mapped_column(default=LeadStatus.NEW, nullable=False)

    dedup_key: Mapped[str | None] = mapped_column(String(500), nullable=True, index=True)

    is_stale: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)  # no longer found on re-check
    last_verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    ai_summary: Mapped[str | None] = mapped_column(Text, nullable=True)  # "why now / who to contact / next step"

    company = relationship("Company", back_populates="leads")
    assigned_to = relationship("User", back_populates="assigned_leads", foreign_keys=[assigned_to_id])
    tender = relationship("Tender", back_populates="lead", uselist=False, cascade="all, delete-orphan")
    project = relationship("Project", back_populates="lead", uselist=False, cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="lead", cascade="all, delete-orphan")
    lead_sources = relationship("LeadSource", back_populates="lead", cascade="all, delete-orphan")
    lead_contacts = relationship("LeadContact", back_populates="lead", cascade="all, delete-orphan")
    activities = relationship(
        "Activity", back_populates="lead", cascade="all, delete-orphan", order_by="Activity.created_at.desc()"
    )
    notes = relationship(
        "Note", back_populates="lead", cascade="all, delete-orphan", order_by="Note.created_at.desc()"
    )
    tasks = relationship("FollowUpTask", back_populates="lead", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="lead", cascade="all, delete-orphan")
    change_history = relationship(
        "ChangeHistory", back_populates="lead", cascade="all, delete-orphan",
        order_by="ChangeHistory.created_at.desc()",
    )
