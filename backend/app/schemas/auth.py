"""Auth request/response schemas."""

from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, Field


class DemoLoginRequest(BaseModel):
    # Plain str: demo emails use reserved .local TLD rejected by EmailStr.
    email: str = Field(min_length=3)
    password: str = Field(min_length=1)


class AuthUser(BaseModel):
    id: UUID
    email: str
    role: str
    organization_id: UUID
    display_name: str


class DemoLoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: AuthUser
