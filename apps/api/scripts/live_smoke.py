"""Run the three PRD demo scenarios against a live local API."""

import os
import time

import httpx

API_URL = os.getenv("API_URL", "http://localhost:8000")
AGENT_EMAIL = os.getenv("DEMO_AGENT_EMAIL", "agent@tokomate.local")
AGENT_PASSWORD = os.getenv("DEMO_AGENT_PASSWORD", "DemoAgent123!")
ORDER_VERIFICATION_CODE = os.getenv("DEMO_ORDER_VERIFICATION_CODE", "TOKO192")
SCENARIOS = [
    ("id", "Adidas Samba hitam size 42 masih ada?", None),
    ("id", "ORD-192 saya sudah sampai mana?", ORDER_VERIFICATION_CODE),
    (
        "id",
        "Barang saya datang rusak dan saya sudah komplain dua kali. Saya mau refund.",
        None,
    ),
]


def main() -> None:
    with httpx.Client(base_url=API_URL, timeout=180) as client:
        login = client.post(
            "/api/auth/login",
            json={"email": AGENT_EMAIL, "password": AGENT_PASSWORD},
        )
        login.raise_for_status()
        staff_headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
        for index, (locale, message, verification_code) in enumerate(SCENARIOS, start=1):
            response = client.post(
                "/api/chat",
                json={
                    "customer_name": f"Demo {index}",
                    "locale": locale,
                    "message": message,
                    "order_verification_code": verification_code,
                },
            )
            response.raise_for_status()
            payload = response.json()
            print(f"Scenario {index}: {payload['assistant_message']['content']}")
            print(
                f"  tools={payload['tool_trace_identifiers']} status={payload['conversation_status']}"
            )
            if payload.get("escalation"):
                escalation_id = payload["escalation"]["id"]
                for _ in range(20):
                    detail = client.get(
                        f"/api/escalations/{escalation_id}", headers=staff_headers
                    ).json()
                    if detail["escalation"]["summary_status"] != "pending":
                        print(f"  summary={detail['escalation']['summary_status']}")
                        break
                    time.sleep(1)


if __name__ == "__main__":
    main()
