"""
Part 6 (4.7): Configurable lending policy.

Loads config/lending_policy.yaml and exposes it as a plain dict, plus
small stateless predicate helpers that decision.py composes in a fixed
precedence order. All thresholds live in the YAML file, not in code --
changing a limit never requires touching this module or retraining the
model.
"""
from __future__ import annotations

import os

import yaml

CONFIG_PATH = os.environ.get(
    "LENDING_POLICY_PATH",
    os.path.join(os.path.dirname(__file__), "..", "config", "lending_policy.yaml"),
)


def load_policy(path: str = CONFIG_PATH) -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


# --- Rule predicates, one per POL-xxx rule in lending_policy.yaml -------

def rule_risk_too_high(risk_band: str) -> bool:            # POL-001
    return risk_band in ("HIGH", "VERY_HIGH")


def rule_unsupported_tenure(tenure: int, policy: dict) -> bool:  # POL-002
    return tenure not in policy["productLimits"]["allowedTenureMonths"]


def rule_negative_disposable_income(disposable_income_after: float) -> bool:  # POL-003
    return disposable_income_after < 0


def rule_projected_dti_too_high(projected_dti: float, policy: dict) -> bool:  # POL-004
    return projected_dti is not None and projected_dti > policy["affordability"]["maxAllowedDTI"]


def rule_product_limit_exceeded(requested_amount: float, policy: dict) -> bool:  # POL-005
    return requested_amount > policy["productLimits"]["maxLoanAmount"]


def rule_risk_band_limit_exceeded(requested_amount: float, risk_band: str, policy: dict) -> bool:  # POL-006
    cap = policy["riskBandCaps"].get(risk_band)
    return cap is not None and requested_amount > cap


def rule_manual_review(score: int, policy: dict) -> bool:  # POL-007
    lo, hi = policy["manualReviewScoreRange"]
    return lo <= score <= hi


def rule_meets_approval_bar(score: int, policy: dict) -> bool:  # POL-008
    return score >= policy["minimumApprovalScore"]
