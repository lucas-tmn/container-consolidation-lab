"""Load a snapshot folder (docs/04) into engine inputs. Weeks of supply, plannable weeks. No database access."""
from __future__ import annotations

import csv
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path

from .engine import PlanLine, week_monday
from .metrics import weeks_of_supply


def _d(s: str) -> date:
    return date.fromisoformat(s[:10])


def _rows(path: Path):
    with open(path, encoding="utf-8", newline="") as f:
        yield from csv.DictReader(f)


def load_items(snap: Path) -> dict[str, tuple[float, float]]:
    return {r["ITEM"]: (float(r["CUBES"]), float(r["FOB_PRICE"] or 0)) for r in _rows(snap / "item_master.csv")}


def load_lines(snap: Path, params: dict) -> tuple[list[PlanLine], dict]:
    """Planned lines of mapped DCs. SEQ is assigned by sorted order (ship date, warehouse, item, qty): stable for one snapshot."""
    wmap = {str(k): v for k, v in params["warehouse_map"].items()}
    excluded = {str(x) for x in params["excluded_warehouses"]}
    direct = {str(x) for x in params.get("container_direct", [])}
    raw = sorted(((_d(r["SHIP_DATE"]), r["WHSE"].strip(), r["ITEM"].strip(), int(float(r["QTY"])), _d(r["DUE_DATE"]) if r["DUE_DATE"] else None)
                  for r in _rows(snap / "planned_lines.csv")), key=lambda t: (t[0], t[1], t[2], t[3]))
    lines, skipped = [], defaultdict(int)
    for i, (ship, wh, item, qty, due) in enumerate(raw, start=1):
        if wh in excluded or wh in direct or wh not in wmap:
            skipped[wh] += 1
            continue
        lines.append(PlanLine(i, item, qty, wmap[wh], week_monday(ship), due))
    return lines, {"skipped_lines_by_warehouse": dict(skipped), "lines": len(lines)}


class SupplyModel:
    """WOS of item at DC = projected shippable inventory at arrival / weekly forecast (reference app rule, docs/03)."""

    def __init__(self, inventory: dict, forecast: dict, dc_whs: dict, missing: float = 0.0, unknown_if_no_forecast: bool = False):
        self.inv = inventory          # (item, whse) -> sorted [(week_ending, shippable_inv)]
        self.fc = forecast            # (item, whse) -> weekly forecast
        self.dc_whs = dc_whs          # dc -> [whse]
        self.missing = missing
        self.unknown_if_no_forecast = unknown_if_no_forecast
        self.cache: dict = {}

    @classmethod
    def from_snapshot(cls, snap: Path, params: dict) -> "SupplyModel":
        inv = defaultdict(list)
        for r in _rows(snap / "inventory_projection.csv"):
            inv[(r["ITEM"].strip(), r["WHSE"].strip())].append((_d(r["WEEK_ENDING"]), float(r["SHIPPABLE_INV"] or 0)))
        for v in inv.values():
            v.sort()
        offs = params["forecast"]["month_offsets"]
        fc: dict = defaultdict(float)
        for r in _rows(snap / "forecast_m.csv"):
            vals = [float(r[f"FC{k}"] or 0) for k in offs]
            fc[(r["ITEM"].strip(), r["LOC"].strip())] += sum(vals) / len(vals) * 12.0 / 52.0   # channels summed
        dc_whs = defaultdict(list)
        for w, dc in params["warehouse_map"].items():
            dc_whs[dc].append(str(w))
        return cls(dict(inv), dict(fc), dict(dc_whs), float(params["supply"]["missing_data_weeks_of_supply"]),
                   bool(params["supply"].get("missing_forecast_is_unknown", False)))

    def wos(self, item: str, dc: str, ship_week: date, arrival_weeks: int):
        key = (item, dc, ship_week, arrival_weeks)
        if key in self.cache:
            return self.cache[key]
        arrival = ship_week + timedelta(weeks=arrival_weeks)
        inv_total, fc_total, have = 0.0, 0.0, False
        for wh in self.dc_whs.get(dc, []):
            series = self.inv.get((item, wh), [])
            at = next((v for we, v in series if we >= arrival), None)
            if at is not None:
                inv_total += max(at, 0.0)
                have = True
            fc_total += self.fc.get((item, wh), 0.0)
        if self.unknown_if_no_forecast and fc_total <= 0:
            out = None            # lab option: no forecast means unknown, not 'short' (reference app counts it as 0 weeks)
        else:
            out = weeks_of_supply(inv_total if have else None, fc_total, self.missing)
        self.cache[key] = out
        return out


def plannable_weeks(snap: Path, params: dict) -> dict:
    """A ship week is plannable only if the vendor has no firm PO for the mapped DCs in that ETD week (docs/06, 20 Nov findings)."""
    wmap = {str(k) for k in params["warehouse_map"]} - {str(x) for x in params["excluded_warehouses"]}
    out: dict = defaultdict(lambda: {"firm_po_lines": 0, "auto_po_lines": 0, "container_eq": 0.0})
    path = snap / "firm_pos.csv"
    if not path.exists():
        return {}
    for r in _rows(path):
        if r["WHSE"].strip() in wmap:
            w = out[_d(r["ETD_WEEK"])]
            w["firm_po_lines"] += int(r["PO_LINES"])
            w["auto_po_lines"] += int(r["AUTO_PO_LINES"])
            w["container_eq"] += float(r["CONTAINER_EQ"])
    return {k: {**v, "plannable": v["firm_po_lines"] == 0} for k, v in sorted(out.items())}


def is_plannable(plannable: dict, week: date) -> bool:
    """A week with no firm PO of the mapped DCs is plannable. Without a firm_pos table the answer is unknown: callers must show that."""
    return plannable.get(week, {}).get("plannable", True)
