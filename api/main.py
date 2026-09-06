import joblib
import pandas as pd
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()
model = joblib.load("models/xgb_credit_risk.pkl")

LATE_MEDIAN = 0.0
INCOME_MEDIAN = 5400.0

FEATURE_ORDER = [
    "revolving_utilization", "age", "late_30_59", "debt_ratio", "monthly_income",
    "open_credit_lines", "late_90_plus", "real_estate_loans", "late_60_89", "dependents",
    "TOTAL_DELINQUENCY", "HAS_PREVIOUS_DELINQUENCY", "HIGH_DEBT_RATIO",
    "INCOME_PER_DEPENDENT", "HAS_MISSING_INCOME",
    "CREDIT_UTILIZATION_LEVEL_Low", "CREDIT_UTILIZATION_LEVEL_Medium",
]


class Applicant(BaseModel):
    revolving_utilization: float
    age: int
    late_30_59: float
    debt_ratio: float
    monthly_income: float | None = None
    open_credit_lines: int
    late_90_plus: float
    real_estate_loans: int
    late_60_89: float
    dependents: float | None = None


def engineer_features(raw: dict) -> pd.DataFrame:
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

    row["HAS_MISSING_INCOME"] = int(row["monthly_income"] is None)
    if row["monthly_income"] is None:
        row["monthly_income"] = INCOME_MEDIAN

    row["dependents"] = row["dependents"] or 0
    row["INCOME_PER_DEPENDENT"] = row["monthly_income"] / (row["dependents"] + 1)

    return pd.DataFrame([row])[FEATURE_ORDER]


def risk_label(probability: float) -> str:
    if probability < 0.10:
        return "Low"
    elif probability < 0.30:
        return "Medium"
    else:
        return "High"


@app.post("/api/v1/credit-risk/predict")
def predict(applicant: Applicant):
    features = engineer_features(applicant.model_dump())
    probability = model.predict_proba(features)[:, 1][0]
    return {
        "probabilityOfDefault": round(float(probability), 4),
        "riskPrediction": risk_label(probability),
        "model": "XGBoost",
        "modelVersion": "1.0",
    }