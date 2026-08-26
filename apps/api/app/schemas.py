import uuid
from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .models import (
    ConversationStatus,
    EscalationStatus,
    Locale,
    Priority,
    Sender,
    StaffRole,
    SummaryStatus,
)


class StaffLoginRequest(BaseModel):
    email: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=8, max_length=200)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        return value.strip().lower()


class StaffUserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    full_name: str
    role: StaffRole


class StaffLoginResponse(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_in: int
    user: StaffUserOut


class ChatRequest(BaseModel):
    conversation_id: uuid.UUID | None = None
    customer_name: str | None = Field(default=None, max_length=120)
    locale: Locale = Locale.ID
    message: str = Field(min_length=1, max_length=4000)
    order_verification_code: str | None = Field(default=None, min_length=4, max_length=40)

    @field_validator("message", "customer_name", "order_verification_code")
    @classmethod
    def strip_text(cls, value: str | None) -> str | None:
        return value.strip() if value is not None else value


class MessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    sender: Sender
    content: str
    tool_metadata: dict[str, Any] | None = None
    created_at: datetime


class EscalationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    conversation_id: uuid.UUID
    order_id: str | None
    issue_category: str
    reason: str
    priority: Priority
    status: EscalationStatus
    summary: str | None
    summary_status: SummaryStatus
    created_at: datetime
    taken_over_at: datetime | None


class ChatResponse(BaseModel):
    conversation_id: uuid.UUID
    conversation_status: ConversationStatus
    user_message: MessageOut
    assistant_message: MessageOut
    tool_trace_identifiers: list[str] = Field(default_factory=list)
    escalation: EscalationOut | None = None
    order_verification_required: bool = False
    order_verified: bool = False
    order_id: str | None = None


class ConversationOut(BaseModel):
    id: uuid.UUID
    customer_name: str
    locale: Locale
    status: ConversationStatus
    detected_order_id: str | None
    verified_order_id: str | None
    created_at: datetime
    updated_at: datetime
    messages: list[MessageOut]
    escalation: EscalationOut | None = None


class DashboardStats(BaseModel):
    active_ai: int
    ai_resolved: int
    escalated: int


class EscalationListItem(BaseModel):
    id: uuid.UUID
    conversation_id: uuid.UUID
    customer_name: str
    order_id: str | None
    issue_category: str
    reason: str
    priority: Priority
    status: EscalationStatus
    summary_status: SummaryStatus
    created_at: datetime


class ProductVariantOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    size: str
    color: str
    stock: int


class ProductOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    description: str
    category: str
    price: int
    variants: list[ProductVariantOut]


class OrderOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    customer_name: str
    status: str
    courier: str | None
    tracking_number: str | None
    estimated_delivery: date | None


class HealthResponse(BaseModel):
    status: Literal["ok", "degraded"]
    database: Literal["ok", "unavailable"]
    ollama: Literal["ok", "unavailable"]
    model: str


class ErrorDetail(BaseModel):
    code: str
    message: str
    retryable: bool = False


class ErrorResponse(BaseModel):
    error: ErrorDetail
