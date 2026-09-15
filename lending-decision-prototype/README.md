# Lending Decision Prototype

Assignment 2: Credit Scoring and Loan Eligibility Decision Prototype.
Extends the Assignment 1 credit-risk model comparison project into a
full decision flow: customer/loan input → features → the reused
Assignment-1 LightGBM model → Probability of Default → credit score →
risk band → affordability assessment → configurable lending policy →
APPROVE / REJECT / REFER / COUNTER_OFFER, with full reason codes.

See [reports/architecture_diagram.png](reports/architecture_diagram.png)
for the full pipeline diagram.

## Where this lives

This folder is meant to sit **inside your existing `credit-risk` repo**,
next to `models/`, as a sibling of your Assignment-1 `notebooks/`,
`api/`, and `src/` folders — same repo, same git history:

```
credit-risk/                              <- your existing Assignment-1 repo
├── models/
│   └── lgbm_credit_risk.pkl              <- already here from Assignment 1, reused as-is
├── notebooks/                            <- Assignment 1
├── api/                                  <- Assignment 1
├── src/                                  <- Assignment 1
└── lending-decision-prototype/           <- THIS project (Assignment 2)
    ├── README.md
    ├── requirements.txt
    ├── config/
    │   └── lending_policy.yaml           # all business thresholds, Part 6
    ├── src/
    │   ├── model_features.py             # frozen model input schema, Part 1
    │   ├── model_loader.py               # loads models/lgbm_credit_risk.pkl (../../models/), Part 1
    │   ├── features.py                   # lending feature catalogue, Part 2
    │   ├── scoring.py                    # PD -> credit score, Part 3
    │   ├── risk.py                       # risk bands, Part 4
    │   ├── affordability.py              # DTI / installment / max amount, Part 5
    │   ├── policy.py                     # policy rule predicates, Part 6
    │   ├── reason_codes.py               # reason-code catalogue, Part 7
    │   └── decision.py                   # precedence + final decision, Parts 6, 8, 9
    ├── api/
    │   └── main.py                       # FastAPI service, Part 8
    ├── tests/                            # pytest suite, Part 9 (30 tests)
    └── reports/                          # one doc per assignment section, see below
```

`src/model_loader.py` points at `../../models/lgbm_credit_risk.pkl`
relative to itself — i.e. your existing `credit-risk/models/lgbm_credit_risk.pkl`
— so **you don't need to move or copy the model file at all.**

## Setup

1. Unzip this project so the `lending-decision-prototype` folder sits
   directly inside `C:\Users\flish\SUMMER2026\credit-risk\` (as shown above).
2. Reuse your existing Assignment-1 virtual environment (it already has
   fastapi, pandas, scikit-learn, lightgbm, joblib) — just add the two
   new dependencies this project needs:

```powershell
cd C:\Users\flish\SUMMER2026\credit-risk\lending-decision-prototype
pip install pyyaml pytest httpx
```

   (Or, for a completely fresh environment, `pip install -r requirements.txt`
   from inside this folder installs everything.)

Because `models/lgbm_credit_risk.pkl` already exists at the parent repo
level, **the real model loads automatically — no extra step needed.**
If it's ever missing (wrong path, file renamed, etc.), the service
automatically falls back to a clearly-labelled temporary stub model
instead of crashing (see `src/model_loader.py` and Part 1) —
`GET /api/v1/models/current` always reports which one is active
(`usingStubModel: true/false`), so you can check this before you run or
submit anything.

## Running the API

```bash
uvicorn api.main:app --reload
```

Interactive docs at `http://127.0.0.1:8000/docs`.

### Sample request

```bash
curl -X POST http://127.0.0.1:8000/api/v1/lending/decision \
  -H "Content-Type: application/json" \
  -d '{
    "customerId": "CUST-001",
    "monthlyIncome": 30000,
    "existingMonthlyDebt": 5000,
    "requestedAmount": 80000,
    "requestedTenure": 12,
    "revolving_utilization": 0.25,
    "age": 35,
    "late_30_59": 0,
    "debt_ratio": 0.2,
    "open_credit_lines": 5,
    "late_90_plus": 0,
    "real_estate_loans": 1,
    "late_60_89": 0,
    "dependents": 1
  }'
```

### Sample response

```json
{
  "applicationId": "b4da5c74-dfab-4867-b566-df955675e1bc",
  "customerId": "CUST-001",
  "probabilityOfDefault": 0.0315,
  "creditScore": 706,
  "riskBand": "LOW",
  "currentDebtToIncomeRatio": 0.1667,
  "projectedDebtToIncomeRatio": 0.4111,
  "disposableIncomeAfter": 17665.6,
  "maximumAffordableAmount": 76352.54,
  "decision": "COUNTER_OFFER",
  "approvedAmount": 76300,
  "tenure": 12,
  "reasonCodes": ["PROJECTED_DTI_TOO_HIGH", "REQUESTED_AMOUNT_ABOVE_AFFORDABILITY_LIMIT"],
  "triggeredRules": ["POL-004"],
  "modelVersion": "credit-risk-v1",
  "policyVersion": "lending-policy-v1",
  "lendingFeatures": { "...": "see Part 2 feature catalogue" }
}
```

### All endpoints

| Method | Path | Purpose |
|---|---|---|
| POST | `/api/v1/lending/decision` | Full pipeline: PD → score → risk → affordability → policy → decision |
| POST | `/api/v1/lending/affordability` | Affordability-only calculator (no model call) |
| GET | `/api/v1/lending/decisions/{applicationId}` | Retrieve a previously made decision |
| GET | `/api/v1/models/current` | Current model + policy version, and whether the stub model is active |

## Running the tests

```bash
pytest -q
```

30 tests covering scoring, risk bands, affordability math, the six
required end-to-end decision scenarios plus boundary cases (Part 9), and
API-level request validation / error handling.

## Documentation (one file per assignment section)

| Report | Covers |
|---|---|
| [01_model_reuse_and_validation.md](reports/01_model_reuse_and_validation.md) | 4.1 — model identity, dataset, metrics, calibration, limitations |
| [02_feature_catalogue.md](reports/02_feature_catalogue.md) | 4.2 — the 10 lending features |
| [03_credit_score_methodology.md](reports/03_credit_score_methodology.md) | 4.3 — PD-to-score transform |
| [04_risk_classification.md](reports/04_risk_classification.md) | 4.4 — risk bands and thresholds |
| [05_affordability_methodology.md](reports/05_affordability_methodology.md) | 4.5, 4.6 — DTI, installment, max loan amount |
| (policy table is in `config/lending_policy.yaml`) | 4.7 — configurable rules |
| [06_test_scenarios.md](reports/06_test_scenarios.md) | Section 6 — six scenarios + results |
| [07_decision_approach_comparison.md](reports/07_decision_approach_comparison.md) | Section 7 — ML-only vs. rules-only vs. hybrid |
| [09_assumptions_and_limitations.md](reports/09_assumptions_and_limitations.md) | Section 13 — every assumption, consolidated |
| [10_final_recommendation.md](reports/10_final_recommendation.md) | Final technical recommendation |
| [architecture_diagram.png](reports/architecture_diagram.png) | Section 12 — pipeline diagram |

Counter-offer logic (4.9) and decision precedence (4.8) are documented in
the `src/decision.py` module docstring, and reason codes (4.10) in
`src/reason_codes.py`.

## Assumptions (summary — full detail in report 09)

- Assumes the real trained model already sits at `credit-risk/models/lgbm_credit_risk.pkl`
  (one level above this folder); if that file is ever missing, a labelled
  stub model is used instead so the service doesn't just crash — check
  `GET /api/v1/models/current` before trusting any output.
- 18% p.a. interest, 40% max DTI, no defined-expense deduction: prototype
  pricing/policy defaults, not a real bank's approved figures.
- Every feature comes from a single self-reported application snapshot —
  no bureau, KYC, employment, or multi-period transaction data.
- This prototype must not be used for real customer lending decisions.
