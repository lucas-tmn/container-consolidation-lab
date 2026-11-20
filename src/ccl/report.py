"""Build the static HTML report (pages Main and How it works, English and Vietnamese) from run folders or from a bundle JSON.
No server, no network, no database. Input: runs/<snapshot>_<week>[_lt][_uf]/plan.json + run.json written by 'ccl plan'."""
from __future__ import annotations

import json
import re
from pathlib import Path

from .config import ROOT, load_params
from .report_i18n import TEXTS

TEMPLATE = ROOT / "ui" / "template.html"
MODES = ("ref", "lt", "uf", "lt_uf")
VARIANTS = ("as_scheduled", "all_levers", "no_destination_change", "no_pull_forward")


def _mode_of(run: dict) -> str:
    m = run.get("mode") or ("lt" if run.get("use_dc_lead_time") else "ref")
    return {"ref_uf": "uf"}.get(m, m)


def params_block(params: dict) -> dict:
    return {
        "container_ft3": params["container"]["volume_ft3"], "fill_min": params["fill"]["min"], "fill_max": params["fill"]["max"],
        "short_weeks": params["supply"]["short_below_weeks"], "buffer_weeks": params["supply"]["arrival_buffer_weeks"],
        "pull_fob_usd": params["approvals"]["pull_forward_fob_usd"],
        "rate_west": params["ocean_rate_usd_per_40hc"]["west"], "rate_east": params["ocean_rate_usd_per_40hc"]["east"],
        "lead_time_weeks": params.get("lead_time_weeks_edw", {}),
    }


def collect_runs(runs_dir: Path, snapshot: str | None = None, params: dict | None = None) -> dict:
    params = params or load_params()
    found = []
    for d in sorted(Path(runs_dir).glob("*")):
        if (d / "plan.json").exists() and (d / "run.json").exists():
            run = json.loads((d / "run.json").read_text(encoding="utf-8"))
            found.append((d, run))
    if not found:
        raise FileNotFoundError(f"no run folders with plan.json and run.json in {runs_dir}")
    snap = snapshot or max(r["snapshot"] for _, r in found)
    found = [(d, r) for d, r in found if r["snapshot"] == snap]
    if not found:
        raise FileNotFoundError(f"no runs for snapshot {snap}")
    weeks: dict = {}
    horizon = {"firm": {}, "planned": {}}
    vendor, generated, commit, version = "", "", "", ""
    for d, run in found:
        res = json.loads((d / "plan.json").read_text(encoding="utf-8"))["results"]
        mode = _mode_of(run)
        slot = weeks.setdefault(run["week"], {"modes": {}})["modes"].setdefault(mode, {"variants": {}, "wos": run.get("wos_summary")})
        for name, r in res.items():
            slot["variants"][name] = {"kpis": r["kpis"], "by_dc": r.get("by_dc"), "todos": r.get("todos"), "moves": r.get("moves")}
        for wk, v in (run.get("plannable_weeks") or {}).items():
            horizon["firm"][wk] = {"week": wk, "lines": v["firm_po_lines"], "auto": v["auto_po_lines"],
                                   "container_eq": v["container_eq"], "plannable": v["plannable"]}
        horizon["planned"].update(run.get("planned_by_week") or {})
        vendor = vendor or run.get("vendor", "")
        generated = max(generated, run.get("run_utc", ""))
        commit, version = run.get("git_commit", commit), run.get("ccl_version", version)
    return {
        "meta": {"snapshot": snap, "vendor": vendor, "generated_utc": generated, "git_commit": commit, "partial": False, "note": "",
                 "dc_count": _dc_count(weeks), "params": params_block(params)},
        "horizon": {"firm": sorted(horizon["firm"].values(), key=lambda x: x["week"]),
                    "planned": [{"week": k, "container_eq": v} for k, v in sorted(horizon["planned"].items())]},
        "weeks": dict(sorted(weeks.items())),
    }


def _dc_count(weeks: dict) -> int:
    n = 0
    for w in weeks.values():
        for m in w["modes"].values():
            for v in m["variants"].values():
                if v.get("by_dc"):
                    n = max(n, len(v["by_dc"]))
    return n


def build_html(bundle: dict, lang: str, template: Path = TEMPLATE) -> str:
    if lang not in TEXTS:
        raise ValueError(f"unknown language {lang}")
    html = template.read_text(encoding="utf-8")
    safe = lambda obj: json.dumps(obj, ensure_ascii=False).replace("</", "<\\/")
    return (html.replace("__LANG__", lang).replace("__I18N__", safe(TEXTS)).replace("__DATA__", safe(bundle)))


def write_report(bundle: dict, out: Path) -> list[Path]:
    out.mkdir(parents=True, exist_ok=True)
    paths = []
    for lang in ("en", "vi"):
        p = out / f"container_lab_{lang}.html"
        p.write_text(build_html(bundle, lang), encoding="utf-8")
        paths.append(p)
    (out / "bundle.json").write_text(json.dumps(bundle, ensure_ascii=False, indent=1), encoding="utf-8")
    return paths


def main_report(a) -> int:
    try:
        if a.bundle:
            bundle = json.loads(Path(a.bundle).read_text(encoding="utf-8"))
        else:
            bundle = collect_runs(Path(a.runs), a.snapshot)
    except FileNotFoundError as e:
        print(f"stopped: {e}. Run 'python -m ccl plan --snapshot ... --week ...' first.")
        return 2
    paths = write_report(bundle, Path(a.out))
    for p in paths:
        print(f"written {p}")
    print(f"snapshot {bundle['meta']['snapshot']}, weeks: {', '.join(bundle['weeks'])} (git-ignored output)")
    return 0
