from src.scoring import pd_to_score, SCORE_MIN, SCORE_MAX


def test_score_is_monotonic_decreasing_in_pd():
    pds = [0.001, 0.01, 0.05, 0.10, 0.30, 0.60, 0.95]
    scores = [pd_to_score(p) for p in pds]
    assert scores == sorted(scores, reverse=True)


def test_score_clipped_to_range():
    assert pd_to_score(0.00000001) == SCORE_MAX
    assert pd_to_score(0.999999) == SCORE_MIN


def test_base_pd_maps_to_base_score():
    from src.scoring import BASE_PD, BASE_SCORE
    assert pd_to_score(BASE_PD) == BASE_SCORE
