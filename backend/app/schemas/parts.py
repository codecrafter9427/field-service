"""Parts used schemas."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class PartUsedCreate(BaseModel):
    work_order_id: UUID
    part_name: str = Field(min_length=1, max_length=200)
    quantity: Decimal = Field(default=Decimal("1"), gt=0)
    unit_cost: Decimal | None = Field(default=None, ge=0)
    notes: str | None = None


class PartUsedOut(BaseModel):
    id: UUID
    organization_id: UUID
    work_order_id: UUID
    part_name: str
    quantity: Decimal
    unit_cost: Decimal | None = None
    notes: str | None = None
    line_total: Decimal | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
