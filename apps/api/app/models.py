import enum
import uuid
from datetime import date, datetime
from typing import Any

from sqlalchemy import (
    JSON,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class Locale(str, enum.Enum):
    ID = "id"
    EN = "en"


class ConversationStatus(str, enum.Enum):
    AI_ACTIVE = "ai_active"
    ESCALATED = "escalated"
    HUMAN_ACTIVE = "human_active"
    RESOLVED = "resolved"


class Sender(str, enum.Enum):
    CUSTOMER = "customer"
    ASSISTANT = "assistant"
    AGENT = "agent"
    SYSTEM = "system"


class Priority(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class EscalationStatus(str, enum.Enum):
    OPEN = "open"
    TAKEN_OVER = "taken_over"


class SummaryStatus(str, enum.Enum):
    PENDING = "pending"
    READY = "ready"
    FAILED = "failed"


def enum_column(enum_type: type[enum.Enum], default: enum.Enum | None = None) -> Mapped[Any]:
    return mapped_column(
        Enum(
            enum_type,
            native_enum=False,
            values_callable=lambda items: [item.value for item in items],
        ),
        default=default,
    )


class Product(Base):
    __tablename__ = "products"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(160), unique=True, index=True)
    description: Mapped[str] = mapped_column(Text, default="")
    category: Mapped[str] = mapped_column(String(80), index=True)
    price: Mapped[int] = mapped_column(Integer)
    variants: Mapped[list["ProductVariant"]] = relationship(
        back_populates="product", cascade="all, delete-orphan", lazy="selectin"
    )


class ProductVariant(Base):
    __tablename__ = "product_variants"
    __table_args__ = (UniqueConstraint("product_id", "size", "color"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    product_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"))
    size: Mapped[str] = mapped_column(String(40), default="")
    color: Mapped[str] = mapped_column(String(60), default="")
    stock: Mapped[int] = mapped_column(Integer, default=0)
    product: Mapped[Product] = relationship(back_populates="variants")


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    customer_name: Mapped[str] = mapped_column(String(120))
    status: Mapped[str] = mapped_column(String(60))
    courier: Mapped[str | None] = mapped_column(String(80), nullable=True)
    tracking_number: Mapped[str | None] = mapped_column(String(120), nullable=True)
    estimated_delivery: Mapped[date | None] = mapped_column(Date, nullable=True)


class FAQ(Base):
    __tablename__ = "faq"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    locale: Mapped[Locale] = enum_column(Locale, Locale.ID)
    question: Mapped[str] = mapped_column(String(240))
    answer: Mapped[str] = mapped_column(Text)
    keywords: Mapped[list[str]] = mapped_column(JSON, default=list)


class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    customer_name: Mapped[str] = mapped_column(String(120))
    locale: Mapped[Locale] = enum_column(Locale, Locale.ID)
    status: Mapped[ConversationStatus] = enum_column(
        ConversationStatus, ConversationStatus.AI_ACTIVE
    )
    detected_order_id: Mapped[str | None] = mapped_column(String(40), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    messages: Mapped[list["Message"]] = relationship(
        back_populates="conversation", cascade="all, delete-orphan", lazy="selectin"
    )
    escalation: Mapped["Escalation | None"] = relationship(
        back_populates="conversation", uselist=False, lazy="selectin"
    )


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    conversation_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("conversations.id", ondelete="CASCADE"), index=True
    )
    sender: Mapped[Sender] = enum_column(Sender)
    content: Mapped[str] = mapped_column(Text)
    tool_metadata: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
    conversation: Mapped[Conversation] = relationship(back_populates="messages")


class Escalation(Base):
    __tablename__ = "escalations"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    conversation_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("conversations.id", ondelete="CASCADE"), unique=True, index=True
    )
    order_id: Mapped[str | None] = mapped_column(String(40), nullable=True)
    issue_category: Mapped[str] = mapped_column(String(80))
    reason: Mapped[str] = mapped_column(Text)
    priority: Mapped[Priority] = enum_column(Priority, Priority.LOW)
    status: Mapped[EscalationStatus] = enum_column(EscalationStatus, EscalationStatus.OPEN)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    summary_status: Mapped[SummaryStatus] = enum_column(SummaryStatus, SummaryStatus.PENDING)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
    taken_over_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    conversation: Mapped[Conversation] = relationship(back_populates="escalation")
