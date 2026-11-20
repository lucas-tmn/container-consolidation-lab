from datetime import date

import pytest

from ccl.config import load_params
from ccl.engine import PlanLine, plan_week, rank_options, run, week_monday
from ccl.metrics import containers

P = load_params()
W = date(2026, 12, 28)
W2 = date(2027, 1, 4)
ITEMS = {"A": (4.0, 10.0), "B": (4.0, 100.0), "C": (4.0, 10.0)}   # cube 4 ft3 per piece


class Sup:
    def __init__(self, table=None, default=0.0):
        self.t, self.d = table or {}, default

    def wos(self, item, dc, week, aw):
        return self.t.get((item, dc), self.d)


def L(seq, item, qty, dc, week=W, due=None):
    return PlanLine(seq, item, qty, dc, week, due)


def test_week_monday():
    assert week_monday(date(2026, 12, 19)) == date(2026, 12, 14)
    assert week_monday(date(2026, 12, 28)) == W


def test_as_scheduled_baseline():
    # Arcadia 600 pcs = 2400 ft3 = exactly 1 container; Mesquite 601 pcs = 2 containers (last 4 ft3)
    lines = [L(1, "A", 600, "Arcadia"), L(2, "A", 601, "Mesquite")]
    r = run(lines, ITEMS, Sup(), P, W, {"destination_change": False, "delay": False, "pull_forward": False})
    k = r["kpis"]
    assert k["containers_before"] == k["containers_after"] == 3
    assert k["changes"] == 0 and r["by_dc"]["Mesquite"]["before"]["containers"] == 2
    assert [t["dc"] for t in r["todos"]] == ["Mesquite"] and r["todos"][0]["leftover"]


def test_destination_change_removes_container_and_needs_approval():
    # Redlands: 1 container + 8 pcs (32 ft3). Leesport: 550 pcs = 2200 ft3 (92%, no overflow of its own), room 200 ft3
    lines = [L(1, "A", 600, "Redlands"), L(2, "A", 8, "Redlands"), L(3, "B", 550, "Leesport")]
    sup = Sup({("A", "Leesport"): 0.0, ("A", "Redlands"): 9.0})                             # A short at Leesport only
    r = run(lines, ITEMS, sup, P, W, {"destination_change": True, "delay": False, "pull_forward": False})
    k = r["kpis"]
    assert k["containers_before"] == 3 and k["containers_after"] == 2
    assert k["destination_change_pcs"] == 8 and k["cost_avoided_usd"] == 8007
    assert any(m.kind == "destination_change" and m.to_dc == "Leesport" for m in r["moves"])
    assert all(t["needs_approval"] for t in r["todos"])


def test_destination_respects_room_and_short():
    lines = [L(1, "A", 600, "Redlands"), L(2, "A", 8, "Redlands"), L(3, "B", 600, "Leesport")]  # Leesport exactly full: no room
    r = run(lines, ITEMS, Sup(), P, W, {"destination_change": True, "delay": False, "pull_forward": False})
    assert r["kpis"]["destination_change_pcs"] == 0
    lines2 = [L(1, "A", 600, "Redlands"), L(2, "A", 8, "Redlands"), L(3, "B", 550, "Leesport")]
    r2 = run(lines2, ITEMS, Sup({("A", "Leesport"): 12.0}), P, W, {"destination_change": True, "delay": False, "pull_forward": False})
    assert r2["kpis"]["destination_change_pcs"] == 0          # A is not short at Leesport


def test_delay_when_not_short_and_late_flag():
    due_early = date(2027, 2, 1)
    lines = [L(1, "A", 600, "Redlands", due=due_early), L(2, "A", 8, "Redlands", due=due_early), L(3, "B", 550, "Leesport")]
    sup = Sup({("A", "Redlands"): 9.0})                       # not short at Redlands -> delay allowed
    r = run(lines, ITEMS, sup, P, W, {"destination_change": False, "delay": True, "pull_forward": False})
    m = [m for m in r["moves"] if m.kind == "delay"][0]
    assert m.qty == 8 and m.to_week == W2 and m.late                      # arrival W2 + 5 weeks > 1 Feb
    assert r["kpis"]["containers_after"] == 2 and r["kpis"]["late_delayed_pcs"] == 8
    r2 = run([L(1, "A", 600, "Redlands", due=date(2027, 6, 1)), L(2, "A", 8, "Redlands", due=date(2027, 6, 1))], ITEMS, sup, P, W,
             {"destination_change": False, "delay": True, "pull_forward": False})
    assert not [m for m in r2["moves"] if m.kind == "delay"][0].late


def test_no_delay_when_item_is_short():
    lines = [L(1, "A", 600, "Redlands"), L(2, "A", 8, "Redlands")]
    r = run(lines, ITEMS, Sup({("A", "Redlands"): 1.0}), P, W, {"destination_change": False, "delay": True, "pull_forward": False})
    assert r["kpis"]["delayed_pcs"] == 0


def test_pull_forward_reaches_min_fill_shortest_first():
    # Advance: 500 pcs = 2000 ft3 (83%). Needs >= 0.9 * 2400 = 2160 -> 40 more pieces. Next week has A (not short) and B (short).
    lines = [L(1, "C", 500, "Advance"), L(2, "A", 100, "Advance", W2), L(3, "B", 100, "Advance", W2)]
    sup = Sup({("A", "Advance"): 9.0, ("B", "Advance"): 1.0})
    r = run(lines, ITEMS, sup, P, W, {"destination_change": False, "delay": False, "pull_forward": True})
    pulls = [m for m in r["moves"] if m.kind == "pull_in"]
    assert [(m.item, m.qty) for m in pulls] == [("B", 40)]               # shortest first, stops at min fill
    assert r["by_dc"]["Advance"]["after"]["last_fill"] == pytest.approx(2160 / 2400)
    assert r["kpis"]["pulled_fob_usd"] == 4000.0


def test_pull_forward_not_committed_when_min_unreachable_or_over_max():
    lines = [L(1, "C", 500, "Advance"), L(2, "A", 10, "Advance", W2)]     # only 40 ft3 available, need 160
    r = run(lines, ITEMS, Sup(), P, W, {"destination_change": False, "delay": False, "pull_forward": True})
    assert r["kpis"]["pulled_pcs"] == 0
    assert r["todos"][0]["leftover"]


def test_pull_forward_approval_threshold():
    items = {"C": (4.0, 10.0), "B": (4.0, 700.0)}
    lines = [L(1, "C", 500, "Advance"), L(2, "B", 100, "Advance", W2)]
    r = run(lines, items, Sup(), P, W, {"destination_change": False, "delay": False, "pull_forward": True})
    t = r["todos"][0]
    assert t["pulled_fob_usd"] == 28000.0 and "pull_forward_over_threshold" in t["reasons"]


def test_dc_lead_time_switch_changes_lateness():
    due = date(2027, 2, 15)
    lines = [L(1, "A", 600, "Arcadia", due=due), L(2, "A", 8, "Arcadia", due=due)]
    sup = Sup({("A", "Arcadia"): 9.0})
    opt = {"destination_change": False, "delay": True, "pull_forward": False}
    buf = run(lines, ITEMS, sup, P, W, opt, use_dc_lead_time=False)
    lt = run(lines, ITEMS, sup, P, W, opt, use_dc_lead_time=True)
    assert not buf["moves"][0].late        # 4 Jan + 5 weeks = 8 Feb <= 15 Feb
    assert lt["moves"][0].late             # 4 Jan + 9 weeks = 8 Mar > 15 Feb


def test_deterministic_and_inputs_not_mutated():
    lines = [L(1, "A", 600, "Redlands"), L(2, "A", 8, "Redlands"), L(3, "B", 550, "Leesport"), L(4, "C", 100, "Leesport", W2)]
    sup = Sup({("A", "Leesport"): 0.0})
    a = rank_options(lines, ITEMS, sup, P, W)
    b = rank_options(lines, ITEMS, sup, P, W)
    assert [m for r in a.values() for m in r["moves"]] == [m for r in b.values() for m in r["moves"]]
    assert lines[1].qty == 8 and a["as_scheduled"]["kpis"]["changes"] == 0


def test_conservation_of_pieces_and_cube():
    lines = [L(1, "A", 600, "Redlands"), L(2, "A", 8, "Redlands"), L(3, "B", 550, "Leesport"), L(4, "C", 120, "Leesport", W2)]
    r = run(lines, ITEMS, Sup({("A", "Leesport"): 0.0}), P, W)
    tot_before = sum(d["before"]["cube"] for d in r["by_dc"].values() if d["before"]) + sum(d["next_before"]["cube"] for d in r["by_dc"].values() if d["next_before"])
    tot_after = sum(d["after"]["cube"] for d in r["by_dc"].values() if d["after"]) + sum(d["next_after"]["cube"] for d in r["by_dc"].values() if d["next_after"])
    assert tot_before == pytest.approx(tot_after)
    assert containers(2400.0) == 1


class SupN(Sup):
    def wos(self, item, dc, week, aw):
        return self.t.get((item, dc), 0.0)       # None allowed in the table


def test_all_or_nothing_overflow_cleanup():
    # Redlands overflow 8 pcs (32 ft3). Leesport has room for only 4 pcs (16 ft3): a partial move saves no container, so nothing moves.
    lines = [L(1, "A", 600, "Redlands"), L(2, "A", 8, "Redlands"), L(3, "B", 596, "Leesport")]    # Leesport 2384 ft3, room 16
    r = run(lines, ITEMS, Sup({("A", "Leesport"): 0.0}), P, W, {"destination_change": True, "delay": False, "pull_forward": False})
    assert r["kpis"]["changes"] == 0 and r["kpis"]["containers_after"] == r["kpis"]["containers_before"]


def test_prefers_destination_that_takes_whole_chunk():
    lines = [L(1, "A", 600, "Redlands"), L(2, "A", 8, "Redlands"), L(3, "B", 550, "Leesport"), L(4, "C", 598, "Advance")]
    # Advance: 2392 ft3 -> room 8 ft3 = 2 pcs, wos 0 (lowest); Leesport: room 200 ft3 = 50 pcs, wos 3 -> must take all 8 pcs
    sup = Sup({("A", "Advance"): 0.0, ("A", "Leesport"): 3.0})
    r = run(lines, ITEMS, sup, P, W, {"destination_change": True, "delay": False, "pull_forward": False})
    mv = [m for m in r["moves"] if m.kind == "destination_change"]
    assert [(m.to_dc, m.qty) for m in mv] == [("Leesport", 8)]


def test_unknown_wos_is_not_needed_and_not_delayable():
    lines = [L(1, "A", 600, "Redlands"), L(2, "A", 8, "Redlands"), L(3, "B", 550, "Leesport")]
    unk = SupN({("A", "Leesport"): None, ("A", "Redlands"): None})
    r = run(lines, ITEMS, unk, P, W)
    assert r["kpis"]["changes"] == 0                       # not a destination (unknown), not delayable (unknown)
