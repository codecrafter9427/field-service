"""Customer acknowledgement (not certified e-signature) schemas."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

DEFAULT_ACK = (
    "I acknowledge the work described was completed. "
    "This is not a certified e-signature."
)


class SignoffCreate(BaseModel):
    signer_name: str = Field(min_length=1, max_length=200)
    acknowledgement_text: str = Field(default=DEFAULT_ACK, min_length=1)
    signature_data_url: str | None = Field(
        default=None,
        description="Optional canvas data URL or storage key stub (demo only)",
        max_length=2_000_000,
    )


class SignoffOut(BaseModel):
    id: UUID
    organization_id: UUID
    work_order_id: UUID
    signer_name: str
    signed_at: datetime
    acknowledgement_text: str
    signature_storage_key: str | None = None
    is_certified_esignature: bool = False
    disclaimer: str = (
        "Acknowledgement only — not a certified electronic signature."
    )
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
