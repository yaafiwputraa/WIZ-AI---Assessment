from datetime import date

from sqlalchemy import select

from .database import SessionLocal
from .models import FAQ, Locale, Order, Product, ProductVariant

PRODUCTS = [
    {
        "name": "Adidas Samba",
        "description": "Classic lifestyle sneakers with a gum sole.",
        "category": "Sneakers",
        "price": 1_499_000,
        "variants": [
            {"size": "41", "color": "Black / Hitam", "stock": 2},
            {"size": "42", "color": "Black / Hitam", "stock": 3},
            {"size": "42", "color": "White / Putih", "stock": 1},
        ],
    },
    {
        "name": "Velocity Run Lite",
        "description": "Lightweight daily running shoes.",
        "category": "Running Shoes",
        "price": 649_000,
        "variants": [
            {"size": "40", "color": "Black / Hitam", "stock": 5},
            {"size": "42", "color": "Blue / Biru", "stock": 4},
        ],
    },
    {
        "name": "Nusantara Canvas",
        "description": "Versatile locally made canvas shoes.",
        "category": "Casual Shoes",
        "price": 389_000,
        "variants": [
            {"size": "39", "color": "White / Putih", "stock": 6},
            {"size": "42", "color": "Black / Hitam", "stock": 0},
        ],
    },
]

FAQS = [
    (
        Locale.ID,
        "Metode pembayaran apa yang tersedia?",
        "Kami menerima transfer bank, virtual account, QRIS, dan kartu debit/kredit.",
        ["pembayaran", "bayar", "transfer", "qris", "kartu"],
    ),
    (
        Locale.EN,
        "Which payment methods are available?",
        "We accept bank transfer, virtual account, QRIS, and debit or credit cards.",
        ["payment", "pay", "transfer", "qris", "card"],
    ),
    (
        Locale.ID,
        "Berapa lama waktu pengiriman?",
        "Pesanan diproses 1–2 hari kerja. Estimasi pengiriman reguler adalah 2–5 hari kerja.",
        ["pengiriman", "kirim", "ongkir", "estimasi", "kurir"],
    ),
    (
        Locale.EN,
        "How long does shipping take?",
        "Orders are processed in 1–2 business days. Regular delivery takes about 2–5 business days.",
        ["shipping", "delivery", "courier", "estimate"],
    ),
    (
        Locale.ID,
        "Apa kebijakan retur dan penukaran?",
        "Retur atau penukaran dapat diajukan maksimal 7 hari setelah barang diterima, selama produk belum digunakan dan label masih terpasang. Keputusan refund ditinjau oleh customer service.",
        ["retur", "refund", "penukaran", "tukar", "kembali"],
    ),
    (
        Locale.EN,
        "What is the return and exchange policy?",
        "Returns or exchanges may be requested within 7 days of delivery when the item is unused and tags remain attached. Refund decisions are reviewed by customer service.",
        ["return", "refund", "exchange", "policy"],
    ),
    (
        Locale.ID,
        "Kapan toko beroperasi?",
        "Customer service beroperasi Senin–Sabtu pukul 09.00–18.00 WIB.",
        ["jam", "operasional", "buka", "customer service"],
    ),
    (
        Locale.EN,
        "What are the store operating hours?",
        "Customer service is available Monday–Saturday from 09:00–18:00 WIB.",
        ["hours", "open", "operating", "customer service"],
    ),
]


def seed() -> None:
    with SessionLocal() as db:
        for data in PRODUCTS:
            product = db.scalar(select(Product).where(Product.name == data["name"]))
            if product is None:
                product = Product(
                    name=data["name"],
                    description=data["description"],
                    category=data["category"],
                    price=data["price"],
                )
                db.add(product)
                db.flush()
            else:
                product.description = data["description"]
                product.category = data["category"]
                product.price = data["price"]
            for variant_data in data["variants"]:
                variant = db.scalar(
                    select(ProductVariant).where(
                        ProductVariant.product_id == product.id,
                        ProductVariant.size == variant_data["size"],
                        ProductVariant.color == variant_data["color"],
                    )
                )
                if variant is None:
                    db.add(ProductVariant(product_id=product.id, **variant_data))
                else:
                    variant.stock = variant_data["stock"]

        order = db.get(Order, "ORD-192")
        if order is None:
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

        for locale, question, answer, keywords in FAQS:
            faq = db.scalar(select(FAQ).where(FAQ.locale == locale, FAQ.question == question))
            if faq is None:
                db.add(FAQ(locale=locale, question=question, answer=answer, keywords=keywords))
            else:
                faq.answer = answer
                faq.keywords = keywords
        db.commit()


if __name__ == "__main__":
    seed()
