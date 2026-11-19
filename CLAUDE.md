# Repo rules for Claude / agents
- This repo is a read-only decision lab. Never add code that writes to EDW, Logility, or any production system.
- Never put PO numbers, vendor ids or user ids in committed files, test data, logs or outputs. Lines are identified by SEQ or by item + warehouse + week.
- Thresholds live in `config/params.yaml`; do not hardcode 0.90, 25,000, 4 weeks or 5 weeks in code.
- Evidence labels in docs: [V] seen in data/screens, [I] inferred, [?] unknown. Keep them when editing.
- Before claiming the engine matches the reference app, run `pytest` and `python -m ccl verify-golden`.
- EDW is Synapse T-SQL: no `FROM (VALUES ...)` (use `SELECT ... UNION ALL SELECT ...`); check column types before date logic (`prqShipdate`/`prqDuedate` are DECIMAL yyyymmdd).
- Lucas (Product Owner) writes in Vietnamese and English; answer in the language he uses. Keep decisions concise.
