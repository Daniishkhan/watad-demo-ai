from fastapi.testclient import TestClient

from watad.api import app


def test_health_endpoint_reports_ready() -> None:
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "watad-api"}


def test_start_and_continue_rfq_workflow_through_api() -> None:
    client = TestClient(app)

    start_response = client.post(
        "/api/workflows/rfq/start",
        json={
            "message": (
                "Need 500 tons of 16mm rebar in Riyadh next week. Cheapest supplier, "
                "60-day payment preferred."
            ),
            "user_id": "user_123",
            "company_id": "company_456",
        },
    )

    assert start_response.status_code == 201
    started = start_response.json()
    assert started["workflow_id"].startswith("wf_")
    assert started["status"] == "needs_clarification"
    assert started["rfq"]["material_name"] == "rebar"
    assert started["rfq"]["delivery_deadline"] is not None
    assert "delivery_site" in started["missing_fields"]
    assert started["questions"]

    workflow_id = started["workflow_id"]
    continue_response = client.post(
        f"/api/workflows/rfq/{workflow_id}/message",
        json={
            "message": (
                "Project Al Yasmin Villas, north Riyadh. Saudi standard is fine. "
                "Split delivery is okay if cheaper."
            )
        },
    )

    assert continue_response.status_code == 200
    continued = continue_response.json()
    assert continued["status"] == "ready_for_supplier_search"
    assert continued["rfq"]["project_name"] == "Al Yasmin Villas"
    assert continued["rfq"]["delivery_site"] == "North Riyadh"
    assert continued["missing_fields"] == []
    assert continued["questions"] == []

    get_response = client.get(f"/api/workflows/rfq/{workflow_id}")

    assert get_response.status_code == 200
    assert get_response.json()["status"] == "ready_for_supplier_search"


def test_rfq_workflow_api_returns_404_for_unknown_workflow() -> None:
    client = TestClient(app)

    response = client.get("/api/workflows/rfq/wf_missing")

    assert response.status_code == 404
    assert response.json() == {"detail": "workflow not found"}
