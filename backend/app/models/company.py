from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin
from app.models.enums import Domain, Region


class Company(Base, UUIDMixin, TimestampMixin):
    """A business/institutional entity (municipality, hotel chain, contractor, etc.)."""

    __tablename__ = "companies"

    name: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    domain_website: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    category: Mapped[Domain | None] = mapped_column(nullable=True)
    city: Mapped[str | None] = mapped_column(String(255), nullable=True)
    address: Mapped[str | None] = mapped_column(String(500), nullable=True)
    region: Mapped[Region] = mapped_column(default=Region.UNKNOWN, nullable=False)
    website: Mapped[str | None] = mapped_column(String(500), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    leads = relationship("Lead", back_populates="company")
    contacts = relationship("Contact", back_populates="company")
