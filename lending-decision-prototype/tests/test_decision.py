"""
Part 9 (Section 6): The six required test scenarios, plus boundary/unit
coverage of the decision engine.

Each scenario monkeypatches src.decision.predict_pd so the decision logic
is tested deterministically and independently of whichever model artifact
(real or stub) happens to be loaded -- this is what the model_loader
module boundary in Part 1 is *for*.
"""
import pytest

from src import decision as decision_module
from src.decision import ApplicationValidationError, evaluate_application
from src.policy import rule_projected_dti_too_high


def _base_application(**overrides):
    app = {
        "customerId": "CUST-TEST",
        "monthlyIncome": 30000,
        "existingMonthlyDebt": 2000,
        "requestedAmount": 10000,
        "requestedTenure": 12,
        "revolving_utilization": 0.1,
        "age": 35,
        "late_30_59": 0,
        "debt_ratio": 0.15,
        "open_credit_lines": 3,
        "late_90_plus": 0,
        "real_estate_loans": 0,
        "late_60_89": 0,
        "dependents": 0,
    }
    app.update(overrides)
    return app


def _with_pd(monkeypatch, pd_value):
    monkeypatch.setattr(decision_module, "predict_pd", lambda raw: pd_value)


# --- Scenario 1: Low-risk / affordable -> normal APPROVE path -----------

def test_scenario_1_low_risk_affordable_approves(monkeypatch):
    _with_pd(monkeypatch, 0.01)
    app = _base_application(monthlyIncome=30000, existingMonthlyDebt=2000,
                             requestedAmount=10000, requestedTenure=24)
    result = evaluate_application(app)
    assert result["riskBand"] == "VERY_LOW"
    assert result["decision"] == "APPROVE"
    assert result["approvedAmount"] == 10000
    assert result["reasonCodes"] == ["APPROVED"]


# --- Scenario 2: Low-risk / unaffordable amount -> COUNTER_OFFER --------

def test_scenario_2_low_risk_unaffordable_counter_offers(monkeypatch):
    _with_pd(monkeypatch, 0.015)
    app = _base_application(monthlyIncome=20000, existingMonthlyDebt=3000,
                             requestedAmount=90000, requestedTenure=12)
    result = evaluate_application(app)
    assert result["riskBand"] in ("VERY_LOW", "LOW")
    assert result["decision"] == "COUNTER_OFFER"
    assert result["approvedAmount"] < 90000
    assert "REQUESTED_AMOUNT_ABOVE_AFFORDABILITY_LIMIT" in result["reasonCodes"]


# --- Scenario 3: Medium-risk / affordable -> policy-dependent approval --

def test_scenario_3_medium_risk_affordable_approves_under_band_cap(monkeypatch):
    _with_pd(monkeypatch, 0.08)
    app = _base_application(monthlyIncome=25000, existingMonthlyDebt=2000,
                             requestedAmount=20000, requestedTenure=24)
    result = evaluate_application(app)
    assert result["riskBand"] == "MEDIUM"
    assert result["decision"] == "APPROVE"  # score 649 clears both the review band and approval bar


# --- Scenario 4: High-risk applicant -> REJECT --------------------------

def test_scenario_4_high_risk_rejects(monkeypatch):
    _with_pd(monkeypatch, 0.25)
    app = _base_application(late_90_plus=2, revolving_utilization=0.9)
    result = evaluate_application(app)
    assert result["riskBand"] == "VERY_HIGH"
    assert result["decision"] == "REJECT"
    assert "RISK_TOO_HIGH" in result["reasonCodes"]
    assert "HIGH_DELINQUENCY_HISTORY" in result["reasonCodes"]
    assert "HIGH_CREDIT_UTILIZATION" in result["reasonCodes"]


# --- Scenario 5: Requested amount above product maximum -----------------

def test_scenario_5_above_product_maximum_counter_offers(monkeypatch):
    _with_pd(monkeypatch, 0.03)
    app = _base_application(monthlyIncome=100000, existingMonthlyDebt=5000,
                             requestedAmount=150000, requestedTenure=12)
    result = evaluate_application(app)
    assert result["decision"] == "COUNTER_OFFER"
    assert "PRODUCT_LIMIT_EXCEEDED" in result["reasonCodes"]
    assert result["approvedAmount"] <= 100000


# --- Scenario 6: Boundary case(s) ----------------------------------------

def test_scenario_6a_boundary_unsupported_tenure_rejects(monkeypatch):
    _with_pd(monkeypatch, 0.01)  # low risk -- isolates the tenure boundary check
    app = _base_application(requestedTenure=13)  # 13 is not in allowedTenureMonths
    result = evaluate_application(app)
    assert result["decision"] == "REJECT"
    assert result["reasonCodes"] == ["UNSUPPORTED_TENURE"]


def test_scenario_6b_boundary_dti_exactly_at_limit_is_not_a_violation():
    # Exactly at the limit must NOT trigger the "too high" rule (strict >)
    assert rule_projected_dti_too_high(0.40, {"affordability": {"maxAllowedDTI": 0.40}}) is False
    assert rule_projected_dti_too_high(0.4001, {"affordability": {"maxAllowedDTI": 0.40}}) is True


# --- Validation / error handling ----------------------------------------

def test_missing_required_field_raises():
    app = _base_application()
    del app["monthlyIncome"]
    with pytest.raises(ApplicationValidationError):
        evaluate_application(app)


def test_negative_requested_amount_raises():
    app = _base_application(requestedAmount=-100)
    with pytest.raises(ApplicationValidationError):
        evaluate_application(app)


def test_negative_existing_debt_raises():
    app = _base_application(existingMonthlyDebt=-1)
    with pytest.raises(ApplicationValidationError):
        evaluate_application(app)
