from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)

VALID_APPLICATION = {
    "customerId": "CUST-API-1",
    "monthlyIncome": 30000,
    "existingMonthlyDebt": 5000,
    "requestedAmount": 20000,
    "requestedTenure": 12,
    "revolving_utilization": 0.2,
    "age": 35,
    "late_30_59": 0,
    "debt_ratio": 0.2,
    "open_credit_lines": 4,
    "late_90_plus": 0,
    "real_estate_loans": 1,
    "late_60_89": 0,
    "dependents": 1,
}


def test_decision_endpoint_happy_path():
    r = client.post("/api/v1/lending/decision", json=VALID_APPLICATION)
    assert r.status_code == 200
    body = r.json()
    for key in ["applicationId", "probabilityOfDefault", "creditScore", "riskBand",
                "decision", "reasonCodes", "modelVersion", "policyVersion"]:
        assert key in body
    assert body["decision"] in ("APPROVE", "REJECT", "REFER", "COUNTER_OFFER")


def test_decision_can_be_retrieved_by_id():
    created = client.post("/api/v1/lending/decision", json=VALID_APPLICATION).json()
    r = client.get(f"/api/v1/lending/decisions/{created['applicationId']}")
    assert r.status_code == 200
    assert r.json()["applicationId"] == created["applicationId"]


def test_unknown_application_id_returns_404():
    r = client.get("/api/v1/lending/decisions/not-a-real-id")
    assert r.status_code == 404


def test_missing_field_returns_422():
    incomplete = {k: v for k, v in VALID_APPLICATION.items() if k != "monthlyIncome"}
    r = client.post("/api/v1/lending/decision", json=incomplete)
    assert r.status_code == 422


def test_negative_amount_returns_422():
    r = client.post("/api/v1/lending/decision", json={**VALID_APPLICATION, "requestedAmount": -500})
    assert r.status_code == 422


def test_malformed_json_returns_422():
    r = client.post("/api/v1/lending/decision", data="{not valid json")
    assert r.status_code == 422


def test_unsupported_tenure_is_a_policy_rejection_not_an_error():
    # An unsupported tenure is a valid request that the lending POLICY
    # rejects (200 + decision=REJECT), not a malformed request (422) --
    # it only fails validation if the field is missing/non-positive.
    r = client.post("/api/v1/lending/decision", json={**VALID_APPLICATION, "requestedTenure": 13})
    assert r.status_code == 200
    body = r.json()
    assert body["decision"] == "REJECT"
    assert "UNSUPPORTED_TENURE" in body["reasonCodes"]


def test_zero_tenure_fails_pydantic_validation():
    r = client.post("/api/v1/lending/decision", json={**VALID_APPLICATION, "requestedTenure": 0})
    assert r.status_code == 422


def test_affordability_endpoint():
    r = client.post("/api/v1/lending/affordability", json={
        "monthlyIncome": 30000, "existingMonthlyDebt": 5000,
        "requestedAmount": 80000, "requestedTenure": 12,
    })
    assert r.status_code == 200
    assert "maximumAffordableAmount" in r.json()


def test_models_current_endpoint():
    r = client.get("/api/v1/models/current")
    assert r.status_code == 200
    assert "modelVersion" in r.json()
    assert "policyVersion" in r.json()
