# 08 – Working agreements

## Query loop (EDW and Databricks)
1. Claude chat writes a **fully written** read-only SQL file `NNN_*.sql` plus `CHAT_NNNN_to_code.md` into the Drive folder `UDF_queue/request`. Claude Code runs only SQL exactly as written and never authors or edits it.
2. Lucas tells Claude Code to run it (VPN; EDW outside Mon–Fri 08:00–18:00 Central).
3. Results come back as `CHAT_NNNN_from_code.md`, `Q-SC-xxxx.csv` and `<file>__summary.csv` in the OneDrive response folder; Claude chat reads and analyses them.
4. Numbering continues the UDF sequence: next CHAT_0251, file 282, Q-SC-1071.

## Data handling
- No PO numbers, vendor ids or user ids in outputs, committed files or logs.
- Read-only everywhere; recommendations only.
- Evidence labels [V]/[I]/[?] in every finding.
- Nothing is sent to Amanda or the app builder without Lucas's agreement.

## Git
- Lucas creates repos; Claude pushes code. Commits end with the Co-Authored-By line required by the session.
- Large snapshots and run outputs are git-ignored; only golden data and docs are committed.

## Known EDW quirks
Synapse rejects `FROM (VALUES ...)`; use `UNION ALL`. `prqShipdate`/`prqDuedate` are DECIMAL yyyymmdd. Check column types before date logic. The forecast table is ~495M rows: filter by `FileDate` first.
