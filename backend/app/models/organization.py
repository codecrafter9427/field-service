"""Organization and User models."""

from __future__ import annotations

from sqlalchemy import Boolean, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import (
    Base,
    OrganizationScopedMixin,
    SoftArchiveMixin,
    TimestampMixin,
    UUIDPrimaryKeyMixin,
)
from app.models.enums import UserRole


class Organization(UUIDPrimaryKeyMixin, TimestampMixin, SoftArchiveMixin, Base):
    __tablename__ = "organizations"

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    slug: Mapped[str] = mapped_column(String(80), nullable=False, unique=True)

    users: Mapped[list[User]] = relationship(back_populates="organization")


class User(
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    OrganizationScopedMixin,
    SoftArchiveMixin,
    Base,
):
    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint("organization_id", "email", name="uq_users_org_email"),
    )

    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[str] = mapped_column(String(200), nullable=False)
    role: Mapped[str] = mapped_column(
        String(32), nullable=False, default=UserRole.TECHNICIAN.value
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    phone: Mapped[str | None] = mapped_column(String(40), nullable=True)
    skills: Mapped[str | None] = mapped_column(Text, nullable=True)

    organization: Mapped[Organization] = relationship(back_populates="users")
