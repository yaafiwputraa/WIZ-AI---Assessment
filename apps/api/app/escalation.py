import re
from dataclasses import dataclass

from .models import Priority

ORDER_ID_PATTERN = re.compile(r"\bORD-[A-Z0-9-]+\b", re.IGNORECASE)


@dataclass(frozen=True)
class EscalationDecision:
    should_escalate: bool
    category: str = ""
    reason: str = ""
    priority: Priority = Priority.LOW


def extract_order_id(text: str) -> str | None:
    match = ORDER_ID_PATTERN.search(text)
    return match.group(0).upper() if match else None


def detect_escalation(text: str) -> EscalationDecision:
    value = " ".join(text.lower().split())

    high_rules = [
        (
            "damaged_product",
            ["barang rusak", "produk rusak", "datang rusak", "damaged product", "arrived damaged"],
            "Customer reports a damaged product",
        ),
        (
            "payment_dispute",
            [
                "sengketa pembayaran",
                "pembayaran bermasalah",
                "tertagih dua kali",
                "payment dispute",
                "charged twice",
            ],
            "Customer reports a payment dispute",
        ),
        (
            "missing_order",
            [
                "pesanan hilang",
                "paket hilang",
                "tidak pernah sampai",
                "missing order",
                "never arrived",
            ],
            "Customer reports a missing order",
        ),
        (
            "repeated_complaint",
            [
                "komplain dua kali",
                "komplain berkali-kali",
                "sudah komplain",
                "complained twice",
                "repeated complaint",
                "contacted support twice",
            ],
            "Customer reports repeated failed support attempts",
        ),
    ]
    for category, phrases, reason in high_rules:
        if any(phrase in value for phrase in phrases):
            return EscalationDecision(True, category, reason, Priority.HIGH)

    refund_request = any(
        phrase in value
        for phrase in [
            "mau refund",
            "minta refund",
            "ajukan refund",
            "pengembalian dana saya",
            "want a refund",
            "request a refund",
            "refund my",
        ]
    )
    if refund_request:
        return EscalationDecision(
            True, "return_refund", "Customer requests a refund", Priority.HIGH
        )

    medium_rules = [
        (
            "delivery_delay",
            ["pengiriman terlambat", "paket terlambat", "delivery is late", "delivery delay"],
            "Customer reports a delivery delay",
        ),
        (
            "product_exchange",
            ["mau tukar", "tukar barang", "product exchange", "want to exchange"],
            "Customer requests a product exchange",
        ),
        (
            "complaint",
            ["saya kecewa", "pelayanan buruk", "sangat marah", "very angry", "terrible service"],
            "Customer expresses strong dissatisfaction",
        ),
    ]
    for category, phrases, reason in medium_rules:
        if any(phrase in value for phrase in phrases):
            return EscalationDecision(True, category, reason, Priority.MEDIUM)

    if any(
        phrase in value
        for phrase in [
            "bicara dengan manusia",
            "hubungkan ke cs",
            "minta agent",
            "customer service manusia",
            "human agent",
            "talk to a person",
            "speak to support",
        ]
    ):
        return EscalationDecision(
            True, "human_request", "Customer explicitly requests a human agent", Priority.LOW
        )

    return EscalationDecision(False)


PRIORITY_ORDER = {Priority.LOW: 0, Priority.MEDIUM: 1, Priority.HIGH: 2}


def enforce_priority(reason: str, requested: Priority) -> Priority:
    detected = detect_escalation(reason)
    floor = detected.priority if detected.should_escalate else Priority.LOW
    return requested if PRIORITY_ORDER[requested] >= PRIORITY_ORDER[floor] else floor
