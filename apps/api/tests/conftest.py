import os
from datetime import date

os.environ["DATABASE_URL"] = "sqlite:///./tokomate-test-bootstrap.db"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.auth import hash_password
from app.database import Base, get_db
from app.main import app
from app.models import FAQ, Locale, Order, Product, ProductVariant, StaffRole, StaffUser
from app.ollama_service import AgentResult
from app.tools import ToolExecutor

AGENT_PASSWORD_HASH = hash_password("DemoAgent123!")
ADMIN_PASSWORD_HASH = hash_password("DemoAdmin123!")


class FakeLLM:
    model = "fake-qwen3:4b"

    def ping(self) -> bool:
        return True

    def respond(self, db, conversation, history, locale):
        message = history[-1].content.lower()
        executor = ToolExecutor(db, conversation, locale)
        if "ord-" in message:
            execution = executor.execute("check_order_status", {"order_id": "ORD-192"})
            content = (
                "Pesanan ORD-192 sudah dikirim dengan JNE. Resi JNE123456, estimasi 26 Agustus 2026."
                if locale == Locale.ID
                else "Order ORD-192 has shipped with JNE. Tracking JNE123456, estimated August 26, 2026."
            )
        elif "samba" in message:
            execution = executor.execute(
                "check_product_stock",
                {"product_name": "Adidas Samba", "size": "42", "color": "hitam"},
            )
            content = (
                "Adidas Samba hitam size 42 tersedia 3 pasang dengan harga Rp1.499.000."
                if locale == Locale.ID
                else "Adidas Samba black size 42 has 3 pairs in stock for Rp1,499,000."
            )
        elif "payment" in message or "pembayaran" in message:
            execution = executor.execute("search_faq", {"query": message})
            content = (
                "Kami menerima transfer bank, virtual account, QRIS, dan kartu."
                if locale == Locale.ID
                else "We accept bank transfer, virtual account, QRIS, and cards."
            )
        else:
            return AgentResult(
                content=(
                    "Maaf, informasi tersebut tidak ditemukan."
                    if locale == Locale.ID
                    else "Sorry, that information was not found."
                ),
                traces=[],
            )
        return AgentResult(
            content=content,
            traces=[
                {
                    "trace_id": execution.trace_id,
                    "tool": execution.name,
                    "arguments": execution.arguments,
                    "result": execution.result,
                }
            ],
        )

    def generate_summary(self, messages, locale):
        if locale == Locale.ID:
            return (
                "Ringkasan: Pelanggan melaporkan barang rusak dan meminta refund.\n\n"
                "Fakta utama:\n- Sudah komplain dua kali\n- Produk datang rusak\n\n"
                "Sentimen: Negatif\nPrioritas: High\n\n"
                "Tindakan yang disarankan: Tinjau kelayakan refund dan hubungi pelanggan."
            )
        return "Summary: The customer reports a damaged product and requests a refund."


@pytest.fixture()
def client():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    testing_session = sessionmaker(bind=engine, expire_on_commit=False)
    Base.metadata.create_all(engine)

    with testing_session() as db:
        product = Product(
            name="Adidas Samba",
            description="Classic lifestyle sneakers",
            category="Sneakers",
            price=1_499_000,
        )
        db.add(product)
        db.flush()
        db.add(ProductVariant(product_id=product.id, size="42", color="Black / Hitam", stock=3))
        db.add(
            Order(
                id="ORD-192",
                customer_name="Budi",
                status="Shipped",
                courier="JNE",
                tracking_number="JNE123456",
                estimated_delivery=date(2026, 8, 26),
            )
        )
        db.add_all(
            [
                FAQ(
                    locale=Locale.ID,
                    question="Metode pembayaran?",
                    answer="Transfer bank, virtual account, QRIS, dan kartu.",
                    keywords=["pembayaran", "qris"],
                ),
                FAQ(
                    locale=Locale.EN,
                    question="Payment methods?",
                    answer="Bank transfer, virtual account, QRIS, and cards.",
                    keywords=["payment", "qris"],
                ),
            ]
        )
        db.add_all(
            [
                StaffUser(
                    email="agent@tokomate.local",
                    full_name="Demo Support Agent",
                    password_hash=AGENT_PASSWORD_HASH,
                    role=StaffRole.AGENT,
                ),
                StaffUser(
                    email="admin@tokomate.local",
                    full_name="Demo Administrator",
                    password_hash=ADMIN_PASSWORD_HASH,
                    role=StaffRole.ADMIN,
                ),
            ]
        )
        db.commit()

    def override_db():
        with testing_session() as db:
            yield db

    app.dependency_overrides[get_db] = override_db
    app.state.session_factory = testing_session
    app.state.llm = FakeLLM()
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    Base.metadata.drop_all(engine)
