def make_contact(client, name, follow_up, status="Pending"):
    response = client.post("/api/v1/contacts", json={
        "name": name,
        "purpose": "Follow up",
        "status": status,
        "next_follow_up_at": follow_up,
    })
    assert response.status_code == 201
    return response.json()


def test_due_overdue_upcoming_and_completed_exclusion(client):
    make_contact(client, "Due", "2026-10-14T09:00:00Z")
    make_contact(client, "Overdue", "2026-10-13T09:00:00Z")
    make_contact(client, "Upcoming", "2026-10-16T09:00:00Z")
    make_contact(client, "Completed", "2026-10-13T09:00:00Z", "Completed")

    params = {"day": "2026-10-14"}
    assert [item["name"] for item in client.get("/api/v1/follow-ups/due", params=params).json()] == ["Due"]
    assert [item["name"] for item in client.get("/api/v1/follow-ups/overdue", params=params).json()] == ["Overdue"]
    assert [item["name"] for item in client.get("/api/v1/follow-ups/upcoming", params={"day": "2026-10-14", "days": 7}).json()] == ["Upcoming"]

    summary = client.get("/api/v1/dashboard/summary").json()
    assert summary["completed_contacts"] == 1
    assert summary["unscheduled"] == 0


def test_unscheduled_and_dashboard_counts(client):
    make_contact(client, "Unscheduled", None)
    result = client.get("/api/v1/follow-ups/unscheduled")
    assert result.status_code == 200
    assert result.json()[0]["name"] == "Unscheduled"
    assert client.get("/api/v1/follow-ups/upcoming", params={"days": 0}).status_code == 422


def test_follow_up_day_boundaries(client):
    make_contact(client, "Start", "2026-10-14T00:00:00Z")
    make_contact(client, "End", "2026-10-14T23:59:59Z")
    make_contact(client, "Tomorrow", "2026-10-15T00:00:00Z")
    make_contact(client, "Before", "2026-10-13T23:59:59Z")

    params = {"day": "2026-10-14"}
    assert [item["name"] for item in client.get("/api/v1/follow-ups/due", params=params).json()] == ["Start", "End"]
    assert [item["name"] for item in client.get("/api/v1/follow-ups/overdue", params=params).json()] == ["Before"]
    assert [item["name"] for item in client.get("/api/v1/follow-ups/upcoming", params={"day": "2026-10-14", "days": 1}).json()] == ["Tomorrow"]
