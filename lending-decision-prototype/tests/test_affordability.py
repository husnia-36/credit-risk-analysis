from src.affordability import assess_affordability, monthly_installment, max_affordable_principal


def test_installment_is_positive_and_inverse_holds():
    installment = monthly_installment(80000, 0.18, 12)
    assert installment > 0
    principal = max_affordable_principal(installment, 0.18, 12)
    assert round(principal) == 80000


def test_zero_principal_or_tenure_gives_zero_installment():
    assert monthly_installment(0, 0.18, 12) == 0.0
    assert monthly_installment(1000, 0.18, 0) == 0.0


def test_affordability_flags_unaffordable_request():
    result = assess_affordability(
        monthly_income=30000, existing_monthly_debt=5000,
        requested_amount=80000, requested_tenure=12,
    )
    assert result["isAffordable"] is False
    assert result["projectedDebtToIncomeRatio"] > result["currentDebtToIncomeRatio"]
    assert result["maximumAffordableAmount"] < 80000


def test_affordability_passes_small_request():
    result = assess_affordability(
        monthly_income=30000, existing_monthly_debt=2000,
        requested_amount=10000, requested_tenure=24,
    )
    assert result["isAffordable"] is True
    assert result["disposableIncomeAfter"] > 0


def test_zero_income_does_not_crash():
    result = assess_affordability(
        monthly_income=0, existing_monthly_debt=0,
        requested_amount=5000, requested_tenure=12,
    )
    assert result["currentDebtToIncomeRatio"] is None
    assert result["isAffordable"] is False
