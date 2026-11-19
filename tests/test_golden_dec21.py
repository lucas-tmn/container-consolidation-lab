import pytest
from ccl.config import load_params
from ccl.golden import APP, DESTS, recompute, verify
from ccl.rules import TodoFacts, approval_reasons, needs_approval

P = load_params()


def test_all_recomputable_checks_match_app():
    rows = verify(P)
    bad = [r for r in rows if not r[3]]
    assert not bad, bad


def test_pcs_per_todo_and_total():
    r = recompute(P)
    for d in DESTS:
        assert r["agg"][d]["pcs"] == APP["pcs"][d]
    assert sum(r["agg"][d]["pcs"] for d in DESTS) == APP["total_pcs"] == 1257


def test_cube_and_fob_within_rounding():
    r = recompute(P)
    for d in DESTS:
        assert r["agg"][d]["cube"] == pytest.approx(APP["cube"][d], abs=1)
        assert r["agg"][d]["fob"] == pytest.approx(APP["fob"][d], abs=1.5)


def test_changes_and_move_cube():
    r = recompute(P)
    assert r["changes"] == 47
    assert r["move_cube"] == pytest.approx(31.84, abs=0.01)   # 8 x 3.98


def test_approvals_four_of_four():
    assert recompute(P)["approvals"] == 4


def test_approval_reasons():
    assert approval_reasons(TodoFacts(pulled_fob_usd=25001), P) == ["pull_forward_over_threshold"]
    assert not needs_approval(TodoFacts(pulled_fob_usd=25000), P)
    assert "destination_change" in approval_reasons(TodoFacts(has_destination_change=True), P)
    assert "container_below_min_fill" in approval_reasons(TodoFacts(last_container_fill=0.89), P)


@pytest.mark.skip(reason="needs frozen snapshot of the 21 Dec and 28 Dec weeks (phase 1)")
def test_containers_15_to_14_and_fill_69_to_97():
    ...


@pytest.mark.skip(reason="needs frozen snapshot of the 28 Dec week (phase 1)")
def test_next_week_containers_reduce():
    ...
