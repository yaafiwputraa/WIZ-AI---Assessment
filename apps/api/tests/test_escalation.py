import pytest

from app.escalation import detect_escalation, enforce_priority, extract_order_id
from app.models import Priority


@pytest.mark.parametrize(
    ("message", "category", "priority"),
    [
        ("Barang saya datang rusak", "damaged_product", Priority.HIGH),
        ("I was charged twice", "payment_dispute", Priority.HIGH),
        ("Pengiriman terlambat", "delivery_delay", Priority.MEDIUM),
        ("Please connect me to a human agent", "human_request", Priority.LOW),
    ],
)
def test_detects_bilingual_escalation(message, category, priority):
    decision = detect_escalation(message)
    assert decision.should_escalate is True
    assert decision.category == category
    assert decision.priority == priority


def test_refund_policy_question_does_not_escalate():
    assert detect_escalation("Apa kebijakan refund toko?").should_escalate is False


def test_extracts_normalized_order_id():
    assert extract_order_id("tolong cek ord-192 ya") == "ORD-192"
    assert extract_order_id("belum punya nomor") is None


def test_priority_floor_cannot_be_lowered():
    assert enforce_priority("Customer reports damaged product", Priority.LOW) == Priority.HIGH
