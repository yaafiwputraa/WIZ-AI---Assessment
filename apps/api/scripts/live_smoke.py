"""Run the three PRD demo scenarios against a live local API."""

import os
import time

import httpx

API_URL = os.getenv("API_URL", "http://localhost:8000")
SCENARIOS = [
    ("id", "Adidas Samba hitam size 42 masih ada?"),
    ("id", "ORD-192 saya sudah sampai mana?"),
    ("id", "Barang saya datang rusak dan saya sudah komplain dua kali. Saya mau refund."),
]


def main() -> None:
    with httpx.Client(base_url=API_URL, timeout=180) as client:
        for index, (locale, message) in enumerate(SCENARIOS, start=1):
            response = client.post(
                "/api/chat",
                json={"customer_name": f"Demo {index}", "locale": locale, "message": message},
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
                    detail = client.get(f"/api/escalations/{escalation_id}").json()
                    if detail["escalation"]["summary_status"] != "pending":
                        print(f"  summary={detail['escalation']['summary_status']}")
                        break
                    time.sleep(1)


if __name__ == "__main__":
    main()
