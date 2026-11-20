"""Build a frozen local snapshot from read-only queries. Row data stays under snapshots/ (git-ignored)."""
from __future__ import annotations
import csv, hashlib, json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from . import __version__
from .sqlguard import check_output_columns, validate_select

SQL_DIR = Path(__file__).resolve().parents[2] / "sql" / "snapshot"


@dataclass(frozen=True)
class Query:
    name: str          # output file stem
    file: str          # file under sql/snapshot
    params: tuple      # parameter names, in the order of the ? placeholders
    query_id: str      # evidence-log id or label


QUERIES = [
    Query("planned_lines", "10_planned_lines.sql", ("vendor", "ship_from", "ship_to"), "SNAP-10"),
    Query("item_master", "11_item_master.sql", ("vendor", "ship_from", "ship_to"), "SNAP-11"),
    Query("inventory_projection", "12_inventory_projection.sql",
          ("vendor", "ship_from", "ship_to", "inventory_run_date", "week_from", "week_to"), "SNAP-12"),
    Query("forecast_m", "13_forecast_m.sql", ("vendor", "ship_from", "ship_to", "forecast_date", "forecast_date"), "SNAP-13"),
]


PROBES = {
    "inventory_run_date": Query("probe_inventory_run", "20_probe_inventory_run.sql", ("run_date", "run_date"), "PROBE-20"),
    "forecast_date": Query("probe_forecast_date", "21_probe_forecast_date.sql", ("run_date", "run_date"), "PROBE-21"),
}


def resolve_latest(conn, values: dict, sql_dir: Path = SQL_DIR) -> dict:
    """Replace any value equal to 'latest' by the newest day that exists on or before values['run_date'] (7-day look-back).
    Raises LookupError when no such day exists, so a snapshot is never built from an empty day by accident."""
    out = dict(values)
    for key, q in PROBES.items():
        if out.get(key) != "latest":
            continue
        sql = load_sql(q, sql_dir)
        cur = conn.cursor()
        cur.execute(sql, tuple(out[p] for p in q.params))
        row = cur.fetchall()
        day = row[0][0] if row else None
        if day is None:
            raise LookupError(f"no {key} found in the 7 days up to {out['run_date']}; pass an explicit date")
        out[key] = day.isoformat() if hasattr(day, "isoformat") else str(day)
    return out


def load_sql(q: Query, sql_dir: Path = SQL_DIR) -> str:
    sql = (sql_dir / q.file).read_text(encoding="utf-8")
    validate_select(sql)
    return sql


def validate_all(queries=QUERIES, sql_dir: Path = SQL_DIR) -> None:
    for q in list(queries) + list(PROBES.values()):
        load_sql(q, sql_dir)


def build_snapshot(connect, outdir: Path, values: dict, queries=QUERIES, sql_dir: Path = SQL_DIR) -> dict:
    """connect() -> DB-API-like connection. values: parameter name -> value (strings for dates)."""
    sqls = {q.name: load_sql(q, sql_dir) for q in queries}   # validate everything before connecting
    outdir.mkdir(parents=True, exist_ok=True)
    manifest = {"ccl_version": __version__, "run_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "parameters": dict(values), "tables": []}
    conn = connect()
    try:
        for q in queries:
            cur = conn.cursor()
            cur.execute(sqls[q.name], tuple(values[p] for p in q.params))
            cols = [d[0] for d in cur.description]
            check_output_columns(cols)
            rows = cur.fetchall()
            with open(outdir / f"{q.name}.csv", "w", newline="", encoding="utf-8") as f:
                w = csv.writer(f)
                w.writerow(cols)
                w.writerows(rows)
            manifest["tables"].append({
                "name": q.name, "query_id": q.query_id, "sql_file": q.file,
                "sql_sha256": hashlib.sha256(sqls[q.name].encode()).hexdigest(),
                "rows": len(rows), "columns": cols,
                "warning": "0 rows: check parameters (run/snapshot dates, vendor name)" if not rows else None})
    finally:
        conn.close()
    (outdir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest
