"""
Part 6/8/9 (4.7, 4.8, 4.9): Decision engine.

Combines the model, score, risk band, affordability, and policy layers
into one APPROVE / REJECT / REFER / COUNTER_OFFER outcome with reason
codes. This is the only module that knows about decision precedence --
every layer below it (model_loader, scoring, risk, affordability, policy)
is precedence-agnostic and reusable on its own.

Decision precedence (documented per 4.8 -- the team's own chosen order,
as the brief permits, since it differs slightly from the brief's six-step
sketch by merging affordability-driven and policy-driven caps into a
single "compute the best supportable amount" step before falling through
to manual review / approval):

  1. Hard rejection rules       -- risk band too high, unsupported tenure
  2. Hard affordability reject  -- disposable income after the loan < 0
  3. Best supportable amount    -- take the tightest of the affordability
                                    cap, product cap, and risk-band cap;
                                    if the requested amount exceeds it,
                                    this becomes a COUNTER_OFFER (or a
                                    REJECT if no viable amount remains)
  4. Manual-review condition    -- score inside the manual-review band
  5. Approval condition         -- score clears the minimum approval bar
  6. Fallback                   -- anything left over is referred for
                                    manual review rather than silently
                                    approved or rejected
"""
from __future__ import annotations

from src.affordability import assess_affordability
from src.features import compute_lending_features
from src.model_features import MissingModelFieldError
from src.model_loader import MODEL_VERSION, predict_pd
from src.policy import (
    load_policy,
    rule_manual_review,
    rule_meets_approval_bar,
    rule_negative_disposable_income,
    rule_risk_too_high,
    rule_unsupported_tenure,
)
from src.risk import risk_band_result


class ApplicationValidationError(ValueError):
    pass


REQUIRED_APPLICATION_FIELDS = [
    "customerId", "monthlyIncome", "existingMonthlyDebt",
    "requestedAmount", "requestedTenure",
]


def _validate(application: dict) -> None:
    missing = [f for f in REQUIRED_APPLICATION_FIELDS if application.get(f) is None]
    if missing:
        raise ApplicationValidationError(f"Missing required field(s): {', '.join(missing)}")
    if application["requestedAmount"] <= 0:
        raise ApplicationValidationError("requestedAmount must be positive")
    if application["requestedTenure"] <= 0:
        raise ApplicationValidationError("requestedTenure must be a positive integer (months)")
    if application["monthlyIncome"] <= 0:
        raise ApplicationValidationError("monthlyIncome must be positive")
    if application["existingMonthlyDebt"] < 0:
        raise ApplicationValidationError("existingMonthlyDebt cannot be negative")


def _build_model_input(application: dict) -> dict:
    """
    Bridges the lending-layer field name (`monthlyIncome`, camelCase, used
    by the loan-application API and the Part 2 feature catalogue) to the
    model layer's frozen field name (`monthly_income`, snake_case, fixed
    by the Assignment-1 training schema -- see model_features.py). Without
    this, the model would always see monthly_income as missing and impute
    the training-set median, regardless of what the applicant reported.
    """
    model_input = dict(application)
    if model_input.get("monthly_income") is None and application.get("monthlyIncome") is not None:
        model_input["monthly_income"] = application["monthlyIncome"]
    return model_input


def _model_risk_reason_codes(application: dict, risk_band: str) -> list[str]:
    """Attach model-driven explainability codes when they materially apply."""
    codes = []
    if risk_band in ("MEDIUM", "HIGH", "VERY_HIGH"):
        total_delinquency = (application.get("late_30_59") or 0) + \
                             (application.get("late_60_89") or 0) + \
                             (application.get("late_90_plus") or 0)
        if total_delinquency > 0:
            codes.append("HIGH_DELINQUENCY_HISTORY")
        utilization = application.get("revolving_utilization")
        if utilization is not None and utilization >= 0.7:
            codes.append("HIGH_CREDIT_UTILIZATION")
    return codes


def evaluate_application(application: dict, policy: dict | None = None) -> dict:
    _validate(application)
    policy = policy or load_policy()

    try:
        pd = predict_pd(_build_model_input(application))
    except MissingModelFieldError as e:
        raise ApplicationValidationError(str(e))

    risk = risk_band_result(pd)
    lending_features = compute_lending_features(application)
    affordability = assess_affordability(
        monthly_income=application["monthlyIncome"],
        existing_monthly_debt=application["existingMonthlyDebt"],
        requested_amount=application["requestedAmount"],
        requested_tenure=application["requestedTenure"],
        annual_rate=policy["pricing"]["annualInterestRate"],
        max_allowed_dti=policy["affordability"]["maxAllowedDTI"],
        defined_expenses=policy["affordability"]["definedExpenses"],
    )

    requested_amount = application["requestedAmount"]
    requested_tenure = application["requestedTenure"]
    reason_codes: list[str] = []
    decision = None
    approved_amount = None
    triggered_rules: list[str] = []

    # 1. Hard rejection rules
    if rule_risk_too_high(risk["riskBand"]):
        decision = "REJECT"
        reason_codes = ["RISK_TOO_HIGH"] + _model_risk_reason_codes(application, risk["riskBand"])
        triggered_rules = ["POL-001"]
    elif rule_unsupported_tenure(requested_tenure, policy):
        decision = "REJECT"
        reason_codes = ["UNSUPPORTED_TENURE"]
        triggered_rules = ["POL-002"]

    # 2. Hard affordability reject
    elif rule_negative_disposable_income(affordability["disposableIncomeAfter"]):
        decision = "REJECT"
        reason_codes = ["AFFORDABILITY_LIMIT_EXCEEDED"]
        triggered_rules = ["POL-003"]

    else:
        # 3. Best supportable amount = tightest of affordability / product / risk-band caps
        affordability_cap = affordability["maximumAffordableAmount"]
        product_cap = policy["productLimits"]["maxLoanAmount"]
        band_cap = policy["riskBandCaps"].get(risk["riskBand"])

        binding = []
        if requested_amount > affordability_cap:
            binding.append(("PROJECTED_DTI_TOO_HIGH", "REQUESTED_AMOUNT_ABOVE_AFFORDABILITY_LIMIT", "POL-004", affordability_cap))
        if requested_amount > product_cap:
            binding.append(("PRODUCT_LIMIT_EXCEEDED", "REQUESTED_AMOUNT_ABOVE_PRODUCT_OR_RISK_LIMIT", "POL-005", product_cap))
        if band_cap is not None and requested_amount > band_cap:
            binding.append(("RISK_BAND_LIMIT_EXCEEDED", "REQUESTED_AMOUNT_ABOVE_PRODUCT_OR_RISK_LIMIT", "POL-006", band_cap))

        if binding:
            effective_max = min(b[3] for b in binding)
            driver_codes = sorted({b[0] for b in binding})
            process_codes = sorted({b[1] for b in binding})
            triggered_rules = [b[2] for b in binding]

            if effective_max < policy["productLimits"]["minLoanAmount"]:
                decision = "REJECT"
                reason_codes = driver_codes + ["REQUESTED_AMOUNT_BELOW_MINIMUM_VIABLE"]
            else:
                decision = "COUNTER_OFFER"
                # Round DOWN to the nearest 100 for a clean offer -- never round up past the cap
                approved_amount = (int(effective_max) // 100) * 100
                reason_codes = driver_codes + process_codes

        # 4/5/6. No binding cap -- score decides REFER vs APPROVE
        elif rule_manual_review(risk["creditScore"], policy):
            decision = "REFER"
            reason_codes = ["MANUAL_REVIEW_REQUIRED"]
            triggered_rules = ["POL-007"]
        elif rule_meets_approval_bar(risk["creditScore"], policy):
            decision = "APPROVE"
            approved_amount = requested_amount
            reason_codes = ["APPROVED"]
            triggered_rules = ["POL-008"]
        else:
            decision = "REFER"
            reason_codes = ["MANUAL_REVIEW_REQUIRED"]
            triggered_rules = ["POL-007-fallback"]

    return {
        "customerId": application["customerId"],
        "probabilityOfDefault": pd,
        "creditScore": risk["creditScore"],
        "riskBand": risk["riskBand"],
        "currentDebtToIncomeRatio": affordability["currentDebtToIncomeRatio"],
        "projectedDebtToIncomeRatio": affordability["projectedDebtToIncomeRatio"],
        "disposableIncomeAfter": affordability["disposableIncomeAfter"],
        "maximumAffordableAmount": affordability["maximumAffordableAmount"],
        "decision": decision,
        "approvedAmount": approved_amount,
        "tenure": requested_tenure,
        "reasonCodes": reason_codes,
        "triggeredRules": triggered_rules,
        "modelVersion": MODEL_VERSION,
        "policyVersion": policy["policyVersion"],
        "lendingFeatures": lending_features,
    }
