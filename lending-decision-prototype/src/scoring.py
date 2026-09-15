"""
Part 3 (4.3): Probability-of-Default -> credit-score transformation.

Method: standard log-odds scorecard scaling (the same family of transform
used by FICO-style scorecards), NOT a copy of the assignment brief's
illustrative table. Anchored to this project's own population statistics:

    score = OFFSET + FACTOR * ln( (1 - PD) / PD )

    FACTOR = PDO / ln(2)     -- "points to double the odds"
    OFFSET = BASE_SCORE - FACTOR * ln(BASE_ODDS)
    BASE_ODDS = (1 - BASE_PD) / BASE_PD

Anchors chosen for this prototype:
    BASE_PD    = 0.0668   (the training population's observed default rate)
    BASE_SCORE = 660      (assigned score at the population-average PD)
    PDO        = 40       (odds double every 40 points -- a conventional,
                            moderate scaling choice; steeper than FICO's
                            typical 20 would compress the range too much
                            for this project's much higher base rate)

This makes the "neutral" applicant (average risk for this population)
land at 660, with score rising for below-average PD and falling for
above-average PD -- monotonic and symmetric in log-odds space.
"""
from __future__ import annotations

import math

SCORE_MIN = 300
SCORE_MAX = 850

BASE_PD = 0.0668
BASE_SCORE = 660
PDO = 40  # points to double the odds

FACTOR = PDO / math.log(2)
_BASE_ODDS = (1 - BASE_PD) / BASE_PD
OFFSET = BASE_SCORE - FACTOR * math.log(_BASE_ODDS)


def pd_to_score(pd: float) -> int:
    """
    Higher score always means lower risk (monotonic decreasing in PD).
    Clipped to [SCORE_MIN, SCORE_MAX] since raw log-odds is unbounded as
    PD approaches 0 or 1.
    """
    pd = min(max(pd, 1e-6), 1 - 1e-6)  # guard against log(0)
    odds = (1 - pd) / pd
    raw_score = OFFSET + FACTOR * math.log(odds)
    return int(round(min(max(raw_score, SCORE_MIN), SCORE_MAX)))
