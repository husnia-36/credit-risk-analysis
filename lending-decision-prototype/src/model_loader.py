"""
Loads the Assignment-1 credit-risk model artifact and exposes a single
predict_pd() function. This is the ONLY module that touches the trained
model object -- everything downstream (scoring, risk, affordability,
policy, decision) only ever sees a probability-of-default float.

If the real trained artifact is not present at MODEL_PATH, this falls
back to a clearly-labelled STUB model so the rest of the prototype
(scoring/risk/affordability/policy/decision/API) can still be built,
wired, and tested end-to-end. Swap in the real .pkl and nothing else in
the codebase needs to change.

Default path assumes this project lives as a SUBFOLDER inside the
existing Assignment-1 repo, reusing its models/ folder directly rather
than duplicating the artifact:

    credit-risk/
    +-- models/lgbm_credit_risk.pkl        <- Assignment-1 artifact (reused, not copied)
    +-- lending-decision-prototype/
        +-- src/model_loader.py            <- this file (..\..\models\... from here)

Override with the CREDIT_RISK_MODEL_PATH environment variable if your
layout differs.
"""
from __future__ import annotations

import os
import warnings

import joblib

from src.model_features import engineer_model_features, FEATURE_ORDER

MODEL_PATH = os.environ.get("CREDIT_RISK_MODEL_PATH", os.path.join(
    os.path.dirname(__file__), "..", "..", "models", "lgbm_credit_risk.pkl"
))
MODEL_VERSION = "credit-risk-v1"


class _StubModel:
    """
    Deterministic, monotonic stand-in used ONLY when the real model
    artifact isn't available. NOT trained on data -- it exists purely so
    the lending pipeline can be exercised end-to-end before the real
    Assignment-1 .pkl is dropped into models/. It approximates PD from a
    weighted combination of the raw risk signals in the same direction
    the real model's SHAP analysis found (utilization, delinquency, and
    debt ratio dominate), sigmoid-squashed into (0, 1).
    """

    def predict_proba(self, X):
        import numpy as np

        w = {
            "revolving_utilization": 1.1,
            "late_30_59": 0.35,
            "late_60_89": 0.55,
            "late_90_plus": 0.75,
            "TOTAL_DELINQUENCY": 0.45,
            "HIGH_DEBT_RATIO": 0.6,
            "HAS_MISSING_INCOME": 0.3,
        }
        z = -4.0
        for col, weight in w.items():
            if col in X.columns:
                z += weight * min(float(X.iloc[0][col]), 5.0)
        p1 = 1.0 / (1.0 + pow(2.718281828, -z))
        return np.array([[1 - p1, p1]])


def _load_model():
    if os.path.exists(MODEL_PATH):
        return joblib.load(MODEL_PATH), False
    warnings.warn(
        f"Real model artifact not found at {MODEL_PATH!r} -- using a temporary "
        "stub model so the lending pipeline can still be built and tested. "
        "Replace models/lgbm_credit_risk.pkl with the real Assignment-1 artifact "
        "before treating any output as production-representative.",
        stacklevel=2,
    )
    return _StubModel(), True


_MODEL, USING_STUB = _load_model()


def predict_pd(raw_applicant: dict) -> float:
    """Returns Probability of Default as a float in [0, 1]."""
    features = engineer_model_features(raw_applicant)
    proba = _MODEL.predict_proba(features)[:, 1][0]
    return round(float(proba), 4)


def model_status() -> dict:
    return {
        "modelVersion": MODEL_VERSION,
        "modelPath": os.path.abspath(MODEL_PATH),
        "usingStubModel": USING_STUB,
        "featureCount": len(FEATURE_ORDER),
    }
