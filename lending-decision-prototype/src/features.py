"""
Part 2 (4.2): Lending-related feature catalogue.

These are DISTINCT from the frozen model-input schema in model_features.py.
They describe the customer/loan at the lending-decision layer and feed the
scoring/risk narrative, the affordability module, and the policy layer --
none of them are re-fed into the trained model.

All features are computed from a single application snapshot (no
multi-period transaction or bureau history is available in the public
dataset this prototype is built on) -- see the "missing-value treatment"
notes and reports/02_feature_catalogue.md for the documented limitation
this implies for INCOME_STABILITY in particular.
"""
from __future__ import annotations

DEFAULT_MONTHLY_INCOME = 5400.0  # same fallback used by the risk model layer


def compute_lending_features(application: dict) -> dict:
    """
    application is expected to carry both the loan-application fields
    (monthlyIncome, existingMonthlyDebt, dependents) and the raw risk
    fields already used by the model layer (late_30_59, late_60_89,
    late_90_plus, revolving_utilization, open_credit_lines,
    real_estate_loans).
    """
    monthly_income = application.get("monthlyIncome")
    income_missing = monthly_income is None
    if income_missing:
        monthly_income = DEFAULT_MONTHLY_INCOME

    existing_monthly_debt = application.get("existingMonthlyDebt") or 0.0
    dependents = application.get("dependents") or 0

    late_30_59 = application.get("late_30_59") or 0
    late_60_89 = application.get("late_60_89") or 0
    late_90_plus = application.get("late_90_plus") or 0
    total_delinquency = late_30_59 + late_60_89 + late_90_plus

    revolving_utilization = application.get("revolving_utilization")
    open_credit_lines = application.get("open_credit_lines") or 0
    real_estate_loans = application.get("real_estate_loans") or 0

    debt_to_income_ratio = (existing_monthly_debt / monthly_income) if monthly_income else None
    disposable_income = monthly_income - existing_monthly_debt

    features = {
        "AVG_MONTHLY_INCOME": round(monthly_income, 2),
        "DEBT_TO_INCOME_RATIO": round(debt_to_income_ratio, 4) if debt_to_income_ratio is not None else None,
        "TOTAL_DELINQUENCY": total_delinquency,
        "INCOME_STABILITY": "UNVERIFIED" if income_missing else "VERIFIED",
        "CREDIT_UTILIZATION": round(revolving_utilization, 4) if revolving_utilization is not None else None,
        "ACTIVE_LOAN_COUNT": open_credit_lines + real_estate_loans,
        "DEPENDENT_RATIO": round(dependents / (monthly_income / 1000), 4) if monthly_income else None,
        "PAYMENT_HISTORY_FLAG": int(total_delinquency > 0),
        "EXISTING_MONTHLY_DEBT": round(existing_monthly_debt, 2),
        "DISPOSABLE_INCOME": round(disposable_income, 2),
    }
    return features
