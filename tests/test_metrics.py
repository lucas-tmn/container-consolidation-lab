import pytest
from ccl import metrics as m


def test_container_eq_and_count():
    assert m.container_eq(2400) == 1.0
    assert m.containers(2400) == 1
    assert m.containers(2401) == 2
    assert m.containers(0) == 0


def test_last_container_fill():
    assert m.last_container_fill(2400) == 1.0
    assert m.last_container_fill(3600) == pytest.approx(0.5)


def test_avg_fill_matches_app_example():
    # 15 containers at 69% average fill -> total cube
    total = 0.69 * 15 * 2400
    assert m.avg_fill(total, 15) == pytest.approx(0.69)


def test_wos_missing_is_zero():
    assert m.weeks_of_supply(None, 10) == 0.0
    assert m.weeks_of_supply(51, 17) == pytest.approx(3.0)
    assert m.is_short(3.0, 4)


def test_weekly_forecast_factor():
    assert m.weekly_forecast_from_monthly([52.0]) == pytest.approx(12.0)


def test_freight():
    assert m.freight_usd({"Redlands": 1, "Leesport": 1}, {"Redlands": "west", "Leesport": "east"},
                         {"west": 8007, "east": 10166}) == 18173
