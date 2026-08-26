import uuid
from collections.abc import Callable
from typing import Any

from fastapi import BackgroundTasks, Depends, FastAPI, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import select, text
from sqlalchemy.orm import Session, selectinload

from .config import get_settings
from .database import SessionLocal, get_db
from .escalation import detect_escalation, extract_order_id
from .models import (
    Conversation,
    ConversationStatus,
    Escalation,
    EscalationStatus,
    Priority,
    Product,
    Sender,
    SummaryStatus,
)
from .ollama_service import OllamaService, OllamaUnavailable
from .repositories import (
    add_message,
    create_conversation,
    create_escalation,
    dashboard_stats,
    get_conversation,
    get_escalation,
    get_order,
    get_recent_messages,
    list_escalations,
    take_over,
)
from .schemas import (
    ChatRequest,
    ChatResponse,
    ConversationOut,
    DashboardStats,
    ErrorResponse,
    EscalationListItem,
    EscalationOut,
    HealthResponse,
    MessageOut,
    OrderOut,
    ProductOut,
)


class APIError(Exception):
    def __init__(self, status_code: int, code: str, message: str, retryable: bool = False):
        self.status_code = status_code
        self.code = code
        self.message = message
        self.retryable = retryable


settings = get_settings()
app = FastAPI(
    title="TokoMate AI API",
    version="0.1.0",
    description="Bilingual AI customer support for Indonesian SMEs",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type"],
)
app.state.llm = OllamaService(settings)
app.state.session_factory = SessionLocal


@app.exception_handler(APIError)
def api_error_handler(_: Request, exc: APIError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
                "retryable": exc.retryable,
            }
        },
    )


@app.exception_handler(RequestValidationError)
def validation_error_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
    errors = exc.errors()
    message = errors[0].get("msg", "Invalid request") if errors else "Invalid request"
    return JSONResponse(
        status_code=422,
        content={"error": {"code": "validation_error", "message": message, "retryable": False}},
    )


def get_llm(request: Request) -> OllamaService:
    return request.app.state.llm


def _acknowledgement(locale: Any) -> str:
    if locale.value == "id":
        return (
            "Maaf atas kendalanya. Kasus ini sudah saya teruskan ke customer service "
            "agar dapat ditangani lebih lanjut."
        )
    return (
        "I’m sorry about the issue. I’ve escalated this case to customer service "
        "for further assistance."
    )


def _conversation_out(conversation: Conversation) -> ConversationOut:
    messages = sorted(conversation.messages, key=lambda item: item.created_at)
    return ConversationOut(
        id=conversation.id,
        customer_name=conversation.customer_name,
        locale=conversation.locale,
        status=conversation.status,
        detected_order_id=conversation.detected_order_id,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
        messages=[MessageOut.model_validate(item) for item in messages],
        escalation=(
            EscalationOut.model_validate(conversation.escalation)
            if conversation.escalation
            else None
        ),
    )


def generate_summary_task(
    conversation_id: uuid.UUID,
    llm: OllamaService,
    session_factory: Callable[[], Session],
) -> None:
    with session_factory() as db:
        conversation = get_conversation(db, conversation_id)
        if not conversation or not conversation.escalation:
            return
        escalation = conversation.escalation
        if escalation.summary_status == SummaryStatus.READY:
            return
        try:
            messages = sorted(conversation.messages, key=lambda item: item.created_at)
            escalation.summary = llm.generate_summary(messages, conversation.locale)
            escalation.summary_status = SummaryStatus.READY
        except OllamaUnavailable:
            escalation.summary = None
            escalation.summary_status = SummaryStatus.FAILED
        db.commit()


@app.post(
    "/api/chat",
    response_model=ChatResponse,
    responses={409: {"model": ErrorResponse}, 503: {"model": ErrorResponse}},
)
def chat(
    payload: ChatRequest,
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    llm: OllamaService = Depends(get_llm),
) -> ChatResponse:
    if payload.conversation_id:
        conversation = get_conversation(db, payload.conversation_id)
        if conversation is None:
            raise APIError(404, "conversation_not_found", "Conversation not found")
        if conversation.status != ConversationStatus.AI_ACTIVE:
            raise APIError(
                409,
                "conversation_inactive",
                "This conversation is no longer handled by the AI.",
            )
        conversation.locale = payload.locale
    else:
        if not payload.customer_name:
            raise APIError(
                422,
                "customer_name_required",
                "Customer name is required for a new conversation.",
            )
        conversation = create_conversation(db, payload.customer_name, payload.locale)

    order_id = extract_order_id(payload.message)
    if order_id:
        conversation.detected_order_id = order_id
    db.commit()

    user_message = add_message(db, conversation.id, Sender.CUSTOMER, payload.message)
    decision = detect_escalation(payload.message)

    if decision.should_escalate:
        escalation = create_escalation(
            db,
            conversation,
            reason=decision.reason,
            category=decision.category,
            priority=decision.priority,
            order_id=order_id,
        )
        assistant_message = add_message(
            db,
            conversation.id,
            Sender.ASSISTANT,
            _acknowledgement(payload.locale),
            {"escalation_id": str(escalation.id), "policy": "deterministic"},
        )
        background_tasks.add_task(
            generate_summary_task,
            conversation.id,
            llm,
            request.app.state.session_factory,
        )
        return ChatResponse(
            conversation_id=conversation.id,
            conversation_status=ConversationStatus.ESCALATED,
            user_message=MessageOut.model_validate(user_message),
            assistant_message=MessageOut.model_validate(assistant_message),
            escalation=EscalationOut.model_validate(escalation),
        )

    history = get_recent_messages(db, conversation.id, limit=30)
    try:
        result = llm.respond(db, conversation, history, payload.locale)
    except OllamaUnavailable as exc:
        raise APIError(
            503,
            "ollama_unavailable",
            "The AI service is temporarily unavailable.",
            retryable=True,
        ) from exc

    assistant_message = add_message(
        db,
        conversation.id,
        Sender.ASSISTANT,
        result.content,
        {"tool_traces": result.traces} if result.traces else None,
    )
    escalation = db.scalar(select(Escalation).where(Escalation.conversation_id == conversation.id))
    if escalation:
        background_tasks.add_task(
            generate_summary_task,
            conversation.id,
            llm,
            request.app.state.session_factory,
        )
    return ChatResponse(
        conversation_id=conversation.id,
        conversation_status=(
            ConversationStatus.ESCALATED if escalation else ConversationStatus.AI_ACTIVE
        ),
        user_message=MessageOut.model_validate(user_message),
        assistant_message=MessageOut.model_validate(assistant_message),
        tool_trace_identifiers=[trace["trace_id"] for trace in result.traces],
        escalation=EscalationOut.model_validate(escalation) if escalation else None,
    )


@app.get("/api/conversations/{conversation_id}", response_model=ConversationOut)
def conversation_detail(
    conversation_id: uuid.UUID, db: Session = Depends(get_db)
) -> ConversationOut:
    conversation = get_conversation(db, conversation_id)
    if conversation is None:
        raise APIError(404, "conversation_not_found", "Conversation not found")
    return _conversation_out(conversation)


@app.post("/api/conversations/{conversation_id}/resolve", response_model=ConversationOut)
def resolve_conversation(
    conversation_id: uuid.UUID, db: Session = Depends(get_db)
) -> ConversationOut:
    conversation = get_conversation(db, conversation_id)
    if conversation is None:
        raise APIError(404, "conversation_not_found", "Conversation not found")
    if conversation.status in {ConversationStatus.ESCALATED, ConversationStatus.HUMAN_ACTIVE}:
        raise APIError(
            409, "conversation_escalated", "An escalated conversation cannot be AI-resolved."
        )
    conversation.status = ConversationStatus.RESOLVED
    db.commit()
    conversation = get_conversation(db, conversation_id)
    return _conversation_out(conversation)


@app.get("/api/dashboard/stats", response_model=DashboardStats)
def stats(db: Session = Depends(get_db)) -> DashboardStats:
    return DashboardStats(**dashboard_stats(db))


@app.get("/api/escalations", response_model=list[EscalationListItem])
def escalations(
    status: EscalationStatus | None = None,
    priority: Priority | None = None,
    limit: int = Query(default=50, ge=1, le=100),
    db: Session = Depends(get_db),
) -> list[EscalationListItem]:
    return [
        EscalationListItem(
            id=item.id,
            conversation_id=item.conversation_id,
            customer_name=customer_name,
            order_id=item.order_id,
            issue_category=item.issue_category,
            reason=item.reason,
            priority=item.priority,
            status=item.status,
            summary_status=item.summary_status,
            created_at=item.created_at,
        )
        for item, customer_name in list_escalations(db, status, priority, limit)
    ]


@app.get("/api/escalations/{escalation_id}", response_model=ConversationOut)
def escalation_detail(escalation_id: uuid.UUID, db: Session = Depends(get_db)) -> ConversationOut:
    escalation = get_escalation(db, escalation_id)
    if escalation is None:
        raise APIError(404, "escalation_not_found", "Escalation not found")
    return _conversation_out(escalation.conversation)


@app.post("/api/escalations/{escalation_id}/takeover", response_model=EscalationOut)
def escalation_takeover(escalation_id: uuid.UUID, db: Session = Depends(get_db)) -> EscalationOut:
    escalation = get_escalation(db, escalation_id)
    if escalation is None:
        raise APIError(404, "escalation_not_found", "Escalation not found")
    return EscalationOut.model_validate(take_over(db, escalation))


@app.get("/api/products", response_model=list[ProductOut])
def products(db: Session = Depends(get_db)) -> list[Product]:
    return list(
        db.scalars(select(Product).options(selectinload(Product.variants)).order_by(Product.name))
    )


@app.get("/api/orders/{order_id}", response_model=OrderOut)
def order_detail(order_id: str, db: Session = Depends(get_db)) -> Any:
    order = get_order(db, order_id)
    if order is None:
        raise APIError(404, "order_not_found", "Order not found")
    return order


@app.get("/api/health", response_model=HealthResponse)
def health(db: Session = Depends(get_db), llm: OllamaService = Depends(get_llm)) -> JSONResponse:
    database_status = "ok"
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        database_status = "unavailable"
    ollama_status = "ok" if llm.ping() else "unavailable"
    overall = "ok" if database_status == "ok" and ollama_status == "ok" else "degraded"
    payload = HealthResponse(
        status=overall,
        database=database_status,
        ollama=ollama_status,
        model=settings.ollama_model,
    )
    return JSONResponse(status_code=200 if overall == "ok" else 503, content=payload.model_dump())
