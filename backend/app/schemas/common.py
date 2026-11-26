"""Shared request/response shapes."""

from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class ErrorBody(BaseModel):
    code: str
    message: str
    details: Any = None


class ErrorResponse(BaseModel):
    error: ErrorBody


class ComingSoonResponse(BaseModel):
    status: str = "coming_soon"
    feature: str
    message: str = "This endpoint is not implemented in the scaffold yet."


class PageMeta(BaseModel):
    page: int = 1
    page_size: int = 20
    total: int = 0


class Page(BaseModel, Generic[T]):
    items: list[T] = Field(default_factory=list)
    meta: PageMeta = Field(default_factory=PageMeta)


class DemoLoginRequest(BaseModel):
    email: str
    password: str


class DemoLoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict[str, str]


class AIRequest(BaseModel):
    input: str
    context_ids: list[str] = Field(default_factory=list)
    options: dict[str, Any] = Field(default_factory=dict)


class AISource(BaseModel):
    type: str
    id: str
    label: str


class AIResponse(BaseModel):
    result: dict[str, Any]
    explanation: str
    sources: list[AISource] = Field(default_factory=list)
    requires_confirmation: bool = True
