"""Connection helper. No credentials in code: server/database come from environment variables and
authentication is interactive Microsoft Entra sign-in (VPN required), so no secret is stored."""
from __future__ import annotations
import os


class ConnectionConfigError(RuntimeError):
    pass


def connect_edw(env=None):
    env = os.environ if env is None else env
    server, database = env.get("CCL_EDW_SERVER"), env.get("CCL_EDW_DATABASE")
    if not server or not database:
        raise ConnectionConfigError("set CCL_EDW_SERVER and CCL_EDW_DATABASE (see README, 'Local refresh')")
    try:
        import pyodbc
    except ImportError as e:  # pragma: no cover
        raise ConnectionConfigError("pip install -e .[edw] (needs pyodbc and an ODBC Driver for SQL Server)") from e
    driver = env.get("CCL_ODBC_DRIVER", "ODBC Driver 18 for SQL Server")
    auth = env.get("CCL_EDW_AUTH", "ActiveDirectoryInteractive")
    cs = (f"Driver={{{driver}}};Server={server};Database={database};Authentication={auth};"
          "Encrypt=yes;ApplicationIntent=ReadOnly")
    return pyodbc.connect(cs, timeout=30)
