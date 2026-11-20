"""Planning engine (docs/03_logic_spec.md). One vendor, one ship week.

Steps: baseline -> spread -> find_overflow -> change_destination -> delay -> pull_forward -> leftover -> rank_options.
No I/O here. Inputs: plan lines, item master, a supply object with wos(item, dc, ship_week, arrival_weeks), params.
Output is deterministic: ties are broken by (WOS, item, seq). Lines are identified by SEQ, never by PO number.
"""
from __future__ import annotations

import copy
import math
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Mapping

from .metrics import avg_fill, containers, last_container_fill
from .rules import TodoFacts, approval_reasons

EPS = 1e-6


@dataclass(frozen=True)
class PlanLine:
    seq: int
    item: str
    qty: int
    dc: str
    week: date                 # Monday of the ship week
    due: date | None = None    # PO due date


@dataclass(frozen=True)
class Move:
    seq: int
    item: str
    qty: int
    kind: str                  # "destination_change" | "delay" | "pull_in"
    from_dc: str
    to_dc: str
    from_week: date
    to_week: date
    late: bool = False


def week_monday(d: date) -> date:
    return d - timedelta(days=d.weekday())


OPTIONS_ALL = {"destination_change": True, "delay": True, "pull_forward": True}


class State:
    """Working copy: buckets[(dc, week)] = {seq: [item, qty, due]}."""

    def __init__(self, lines, items: Mapping[str, tuple], params: dict, week: date):
        self.items, self.p, self.week = items, params, week
        self.next_week = week + timedelta(days=7)
        self.V = float(params["container"]["volume_ft3"])
        self.fmin = float(params["fill"]["min"])
        self.fmax = float(params["fill"]["max"])
        self.short = float(params["supply"]["short_below_weeks"])
        self.buckets: dict = defaultdict(dict)
        self.moves: list[Move] = []
        for l in lines:
            if l.week in (week, self.next_week):
                self.buckets[(l.dc, l.week)][l.seq] = [l.item, l.qty, l.due]

    def cpp(self, item: str) -> float:
        try:
            return float(self.items[item][0])
        except KeyError:
            raise KeyError(f"item {item} missing in item master") from None

    def fob(self, item: str) -> float:
        return float(self.items[item][1])

    def cube(self, dc: str, week: date) -> float:
        return sum(q * self.cpp(i) for i, q, _ in self.buckets.get((dc, week), {}).values())

    def dcs(self) -> list[str]:
        return sorted({dc for (dc, w), b in self.buckets.items() if w == self.week and b})

    def take(self, dc: str, week: date, seq: int, qty: int):
        b = self.buckets[(dc, week)]
        item, q, due = b[seq]
        b[seq][1] = q - qty
        if b[seq][1] <= 0:
            del b[seq]
        return item, due

    def put(self, dc: str, week: date, seq: int, item: str, qty: int, due) -> None:
        b = self.buckets[(dc, week)]
        if seq in b:
            b[seq][1] += qty
        else:
            b[seq] = [item, qty, due]


def _arrival_weeks(dc: str, params: dict, use_dc_lead_time: bool) -> int:
    if use_dc_lead_time:
        lt = params.get("lead_time_weeks_edw", {})
        if dc in lt:
            return int(lt[dc])
    return int(params["supply"]["arrival_buffer_weeks"])


# ---- step 1 and 2 -----------------------------------------------------------------------------
def baseline(st: State, week: date | None = None) -> dict:
    w = week or st.week
    out = {}
    dcs = sorted({dc for (dc, ww), b in st.buckets.items() if ww == w and b})
    for dc in dcs:
        c = st.cube(dc, w)
        n = containers(c, st.V)
        out[dc] = {"cube": c, "containers": n, "last_fill": last_container_fill(c, st.V), "avg_fill": avg_fill(c, n, st.V)}
    return out


def spread(cube_ft3: float, container_ft3: float) -> list[float]:
    """Even fill across the containers of a DC (informational: the container count does not change)."""
    n = containers(cube_ft3, container_ft3)
    return [] if n == 0 else [cube_ft3 / (n * container_ft3)] * n


# ---- step 3 -----------------------------------------------------------------------------------
def find_overflow(st: State, dc: str, wos) -> tuple[float, list]:
    """Cube of the last partial container (if below fill.min) and its candidate lines, least needed first."""
    c = st.cube(dc, st.week)
    n = containers(c, st.V)
    if n == 0 or last_container_fill(c, st.V) >= st.fmin - EPS:
        return 0.0, []
    remaining = c - (n - 1) * st.V
    cands = [(seq, e[0], e[1]) for seq, e in st.buckets[(dc, st.week)].items()]
    cands.sort(key=lambda t: (-wos(t[1], dc), t[1], t[0]))
    return remaining, cands


# ---- step 4 -----------------------------------------------------------------------------------
def change_destination(st: State, dc: str, remaining: float, cands: list, wos) -> float:
    for seq, item, _ in cands:
        if remaining <= EPS:
            break
        cpp = st.cpp(item)
        dests = []
        for d in st.dcs():
            if d == dc:
                continue
            cd = st.cube(d, st.week)
            n = containers(cd, st.V)
            room = n * st.V - cd if cd > EPS else 0.0
            if room > cpp - EPS and wos(item, d) < st.short:
                dests.append((wos(item, d), d, room))
        for _, d, room in sorted(dests):
            e = st.buckets[(dc, st.week)].get(seq)
            if e is None or remaining <= EPS:
                break
            q = min(e[1], int(room // cpp + EPS), math.ceil(remaining / cpp - EPS))
            if q < 1:
                continue
            _, due = st.take(dc, st.week, seq, q)
            st.put(d, st.week, seq, item, q, due)
            st.moves.append(Move(seq, item, q, "destination_change", dc, d, st.week, st.week))
            remaining -= q * cpp
    return remaining


# ---- step 5 -----------------------------------------------------------------------------------
def delay_one_week(st: State, dc: str, remaining: float, cands: list, wos, use_dc_lead_time: bool) -> float:
    aw = _arrival_weeks(dc, st.p, use_dc_lead_time)
    for seq, item, _ in cands:
        if remaining <= EPS:
            break
        e = st.buckets[(dc, st.week)].get(seq)
        if e is None or wos(item, dc) < st.short:      # still needed at this DC: do not delay
            continue
        cpp = st.cpp(item)
        q = min(e[1], math.ceil(remaining / cpp - EPS))
        _, due = st.take(dc, st.week, seq, q)
        new_arrival = st.next_week + timedelta(weeks=aw)
        late = due is not None and new_arrival > due
        st.put(dc, st.next_week, seq, item, q, due)
        st.moves.append(Move(seq, item, q, "delay", dc, dc, st.week, st.next_week, late))
        remaining -= q * cpp
    return remaining


# ---- step 6 -----------------------------------------------------------------------------------
def pull_forward(st: State, dc: str, wos) -> bool:
    """Pull next-week lines of this DC, shortest items first, until the last container reaches fill.min..fill.max.
    Committed only if fill.min is reached; returns True when pulled."""
    c = st.cube(dc, st.week)
    n = containers(c, st.V)
    if n == 0 or last_container_fill(c, st.V) >= st.fmin - EPS:
        return False
    last = c - (n - 1) * st.V
    need = st.fmin * st.V - last
    room = st.fmax * st.V - last
    cands = [(seq, e[0], e[1]) for seq, e in st.buckets.get((dc, st.next_week), {}).items()]
    cands.sort(key=lambda t: (wos(t[1], dc), t[1], t[0]))
    plan, got = [], 0.0
    for seq, item, qty in cands:
        if got >= need - EPS:
            break
        cpp = st.cpp(item)
        q = min(qty, int((room - got) // cpp + EPS), math.ceil((need - got) / cpp - EPS))
        if q >= 1:
            plan.append((seq, item, q))
            got += q * cpp
    if got < need - EPS:
        return False
    for seq, item, q in plan:
        _, due = st.take(dc, st.next_week, seq, q)
        st.put(dc, st.week, seq, item, q, due)
        st.moves.append(Move(seq, item, q, "pull_in", dc, dc, st.next_week, st.week))
    return True


# ---- run, kpis, rank --------------------------------------------------------------------------
def _rate(dc: str, params: dict) -> float:
    region = params["destination_rate_region"].get(dc)
    return float(params["ocean_rate_usd_per_40hc"][region]) if region else 0.0


def run(lines, items, supply, params: dict, week: date, options: dict | None = None, use_dc_lead_time: bool | None = None) -> dict:
    opt = dict(OPTIONS_ALL if options is None else options)
    udl = bool(params["supply"].get("use_dc_lead_time", False)) if use_dc_lead_time is None else use_dc_lead_time
    st = State(copy.deepcopy(list(lines)), items, params, week)
    before = baseline(st)
    next_before = baseline(st, st.next_week)

    def wos(item, dc):
        return supply.wos(item, dc, week, _arrival_weeks(dc, params, udl))

    for dc in st.dcs():                                                    # steps 3-5
        remaining, cands = find_overflow(st, dc, wos)
        if remaining <= EPS:
            continue
        if opt.get("destination_change", True):
            remaining = change_destination(st, dc, remaining, cands, wos)
        if opt.get("delay", True) and remaining > EPS:
            delay_one_week(st, dc, remaining, cands, wos, udl)
    pulled_dcs = []
    if opt.get("pull_forward", True):                                      # step 6
        for dc in st.dcs():
            if pull_forward(st, dc, wos):
                pulled_dcs.append(dc)
    after = baseline(st)
    next_after = baseline(st, st.next_week)
    return _report(st, before, after, next_before, next_after, opt, udl)


def _report(st: State, before, after, nb, na, opt, udl) -> dict:
    p, V = st.p, st.V
    dcs = sorted(set(before) | set(after))
    cb = sum(before[d]["containers"] for d in before)
    ca = sum(after[d]["containers"] for d in after)
    tcb = sum(before[d]["cube"] for d in before)
    tca = sum(after[d]["cube"] for d in after)
    cost = sum((before.get(d, {}).get("containers", 0) - after.get(d, {}).get("containers", 0)) * _rate(d, p) for d in dcs)
    moves = st.moves
    todos = []
    for dc in dcs:                                                         # step 7: one to-do per affected DC
        mine = [m for m in moves if dc in (m.from_dc, m.to_dc)]
        fill = after[dc]["last_fill"] if dc in after else 1.0
        leftover = dc in after and fill < st.fmin - EPS
        if not mine and not leftover:
            continue
        facts = TodoFacts(
            pulled_fob_usd=sum(m.qty * st.fob(m.item) for m in moves if m.kind == "pull_in" and m.to_dc == dc),
            has_destination_change=any(m.kind == "destination_change" for m in mine),
            delay_misses_po_due=any(m.kind == "delay" and m.late and m.from_dc == dc for m in moves),
            last_container_fill=fill)
        reasons = approval_reasons(facts, p)
        todos.append({"dc": dc, "moves": len(mine), "last_fill": round(fill, 4), "leftover": leftover,
                      "pulled_fob_usd": round(facts.pulled_fob_usd, 2), "needs_approval": bool(reasons), "reasons": reasons})

    def pcs(kind):
        return sum(m.qty for m in moves if m.kind == kind)

    def cube_of(kind):
        return sum(m.qty * st.cpp(m.item) for m in moves if m.kind == kind)

    return {
        "week": st.week.isoformat(), "options": opt, "use_dc_lead_time": udl,
        "kpis": {
            "containers_before": cb, "containers_after": ca,
            "avg_fill_before": round(tcb / (cb * V), 4) if cb else 0.0,
            "avg_fill_after": round(tca / (ca * V), 4) if ca else 0.0,
            "cost_avoided_usd": cost,
            "destination_change_pcs": pcs("destination_change"), "delayed_pcs": pcs("delay"),
            "late_delayed_pcs": sum(m.qty for m in moves if m.kind == "delay" and m.late),
            "pulled_pcs": pcs("pull_in"), "pulled_cube_ft3": round(cube_of("pull_in"), 1),
            "pulled_fob_usd": round(sum(m.qty * st.fob(m.item) for m in moves if m.kind == "pull_in"), 2),
            "changes": len(moves), "todos": len(todos), "todos_needing_approval": sum(t["needs_approval"] for t in todos),
            "next_week_containers_before": sum(v["containers"] for v in nb.values()),
            "next_week_containers_after": sum(v["containers"] for v in na.values()),
        },
        "by_dc": {d: {"before": before.get(d), "after": after.get(d), "next_before": nb.get(d), "next_after": na.get(d)} for d in dcs},
        "todos": todos, "moves": moves,
    }


def rank_options(lines, items, supply, params: dict, week: date, use_dc_lead_time: bool | None = None) -> dict:
    variants = {
        "as_scheduled": {"destination_change": False, "delay": False, "pull_forward": False},
        "all_levers": dict(OPTIONS_ALL),
        "no_destination_change": {"destination_change": False, "delay": True, "pull_forward": True},
        "no_pull_forward": {"destination_change": True, "delay": True, "pull_forward": False},
    }
    return {name: run(lines, items, supply, params, week, opt, use_dc_lead_time) for name, opt in variants.items()}


def plan_week(lines, items, supply, params: dict, week: date, use_dc_lead_time: bool | None = None) -> dict:
    return rank_options(lines, items, supply, params, week, use_dc_lead_time)
