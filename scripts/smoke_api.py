from __future__ import annotations

import json
import os
import urllib.request
from typing import Any, cast

BASE_URL = os.environ.get("WATAD_API_BASE_URL", "http://127.0.0.1:8000")


def main() -> None:
    health = _get("/health")
    if health != {"status": "ok", "service": "watad-api"}:
        raise AssertionError(f"unexpected health response: {health}")

    started = _post(
        "/api/workflows/rfq/start",
        {
            "message": (
                "Need 500 tons of 16mm rebar in Riyadh next week. Cheapest supplier, "
                "60-day payment preferred."
            ),
            "user_id": "user_123",
            "company_id": "company_456",
        },
    )
    _assert_equal(started["status"], "needs_clarification")

    workflow_id = cast(str, started["workflow_id"])
    continued = _post(
        f"/api/workflows/rfq/{workflow_id}/message",
        {
            "message": (
                "Project Al Yasmin Villas, north Riyadh. Saudi standard is fine. "
                "Split delivery is okay if cheaper."
            )
        },
    )

    _assert_equal(continued["status"], "draft_artifacts_ready")
    _assert_equal(continued["recommendation"]["recommended_supplier_id"], "SUP-002")
    _assert_equal(continued["credit_check"]["status"], "finance_approval_required")
    _assert_equal(continued["approval_requests"][0]["action"], "finance_review")
    _assert_equal(
        [document["document_type"] for document in continued["generated_documents"]],
        [
            "rfq_draft",
            "supplier_outreach_draft",
            "award_recommendation_memo",
            "po_preview",
        ],
    )

    approved = _post(
        f"/api/workflows/rfq/{workflow_id}/approve",
        {"action": "finance_review", "decided_by": "finance_1"},
    )
    _assert_equal(approved["status"], "approval_recorded")
    _assert_equal(approved["approval_requests"][0]["status"], "approved")

    print(
        json.dumps(
            {
                "workflow_id": workflow_id,
                "final_status": continued["status"],
                "recommended_supplier_id": continued["recommendation"]["recommended_supplier_id"],
                "credit_status": continued["credit_check"]["status"],
                "approval_action": continued["approval_requests"][0]["action"],
                "generated_documents": [
                    document["document_type"] for document in continued["generated_documents"]
                ],
                "approval_after_decision": approved["approval_requests"][0]["status"],
            },
            indent=2,
        )
    )


def _get(path: str) -> dict[str, Any]:
    with urllib.request.urlopen(f"{BASE_URL}{path}", timeout=5) as response:
        return cast(dict[str, Any], json.loads(response.read().decode()))


def _post(path: str, payload: dict[str, object]) -> dict[str, Any]:
    request = urllib.request.Request(
        f"{BASE_URL}{path}",
        data=json.dumps(payload).encode(),
        headers={"content-type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=5) as response:
        return cast(dict[str, Any], json.loads(response.read().decode()))


def _assert_equal(actual: object, expected: object) -> None:
    if actual != expected:
        raise AssertionError(f"expected {expected!r}, got {actual!r}")


if __name__ == "__main__":
    main()
