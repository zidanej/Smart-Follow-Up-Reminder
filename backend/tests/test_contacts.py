def contact_payload(name="Rahul Sharma", **overrides):
    payload = {
        "name": name,
        "company": "ABC Technologies",
        "email": "rahul@example.com",
        "purpose": "Python backend opportunity",
        "status": "Pending",
        "last_contacted_at": "2026-10-14T09:00:00Z",
        "next_follow_up_at": "2026-10-17T09:00:00Z",
        "notes": "Sent resume",
    }
    payload.update(overrides)
    return payload


def test_health_and_contact_crud(client):
    assert client.get("/health").json() == {"status": "ok"}
    created = client.post("/api/v1/contacts", json=contact_payload())
    assert created.status_code == 201
    contact_id = created.json()["id"]
    assert client.get("/api/v1/contacts/%s" % contact_id).json()["name"] == "Rahul Sharma"

    updated = client.patch("/api/v1/contacts/%s" % contact_id, json={"status": "Replied", "company": "New Co"})
    assert updated.status_code == 200
    assert updated.json()["status"] == "Replied"
    assert updated.json()["purpose"] == "Python backend opportunity"

    assert client.delete("/api/v1/contacts/%s" % contact_id).status_code == 204
    assert client.get("/api/v1/contacts/%s" % contact_id).status_code == 404


def test_validation_and_missing_contact(client):
    assert client.post("/api/v1/contacts", json={"name": "", "purpose": "x"}).status_code == 422
    assert client.post("/api/v1/contacts", json=contact_payload(status="Unknown")).status_code == 422
    assert client.post("/api/v1/contacts", json=contact_payload(email="not-an-email")).status_code == 422
    assert client.get("/api/v1/contacts/999").status_code == 404


def test_search_status_pagination_and_persistence(client):
    for index in range(3):
        response = client.post("/api/v1/contacts", json=contact_payload("Person %s" % index, status="Replied" if index == 2 else "Pending"))
        assert response.status_code == 201
    result = client.get("/api/v1/contacts", params={"search": "Person 1", "page": 1, "page_size": 1})
    assert result.status_code == 200
    assert result.json()["total"] == 1
    filtered = client.get("/api/v1/contacts", params={"status": "Replied"})
    assert filtered.json()["total"] == 1


def test_interaction_history_updates_last_contacted(client):
    created = client.post("/api/v1/contacts", json=contact_payload())
    contact_id = created.json()["id"]
    interaction = client.post("/api/v1/contacts/%s/interactions" % contact_id, json={
        "interaction_type": "Email",
        "interaction_date": "2026-10-15T10:00:00Z",
        "description": "Sent a follow-up email",
        "outcome": "Waiting for reply",
    })
    assert interaction.status_code == 201
    assert client.get("/api/v1/contacts/%s/interactions" % contact_id).json()[0]["description"] == "Sent a follow-up email"
    assert client.get("/api/v1/contacts/%s" % contact_id).json()["last_contacted_at"].startswith("2026-10-15")
    older = client.post("/api/v1/contacts/%s/interactions" % contact_id, json={
        "interaction_type": "Note",
        "interaction_date": "2026-10-14T10:00:00Z",
        "description": "An older note",
    })
    assert older.status_code == 201
    detail = client.get("/api/v1/contacts/%s" % contact_id)
    assert detail.status_code == 200
    assert len(detail.json()["interactions"]) == 2
    assert detail.json()["last_contacted_at"].startswith("2026-10-15")
    assert client.post("/api/v1/contacts/%s/interactions" % contact_id, json={"interaction_type": "Chat", "interaction_date": "2026-10-15T10:00:00Z", "description": "bad"}).status_code == 422


def test_timestamps_are_normalized_to_utc(client):
    created = client.post("/api/v1/contacts", json=contact_payload(next_follow_up_at="2026-10-14T23:00:00-05:00"))
    assert created.status_code == 201
    assert created.json()["next_follow_up_at"] == "2026-10-15T04:00:00Z"


def test_repeated_idempotency_key_returns_one_contact(client):
    headers = {"Idempotency-Key": "submission-123"}
    first = client.post("/api/v1/contacts", json=contact_payload("Retry-safe"), headers=headers)
    second = client.post("/api/v1/contacts", json=contact_payload("Retry-safe"), headers=headers)
    assert first.status_code == 201
    assert second.status_code == 201
    assert second.json()["id"] == first.json()["id"]
    assert client.get("/api/v1/contacts", params={"search": "Retry-safe"}).json()["total"] == 1


def test_delete_removes_only_selected_contact_and_interactions(client):
    selected = client.post("/api/v1/contacts", json=contact_payload("Delete me")).json()
    retained = client.post("/api/v1/contacts", json=contact_payload("Keep me", email="keep@example.com")).json()
    interaction = client.post("/api/v1/contacts/%s/interactions" % selected["id"], json={
        "interaction_type": "Note",
        "interaction_date": "2026-10-15T10:00:00Z",
        "description": "Should be deleted with contact",
    })
    assert interaction.status_code == 201
    assert client.delete("/api/v1/contacts/%s" % selected["id"]).status_code == 204
    assert client.get("/api/v1/contacts/%s" % selected["id"]).status_code == 404
    assert client.get("/api/v1/contacts/%s" % retained["id"]).status_code == 200
    assert client.get("/api/v1/contacts/%s/interactions" % selected["id"]).status_code == 404
