from __future__ import annotations
import argparse
from .config import load_params
from .golden import verify
from datetime import date, datetime, timedelta, timezone
from pathlib import Path


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="ccl")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("verify-golden", help="recompute the reference Dec 21 plan totals and compare with the app")
    p = sub.add_parser("plan", help="plan one ship week on a frozen snapshot (all four option sets)")
    p.add_argument("--snapshot", required=True, help="snapshot folder, for example snapshots/2026-11-19")
    p.add_argument("--week", required=True, help="any date in the ship week, YYYY-MM-DD")
    p.add_argument("--lead-time", action="store_true", help="lab option: measure supply at ship week + DC lead time instead of the fixed buffer")
    p.add_argument("--out", default="runs", help="output root (git-ignored)")
    p.add_argument("--unknown-forecast", action="store_true", help="lab option: an item without forecast has unknown supply (never 'needs it', never delayed) instead of 0 weeks")
    p.add_argument("--allow-unplannable", action="store_true", help="plan a week that already has firm POs (not recommended)")
    rp = sub.add_parser("report", help="build the HTML report (EN and VI, pages Main and How it works) from runs/ or from a bundle file")
    rp.add_argument("--runs", default="runs", help="folder with the run folders written by 'ccl plan'")
    rp.add_argument("--snapshot", default=None, help="snapshot name to report (default: the newest in runs)")
    rp.add_argument("--bundle", default=None, help="use a prepared bundle JSON instead of runs (for example ui/sample/bundle_2026-11-19.json)")
    rp.add_argument("--out", default="report", help="output folder (git-ignored)")
    sub.add_parser("doctor", help="check the local setup for refresh: python, ODBC driver, env vars, EDW time window")
    r = sub.add_parser("refresh", help="read-only pull from EDW into snapshots/<run-date>/ (VPN + interactive sign-in)")
    r.add_argument("--vendor", required=True, help="exact vendor NAME, for example 'GRAND WOOD VN CO LTD'")
    r.add_argument("--ship-from", required=True, help="first ship date, YYYY-MM-DD")
    r.add_argument("--ship-to", required=True, help="end ship date (exclusive), YYYY-MM-DD")
    r.add_argument("--run-date", default=None, help="upper bound for 'latest' and default folder name, YYYY-MM-DD (default: today)")
    r.add_argument("--inventory-run-date", default="latest", help="SupplyPlanDetail run day, YYYY-MM-DD or 'latest' (default: latest within 7 days)")
    r.add_argument("--forecast-date", default="latest", help="forecast FileDate day, YYYY-MM-DD or 'latest' (default: latest within 7 days)")
    r.add_argument("--out", default="snapshots", help="output root (git-ignored)")
    r.add_argument("--dry-run", action="store_true", help="validate the queries only; no connection")
    r.add_argument("--allow-business-hours", action="store_true",
                   help="override the Mon-Fri 08:00-18:00 Central rule (only if the business agreed)")
    a = ap.parse_args(argv)
    if a.cmd == "doctor":
        return _doctor()
    if a.cmd == "refresh":
        return _refresh(a)
    if a.cmd == "report":
        from .report import main_report
        return main_report(a)
    params = load_params()
    if a.cmd == "verify-golden":
        rows = verify(params)
        w = max(len(r[0]) for r in rows)
        for name, ours, app, ok in rows:
            print(f"{name:<{w}}  ours={ours:>9}  app={app:>9}  {'OK' if ok else 'DIFF'}")
        bad = [r for r in rows if not r[3]]
        print(f"\n{len(rows) - len(bad)}/{len(rows)} checks match; pending (need snapshot): containers 15->14, avg fill 69%->97%, next-week containers")
        return 1 if bad else 0
    if a.cmd == "plan":
        return _plan(a, params)
    return 0


def _aw(dc, params, use_lt):
    from .engine import _arrival_weeks
    return _arrival_weeks(dc, params, use_lt)


def _manifest_vendor(snap: Path) -> str:
    import json
    try:
        return json.loads((snap / "manifest.json").read_text(encoding="utf-8"))["parameters"]["vendor"]
    except Exception:
        return ""


def _plan(a, params) -> int:
    import hashlib, json, subprocess
    from .engine import plan_week, week_monday
    from .supply import SupplyModel, is_plannable, load_items, load_lines, planned_by_week, plannable_weeks, wos_summary
    snap = Path(a.snapshot)
    week = week_monday(date.fromisoformat(a.week))
    lines, info = load_lines(snap, params)
    pw = plannable_weeks(snap, params)
    if not (snap / "firm_pos.csv").exists():
        print("WARNING: no firm_pos.csv in this snapshot; plannable weeks unknown (refresh again).")
    elif not is_plannable(pw, week) and not a.allow_unplannable:
        print(f"stopped: week {week} already has firm POs for the mapped DCs ({pw[week]['firm_po_lines']} lines, "
              f"{pw[week]['container_eq']:.2f} container-eq). Plannable weeks start later; pass --allow-unplannable to override.")
        return 6
    if a.unknown_forecast:
        params = {**params, "supply": {**params["supply"], "missing_forecast_is_unknown": True}}
    items = load_items(snap)
    supply = SupplyModel.from_snapshot(snap, params)
    res = plan_week(lines, items, supply, params, week, use_dc_lead_time=a.lead_time)
    print(f"snapshot {snap.name}  week {week}  supply measured at ship week + {'DC lead time' if a.lead_time else str(params['supply']['arrival_buffer_weeks']) + ' weeks (reference rule)'}"
          f"{'; unknown forecast = unknown' if a.unknown_forecast else ''}")
    cols = ["containers_before", "containers_after", "avg_fill_before", "avg_fill_after", "cost_avoided_usd", "destination_change_pcs",
            "delayed_pcs", "late_delayed_pcs", "pulled_pcs", "pulled_fob_usd", "changes", "lines_touched", "small_moves_le_2pcs", "todos", "todos_needing_approval",
            "next_week_containers_before", "next_week_containers_after"]
    print(f"{'':<28}" + "".join(f"{n[:14]:>15}" for n in res))
    for c in cols:
        print(f"{c:<28}" + "".join(f"{r['kpis'][c]:>15}" for r in res.values()))
    out = Path(a.out) / f"{snap.name}_{week}{'_lt' if a.lead_time else ''}{'_uf' if a.unknown_forecast else ''}"
    out.mkdir(parents=True, exist_ok=True)
    def conv(r):
        return {**r, "moves": [{**m.__dict__, "from_week": str(m.from_week), "to_week": str(m.to_week),
                                "cube_ft3": round(m.qty * items[m.item][0], 1)} for m in r["moves"]]}
    try:
        commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True, timeout=5).stdout.strip()
    except Exception:
        commit = ""
    cfg_hash = hashlib.sha256((Path(__file__).resolve().parents[2] / "config" / "params.yaml").read_bytes()).hexdigest()
    (out / "plan.json").write_text(json.dumps({"results": {k: conv(v) for k, v in res.items()}}, indent=1, default=str), encoding="utf-8")
    (out / "run.json").write_text(json.dumps({
        "snapshot": snap.name, "week": str(week), "use_dc_lead_time": a.lead_time, "config_sha256": cfg_hash, "git_commit": commit,
        "run_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"), "load_info": info,
        "plannable_weeks": {str(k): v for k, v in pw.items()},
        "planned_by_week": planned_by_week(lines, items, float(params["container"]["volume_ft3"])),
        "wos_summary": wos_summary(lines, supply, week, {d: _aw(d, params, a.lead_time) for d in {l.dc for l in lines}}),
        "vendor": _manifest_vendor(snap), "mode": ("lt" if a.lead_time else "ref") + ("_uf" if a.unknown_forecast else "")},
        indent=1, default=str), encoding="utf-8")
    print(f"written {out}/plan.json and run.json (git-ignored)")
    return 0


def _doctor() -> int:
    import os, sys
    from .sqlguard import in_business_window
    ok = True
    def line(name, good, detail):
        nonlocal ok
        ok = ok and good
        print(f"{'OK  ' if good else 'FIX '} {name}: {detail}")
    line("python", sys.version_info >= (3, 10), sys.version.split()[0])
    try:
        import pyodbc
        drivers = [d for d in pyodbc.drivers() if "SQL Server" in d]
        line("pyodbc", True, pyodbc.version)
        line("odbc driver", bool(drivers), ", ".join(drivers) or "none found: install Microsoft ODBC Driver 18 for SQL Server")
    except ImportError:
        line("pyodbc", False, "missing: pip install -e .[edw]")
    for v in ("CCL_EDW_SERVER", "CCL_EDW_DATABASE"):
        line(v, bool(os.environ.get(v)), "set" if os.environ.get(v) else "not set (value is never printed)")
    blocked = in_business_window()
    print(f"{'WAIT' if blocked else 'OK  '} edw window: " + ("inside Mon-Fri 08:00-18:00 Central, refresh will refuse"
          if blocked else "outside Mon-Fri 08:00-18:00 Central, refresh allowed"))
    print("note: EDW needs VPN and an interactive Entra sign-in; no password or token is stored by this tool")
    return 0 if ok else 1


def _refresh(a) -> int:
    from .db import ConnectionConfigError, connect_edw
    from .snapshot import QUERIES, build_snapshot, resolve_latest, validate_all
    from .sqlguard import SqlGuardError, in_business_window
    try:
        validate_all()
    except SqlGuardError as e:
        print(f"refused: {e}")
        return 2
    print(f"queries validated read-only: {', '.join(q.name for q in QUERIES)}")
    if a.dry_run:
        return 0
    if in_business_window() and not a.allow_business_hours:
        print("refused: inside Mon-Fri 08:00-18:00 US Central. Run later or pass --allow-business-hours if agreed.")
        return 3
    run = a.run_date or date.today().isoformat()
    ship_from = date.fromisoformat(a.ship_from)
    ship_to = date.fromisoformat(a.ship_to)
    values = {"vendor": a.vendor, "ship_from": a.ship_from, "ship_to": a.ship_to, "run_date": run,
              "inventory_run_date": a.inventory_run_date, "forecast_date": a.forecast_date,
              # week endings: from the ship window start up to 8 weeks past its end (supply is read at arrival)
              "week_from": a.ship_from, "week_to": (ship_to + timedelta(weeks=8)).isoformat()}
    try:
        conn = connect_edw()
        try:
            values = resolve_latest(conn, values)
        except LookupError as e:
            conn.close()
            print(f"stopped: {e}")
            return 5
        folder = a.run_date or values["inventory_run_date"]    # folder is named after the data day
        print(f"inventory run day: {values['inventory_run_date']}   forecast snapshot day: {values['forecast_date']}")
        manifest = build_snapshot(lambda: conn, Path(a.out) / folder, values)
    except ConnectionConfigError as e:
        print(f"cannot connect: {e}")
        return 4
    for t in manifest["tables"]:
        print(f"{t['name']:<22} rows={t['rows']:>8}" + (f"   WARNING {t['warning']}" if t["warning"] else ""))
    print(f"snapshot written to {Path(a.out) / folder} (not committed: git-ignored)")
    return 0
