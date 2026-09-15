# Final Technical Recommendation

This prototype demonstrates that the Assignment-1 LightGBM credit-risk
model can participate in a full lending decision process — feature layer,
score, risk band, affordability, policy, and decision — while keeping
each stage independently owned, testable, and explainable:

```
Machine Learning + Credit Scoring + Risk Assessment + Affordability + Business Policy
    = Structured Lending Recommendation
```

## What worked well

- **Clean separation of responsibilities.** The model (`src/model_loader.py`)
  never sees a decision, and the decision engine (`src/decision.py`) never
  touches the model directly — everything flows through a plain
  probability-of-default float. This means the model can be retrained,
  swapped, or A/B tested without touching a single policy rule, and vice
  versa — confirmed directly by this project's own test suite, which
  exercises the decision logic entirely independently of whichever model
  (real or stub) happens to be loaded.
- **Configurable policy.** All eight policy rules and every business
  threshold live in `config/lending_policy.yaml`, not in code — a policy
  or risk team could change the maximum DTI or a product cap without a
  code change or a model retrain.
- **Explainable, typed reason codes.** Every non-APPROVE decision returns
  reason codes tagged by type (model / affordability / policy / process),
  satisfying the assignment's explainability requirement directly rather
  than as an afterthought.

## Recommended next steps before any production use

1. **Load the real trained model artifact** (`models/lgbm_credit_risk.pkl`
   from Assignment 1) in place of the temporary stub used to build and
   test this prototype (Part 1) — this is the single most important
   remaining step.
2. **Calibrate PD** against a real or better-labelled population before
   treating the credit score or risk bands as anything beyond a relative
   ranking (Parts 1, 3, 4).
3. **Replace assumed pricing/affordability constants** (18% p.a. interest,
   40% max DTI, zero defined expenses) with figures from an actual product
   and risk-appetite decision, not this prototype's placeholders (Part 5).
4. **Add real bureau/KYC/employment data sources** where available — this
   prototype's biggest limitation is that every feature comes from a
   single self-reported snapshot (Section 13).
5. **Periodically re-validate model and policy together** — since they
   are now decoupled, nothing currently guarantees a retrained model's PD
   distribution still lines up sensibly with the existing score/risk/policy
   thresholds; this should become a release-checklist item.

## Bottom line

The **hybrid ML + rules architecture** (Section 7) is the right shape for
a real digital lending system, and this prototype is a working, tested
demonstration of that shape — not yet a production system, but a solid
foundation whose remaining gaps are clearly identified data and
calibration work rather than architectural rework.
