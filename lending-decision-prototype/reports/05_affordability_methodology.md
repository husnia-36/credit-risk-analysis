# 4.5 / 4.6 Affordability, Loan Amount, and Tenure Assessment

Credit risk (PD/score/band) and affordability are computed as two
separate, independent assessments and only combined in the policy/decision
layer — a low-PD applicant can still fail affordability, and vice versa.

## Formulas used

```
Current DTI     = ExistingMonthlyDebt / MonthlyIncome
Proposed Installment = amortizing-loan payment for (requestedAmount, annualRate, requestedTenure)
Projected DTI   = (ExistingMonthlyDebt + ProposedInstallment) / MonthlyIncome
Disposable Income (before) = MonthlyIncome - ExistingMonthlyDebt - DefinedExpenses
Disposable Income (after)  = Disposable Income (before) - ProposedInstallment
Max Affordable Installment = max(0, MaxAllowedDTI * MonthlyIncome - ExistingMonthlyDebt)
Max Affordable Amount      = principal whose installment == Max Affordable Installment, at the requested tenure
```

## Interest / installment assumption

An **equal-instalment amortizing loan** is assumed (the standard formula
used for mortgages and personal instalment loans):

```
installment = P * r * (1+r)^n / ((1+r)^n - 1)
```

where `P` = principal, `r` = monthly interest rate (`annualRate / 12`),
`n` = tenure in months. **No fees are modelled** — this is an explicit
simplification (see Section 13 of the assignment brief, which anticipates
"simplified interest-rate or installment calculations").

## Method chosen for loan amount / tenure assessment (4.6)

This prototype uses **Option A from the brief**: derive a maximum
affordable *installment* first (from income, existing debt, and the
policy's maximum allowed DTI), then invert the amortization formula to
get a maximum affordable *principal* at the requested tenure. This is
combined with the risk-based product/band caps applied downstream in the
policy layer (Part 6) — affordability answers "what can this customer's
income support," policy answers "what is the bank additionally willing to
lend given this applicant's risk band and product rules."

## Which numbers are customer capacity vs. bank policy

| Input | Source |
|---|---|
| `monthlyIncome`, `existingMonthlyDebt`, `requestedAmount`, `requestedTenure` | **Customer capacity** — facts about this specific application |
| `annualInterestRate` (pricing assumption, default 18% p.a.) | **Bank policy** — a pricing decision, configurable in `config/lending_policy.yaml` |
| `maxAllowedDTI` (default 40%) | **Bank policy** — a risk-appetite decision, configurable |
| `definedExpenses` (default 0) | **Bank policy** — an optional living-cost allowance a bank may choose to subtract; left at 0 by default since the dataset has no per-applicant expense data (documented limitation) |

`src/affordability.py` is written as a pure calculator that takes all
policy values as explicit parameters — it never hardcodes a business
threshold internally — so the actual values always come from (and can be
changed in) the policy configuration in Part 6, not from this module.

## Worked check against the brief's illustrative scenario

Running this module on the brief's own example input
(`monthlyIncome=30000, existingMonthlyDebt=5000, requestedAmount=80000, requestedTenure=12`)
with this project's own assumptions (18% p.a., 40% max DTI) produces:

- Current DTI: 0.17 (brief's illustrative value: 0.17 — matches)
- Projected DTI: 0.41 (brief's illustrative value: 0.32 — differs, because the brief's own pricing/DTI assumptions were never disclosed and are explicitly marked "illustrative only")
- Maximum affordable amount: ETB 76,352.54 (brief's illustrative value: ETB 65,000)
- Result shape: requested amount (80,000) exceeds the maximum affordable amount → **COUNTER_OFFER**, which matches the brief's own worked example's decision outcome even though the exact figures differ — confirming the pipeline reproduces the *right kind* of outcome, as intended ("interns should not copy these ranges without justification").
