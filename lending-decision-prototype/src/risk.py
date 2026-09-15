"""
Part 4 (4.4): Risk classification into five bands.

Thresholds are defined on PD (the model's native, continuous output) and
are grounded in the Assignment-1 EDA findings rather than picked
arbitrarily -- see reports/04_risk_classification.md for the evidence.
The corresponding score cutoffs are a pure display transform of the same
PD thresholds (via scoring.pd_to_score), so band membership computed from
PD or from score is always consistent by construction.
"""
from __future__ import annotations

from src.scoring import pd_to_score

# (upper-bound-exclusive PD, band name), evaluated in order
_BANDS = [
    (0.02, "VERY_LOW"),
    (0.0668, "LOW"),
    (0.12, "MEDIUM"),
    (0.20, "HIGH"),
    (float("inf"), "VERY_HIGH"),
]

TREATMENT = {
    "VERY_LOW": "Normal policy checks",
    "LOW": "Normal policy checks",
    "MEDIUM": "Additional rules or limits",
    "HIGH": "Reject or manual review",
    "VERY_HIGH": "Normally reject",
}


def classify_risk(probability_of_default: float) -> str:
    for upper_bound, band in _BANDS:
        if probability_of_default < upper_bound:
            return band
    return "VERY_HIGH"  # unreachable, last band is inf-bounded


def risk_band_result(probability_of_default: float) -> dict:
    band = classify_risk(probability_of_default)
    return {
        "riskBand": band,
        "creditScore": pd_to_score(probability_of_default),
        "treatment": TREATMENT[band],
    }
