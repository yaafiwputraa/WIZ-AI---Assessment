def new_chat(client, message, locale="id", name="Budi"):
    return client.post(
        "/api/chat",
        json={"customer_name": name, "locale": locale, "message": message},
    )


def test_product_stock_scenario_records_tool_trace(client):
    response = new_chat(client, "Adidas Samba hitam size 42 masih ada?")
    assert response.status_code == 200
    payload = response.json()
    assert "3" in payload["assistant_message"]["content"]
    assert "1.499.000" in payload["assistant_message"]["content"]
    assert len(payload["tool_trace_identifiers"]) == 1

    detail = client.get(f"/api/conversations/{payload['conversation_id']}").json()
    metadata = detail["messages"][-1]["tool_metadata"]
    assert metadata["tool_traces"][0]["tool"] == "check_product_stock"
    assert metadata["tool_traces"][0]["result"]["matching_variants"][0]["stock"] == 3


def test_order_tracking_scenario(client):
    response = new_chat(client, "ORD-192 saya sudah sampai mana?")
    assert response.status_code == 200
    payload = response.json()
    content = payload["assistant_message"]["content"]
    assert all(item in content for item in ["ORD-192", "JNE", "JNE123456"])
    assert payload["tool_trace_identifiers"]


def test_english_product_scenario(client):
    response = new_chat(client, "Is Adidas Samba black size 42 in stock?", locale="en")
    assert response.status_code == 200
    assert "3 pairs" in response.json()["assistant_message"]["content"]


def test_escalation_summary_dashboard_and_idempotent_takeover(client):
    response = new_chat(
        client,
        "Barang saya datang rusak dan saya sudah komplain dua kali. Saya mau refund.",
    )
    assert response.status_code == 200
    payload = response.json()
    escalation_id = payload["escalation"]["id"]
    assert payload["conversation_status"] == "escalated"
    assert payload["escalation"]["priority"] == "high"

    tickets = client.get("/api/escalations").json()
    assert tickets[0]["id"] == escalation_id
    detail = client.get(f"/api/escalations/{escalation_id}").json()
    assert detail["escalation"]["summary_status"] == "ready"
    assert "refund" in detail["escalation"]["summary"].lower()

    first = client.post(f"/api/escalations/{escalation_id}/takeover")
    second = client.post(f"/api/escalations/{escalation_id}/takeover")
    assert first.status_code == second.status_code == 200
    assert second.json()["status"] == "taken_over"
    assert client.get(f"/api/escalations/{escalation_id}").json()["status"] == "human_active"


def test_resolve_and_reject_more_messages(client):
    response = new_chat(client, "What payment methods are available?", locale="en")
    conversation_id = response.json()["conversation_id"]
    resolved = client.post(f"/api/conversations/{conversation_id}/resolve")
    assert resolved.status_code == 200
    assert resolved.json()["status"] == "resolved"
    rejected = client.post(
        "/api/chat",
        json={"conversation_id": conversation_id, "locale": "en", "message": "Hello?"},
    )
    assert rejected.status_code == 409
    assert rejected.json()["error"]["code"] == "conversation_inactive"


def test_unknown_fact_is_not_invented(client):
    response = new_chat(client, "Do you sell Moon Boots XR-999?", locale="en")
    assert response.status_code == 200
    assert "not found" in response.json()["assistant_message"]["content"].lower()


def test_dashboard_stats(client):
    first = new_chat(client, "What payment methods are available?", locale="en").json()
    client.post(f"/api/conversations/{first['conversation_id']}/resolve")
    new_chat(client, "Barang saya datang rusak")
    stats = client.get("/api/dashboard/stats").json()
    assert stats == {"active_ai": 0, "ai_resolved": 1, "escalated": 1}


def test_new_conversation_requires_name(client):
    response = client.post("/api/chat", json={"locale": "id", "message": "Halo"})
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "customer_name_required"
