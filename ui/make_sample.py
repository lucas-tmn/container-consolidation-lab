"""Writes ui/sample/bundle_demo.json: a SYNTHETIC bundle (invented items DEMO-xxx) so the report can be opened without EDW access.
Horizon and WOS shares come from aggregate findings of 19-20 Nov 2026; moves and DC numbers are invented."""
import json, random
from pathlib import Path
random.seed(7)
DCS = ["Advance", "Arcadia", "Ecru", "Leesport", "Mesquite", "Redlands"]
before = {"Advance": (9, .709), "Arcadia": (11, .4535), "Ecru": (18, .288), "Leesport": (6, .9131), "Mesquite": (22, .9311), "Redlands": (10, .1975)}
after = {"Advance": (8, .9996), "Arcadia": (10, .9999), "Ecru": (18, .9997), "Leesport": (6, .9998), "Mesquite": (22, .9999), "Redlands": (9, .9977)}
def dc(d):
    return {"before": {"cube": 2400 * (before[d][0] - 1 + before[d][1]), "containers": before[d][0], "last_fill": before[d][1], "avg_fill": 0},
            "after": {"cube": 2400 * (after[d][0] - 1 + after[d][1]), "containers": after[d][0], "last_fill": after[d][1], "avg_fill": 0}}
moves = []
for i in range(1, 21):
    s, t = random.choice([("Advance", "Ecru"), ("Arcadia", "Ecru"), ("Redlands", "Mesquite"), ("Arcadia", "Leesport")])
    q = random.randint(5, 60)
    moves.append({"seq": i * 7, "item": f"DEMO-{i:03d}", "qty": q, "kind": "destination_change", "from_dc": s, "to_dc": t,
                  "from_week": "2026-12-28", "to_week": "2026-12-28", "late": False, "cube_ft3": q * 4.2})
moves.append({"seq": 150, "item": "DEMO-099", "qty": 12, "kind": "delay", "from_dc": "Redlands", "to_dc": "Redlands",
              "from_week": "2026-12-28", "to_week": "2027-01-04", "late": True, "cube_ft3": 50.4})
def kp(cb, ca, nb, na, chg, appr):
    return {"containers_before": cb, "containers_after": ca, "avg_fill_before": .85, "avg_fill_after": .93, "cost_avoided_usd": (cb - ca) * 9000,
            "destination_change_pcs": sum(m["qty"] for m in moves if m["kind"] == "destination_change"), "delayed_pcs": 12, "late_delayed_pcs": 12,
            "pulled_pcs": 0, "pulled_cube_ft3": 0, "pulled_fob_usd": 0, "changes": chg, "lines_touched": chg, "small_moves_le_2pcs": 0,
            "todos": chg, "todos_needing_approval": appr, "next_week_containers_before": nb, "next_week_containers_after": na}
v = {"all_levers": {"kpis": kp(76, 73, 30, 31, 21, 21), "by_dc": {d: dc(d) for d in DCS}, "todos": [], "moves": moves},
     "no_pull_forward": {"kpis": kp(76, 73, 30, 31, 21, 21), "by_dc": {d: dc(d) for d in DCS}, "todos": [], "moves": moves},
     "no_destination_change": {"kpis": kp(76, 76, 30, 30, 0, 0), "by_dc": {d: {"before": dc(d)["before"], "after": dc(d)["before"]} for d in DCS}, "todos": [], "moves": []}}
bundle = {"meta": {"snapshot": "demo", "vendor": "DEMO VENDOR", "generated_utc": "2026-11-20T00:00:00+00:00", "git_commit": "", "partial": True,
                   "note": "synthetic demo data (invented items and moves). Run ccl plan and ccl report for real results.", "dc_count": 6,
                   "params": {"container_ft3": 2400, "fill_min": .9, "fill_max": 1.0, "short_weeks": 4, "buffer_weeks": 5, "pull_fob_usd": 25000,
                              "rate_west": 8007, "rate_east": 10166, "lead_time_weeks": {"Arcadia": 9, "Advance": 8, "Leesport": 7, "Ecru": 7, "Mesquite": 6, "Redlands": 5}}},
          "horizon": {"firm": [{"week": w, "lines": 1, "auto": 1, "container_eq": c, "plannable": False} for w, c in
                               [("2026-11-23", 60.0), ("2026-11-30", 22.33), ("2026-12-07", 43.76), ("2026-12-14", 116.38), ("2026-12-21", 111.35)]],
                      "planned": [{"week": w, "container_eq": c} for w, c in [("2026-12-28", 73.49), ("2027-01-04", 32.96), ("2027-01-11", 42.61)]]},
          "weeks": {"2026-12-28": {"modes": {"ref": {"variants": v, "wos": {"lines": 427, "ok": 211, "zero_inventory": 160, "no_forecast": 56, "no_inventory": 0}}}}}}
Path(__file__).with_name("sample").joinpath("bundle_demo.json").write_text(json.dumps(bundle, indent=1), encoding="utf-8")
