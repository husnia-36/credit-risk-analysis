# 4.4 Risk Classification

Risk bands are defined directly on PD (the model's native continuous
output); the corresponding score cutoffs are the same thresholds passed
through `scoring.pd_to_score()`, so classifying on score or on PD always
agrees.

## Thresholds and evidence

| Risk Band | PD range | Score range (derived) | Typical interpretation | Treatment |
|---|---|---|---|---|
| VERY_LOW | < 2% | 732–850 | Strong risk profile | Normal policy checks |
| LOW | 2% – < 6.68% | 660–731 | Acceptable risk profile | Normal policy checks |
| MEDIUM | 6.68% – < 12% | 623–659 | Borderline / moderate risk | Additional rules or limits |
| HIGH | 12% – < 20% | 588–622 | Weak risk profile | Reject or manual review |
| VERY_HIGH | ≥ 20% | 300–587 | Very weak risk profile | Normally reject |

**Why these specific cut points, not round numbers:**

- **6.68%** is the exact observed population default rate from the Assignment-1 training data — the LOW/MEDIUM boundary is set exactly at "average risk for this population," so MEDIUM and above always means *above-average* risk for an applicant like this, not an arbitrary round number.
- **2%** approximates the observed default rate of the lowest-risk cohort identified in the Assignment-1 EDA bucketed analysis (the lowest utilization/delinquency quintile showed a default rate near 1.94%) — VERY_LOW is set to match "the kind of applicant this population's own data shows rarely defaults."
- **20%** approximates the observed default rate of the highest-risk cohort in the same bucketed analysis (the highest utilization quintile showed a default rate near 19.88%, roughly a 10x spread from the lowest) — VERY_HIGH begins where an applicant's individual PD exceeds even that worst-cohort average.
- **12%** (MEDIUM/HIGH boundary) is set at roughly midway (in log-odds terms) between the population average and the worst-cohort rate, giving MEDIUM a genuine "borderline" band rather than collapsing straight from average risk to reject-tier risk.

## Direction consistency

Risk strictly increases moving down the table (VERY_LOW → VERY_HIGH), and
credit score strictly decreases over the same direction — there is no
band where a higher score corresponds to higher classified risk.
