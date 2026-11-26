"""Work orders, assignments, checklists, and job execution records."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import (
    Base,
    OrganizationScopedMixin,
    SoftArchiveMixin,
    TimestampMixin,
    UUIDPrimaryKeyMixin,
)
from app.models.enums import (
    JobActivityType,
    WorkOrderPriority,
    WorkOrderStatus,
)

if TYPE_CHECKING:
    from app.models.organization import User


class WorkOrder(
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    OrganizationScopedMixin,
    SoftArchiveMixin,
    Base,
):
    __tablename__ = "work_orders"

    customer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("customers.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    service_location_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("service_locations.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    asset_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("assets.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(40), nullable=False, default=WorkOrderStatus.DRAFT.value, index=True
    )
    priority: Mapped[str] = mapped_column(
        String(20), nullable=False, default=WorkOrderPriority.NORMAL.value
    )
    due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    skill_required: Mapped[str | None] = mapped_column(String(100), nullable=True)
    estimate_amount: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    labor_rate: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    created_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    assignments: Mapped[list[WorkOrderAssignment]] = relationship(
        back_populates="work_order"
    )
    checklists: Mapped[list[Checklist]] = relationship(back_populates="work_order")
    activities: Mapped[list[JobActivity]] = relationship(back_populates="work_order")
    time_entries: Mapped[list[TimeEntry]] = relationship(back_populates="work_order")
    parts_used: Mapped[list[PartUsed]] = relationship(back_populates="work_order")
    attachments: Mapped[list[Attachment]] = relationship(back_populates="work_order")
    signoffs: Mapped[list[CustomerSignoff]] = relationship(back_populates="work_order")


class WorkOrderAssignment(
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    OrganizationScopedMixin,
    Base,
):
    __tablename__ = "work_order_assignments"

    work_order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("work_orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    technician_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    assigned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    work_order: Mapped[WorkOrder] = relationship(back_populates="assignments")
    technician: Mapped[User] = relationship()


class Checklist(
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    OrganizationScopedMixin,
    Base,
):
    __tablename__ = "checklists"

    work_order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("work_orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    template_key: Mapped[str | None] = mapped_column(String(80), nullable=True)

    work_order: Mapped[WorkOrder] = relationship(back_populates="checklists")
    items: Mapped[list[ChecklistItem]] = relationship(back_populates="checklist")


class ChecklistItem(
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    OrganizationScopedMixin,
    Base,
):
    __tablename__ = "checklist_items"

    checklist_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("checklists.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    label: Mapped[str] = mapped_column(String(255), nullable=False)
    is_required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_completed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    checklist: Mapped[Checklist] = relationship(back_populates="items")


class JobActivity(
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    OrganizationScopedMixin,
    Base,
):
    __tablename__ = "job_activities"

    work_order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("work_orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    actor_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    activity_type: Mapped[str] = mapped_column(
        String(40), nullable=False, default=JobActivityType.NOTE.value
    )
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    work_order: Mapped[WorkOrder] = relationship(back_populates="activities")


class TimeEntry(
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    OrganizationScopedMixin,
    Base,
):
    __tablename__ = "time_entries"

    work_order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("work_orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    technician_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    was_corrected: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    work_order: Mapped[WorkOrder] = relationship(back_populates="time_entries")


class PartUsed(
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    OrganizationScopedMixin,
    Base,
):
    __tablename__ = "parts_used"

    work_order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("work_orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    part_name: Mapped[str] = mapped_column(String(200), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=1)
    unit_cost: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    work_order: Mapped[WorkOrder] = relationship(back_populates="parts_used")


class Attachment(
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    OrganizationScopedMixin,
    Base,
):
    """Attachment metadata only — binary upload adapter is Milestone 2+."""

    __tablename__ = "attachments"

    work_order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("work_orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    content_type: Mapped[str | None] = mapped_column(String(120), nullable=True)
    storage_key: Mapped[str] = mapped_column(String(512), nullable=False)
    byte_size: Mapped[int | None] = mapped_column(Integer, nullable=True)
    uploaded_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    work_order: Mapped[WorkOrder] = relationship(back_populates="attachments")


class CustomerSignoff(
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    OrganizationScopedMixin,
    Base,
):
    """Customer acknowledgement — not a certified e-signature."""

    __tablename__ = "customer_signoffs"

    work_order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("work_orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    signer_name: Mapped[str] = mapped_column(String(200), nullable=False)
    signed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    acknowledgement_text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="I acknowledge the work described was completed. This is not a certified e-signature.",
    )
    signature_storage_key: Mapped[str | None] = mapped_column(String(512), nullable=True)

    work_order: Mapped[WorkOrder] = relationship(back_populates="signoffs")


class AuditEvent(UUIDPrimaryKeyMixin, TimestampMixin, OrganizationScopedMixin, Base):
    __tablename__ = "audit_events"

    actor_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    entity_type: Mapped[str] = mapped_column(String(80), nullable=False)
    entity_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    action: Mapped[str] = mapped_column(String(80), nullable=False)
    payload: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
