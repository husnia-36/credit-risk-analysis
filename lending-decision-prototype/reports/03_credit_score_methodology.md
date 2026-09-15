# 4.3 Credit-Score Methodology

## Score range

**300–850.** This range is used because it is a familiar convention for
both technical and business stakeholders reviewing this prototype, not
because the illustrative bands in the assignment brief were copied —
the underlying formula and anchor points below are derived from this
project's own model and population statistics.

## Method

Standard **log-odds scorecard scaling** (the same family of transform used
in FICO-style scorecards):

```
score = OFFSET + FACTOR * ln( (1 - PD) / PD )

FACTOR = PDO / ln(2)                    (points to double the odds)
OFFSET = BASE_SCORE - FACTOR * ln(BASE_ODDS)
BASE_ODDS = (1 - BASE_PD) / BASE_PD
```

## Anchors chosen, and why

| Parameter | Value | Justification |
|---|---|---|
| `BASE_PD` | 0.0668 | The Assignment-1 training population's actual observed default rate — the "neutral, average-risk applicant" anchor is grounded in this project's own data, not an arbitrary midpoint. |
| `BASE_SCORE` | 660 | The score assigned to an applicant at exactly the population-average PD. Chosen near the middle of the 300–850 range so there is roughly symmetric room to move up (lower-than-average risk) and down (higher-than-average risk) in log-odds space. |
| `PDO` (points to double the odds) | 40 | A moderate scaling choice. A steeper, more conventional PDO of 20 (common in commercial bureau scorecards) was considered and rejected for this prototype: it compresses the usable score range too tightly given this dataset's much higher base default rate (6.68%) than a typical bureau population, pushing most applicants toward the low end of the scale. 40 spreads scores more usefully across the population actually seen in this project. |

The score is **monotonic and strictly decreasing in PD** by construction (a
direct algebraic property of the log-odds transform: as PD rises, `(1-PD)/PD`
falls, so `ln(odds)` falls, so score falls). **Higher score always means
lower risk** — there is no branch or exception to this in the formula.

Because raw log-odds is unbounded as PD approaches 0 or 1, the computed
score is clipped to `[300, 850]`.

## Derived mapping (illustrative — computed from the formula, not assumed)

| Probability of Default | Score |
|---|---|
| 0.1% | 850 (clipped) |
| 2% | 732 |
| 5% | 678 |
| 6.68% (population average) | 660 |
| 10% | 635 |
| 20% | 588 |
| 50% | 508 |
| 90% | 381 |
| 99% | 300 (clipped) |

## Limitations

- **Experimental, not a bureau-equivalent score.** It is calibrated to this project's own model and dataset, not to any real bureau's scored population — it should not be presented to a real customer as a FICO-equivalent number.
- **Inherits the model's calibration gap** documented in Part 1: since the underlying PD values have not been validated against real observed frequencies, the score is best read as a consistent *relative* risk ranking (an applicant scored 700 is meaningfully lower-risk than one scored 600) rather than a number with an exact real-world meaning ("a 660 defaults X% of the time").
- **Clipping at the extremes** means very low or very high PDs are indistinguishable at the boundary (e.g. PD 0.05% and PD 0.001% both show as 850). This is an acceptable simplification for a prototype but would need wider tail resolution in production.
