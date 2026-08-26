import json
import uuid
from dataclasses import dataclass
from typing import Any

from sqlalchemy.orm import Session

from .escalation import enforce_priority
from .models import Conversation, Locale, Priority
from .repositories import (
    check_stock,
    create_escalation,
    find_product,
    get_order,
    search_faq,
    search_products,
)

TOOL_SCHEMAS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "search_products",
            "description": "Search the store catalog. Use this before claiming a product exists.",
            "parameters": {
                "type": "object",
                "required": ["query"],
                "properties": {
                    "query": {"type": "string"},
                    "max_price": {"type": ["integer", "null"]},
                    "category": {"type": ["string", "null"]},
                    "color": {"type": ["string", "null"]},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "check_product_stock",
            "description": "Check stock for a named product and optional size or color.",
            "parameters": {
                "type": "object",
                "required": ["product_name"],
                "properties": {
                    "product_name": {"type": "string"},
                    "size": {"type": ["string", "null"]},
                    "color": {"type": ["string", "null"]},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_product_price",
            "description": "Get the current database price of a named product.",
            "parameters": {
                "type": "object",
                "required": ["product_name"],
                "properties": {"product_name": {"type": "string"}},
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "check_order_status",
            "description": "Look up an order by its exact ORD-* identifier.",
            "parameters": {
                "type": "object",
                "required": ["order_id"],
                "properties": {"order_id": {"type": "string"}},
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_faq",
            "description": "Search store payment, shipping, return, refund, exchange, or opening-hour policies.",
            "parameters": {
                "type": "object",
                "required": ["query"],
                "properties": {"query": {"type": "string"}},
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "escalate_to_human",
            "description": "Escalate a sensitive, unresolved, or explicitly requested case to a human agent.",
            "parameters": {
                "type": "object",
                "required": ["reason", "issue_category", "priority"],
                "properties": {
                    "reason": {"type": "string"},
                    "issue_category": {"type": "string"},
                    "priority": {"type": "string", "enum": ["low", "medium", "high"]},
                    "order_id": {"type": ["string", "null"]},
                },
            },
        },
    },
]


@dataclass
class ToolExecution:
    trace_id: str
    name: str
    arguments: dict[str, Any]
    result: dict[str, Any]


def product_dict(product: Any) -> dict[str, Any]:
    return {
        "id": str(product.id),
        "name": product.name,
        "description": product.description,
        "category": product.category,
        "price_idr": product.price,
        "variants": [
            {"size": variant.size, "color": variant.color, "stock": variant.stock}
            for variant in product.variants
        ],
    }


class ToolExecutor:
    def __init__(self, db: Session, conversation: Conversation, locale: Locale):
        self.db = db
        self.conversation = conversation
        self.locale = locale

    def execute(self, name: str, arguments: dict[str, Any]) -> ToolExecution:
        trace_id = str(uuid.uuid4())
        try:
            result = self._execute(name, arguments)
        except (TypeError, ValueError) as exc:
            result = {
                "ok": False,
                "error": "invalid_tool_arguments",
                "message": str(exc),
            }
        return ToolExecution(trace_id, name, arguments, result)

    def _execute(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        if name == "search_products":
            query = str(arguments.get("query", "")).strip()
            if not query:
                raise ValueError("query is required")
            products = search_products(
                self.db,
                query,
                max_price=arguments.get("max_price"),
                category=arguments.get("category"),
                color=arguments.get("color"),
            )
            return {
                "ok": True,
                "found": bool(products),
                "products": [product_dict(product) for product in products],
            }

        if name == "check_product_stock":
            product_name = str(arguments.get("product_name", "")).strip()
            if not product_name:
                raise ValueError("product_name is required")
            product, variants = check_stock(
                self.db,
                product_name,
                size=_optional_string(arguments.get("size")),
                color=_optional_string(arguments.get("color")),
            )
            if product is None:
                return {"ok": True, "found": False, "product_name": product_name}
            return {
                "ok": True,
                "found": True,
                "product_name": product.name,
                "price_idr": product.price,
                "matching_variants": [
                    {"size": item.size, "color": item.color, "stock": item.stock}
                    for item in variants
                ],
                "available": any(item.stock > 0 for item in variants),
            }

        if name == "get_product_price":
            product_name = str(arguments.get("product_name", "")).strip()
            if not product_name:
                raise ValueError("product_name is required")
            product = find_product(self.db, product_name)
            return (
                {"ok": True, "found": False, "product_name": product_name}
                if product is None
                else {
                    "ok": True,
                    "found": True,
                    "product_name": product.name,
                    "price_idr": product.price,
                }
            )

        if name == "check_order_status":
            order_id = str(arguments.get("order_id", "")).strip().upper()
            if not order_id:
                raise ValueError("order_id is required")
            order = get_order(self.db, order_id)
            if order is None:
                return {"ok": True, "found": False, "order_id": order_id}
            return {
                "ok": True,
                "found": True,
                "order": {
                    "order_id": order.id,
                    "status": order.status,
                    "courier": order.courier,
                    "tracking_number": order.tracking_number,
                    "estimated_delivery": (
                        order.estimated_delivery.isoformat() if order.estimated_delivery else None
                    ),
                },
            }

        if name == "search_faq":
            query = str(arguments.get("query", "")).strip()
            if not query:
                raise ValueError("query is required")
            matches = search_faq(self.db, query, self.locale)
            return {
                "ok": True,
                "found": bool(matches),
                "matches": [{"question": item.question, "answer": item.answer} for item in matches],
            }

        if name == "escalate_to_human":
            reason = str(arguments.get("reason", "")).strip()
            category = str(arguments.get("issue_category", "complaint")).strip()
            try:
                requested = Priority(str(arguments.get("priority", "low")).lower())
            except ValueError as exc:
                raise ValueError("priority must be low, medium, or high") from exc
            priority = enforce_priority(reason, requested)
            escalation = create_escalation(
                self.db,
                self.conversation,
                reason=reason or "Human assistance requested",
                category=category or "human_request",
                priority=priority,
                order_id=_optional_string(arguments.get("order_id")),
            )
            return {
                "ok": True,
                "status": "escalated",
                "escalation_id": str(escalation.id),
                "priority": escalation.priority.value,
                "reason": escalation.reason,
            }

        return {"ok": False, "error": "unknown_tool", "message": f"Unknown tool: {name}"}


def _optional_string(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def tool_result_content(execution: ToolExecution) -> str:
    return json.dumps(execution.result, ensure_ascii=False, default=str)
