"""Golden data: the reference app's Dec 21 plan (lines only, no PO numbers) and the app's displayed numbers."""
from __future__ import annotations
import csv
from collections import defaultdict
from pathlib import Path
from .config import ROOT
from .metrics import container_eq
from .rules import TodoFacts, needs_approval

GOLDEN = ROOT / "data" / "golden"
DESTS = ["Mesquite", "Advance", "Arcadia", "Leesport"]

# Numbers displayed by the reference app (screenshots + Impact_of_this_plan.xlsx, 19 Nov 2026).
APP = {
    "pcs": {"Mesquite": 291, "Advance": 350, "Arcadia": 322, "Leesport": 294}, "total_pcs": 1257,
    "cube": {"Mesquite": 2138, "Advance": 2068, "Arcadia": 1771, "Leesport": 1531},
    "fob": {"Mesquite": 33711, "Advance": 37509, "Arcadia": 29103, "Leesport": 27583},
    "changes": 47, "move_cube": 32, "cost_avoided": 8007, "approvals": 4,
    "containers": (15, 14), "avg_fill": (0.69, 0.97),
    "next_week_containers": {"Mesquite": (9, 8), "Advance": (12, 11), "Arcadia": (18, 17), "Leesport": (7, 6)},
}


def load_items() -> dict[str, tuple[float, float]]:
    out = {}
    with open(GOLDEN / "item_master_subset.csv", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            out[r["item"]] = (float(r["cube_ft3_per_piece"]), float(r["fob_usd_per_piece"]))
    return out


def load_lines() -> list[dict]:
    with open(GOLDEN / "dec21_plan_lines.csv", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def recompute(params: dict) -> dict:
    items = load_items()
    lines = load_lines()
    agg = defaultdict(lambda: {"pcs": 0, "cube": 0.0, "fob": 0.0})
    move_cube = 0.0
    for l in lines:
        q = int(l["qty"]); c, p = items[l["item"]]
        if l["change_type"] == "pull_in":
            a = agg[l["destination"]]
            a["pcs"] += q; a["cube"] += q * c; a["fob"] += q * p
        elif l["change_type"] == "destination_change":
            move_cube += q * c
    approvals = 0
    for d in DESTS:
        t = TodoFacts(pulled_fob_usd=agg[d]["fob"], has_destination_change=(d == "Leesport"))
        approvals += needs_approval(t, params)
    return {"agg": dict(agg), "changes": len(lines), "move_cube": move_cube,
            "approvals": approvals, "cost_avoided": params["ocean_rate_usd_per_40hc"]["west"],
            "container_eq": {d: container_eq(agg[d]["cube"], params["container"]["volume_ft3"]) for d in DESTS}}


def verify(params: dict) -> list[tuple[str, float, float, bool]]:
    r = recompute(params); rows = []
    for d in DESTS:
        rows.append((f"pcs {d}", r["agg"][d]["pcs"], APP["pcs"][d], r["agg"][d]["pcs"] == APP["pcs"][d]))
    tot = sum(r["agg"][d]["pcs"] for d in DESTS)
    rows.append(("pcs total", tot, APP["total_pcs"], tot == APP["total_pcs"]))
    for d in DESTS:
        rows.append((f"ft3 {d}", round(r["agg"][d]["cube"]), APP["cube"][d], abs(r["agg"][d]["cube"] - APP["cube"][d]) <= 1))
    for d in DESTS:
        rows.append((f"FOB {d}", round(r["agg"][d]["fob"]), APP["fob"][d], abs(r["agg"][d]["fob"] - APP["fob"][d]) <= 1.5))
    rows.append(("PO changes", r["changes"], APP["changes"], r["changes"] == APP["changes"]))
    rows.append(("move ft3", round(r["move_cube"]), APP["move_cube"], abs(r["move_cube"] - APP["move_cube"]) <= 0.5))
    rows.append(("cost avoided", r["cost_avoided"], APP["cost_avoided"], r["cost_avoided"] == APP["cost_avoided"]))
    rows.append(("approvals", r["approvals"], APP["approvals"], r["approvals"] == APP["approvals"]))
    return rows
