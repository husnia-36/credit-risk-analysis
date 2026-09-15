# Section 6: Test Scenarios and Results

All six scenarios are implemented as automated tests in `tests/test_decision.py`
(`pytest -q` → 30 passed, 0 failed, including these six plus unit tests for
scoring, risk, affordability, and API-level validation). Each scenario below
monkeypatches the PD returned by the model layer so the decision logic is
tested deterministically, independent of whichever model artifact (real or
temporary stub — see Part 1) happens to be loaded at test time; the actual
JSON responses below were captured from real runs of `evaluate_application()`.

| # | Scenario | Expected focus | PD (test input) | Result |
|---|---|---|---|---|
| 1 | Low-risk / affordable | Normal APPROVE path | 0.01 | **APPROVE** — VERY_LOW band, score 773, requested 10,000 well under the 200,304 affordability ceiling |
| 2 | Low-risk / unaffordable amount | COUNTER_OFFER or REJECT based on policy | 0.015 | **COUNTER_OFFER** — VERY_LOW band (score 749) but requested 90,000 exceeds the income-based affordability ceiling (54,538); offer reduced to 54,500 |
| 3 | Medium-risk / affordable | Policy-dependent approval, reduced limit, or REFER | 0.08 | **APPROVE** — MEDIUM band, score 649 clears both the manual-review range (605–640) and the 623 approval bar; requested 20,000 is within the MEDIUM band's 50,000 policy cap |
| 4 | High-risk applicant | REJECT or REFER according to policy | 0.25 | **REJECT** — VERY_HIGH band, score 571; reason codes distinguish the policy trigger (`RISK_TOO_HIGH`) from its model-level drivers (`HIGH_DELINQUENCY_HISTORY`, `HIGH_CREDIT_UTILIZATION`) |
| 5 | Requested amount above product maximum | COUNTER_OFFER or REJECT | 0.03 | **COUNTER_OFFER** — LOW band, plenty of income/affordability headroom (ceiling 381,763), but the product's hard maximum (100,000) binds first; offer capped at 100,000 |
| 6 | Boundary case | Threshold behaviour at score, DTI, amount, or tenure limit | 0.01 | **REJECT** (`UNSUPPORTED_TENURE`) — requested tenure of 13 months falls one month outside the product's supported tenure list `[3, 6, 12, 18, 24, 36]`; a second boundary check (unit-level, not a full application) confirms a projected DTI of *exactly* 0.40 does **not** trigger `PROJECTED_DTI_TOO_HIGH` (the rule is strictly `>`), while 0.4001 does |

## What each scenario demonstrates

- **Scenario 1** confirms the "everything is fine" path produces a clean APPROVE with a single `APPROVED` reason code.
- **Scenario 2** confirms risk and affordability are independently evaluated — a very-low-risk applicant can still be counter-offered purely on income/DTI grounds.
- **Scenario 3** confirms the manual-review score band and the risk-band spending cap coexist correctly — this applicant clears both.
- **Scenario 4** confirms multiple reason codes of different *types* (policy-level `RISK_TOO_HIGH` plus two model-level drivers) can be returned together, satisfying the explainability requirement in 4.10.
- **Scenario 5** confirms that even an applicant with large affordability headroom is still bound by the bank's hard product limit — a policy constraint independent of both the model and the customer's actual capacity.
- **Scenario 6** confirms exact-boundary behaviour on two different rule types: a discrete/list-based rule (tenure) and a continuous-threshold rule (DTI), the latter checked precisely at the boundary value itself rather than just "near" it.

## Running the tests

```bash
pip install -r requirements.txt
pytest -q
```
