"""Asset request/response schemas."""

from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field


class AssetCreate(BaseModel):
    customer_id: UUID
    service_location_id: UUID | None = None
    name: str = Field(min_length=1, max_length=200)
    serial_number: str | None = Field(default=None, max_length=120)
    asset_type: str | None = Field(default=None, max_length=100)
    manufacturer: str | None = Field(default=None, max_length=120)
    model_number: str | None = Field(default=None, max_length=120)
    warranty_expires_on: date | None = None
    maintenance_notes: str | None = None


class AssetUpdate(BaseModel):
    service_location_id: UUID | None = None
    name: str | None = Field(default=None, min_length=1, max_length=200)
    serial_number: str | None = Field(default=None, max_length=120)
    asset_type: str | None = Field(default=None, max_length=100)
    manufacturer: str | None = Field(default=None, max_length=120)
    model_number: str | None = Field(default=None, max_length=120)
    warranty_expires_on: date | None = None
    maintenance_notes: str | None = None


class AssetOut(BaseModel):
    id: UUID
    organization_id: UUID
    customer_id: UUID
    service_location_id: UUID | None = None
    name: str
    serial_number: str | None = None
    asset_type: str | None = None
    manufacturer: str | None = None
    model_number: str | None = None
    warranty_expires_on: date | None = None
    maintenance_notes: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ServiceHistoryItem(BaseModel):
    work_order_id: UUID
    title: str
    status: str
    priority: str
    customer_id: UUID
    customer_name: str | None = None
    asset_id: UUID | None = None
    asset_name: str | None = None
    scheduled_start: datetime | None = None
    completed_note: str | None = None
    updated_at: datetime
