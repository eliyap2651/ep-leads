import uuid

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin
from app.models.enums import ProjectStage


class Project(Base, UUIDMixin, TimestampMixin):
    """An early-stage project (pre-tender): new hotel, new school, factory relocation, etc."""

    __tablename__ = "projects"

    lead_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("leads.id", ondelete="CASCADE"), nullable=True, index=True
    )
    name: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    developer: Mapped[str | None] = mapped_column(String(500), nullable=True)
    contractor: Mapped[str | None] = mapped_column(String(500), nullable=True)
    architect: Mapped[str | None] = mapped_column(String(500), nullable=True)
    project_manager: Mapped[str | None] = mapped_column(String(500), nullable=True)
    city: Mapped[str | None] = mapped_column(String(255), nullable=True)
    stage: Mapped[ProjectStage | None] = mapped_column(nullable=True)
    unit_count: Mapped[int | None] = mapped_column(nullable=True)
    room_count: Mapped[int | None] = mapped_column(nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_url: Mapped[str | None] = mapped_column(Text, nullable=True)

    lead = relationship("Lead", back_populates="project")
