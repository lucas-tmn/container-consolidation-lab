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
    p = sub.add_parser("plan", help="(phase 1) plan one vendor-week on a frozen snapshot")
    p.add_argument("--vendor"); p.add_argument("--week"); p.add_argument("--snapshot")
    sub.add_parser("doctor", help="check the local setup for refresh: python, ODBC driver, env vars, EDW time window")
    r = sub.add_parser("refresh", help="read-only pull from EDW into snapshots/<run-date>/ (VPN + interactive sign-in)")
    r.add_argument("--vendor", required=True, help="exact vendor NAME, for example 'GRAND WOOD VN CO LTD'")
    r.add_argument("--ship-from", required=True, help="first ship date, YYYY-MM-DD")
    r.add_argument("--ship-to", required=True, help="end ship date (exclusive), YYYY-MM-DD")
    r.add_argument("--run-date", default=None, help="folder name and default run day, YYYY-MM-DD (default: today)")
    r.add_argument("--inventory-run-date", default=None, help="SupplyPlanDetail run day (default: run date)")
    r.add_argument("--forecast-date", default=None, help="forecast FileDate day (default: run date)")
    r.add_argument("--out", default="snapshots", help="output root (git-ignored)")
    r.add_argument("--dry-run", action="store_true", help="validate the queries only; no connection")
    r.add_argument("--allow-business-hours", action="store_true",
                   help="override the Mon-Fri 08:00-18:00 Central rule (only if the business agreed)")
    a = ap.parse_args(argv)
    if a.cmd == "doctor":
        return _doctor()
    if a.cmd == "refresh":
        return _refresh(a)
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
        from .engine import plan_week
        plan_week(a.snapshot, a.vendor, a.week, params)
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
    from .snapshot import QUERIES, build_snapshot, validate_all
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
    values = {"vendor": a.vendor, "ship_from": a.ship_from, "ship_to": a.ship_to,
              "inventory_run_date": a.inventory_run_date or run, "forecast_date": a.forecast_date or run,
              # week endings: from the ship window start up to 8 weeks past its end (supply is read at arrival)
              "week_from": a.ship_from, "week_to": (ship_to + timedelta(weeks=8)).isoformat()}
    try:
        manifest = build_snapshot(connect_edw, Path(a.out) / run, values)
    except ConnectionConfigError as e:
        print(f"cannot connect: {e}")
        return 4
    for t in manifest["tables"]:
        print(f"{t['name']:<22} rows={t['rows']:>8}" + (f"   WARNING {t['warning']}" if t["warning"] else ""))
    print(f"snapshot written to {Path(a.out) / run} (not committed: git-ignored)")
    return 0
