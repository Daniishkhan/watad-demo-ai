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
    assert continued["status"] == "finance_approval_required"
    assert continued["rfq"]["project_name"] == "Al Yasmin Villas"
    assert continued["rfq"]["delivery_site"] == "North Riyadh"
    assert continued["missing_fields"] == []
    assert continued["questions"] == []
    assert [candidate["supplier_id"] for candidate in continued["supplier_candidates"]] == [
        "SUP-002",
        "SUP-001",
        "SUP-003",
    ]
    assert continued["recommendation"]["recommended_supplier_id"] == "SUP-002"
    assert continued["credit_check"]["status"] == "finance_approval_required"
    assert continued["credit_check"]["finance_approval_required"] is True

    get_response = client.get(f"/api/workflows/rfq/{workflow_id}")

    assert get_response.status_code == 200
    assert get_response.json()["status"] == "finance_approval_required"


def test_credit_check_tool_returns_finance_approval_requirement() -> None:
    client = TestClient(app)

    response = client.post(
        "/tools/credit/check",
        json={
            "rfq": {"payment_preference": "60_days"},
            "recommendation": {
                "recommended_supplier_id": "SUP-002",
                "recommended_supplier_name": "Riyadh Metals",
                "optimization_goal": "lowest_price",
                "reason": "Best fit",
                "estimated_total_price_sar": 1_180_000,
            },
            "company_id": "company_456",
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "finance_approval_required"
    assert response.json()["required_actions"] == [
        "route_to_finance_reviewer",
        "collect_latest_bank_statement",
        "collect_signed_project_contract",
    ]


def test_offer_comparison_tool_returns_award_recommendation() -> None:
    client = TestClient(app)

    response = client.post(
        "/tools/offers/compare",
        json={
            "rfq": {
                "material_category": "steel",
                "material_name": "rebar",
                "specification": "16mm rebar",
                "quantity": 500,
                "unit": "tons",
                "delivery_city": "Riyadh",
                "delivery_site": "North Riyadh",
                "delivery_deadline": "2026-05-18",
                "project_name": "Al Yasmin Villas",
                "payment_preference": "60_days",
                "optimization_preference": "lowest_price",
                "certification_requirements": ["Saudi standard"],
                "split_delivery_acceptable": True,
            },
            "supplier_candidates": [
                {
                    "supplier_id": "SUP-002",
                    "supplier_name": "Riyadh Metals",
                    "fit_score": 0.94,
                    "unit_price_sar": 2360,
                    "available_quantity": 500,
                    "delivery_days": 8,
                    "payment_terms": ["30_days", "60_days"],
                    "reliability_score": 0.89,
                    "strengths": ["supports requested payment terms"],
                    "risks": ["delivery may miss requested deadline"],
                    "total_price_sar": 1_180_000,
                },
                {
                    "supplier_id": "SUP-001",
                    "supplier_name": "Al Noor Steel",
                    "fit_score": 0.91,
                    "unit_price_sar": 2410,
                    "available_quantity": 500,
                    "delivery_days": 6,
                    "payment_terms": ["30_days"],
                    "reliability_score": 0.94,
                    "strengths": ["fast delivery window"],
                    "risks": ["payment terms do not match preference"],
                    "total_price_sar": 1_205_000,
                },
            ],
        },
    )

    assert response.status_code == 200
    assert response.json()["recommended_supplier_id"] == "SUP-002"


def test_supplier_search_tool_returns_catalog_backed_candidates() -> None:
    client = TestClient(app)

    response = client.post(
        "/tools/suppliers/search",
        json={
            "rfq": {
                "material_category": "steel",
                "material_name": "rebar",
                "specification": "16mm rebar",
                "quantity": 500,
                "unit": "tons",
                "delivery_city": "Riyadh",
                "delivery_site": "North Riyadh",
                "delivery_deadline": "2026-05-18",
                "project_name": "Al Yasmin Villas",
                "payment_preference": "60_days",
                "optimization_preference": "lowest_price",
                "certification_requirements": ["Saudi standard"],
                "split_delivery_acceptable": True,
            }
        },
    )

    assert response.status_code == 200
    candidates = response.json()
    assert [candidate["supplier_id"] for candidate in candidates] == [
        "SUP-002",
        "SUP-001",
        "SUP-003",
    ]
    assert candidates[0]["supplier_name"] == "Riyadh Metals"


def test_rfq_workflow_api_returns_404_for_unknown_workflow() -> None:
    client = TestClient(app)

    response = client.get("/api/workflows/rfq/wf_missing")

    assert response.status_code == 404
    assert response.json() == {"detail": "workflow not found"}
