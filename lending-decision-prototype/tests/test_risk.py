from src.risk import classify_risk


def test_band_boundaries():
    assert classify_risk(0.019) == "VERY_LOW"
    assert classify_risk(0.02) == "LOW"          # boundary is inclusive-below on the upper band
    assert classify_risk(0.0667) == "LOW"
    assert classify_risk(0.0668) == "MEDIUM"
    assert classify_risk(0.1199) == "MEDIUM"
    assert classify_risk(0.12) == "HIGH"
    assert classify_risk(0.1999) == "HIGH"
    assert classify_risk(0.20) == "VERY_HIGH"
    assert classify_risk(0.99) == "VERY_HIGH"


def test_risk_increases_monotonically():
    order = ["VERY_LOW", "LOW", "MEDIUM", "HIGH", "VERY_HIGH"]
    pds = [0.01, 0.04, 0.09, 0.15, 0.5]
    bands = [classify_risk(p) for p in pds]
    assert [order.index(b) for b in bands] == sorted(order.index(b) for b in bands)
