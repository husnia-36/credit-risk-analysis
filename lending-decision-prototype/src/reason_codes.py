"""
Part 7 (4.10): Reason-code catalogue.

Every code returned by decision.py must appear here. `type` distinguishes
model-driven risk reasons from affordability, policy, and process reasons,
per the assignment's explainability requirement.
"""
from __future__ import annotations

REASON_CODES = {
    "RISK_TOO_HIGH":                              {"type": "model",        "meaning": "Overall risk band (HIGH or VERY_HIGH) is outside the bank's risk appetite"},
    "HIGH_DELINQUENCY_HISTORY":                   {"type": "model",        "meaning": "Past delinquency history contributes materially to the predicted risk"},
    "HIGH_CREDIT_UTILIZATION":                    {"type": "model",        "meaning": "High revolving credit utilization contributes materially to the predicted risk"},
    "PROJECTED_DTI_TOO_HIGH":                     {"type": "affordability", "meaning": "The new installment would push projected DTI above the maximum allowed"},
    "AFFORDABILITY_LIMIT_EXCEEDED":               {"type": "affordability", "meaning": "Disposable income after the new installment would be negative"},
    "PRODUCT_LIMIT_EXCEEDED":                     {"type": "policy",        "meaning": "Requested amount exceeds the product's configured maximum"},
    "RISK_BAND_LIMIT_EXCEEDED":                   {"type": "policy",        "meaning": "Requested amount exceeds the configured cap for this applicant's risk band"},
    "UNSUPPORTED_TENURE":                         {"type": "policy",        "meaning": "Requested tenure is not offered for this product"},
    "MANUAL_REVIEW_REQUIRED":                     {"type": "process",       "meaning": "Score falls in the manual-review range; a human must decide"},
    "REQUESTED_AMOUNT_ABOVE_AFFORDABILITY_LIMIT": {"type": "process",       "meaning": "Counter-offer: proposed amount reduced to the affordability-based maximum"},
    "REQUESTED_AMOUNT_ABOVE_PRODUCT_OR_RISK_LIMIT": {"type": "process",     "meaning": "Counter-offer: proposed amount reduced to the product or risk-band cap"},
    "REQUESTED_AMOUNT_BELOW_MINIMUM_VIABLE":      {"type": "process",       "meaning": "Even the maximum supportable amount falls below the product minimum; no viable counter-offer"},
    "APPROVED":                                   {"type": "process",       "meaning": "All checks passed; loan approved as requested"},
}


def describe(code: str) -> dict:
    return REASON_CODES.get(code, {"type": "unknown", "meaning": "Undocumented reason code"})
