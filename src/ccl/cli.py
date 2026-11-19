from __future__ import annotations
import argparse
from .config import load_params
from .golden import verify


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="ccl")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("verify-golden", help="recompute the reference Dec 21 plan totals and compare with the app")
    p = sub.add_parser("plan", help="(phase 1) plan one vendor-week on a frozen snapshot")
    p.add_argument("--vendor"); p.add_argument("--week"); p.add_argument("--snapshot")
    a = ap.parse_args(argv)
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
