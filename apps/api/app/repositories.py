import uuid
from collections.abc import Sequence
from datetime import UTC, datetime

from sqlalchemy import String, cast, func, or_, select
from sqlalchemy.orm import Session, selectinload

from .models import (
    FAQ,
    Conversation,
    ConversationStatus,
    Escalation,
    EscalationStatus,
    Locale,
    Message,
    Order,
    Priority,
    Product,
    ProductVariant,
    Sender,
)


def create_conversation(db: Session, customer_name: str, locale: Locale) -> Conversation:
    conversation = Conversation(customer_name=customer_name, locale=locale)
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    return conversation


def get_conversation(db: Session, conversation_id: uuid.UUID) -> Conversation | None:
    return db.scalar(
        select(Conversation)
        .where(Conversation.id == conversation_id)
        .options(selectinload(Conversation.messages), selectinload(Conversation.escalation))
    )


def add_message(
    db: Session,
    conversation_id: uuid.UUID,
    sender: Sender,
    content: str,
    tool_metadata: dict | None = None,
) -> Message:
    message = Message(
        conversation_id=conversation_id,
        sender=sender,
        content=content,
        tool_metadata=tool_metadata,
    )
    db.add(message)
    db.commit()
    db.refresh(message)
    return message


def get_recent_messages(db: Session, conversation_id: uuid.UUID, limit: int = 30) -> list[Message]:
    rows = list(
        db.scalars(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.desc())
            .limit(limit)
        )
    )
    return list(reversed(rows))


def search_products(
    db: Session,
    query: str,
    max_price: int | None = None,
    category: str | None = None,
    color: str | None = None,
    limit: int = 5,
) -> list[Product]:
    terms = [term for term in query.lower().split() if len(term) > 1]
    conditions = []
    for term in terms:
        pattern = f"%{term}%"
        conditions.append(
            or_(
                func.lower(Product.name).like(pattern),
                func.lower(Product.description).like(pattern),
                func.lower(Product.category).like(pattern),
                func.lower(ProductVariant.color).like(pattern),
            )
        )
    statement = (
        select(Product).outerjoin(ProductVariant).options(selectinload(Product.variants)).distinct()
    )
    if conditions:
        statement = statement.where(or_(*conditions))
    if max_price is not None:
        statement = statement.where(Product.price <= max_price)
    if category:
        statement = statement.where(func.lower(Product.category).like(f"%{category.lower()}%"))
    if color:
        statement = statement.where(func.lower(ProductVariant.color).like(f"%{color.lower()}%"))
    return list(db.scalars(statement.limit(limit)).unique())


def find_product(db: Session, product_name: str) -> Product | None:
    return db.scalar(
        select(Product)
        .where(func.lower(Product.name).like(f"%{product_name.lower()}%"))
        .options(selectinload(Product.variants))
        .limit(1)
    )


def check_stock(
    db: Session, product_name: str, size: str | None = None, color: str | None = None
) -> tuple[Product | None, list[ProductVariant]]:
    product = find_product(db, product_name)
    if product is None:
        return None, []
    variants = product.variants
    if size:
        variants = [item for item in variants if item.size.lower() == size.lower()]
    if color:
        normalized = color.lower()
        aliases = {"hitam": "black", "putih": "white", "biru": "blue", "merah": "red"}
        normalized = aliases.get(normalized, normalized)
        variants = [
            item
            for item in variants
            if normalized in item.color.lower() or color.lower() in item.color.lower()
        ]
    return product, variants


def get_order(db: Session, order_id: str) -> Order | None:
    return db.get(Order, order_id.upper())


def search_faq(db: Session, query: str, locale: Locale, limit: int = 3) -> list[FAQ]:
    terms = [term for term in query.lower().split() if len(term) > 2]
    statement = select(FAQ).where(FAQ.locale == locale)
    if terms:
        conditions = []
        for term in terms:
            pattern = f"%{term}%"
            conditions.extend(
                [
                    func.lower(FAQ.question).like(pattern),
                    func.lower(FAQ.answer).like(pattern),
                    func.lower(cast(FAQ.keywords, String)).like(pattern),
                ]
            )
        statement = statement.where(or_(*conditions))
    return list(db.scalars(statement.limit(limit)))


def create_escalation(
    db: Session,
    conversation: Conversation,
    reason: str,
    category: str,
    priority: Priority,
    order_id: str | None = None,
) -> Escalation:
    existing = db.scalar(select(Escalation).where(Escalation.conversation_id == conversation.id))
    if existing:
        return existing
    escalation = Escalation(
        conversation_id=conversation.id,
        order_id=order_id or conversation.detected_order_id,
        reason=reason,
        issue_category=category,
        priority=priority,
    )
    conversation.status = ConversationStatus.ESCALATED
    db.add(escalation)
    db.commit()
    db.refresh(escalation)
    return escalation


def list_escalations(
    db: Session,
    status: EscalationStatus | None,
    priority: Priority | None,
    limit: int,
) -> Sequence[tuple[Escalation, str]]:
    statement = (
        select(Escalation, Conversation.customer_name)
        .join(Conversation)
        .order_by(Escalation.created_at.desc())
        .limit(limit)
    )
    if status:
        statement = statement.where(Escalation.status == status)
    if priority:
        statement = statement.where(Escalation.priority == priority)
    return db.execute(statement).all()


def get_escalation(db: Session, escalation_id: uuid.UUID) -> Escalation | None:
    return db.scalar(
        select(Escalation)
        .where(Escalation.id == escalation_id)
        .options(
            selectinload(Escalation.conversation).selectinload(Conversation.messages),
            selectinload(Escalation.conversation).selectinload(Conversation.escalation),
        )
    )


def take_over(db: Session, escalation: Escalation) -> Escalation:
    if escalation.status == EscalationStatus.TAKEN_OVER:
        return escalation
    escalation.status = EscalationStatus.TAKEN_OVER
    escalation.taken_over_at = datetime.now(UTC)
    escalation.conversation.status = ConversationStatus.HUMAN_ACTIVE
    db.commit()
    db.refresh(escalation)
    return escalation


def dashboard_stats(db: Session) -> dict[str, int]:
    active_ai = db.scalar(
        select(func.count())
        .select_from(Conversation)
        .where(Conversation.status == ConversationStatus.AI_ACTIVE)
    )
    ai_resolved = db.scalar(
        select(func.count())
        .select_from(Conversation)
        .where(Conversation.status == ConversationStatus.RESOLVED)
    )
    escalated = db.scalar(select(func.count()).select_from(Escalation))
    return {
        "active_ai": int(active_ai or 0),
        "ai_resolved": int(ai_resolved or 0),
        "escalated": int(escalated or 0),
    }
