"""
Reproduces the EXACT feature engineering used to train the Assignment-1
LightGBM model. This schema is frozen -- do not add or remove columns here
without retraining the model. New lending-layer features (Part 2 of this
assignment) live in features.py, not here.
"""
from __future__ import annotations

import pandas as pd

LATE_MEDIAN = 0.0
INCOME_MEDIAN = 5400.0  # median monthly_income from the Assignment-1 training set

FEATURE_ORDER = [
    "revolving_utilization", "age", "late_30_59", "debt_ratio", "monthly_income",
    "open_credit_lines", "late_90_plus", "real_estate_loans", "late_60_89", "dependents",
    "TOTAL_DELINQUENCY", "HAS_PREVIOUS_DELINQUENCY", "HIGH_DEBT_RATIO",
    "INCOME_PER_DEPENDENT", "HAS_MISSING_INCOME",
    "CREDIT_UTILIZATION_LEVEL_Low", "CREDIT_UTILIZATION_LEVEL_Medium",
]


class MissingModelFieldError(ValueError):
    """Raised when a raw field the risk model requires is absent."""


REQUIRED_RAW_FIELDS = [
    "revolving_utilization", "age", "late_30_59", "debt_ratio",
    "open_credit_lines", "late_90_plus", "real_estate_loans", "late_60_89",
]


def engineer_model_features(raw: dict) -> pd.DataFrame:
    """
    Takes a dict of raw applicant fields (the same 10 fields the Assignment-1
    API accepted) and returns a single-row DataFrame in the exact column
    order the trained model expects.
    """
    missing = [f for f in REQUIRED_RAW_FIELDS if raw.get(f) is None]
    if missing:
        raise MissingModelFieldError(f"Missing required risk-model field(s): {', '.join(missing)}")

    row = dict(raw)

    for col in ["late_30_59", "late_60_89", "late_90_plus"]:
        if row[col] in (96, 98):
            row[col] = LATE_MEDIAN

    row["TOTAL_DELINQUENCY"] = row["late_30_59"] + row["late_60_89"] + row["late_90_plus"]
    row["HAS_PREVIOUS_DELINQUENCY"] = int(row["TOTAL_DELINQUENCY"] > 0)

    u = row["revolving_utilization"]
    level = "Low" if u < 0.3 else ("Medium" if u < 0.7 else "High")
    row["CREDIT_UTILIZATION_LEVEL_Low"] = int(level == "Low")
    row["CREDIT_UTILIZATION_LEVEL_Medium"] = int(level == "Medium")

    row["HIGH_DEBT_RATIO"] = int(row["debt_ratio"] > 0.468)

    row["HAS_MISSING_INCOME"] = int(row.get("monthly_income") is None)
    if row.get("monthly_income") is None:
        row["monthly_income"] = INCOME_MEDIAN

    row["dependents"] = row.get("dependents") or 0
    row["INCOME_PER_DEPENDENT"] = row["monthly_income"] / (row["dependents"] + 1)

    return pd.DataFrame([row])[FEATURE_ORDER]
