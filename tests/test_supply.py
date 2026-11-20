import csv
from datetime import date
from pathlib import Path

from ccl.config import load_params
from ccl.supply import SupplyModel, is_plannable, load_items, load_lines, plannable_weeks

P = load_params()


def _w(path: Path, header, rows):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)


def _snap(tmp_path):
    _w(tmp_path / "planned_lines.csv", ["SHIP_DATE", "DUE_DATE", "ITEM", "WHSE", "QTY", "LOAD_DATE"], [
        ["2026-12-30", "2027-02-10", "X1", "5", "10", "2026-11-19"],
        ["2026-12-30", "2027-02-10", "X1", "335", "99", "2026-11-19"],
        ["2026-12-31", "2027-03-01", "X2", "1", "5", "2026-11-19"],
        ["2026-12-31", "2027-03-01", "X2", "XX", "5", "2026-11-19"]])
    _w(tmp_path / "item_master.csv", ["ITEM", "CUBES", "FOB_PRICE", "CONTAINER_VOLUME"], [["X1", "4.0", "10", "2400"], ["X2", "2.0", "5", "2400"]])
    _w(tmp_path / "inventory_projection.csv", ["RUN_DATE", "ITEM", "WHSE", "WEEK_ENDING", "SHIPPABLE_INV", "NET_FCST", "SAFETY_STK"], [
        ["2026-11-19", "X1", "5", "2027-01-30", "-5", "0", "0"], ["2026-11-19", "X1", "5", "2027-02-06", "100", "0", "0"]])
    ch = ["FILE_DATE", "ITEM", "LOC", "CHANNEL"] + [f"FC{i}" for i in range(12)]
    row = lambda ch_, v: ["2026-11-19", "X1", "5", ch_] + [str(v)] * 12
    _w(tmp_path / "forecast_m.csv", ch, [row("ECOMM", 52), row("NFM", 52)])
    _w(tmp_path / "firm_pos.csv", ["ETD_WEEK", "WHSE", "PO_LINES", "AUTO_PO_LINES", "QTY", "CONTAINER_EQ"], [
        ["2026-12-21", "5", "10", "9", "100", "2.5"], ["2026-12-21", "C", "3", "0", "10", "0.5"], ["2026-12-28", "C", "6", "0", "10", "1.0"],
        ["2026-12-21", "335", "50", "0", "100", "9.0"]])
    return tmp_path


def test_load_lines_maps_excludes_and_assigns_seq(tmp_path):
    lines, info = load_lines(_snap(tmp_path), P)
    assert [(l.seq, l.item, l.dc, l.week) for l in lines] == [(2, "X1", "Redlands", date(2026, 12, 28)), (3, "X2", "Arcadia", date(2026, 12, 28))]
    assert info["skipped_lines_by_warehouse"] == {"335": 1, "XX": 1}


def test_items_and_wos(tmp_path):
    snap = _snap(tmp_path)
    assert load_items(snap)["X1"] == (4.0, 10.0)
    s = SupplyModel.from_snapshot(snap, P)
    # weekly forecast = 2 channels x 52 x 12/52 = 24; arrival 28 Dec + 5 weeks = 1 Feb -> week ending 6 Feb: inventory 100
    assert abs(s.wos("X1", "Redlands", date(2026, 12, 28), 5) - 100 / 24) < 1e-9
    assert s.wos("X1", "Redlands", date(2026, 12, 28), 4) == 0.0       # inventory at 30 Jan is negative -> 0 supply
    assert s.wos("X9", "Redlands", date(2026, 12, 28), 5) == 0.0       # no data -> 0 (reference app rule)


def test_plannable_weeks(tmp_path):
    pw = plannable_weeks(_snap(tmp_path), P)
    assert pw[date(2026, 12, 21)]["plannable"] is False and pw[date(2026, 12, 21)]["auto_po_lines"] == 9
    assert date(2026, 12, 28) not in pw        # only unmapped warehouse C has POs that week
    assert is_plannable(pw, date(2026, 12, 28)) and not is_plannable(pw, date(2026, 12, 21))


def test_cli_plan_end_to_end(tmp_path, monkeypatch, capsys):
    from ccl.cli import main
    (tmp_path / "s").mkdir()
    snap = _snap(tmp_path / "s")
    monkeypatch.chdir(tmp_path)
    assert main(["plan", "--snapshot", str(snap), "--week", "2026-12-30", "--out", str(tmp_path / "runs")]) == 0
    out = capsys.readouterr().out
    assert "containers_before" in out and (tmp_path / "runs" / "s_2026-12-28" / "run.json").exists()
    assert main(["plan", "--snapshot", str(snap), "--week", "2026-12-23", "--out", str(tmp_path / "runs")]) == 6   # firm POs that week
