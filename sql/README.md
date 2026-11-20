# sql/
Read-only EDW (Synapse T-SQL) reference queries used to build frozen snapshots. They contain no PO numbers, vendor ids or user ids in output. Run through the Claude chat -> Claude Code loop (docs/08). Query ids refer to the UDF evidence log.

## sql/snapshot/
Parameterized (`?` placeholders, bound by the driver; never string-built) queries run by `ccl refresh` into `snapshots/<run-date>/`. All four pass `ccl.sqlguard.validate_select` (single SELECT, no writes, no temp tables) before any connection is opened, and output columns are checked so no order numbers, vendor ids or user ids can reach a snapshot. Files 01-03 are single-shot reference queries for the chat loop.

