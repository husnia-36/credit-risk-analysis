# Section 13: Assumptions and Limitations

Consolidated from every layer's own report (each linked below) — this is
the single place a reviewer can read every assumption made in this
prototype.

## Data assumptions

- **No real income/expense data.** The underlying dataset (Give Me Some
  Credit) has a single `monthly_income` field per applicant and nothing
  else — no employer, no multi-period history, no verified payslip. All
  "income" fields in this prototype are therefore this one self-reported
  number, not a verified figure. See [01](01_model_reuse_and_validation.md).
- **`INCOME_STABILITY` is a coarse proxy** (verified/unverified), not a
  real volatility measure, for the same reason. See [02](02_feature_catalogue.md).
- **No bureau, collateral, KYC, employment, or transactional data** of any
  kind is available or used — every affordability and policy calculation
  works only from the fields the application itself supplies.
- **Default definition mismatch.** The model's target (90+ days
  delinquent within 2 years, from a public consumer-credit dataset) is
  not guaranteed to match any specific bank's contractual or regulatory
  default definition.

## Modelling assumptions

- **PD is not calibrated** to a real observed population — it is a
  reliable *relative* risk ranking, not a validated absolute probability.
  See [01](01_model_reuse_and_validation.md).
- **The credit score is experimental**, derived by a standard log-odds
  transform anchored to this project's own population statistics, not to
  any bureau's scored population. See [03](03_credit_score_methodology.md).
- **Risk-band thresholds are evidence-based but prototype-grade** —
  grounded in this project's own EDA cohort default rates, not in a
  production risk-appetite exercise. See [04](04_risk_classification.md).

## Pricing / affordability assumptions

- **Simplified interest calculation**: a standard equal-instalment
  amortizing loan, 18% p.a. assumed rate, no fees modelled.
- **40% maximum DTI** and **no defined living-expense deduction** by
  default — both are configurable policy values, not customer facts.
  See [05](05_affordability_methodology.md).

## Policy assumptions

- All thresholds in `config/lending_policy.yaml` (product limits, risk-band
  caps, manual-review score range, minimum approval score) are the
  team's own reasoned defaults for this prototype, not a real bank's
  approved policy. They are deliberately kept in one configuration file
  so a real policy team could replace them without touching code.

## Explicit exclusion

- **This prototype must not be used for real customer lending decisions.**
  It exists to demonstrate the separation between predictive risk,
  scoring, affordability, policy, and final decisioning — not to make
  real credit decisions.
