# 4.2 Feature Design and Feature Catalogue

These ten features sit above the frozen risk-model schema (Part 1) and feed
the scoring, affordability, and policy layers. They are computed once per
application in `src/features.py`.

| Feature | Data type | Business definition | Source field(s) | Calculation | Missing-value treatment | Expected direction of risk | Used by |
|---|---|---|---|---|---|---|---|
| `AVG_MONTHLY_INCOME` | float | Applicant's monthly income capacity | `monthlyIncome` | Passthrough (single-snapshot proxy — see limitation below) | Imputed with the training-set median (5,400) and `INCOME_STABILITY` set to `UNVERIFIED` | Higher → lower risk | Affordability, policy |
| `DEBT_TO_INCOME_RATIO` | float | Current debt burden before the new loan | `existingMonthlyDebt`, `monthlyIncome` | `existingMonthlyDebt / monthlyIncome` | `existingMonthlyDebt` defaults to 0 if absent | Higher → higher risk | Affordability, policy |
| `TOTAL_DELINQUENCY` | int | Combined count of delinquency events across all severities | `late_30_59`, `late_60_89`, `late_90_plus` | Sum of the three counts (sentinel values already cleaned at the model layer) | Each defaults to 0 if absent | Higher → higher risk | Model (already, Part 1), policy, reason codes |
| `INCOME_STABILITY` | categorical (`VERIFIED`/`UNVERIFIED`) | Whether income was actually supplied by the applicant vs. imputed | `monthlyIncome` presence | `VERIFIED` if `monthlyIncome` provided, else `UNVERIFIED` | N/A (this *is* the missing-value flag) | `UNVERIFIED` → higher risk | Policy, explainability |
| `CREDIT_UTILIZATION` | float | Pressure on available revolving credit | `revolving_utilization` | Passthrough (already used banded in the model layer) | Left `None`/unknown if absent — not defaulted, since it materially affects risk | Higher → higher risk | Model (already, Part 1), policy |
| `ACTIVE_LOAN_COUNT` | int | Current lines of exposure | `open_credit_lines`, `real_estate_loans` | Sum of the two counts | Each defaults to 0 if absent | Higher → moderately higher risk / exposure | Policy, affordability context |
| `DEPENDENT_RATIO` | float | Household burden relative to income | `dependents`, `monthlyIncome` | `dependents / (monthlyIncome / 1000)` | `dependents` defaults to 0 if absent | Higher → higher risk (less disposable capacity per dependent) | Affordability |
| `PAYMENT_HISTORY_FLAG` | binary (0/1) | Whether the applicant has ever been delinquent, at any severity | `TOTAL_DELINQUENCY` | `1 if TOTAL_DELINQUENCY > 0 else 0` | Inherits `TOTAL_DELINQUENCY`'s treatment | 1 → higher risk | Policy, reason codes |
| `EXISTING_MONTHLY_DEBT` | float | Current monthly repayment obligations | `existingMonthlyDebt` | Passthrough | Defaults to 0 if absent | Higher → higher risk | Affordability |
| `DISPOSABLE_INCOME` | float | Income left after existing obligations, before the new loan | `monthlyIncome`, `existingMonthlyDebt` | `monthlyIncome - existingMonthlyDebt` | Inherits both fields' treatment | Lower → higher risk | Affordability |

## Notes and limitations

- **`INCOME_STABILITY` is a coarse proxy.** A real "income consistency/volatility" measure needs multiple income observations over time; this public, single-snapshot dataset only ever has one income figure per applicant, so the feature is reduced to a verified/unverified flag rather than a true stability measure. This is documented as an assumption per Section 13 of the assignment.
- **`CREDIT_UTILIZATION` is deliberately not defaulted** when missing (unlike most other fields) because it is one of the two strongest risk drivers found in Assignment 1's EDA (~10x spread in default rate across utilization buckets) — silently imputing it would materially distort the affordability/policy layers, so a missing value is instead surfaced as a validation error at the API layer (Part 8) rather than guessed.
- Loan-specific derived quantities that depend on the *requested* loan (proposed installment, projected DTI, disposable income *after* the new loan) are deliberately kept out of this catalogue and live in the affordability module (Part 5) instead, since the assignment brief treats "feature design" (4.2) and "affordability assessment" (4.5) as separate stages with separate responsibilities.
