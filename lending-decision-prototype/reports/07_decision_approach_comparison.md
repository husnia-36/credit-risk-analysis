# Section 7: Decision Approach Comparison

## Machine Learning Only

A model (e.g. the LightGBM classifier from Part 1) outputs a PD or a
direct approve/reject call, with no separate policy layer.

**Strengths:** best raw predictive flexibility — it can pick up nonlinear,
interacting risk patterns (e.g. the utilization × delinquency interaction
found in this project's SHAP analysis) that a human-written rule would
likely miss or under-weight. It adapts automatically as it's retrained on
new data.

**Limitations:** governance and auditability suffer badly. A regulator or
credit committee cannot easily be shown *why* a specific applicant was
declined beyond "the model said so" (even with SHAP, that explanation is
statistical, not a business rule a policy team signed off on). There is
no clean way to encode a hard business constraint ("never lend above
product limit X", "always refer applicants under 18-months-on-book") —
such rules would have to be smuggled into training data or grafted on
after the fact, defeating the point of a clean policy layer. Changing a
single threshold (e.g. tightening the maximum DTI) requires retraining or
hand-editing the model, which is slow and hard to audit precisely because
nothing is separated out.

## Rule-Based Only

All decisioning — including risk assessment — is done through explicit,
hand-written business rules, with no statistical model.

**Strengths:** maximum transparency and direct policy control. Every
decision traces to a named rule ID a business/compliance stakeholder
wrote and approved (exactly the `POL-xxx` table this project uses for the
*policy* layer). Trivially auditable, easy to change one threshold
without touching anything else, and easy to explain to a customer or
regulator in plain language.

**Limitations:** cannot capture complex, nonlinear risk patterns.
A rule-only system would have to reduce risk to a handful of manually
chosen cutoffs (e.g. "utilization over 70% is risky"), throwing away the
~10x default-rate spread this project's own EDA found across utilization
buckets, and the interaction effects a boosting model picks up
automatically. Rules also tend to proliferate and conflict as more edge
cases are patched in over time, becoming their own maintenance burden.

## Hybrid: ML + Rules (the approach this prototype uses)

The model is used *only* to produce a PD (Part 1); everything else —
scoring, risk banding, affordability, policy, and the final decision — is
explicit, configurable logic (Parts 3–9), consuming that PD as one input
among several.

**Strengths:** keeps the model's predictive power for the one job it is
actually good at (ranking relative risk from complex patterns) while
keeping every business-controllable decision — DTI limits, product caps,
manual-review bands, tenure restrictions — in a human-auditable
configuration file (`config/lending_policy.yaml`) that a policy team can
change without a data scientist or a retraining cycle. Reason codes
(Part 7) can cleanly distinguish "the model flagged this as risky"
(`HIGH_DELINQUENCY_HISTORY`) from "the bank's policy caps this loan size"
(`PRODUCT_LIMIT_EXCEEDED`), which is exactly the explainability
separation regulators and credit committees actually want.

**Limitations:** more moving parts and integration complexity than either
pure approach — a bug can now live in the model, the feature engineering,
the scoring transform, the policy config, or the precedence logic that
combines them, and testing has to cover all of these layers (as this
project's `tests/` directory does). It also introduces its own new
failure mode: model and policy can drift out of sync with each other
(e.g. a score threshold tuned for one model version stops making sense
after the model is retrained and its PD distribution shifts) if the two
are not periodically re-validated together.

## Recommendation

**Hybrid ML + Rules** is the right approach for a practical banking
environment, and is what this prototype implements. The reasoning, against
the criteria the assignment asks for:

- **Predictive value:** only the hybrid and ML-only approaches capture the
  model's demonstrated ability to separate risk far better than simple
  cutoffs (ROC-AUC 0.867 vs. a rule-only system's much cruder binning).
- **Explainability:** the hybrid approach is the only one that can cleanly
  label *which* reasons are model-driven vs. policy-driven (Part 7's
  reason-code catalogue) — ML-only conflates everything into the model,
  and rule-only has nothing to explain beyond the rules themselves.
- **Auditability:** a hybrid system lets an auditor inspect the policy
  layer (`config/lending_policy.yaml` and the `POL-xxx` table) completely
  independently of the model's internals, satisfying most audit needs
  without requiring the auditor to understand gradient boosting.
- **Maintainability / change management:** business teams can change a
  DTI limit or a product cap by editing one YAML value and redeploying —
  no retraining, no data science involvement, no downtime for the model.
  This is a substantial practical advantage over ML-only, where every
  policy change is entangled with the model.
- **Separation of responsibilities:** this is the assignment's own
  explicit design goal (Section 1: "the assignment intentionally
  separates predictive modelling from business decisioning"), and only
  the hybrid approach satisfies it — the model estimates risk; the bank,
  through the policy layer, decides what to do about it.

The added integration complexity is a real, ongoing cost (documented
above), but it is the correct tradeoff for a regulated lending context,
where explainability and policy control cannot be sacrificed for
predictive power alone.
