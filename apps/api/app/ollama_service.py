from dataclasses import dataclass
from typing import Any

from ollama import Client
from pydantic import BaseModel, Field

from .config import Settings
from .models import Conversation, Locale, Message, Sender
from .tools import TOOL_SCHEMAS, ToolExecutor, tool_result_content


class OllamaUnavailable(RuntimeError):
    pass


class SummaryPayload(BaseModel):
    overview: str
    key_facts: list[str] = Field(default_factory=list, max_length=6)
    sentiment: str
    suggested_action: str
    priority: str


@dataclass
class AgentResult:
    content: str
    traces: list[dict[str, Any]]


class OllamaService:
    def __init__(self, settings: Settings):
        self.model = settings.ollama_model
        self.client = Client(
            host=settings.ollama_base_url,
            timeout=settings.ollama_timeout_seconds,
        )

    def ping(self) -> bool:
        try:
            self.client.list()
            return True
        except Exception:
            return False

    def respond(
        self,
        db: Any,
        conversation: Conversation,
        history: list[Message],
        locale: Locale,
        order_verification_code: str | None = None,
    ) -> AgentResult:
        messages: list[dict[str, Any]] = [{"role": "system", "content": _system_prompt(locale)}]
        for item in history:
            if item.sender == Sender.CUSTOMER:
                messages.append({"role": "user", "content": item.content})
            elif item.sender == Sender.ASSISTANT:
                messages.append({"role": "assistant", "content": item.content})

        executor = ToolExecutor(db, conversation, locale, order_verification_code)
        traces: list[dict[str, Any]] = []

        try:
            for _ in range(4):
                response = self.client.chat(
                    model=self.model,
                    messages=messages,
                    tools=TOOL_SCHEMAS,
                    stream=False,
                    think=False,
                    options={"temperature": 0.1},
                )
                assistant = response.message
                calls = list(assistant.tool_calls or [])
                if not calls:
                    content = (assistant.content or "").strip()
                    if not content:
                        content = _safe_fallback(locale)
                    return AgentResult(content=content, traces=traces)

                assistant_payload = assistant.model_dump(exclude_none=True)
                messages.append(assistant_payload)
                for call in calls:
                    execution = executor.execute(call.function.name, call.function.arguments or {})
                    traces.append(
                        {
                            "trace_id": execution.trace_id,
                            "tool": execution.name,
                            "arguments": execution.arguments,
                            "result": execution.result,
                        }
                    )
                    messages.append(
                        {
                            "role": "tool",
                            "tool_name": execution.name,
                            "content": tool_result_content(execution),
                        }
                    )
            return AgentResult(content=_safe_fallback(locale), traces=traces)
        except Exception as exc:
            raise OllamaUnavailable(str(exc)) from exc

    def generate_summary(self, messages: list[Message], locale: Locale) -> str:
        transcript = "\n".join(
            f"{message.sender.value}: {message.content}" for message in messages[-30:]
        )
        language = "Bahasa Indonesia" if locale == Locale.ID else "English"
        prompt = (
            f"Summarize this escalated customer-support transcript in {language}. "
            "Use only facts in the transcript. Return the requested JSON fields.\n\n"
            f"{transcript}"
        )
        last_error: Exception | None = None
        for _ in range(2):
            try:
                response = self.client.chat(
                    model=self.model,
                    messages=[
                        {
                            "role": "system",
                            "content": "You create factual, concise customer-support handoff summaries.",
                        },
                        {"role": "user", "content": prompt},
                    ],
                    format=SummaryPayload.model_json_schema(),
                    stream=False,
                    think=False,
                    options={"temperature": 0},
                )
                payload = SummaryPayload.model_validate_json(response.message.content)
                return _render_summary(payload, locale)
            except Exception as exc:
                last_error = exc
        raise OllamaUnavailable(str(last_error or "Summary generation failed"))


def _system_prompt(locale: Locale) -> str:
    language = "Bahasa Indonesia" if locale == Locale.ID else "English"
    return f"""
You are TokoMate AI, a friendly customer-support assistant for an Indonesian SME.
Reply only in {language}, using concise and natural customer-service language.

Rules:
- Product existence, price, stock, order status, shipping facts, and policy facts MUST come from tools.
- Never guess or invent business facts. If a tool says found=false, say the information was not found.
- Never reveal order status, courier, tracking, or delivery facts unless the order tool says verified=true.
- If the order tool says verification_required=true, direct the customer to the separate order
  verification field. Never ask them to place the verification code in the normal chat message.
- Use check_product_stock for stock/variant questions, check_order_status for ORD-* questions,
  search_products for catalog discovery, get_product_price for price, and search_faq for policies.
- Escalate refunds, damaged products, payment disputes, missing orders, unresolved/repeated complaints,
  strong dissatisfaction, uncertainty on sensitive issues, or an explicit human-agent request.
- Do not promise a refund or decide eligibility. Acknowledge escalation politely.
- You are in a tool loop and may call more than one tool before replying.
""".strip()


def _safe_fallback(locale: Locale) -> str:
    if locale == Locale.ID:
        return "Maaf, saya belum bisa memastikan informasinya. Silakan coba lagi atau minta bantuan agen."
    return "Sorry, I could not verify that information. Please try again or ask for a human agent."


def _render_summary(payload: SummaryPayload, locale: Locale) -> str:
    facts = "\n".join(f"- {fact}" for fact in payload.key_facts) or "-"
    if locale == Locale.ID:
        return (
            f"Ringkasan: {payload.overview}\n\nFakta utama:\n{facts}\n\n"
            f"Sentimen: {payload.sentiment}\nPrioritas: {payload.priority}\n\n"
            f"Tindakan yang disarankan: {payload.suggested_action}"
        )
    return (
        f"Summary: {payload.overview}\n\nKey facts:\n{facts}\n\n"
        f"Sentiment: {payload.sentiment}\nPriority: {payload.priority}\n\n"
        f"Suggested action: {payload.suggested_action}"
    )
