import json
import re
from datetime import datetime, timezone
from pathlib import Path

import pytest

from ccl.snapshot import QUERIES, SQL_DIR, build_snapshot, validate_all
from ccl.sqlguard import SqlGuardError, check_output_columns, in_business_window, validate_select


@pytest.mark.parametrize("sql", [
    "SELECT 1", "select a from t where b = ?", "WITH x AS (SELECT 1 AS a) SELECT a FROM x;",
    "SELECT [Item SKU], 'update me' AS note FROM t  -- DROP TABLE x",
])
def test_guard_accepts_reads(sql):
    validate_select(sql)


@pytest.mark.parametrize("sql", [
    "", "DELETE FROM t", "SELECT 1; SELECT 2", "SELECT * INTO #t FROM s", "UPDATE t SET a = 1",
    "WITH x AS (SELECT 1 a) INSERT INTO t SELECT a FROM x", "EXEC sp_who", "SELECT * FROM #temp",
    "DECLARE @a int; SELECT 1", "SELECT 1 FROM OPENROWSET('x','y','z')", "DROP TABLE t",
])
def test_guard_rejects_writes(sql):
    with pytest.raises(SqlGuardError):
        validate_select(sql)


def test_output_columns_block_identifiers():
    check_output_columns(["ITEM", "WHSE", "QTY"])
    for bad in ("prqOrderNumber", "PO_NUMBER", "VendorNumber", "USRA"):
        with pytest.raises(SqlGuardError):
            check_output_columns([bad])


def test_business_window_central():
    # Fri 2026-11-20 16:00 UTC = 10:00 Central (inside); 03:00 UTC = Thu 21:00 Central (outside); Sat noon outside
    assert in_business_window(datetime(2026, 11, 20, 16, 0, tzinfo=timezone.utc))
    assert not in_business_window(datetime(2026, 11, 20, 3, 0, tzinfo=timezone.utc))
    assert not in_business_window(datetime(2026, 11, 21, 18, 0, tzinfo=timezone.utc))


def test_snapshot_sql_files_valid_and_params_match():
    validate_all()
    for q in QUERIES:
        body = re.sub(r"--[^\n]*", "", (SQL_DIR / q.file).read_text(encoding="utf-8"))
        assert body.count("?") == len(q.params), q.name


def test_reference_sql_files_pass_guard():
    for f in Path(__file__).resolve().parents[1].glob("sql/*.sql"):
        validate_select(f.read_text(encoding="utf-8"))


class _Cur:
    def __init__(self, log): self.log, self.description, self._rows = log, [], []
    def execute(self, sql, params):
        self.log.append((sql, params))
        self.description = [("ITEM",), ("QTY",)]
        self._rows = [("A", 1), ("B", 2)]
    def fetchall(self): return self._rows


class _Conn:
    def __init__(self, log): self.log, self.closed = log, False
    def cursor(self): return _Cur(self.log)
    def close(self): self.closed = True


def test_build_snapshot_with_fake_connection(tmp_path):
    log, conn = [], None
    def connect():
        nonlocal conn
        conn = _Conn(log)
        return conn
    values = {"vendor": "V", "ship_from": "2026-12-07", "ship_to": "2027-01-04", "inventory_run_date": "2026-11-19",
              "forecast_date": "2026-11-19", "week_from": "2026-12-07", "week_to": "2027-03-01"}
    m = build_snapshot(connect, tmp_path / "snap", values)
    assert conn.closed and len(log) == len(QUERIES)
    assert log[3][1] == ("V", "2026-12-07", "2027-01-04", "2026-11-19", "2026-11-19")   # forecast date bound twice
    assert [t["rows"] for t in m["tables"]] == [2, 2, 2, 2]
    saved = json.loads((tmp_path / "snap" / "manifest.json").read_text())
    assert saved["tables"][0]["name"] == "planned_lines" and len(saved["tables"][0]["sql_sha256"]) == 64
    assert (tmp_path / "snap" / "forecast_m.csv").read_text().splitlines()[0] == "ITEM,QTY"


def test_build_snapshot_refuses_bad_sql_before_connecting(tmp_path):
    (tmp_path / "sql").mkdir()
    (tmp_path / "sql" / "x.sql").write_text("DELETE FROM t")
    from ccl.snapshot import Query
    called = []
    with pytest.raises(SqlGuardError):
        build_snapshot(lambda: called.append(1), tmp_path / "o", {}, [Query("x", "x.sql", (), "T")], tmp_path / "sql")
    assert not called


def test_probe_sql_files_valid_and_params_match():
    from ccl.snapshot import PROBES
    for q in PROBES.values():
        body = re.sub(r"--[^\n]*", "", (SQL_DIR / q.file).read_text(encoding="utf-8"))
        assert body.count("?") == len(q.params), q.name
        validate_select(body)


class _ProbeConn:
    def __init__(self, days): self.days, self.log = days, []
    def cursor(self):
        conn = self
        class C:
            def execute(self, sql, params):
                conn.log.append(params)
                self._row = conn.days.pop(0)
            def fetchall(self): return [(self._row,)]
        return C()


def test_resolve_latest_replaces_only_latest_values():
    from datetime import date
    from ccl.snapshot import resolve_latest
    conn = _ProbeConn([date(2026, 11, 19), date(2026, 11, 18)])
    v = {"run_date": "2026-11-20", "inventory_run_date": "latest", "forecast_date": "latest", "vendor": "V"}
    out = resolve_latest(conn, v)
    assert out["inventory_run_date"] == "2026-11-19" and out["forecast_date"] == "2026-11-18"
    assert conn.log[0] == ("2026-11-20", "2026-11-20")
    fixed = resolve_latest(_ProbeConn([]), {"run_date": "2026-11-20", "inventory_run_date": "2026-11-17", "forecast_date": "2026-10-24"})
    assert fixed["inventory_run_date"] == "2026-11-17" and fixed["forecast_date"] == "2026-10-24"


def test_resolve_latest_raises_when_no_day_exists():
    from ccl.snapshot import resolve_latest
    with pytest.raises(LookupError):
        resolve_latest(_ProbeConn([None]), {"run_date": "2026-11-20", "inventory_run_date": "latest", "forecast_date": "x"})
