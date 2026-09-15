"""
Part 5 (4.5, 4.6): Affordability assessment and loan amount/tenure
assessment.

This module is a pure calculator: every threshold it needs (max allowed
DTI, pricing assumption, defined-expense allowance) is passed in as a
parameter rather than hardcoded, so it is clear which numbers come from
CUSTOMER CAPACITY (income, existing debt -- facts about the applicant)
and which come from BANK POLICY (max DTI, interest rate, expense
allowance -- configurable business decisions, owned by policy.py /
config/lending_policy.yaml). The defaults below exist only so this module
is independently testable; policy.py is expected to always pass its own
configured values explicitly.

Interest/installment assumption: a standard amortizing (equal monthly
installment) loan is assumed -- the same formula used for mortgages and
personal instalment loans:

    installment = P * r * (1 + r)^n / ((1 + r)^n - 1)

where P = principal, r = monthly interest rate (annual rate / 12),
n = tenure in months. Fees are NOT modelled (documented simplification,
see reports/05_affordability_methodology.md).
"""
from __future__ import annotations

DEFAULT_ANNUAL_INTEREST_RATE = 0.18  # 18% p.a. -- documented pricing assumption
DEFAULT_MAX_ALLOWED_DTI = 0.40       # 40% -- documented policy assumption
DEFAULT_DEFINED_EXPENSES = 0.0       # no separate living-cost deduction by default


def monthly_installment(principal: float, annual_rate: float, tenure_months: int) -> float:
    if principal <= 0 or tenure_months <= 0:
        return 0.0
    r = annual_rate / 12
    if r == 0:
        return principal / tenure_months
    factor = (1 + r) ** tenure_months
    return principal * r * factor / (factor - 1)


def max_affordable_principal(max_installment: float, annual_rate: float, tenure_months: int) -> float:
    """Inverse of monthly_installment: largest principal whose installment <= max_installment."""
    if max_installment <= 0 or tenure_months <= 0:
        return 0.0
    r = annual_rate / 12
    if r == 0:
        return max_installment * tenure_months
    factor = (1 + r) ** tenure_months
    return max_installment * (factor - 1) / (r * factor)


def assess_affordability(
    monthly_income: float,
    existing_monthly_debt: float,
    requested_amount: float,
    requested_tenure: int,
    annual_rate: float = DEFAULT_ANNUAL_INTEREST_RATE,
    max_allowed_dti: float = DEFAULT_MAX_ALLOWED_DTI,
    defined_expenses: float = DEFAULT_DEFINED_EXPENSES,
) -> dict:
    current_dti = (existing_monthly_debt / monthly_income) if monthly_income else None

    proposed_installment = monthly_installment(requested_amount, annual_rate, requested_tenure)

    projected_dti = (
        (existing_monthly_debt + proposed_installment) / monthly_income
        if monthly_income else None
    )

    disposable_income_before = monthly_income - existing_monthly_debt - defined_expenses
    disposable_income_after = disposable_income_before - proposed_installment

    max_installment = max(
        0.0,
        max_allowed_dti * monthly_income - existing_monthly_debt,
    ) if monthly_income else 0.0
    max_affordable_amount = max_affordable_principal(max_installment, annual_rate, requested_tenure)

    is_affordable = (
        projected_dti is not None
        and projected_dti <= max_allowed_dti
        and disposable_income_after >= 0
    )

    return {
        "currentDebtToIncomeRatio": round(current_dti, 4) if current_dti is not None else None,
        "projectedDebtToIncomeRatio": round(projected_dti, 4) if projected_dti is not None else None,
        "proposedInstallment": round(proposed_installment, 2),
        "disposableIncomeBefore": round(disposable_income_before, 2),
        "disposableIncomeAfter": round(disposable_income_after, 2),
        "maximumAffordableInstallment": round(max_installment, 2),
        "maximumAffordableAmount": round(max_affordable_amount, 2),
        "isAffordable": is_affordable,
        "assumptions": {
            "annualInterestRate": annual_rate,
            "maxAllowedDTI": max_allowed_dti,
            "definedExpenses": defined_expenses,
            "installmentType": "equal-instalment amortizing loan, no fees modelled",
        },
    }
