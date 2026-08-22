import uuid
from datetime import date

from sqlalchemy import Date, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class Tender(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "tenders"

    lead_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("leads.id", ondelete="CASCADE"), nullable=True, index=True
    )
    title: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    tender_number: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    publishing_body: Mapped[str | None] = mapped_column(String(500), nullable=True)
    field: Mapped[str | None] = mapped_column(String(255), nullable=True)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    publish_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    submission_deadline: Mapped[date | None] = mapped_column(Date, nullable=True)
    site_visit_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    contact_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    contact_phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    contact_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    eligibility_conditions: Mapped[str | None] = mapped_column(Text, nullable=True)
    guarantees: Mapped[str | None] = mapped_column(Text, nullable=True)
    quantities: Mapped[str | None] = mapped_column(Text, nullable=True)
    furniture_items: Mapped[str | None] = mapped_column(Text, nullable=True)
    specifications: Mapped[str | None] = mapped_column(Text, nullable=True)
    installation_requirements: Mapped[str | None] = mapped_column(Text, nullable=True)
    delivery_requirements: Mapped[str | None] = mapped_column(Text, nullable=True)
    standards: Mapped[str | None] = mapped_column(Text, nullable=True)
    required_documents: Mapped[str | None] = mapped_column(Text, nullable=True)
    furniture_supplier_eligible: Mapped[bool | None] = mapped_column(nullable=True)
    classification_required: Mapped[str | None] = mapped_column(String(500), nullable=True)
    estimated_value: Mapped[float | None] = mapped_column(Numeric(14, 2), nullable=True)
    competition_level: Mapped[str | None] = mapped_column(String(50), nullable=True)
    feasibility_score: Mapped[int | None] = mapped_column(nullable=True)
    is_open: Mapped[bool] = mapped_column(default=True, nullable=False)
    source_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    document_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("documents.id", ondelete="SET NULL"), nullable=True
    )
    ai_analysis_raw: Mapped[str | None] = mapped_column(Text, nullable=True)

    lead = relationship("Lead", back_populates="tender")
