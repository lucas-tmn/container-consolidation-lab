"""Read-only guard for every statement the lab sends to EDW/Fabric.

Only one SELECT (optionally with CTEs) is accepted. Anything that can write, create temp
objects, run procedures or change session state is rejected before a connection is used.
"""
from __future__ import annotations
import re
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

FORBIDDEN = {
    "INSERT", "UPDATE", "DELETE", "MERGE", "DROP", "ALTER", "CREATE", "TRUNCATE", "EXEC", "EXECUTE",
    "GRANT", "REVOKE", "DENY", "INTO", "OPENROWSET", "OPENQUERY", "OPENDATASOURCE", "BULK", "WAITFOR",
    "SHUTDOWN", "BACKUP", "RESTORE", "DBCC", "KILL", "DECLARE", "SET", "XP_CMDSHELL", "COPY", "RENAME",
}
# Columns that must never appear in a snapshot (rule in CLAUDE.md: no PO numbers, vendor ids, user ids).
FORBIDDEN_COLUMNS = ("ordernum", "ordernumber", "ponumber", "vendornum", "vendornumber", "userid", "usra", "usrc")


class SqlGuardError(ValueError):
    pass


def _strip(sql: str) -> str:
    s = re.sub(r"/\*.*?\*/", " ", sql, flags=re.S)        # block comments
    s = re.sub(r"--[^\n]*", " ", s)                       # line comments
    s = re.sub(r"'(?:[^']|'')*'", "''", s)                # string literals
    s = re.sub(r"\[[^\]]*\]", "[x]", s)                   # bracketed identifiers
    s = re.sub(r'"[^"]*"', '"x"', s)                      # quoted identifiers
    return s


def validate_select(sql: str) -> None:
    """Raise SqlGuardError unless sql is a single read-only SELECT / WITH...SELECT."""
    s = _strip(sql).strip().rstrip(";").strip()
    if not s:
        raise SqlGuardError("empty statement")
    if ";" in s:
        raise SqlGuardError("more than one statement")
    first = re.match(r"[A-Za-z_]+", s)
    if not first or first.group(0).upper() not in ("SELECT", "WITH"):
        raise SqlGuardError("statement must start with SELECT or WITH")
    bad = sorted({w.upper() for w in re.findall(r"[A-Za-z_]+", s)} & FORBIDDEN)
    if bad:
        raise SqlGuardError("forbidden keyword(s): " + ", ".join(bad))
    if re.search(r"#\w+", s):
        raise SqlGuardError("temp tables are not allowed")


def check_output_columns(columns) -> None:
    for c in columns:
        low = str(c).lower().replace("_", "")
        if any(f in low for f in FORBIDDEN_COLUMNS):
            raise SqlGuardError(f"output column not allowed (identifier data): {c}")


def in_business_window(now: datetime | None = None) -> bool:
    """True inside Mon-Fri 08:00-18:00 US Central, when heavy EDW queries are not allowed (docs/08)."""
    now = now or datetime.now(timezone.utc)
    c = now.astimezone(ZoneInfo("America/Chicago"))
    return c.weekday() < 5 and 8 <= c.hour < 18
