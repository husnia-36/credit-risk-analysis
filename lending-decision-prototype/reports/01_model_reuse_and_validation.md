# 4.1 Credit-Risk Model Reuse and Validation

## Model identity

| Item | Value |
|---|---|
| Model name | LightGBM binary classifier (`LGBMClassifier`) |
| Model version | `credit-risk-v1` |
| Artifact | `models/lgbm_credit_risk.pkl` (joblib-persisted, carried over unchanged from Assignment 1) |
| Served alongside | An XGBoost model was also trained and compared in Assignment 1; LightGBM was selected for production use because it had the best ROC-AUC (0.867) and the best recall (0.77) of all five candidates tested |

## Training dataset

- **Source:** "Give Me Some Credit" (Kaggle) — a public consumer credit-risk dataset of ~150,000 historical borrowers.
- **Cleaning:** rows with `age == 0` were dropped (invalid data, 1 row); sentinel values `96`/`98` in the three late-payment columns were treated as missing and replaced with the column median (`0.0`); extreme values in `revolving_utilization` and `debt_ratio` were clipped at the 99th percentile before being used for bucketed/derived features, to keep those derived features robust to corrupted outliers (the raw columns themselves were left unclipped for the model).
- **Split:** stratified 80/20 train/test split (120,000 / 30,000 rows), preserving the 6.68% default rate in both sets (2,005 positive cases in the test set).

## Target variable and default definition

- **Target column:** `SeriousDlqin2yrs` (renamed conceptually to "default" in this project).
- **Definition:** 1 if the borrower experienced a serious delinquency (90+ days past due) within two years of the observation date, else 0. This is the dataset's own definition — it is **not** identical to any specific bank's regulatory or product definition of default, which is an explicitly documented limitation (see below and Section 13 of the assignment).

## Input features required by the model (fixed, 17 total)

The model expects exactly this feature vector, in this order — this schema is frozen; it is **not** extended by the new lending features built in Part 2, which live in a separate layer above the model (see `src/model_features.py` vs `src/features.py`):

```
revolving_utilization, age, late_30_59, debt_ratio, monthly_income,
open_credit_lines, late_90_plus, real_estate_loans, late_60_89, dependents,
TOTAL_DELINQUENCY, HAS_PREVIOUS_DELINQUENCY, HIGH_DEBT_RATIO,
INCOME_PER_DEPENDENT, HAS_MISSING_INCOME,
CREDIT_UTILIZATION_LEVEL_Low, CREDIT_UTILIZATION_LEVEL_Medium
```

10 of these are raw applicant fields; 7 are engineered in Assignment 1 (`TOTAL_DELINQUENCY`, `HAS_PREVIOUS_DELINQUENCY`, `HIGH_DEBT_RATIO`, `INCOME_PER_DEPENDENT`, `HAS_MISSING_INCOME`, and the one-hot `CREDIT_UTILIZATION_LEVEL_*` pair). `src/model_features.py` reproduces this exact transformation so the model always sees the schema it was trained on.

## Evaluation metrics and final test results

| Metric | Value (test set) |
|---|---|
| Accuracy | 0.81 |
| Precision (default class) | 0.22 |
| Recall (default class) | 0.77 |
| F1 (default class) | 0.35 |
| ROC-AUC | 0.867 |

Precision/recall/F1 are reported for the positive ("default") class specifically, since accuracy alone is misleading at a 6.68% base rate. Of 2,005 actual defaulters in the test set, LightGBM missed 457 — the fewest of the five models compared in Assignment 1.

## Class imbalance handling

`class_weight="balanced"` was used (LightGBM's built-in reweighting), as opposed to XGBoost's `scale_pos_weight` (≈13.96) approach used for the XGBoost candidate. No resampling (SMOTE, undersampling) was used.

## Calibration

**Not formally assessed.** Assignment 1 verified that `predict_proba` outputs match a manual SHAP-based reconstruction (`sigmoid(baseline + sum(shap_values))`) to high precision — confirming the probabilities are computed correctly — but no calibration curve, Brier score, or Platt/isotonic recalibration was performed against actual observed default rates. This means the raw PD values should be treated as a well-ordered risk ranking that is reasonably informative in relative terms, but the *absolute* probability values (e.g. "6% PD") should not yet be assumed to mean exactly "6 in 100 similar applicants defaulted." This is called out explicitly as a limitation below and is one reason the credit-score transformation in Part 3 is described as **experimental**.

## Known limitations / assumptions carried into this prototype

- The dataset's default definition (90+ days delinquent within 2 years) may not match a specific lender's contractual or regulatory default definition.
- No bureau, collateral, KYC, employment-verification, or multi-period transactional data is available — several lending features in Part 2 are necessarily approximated from single-snapshot application data.
- Probability outputs are not calibrated to a known real-world population; they are directionally reliable (higher PD = higher risk) but not validated as literal probabilities.
- The model was trained on a single historical U.S.-style consumer credit dataset; applying it to a different market (e.g. a different country's lending population) without local recalibration is a modeling assumption, not a validated claim.

## Minimum model output (contract)

```json
{
  "customerId": "CUST-001",
  "probabilityOfDefault": 0.064,
  "modelVersion": "credit-risk-v1"
}
```

This is produced by `src/model_features.py` + the loaded `models/lgbm_credit_risk.pkl`, and is the **only** thing the model layer returns. Credit score, risk band, affordability, and the final decision are all computed in later layers — the model itself never sees or returns a decision.
