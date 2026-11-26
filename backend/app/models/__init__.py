"""ORM models for Field Service Milestone 1."""

from app.core.database import Base
from app.models.asset import Asset
from app.models.customer import Customer, ServiceLocation
from app.models.enums import JobActivityType, UserRole, WorkOrderPriority, WorkOrderStatus
from app.models.organization import Organization, User
from app.models.work_order import (
    Attachment,
    AuditEvent,
    Checklist,
    ChecklistItem,
    CustomerSignoff,
    JobActivity,
    PartUsed,
    TimeEntry,
    WorkOrder,
    WorkOrderAssignment,
)

__all__ = [
    "Base",
    "Organization",
    "User",
    "UserRole",
    "Customer",
    "ServiceLocation",
    "Asset",
    "WorkOrder",
    "WorkOrderStatus",
    "WorkOrderPriority",
    "WorkOrderAssignment",
    "Checklist",
    "ChecklistItem",
    "JobActivity",
    "JobActivityType",
    "TimeEntry",
    "PartUsed",
    "Attachment",
    "CustomerSignoff",
    "AuditEvent",
]
