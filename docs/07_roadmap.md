# 07 – Roadmap

| Phase | Goal | Output | Exit criteria |
|---|---|---|---|
| 0 – Spec and golden data (this commit) | Decide scope, record logic, capture the answer key | docs, config, golden CSV, metric functions + tests, HTML prototype | golden pull-in tests pass |
| 1 – Engine v1 | Plan one vendor-week end to end on a frozen snapshot | snapshot builder (SQL), engine steps 1–8, CLI `plan`, report | matches 15 -> 14 and 69% -> 97% on the Dec 21 week, or gaps explained |
| 2 – Backtest and KPIs | Measure value and risk on history | `backtest` command, KPI history, risk metrics | >= 8 historical weeks, KPI table, stock-out risk numbers |
| 3 – Improvements | Beat the reference on the same weeks | DC lead-time arrival, multi-week plan, fresh forecast, weight, sensitivity | no worse risk, equal or better containers, documented trade-offs |

Pilot scope: Grand Wood VN CO LTD (exact name), warehouses 1, 5, 15, 17, 28, ECR (+335 as a switch), ship weeks 14 Dec 2026 – 25 Jan 2027, frozen local copy. Expand only after phase 2.

Commands (target): `ccl verify-golden`, `ccl plan --vendor ... --week ... --snapshot ...`, `ccl plan-multi --from --to`, `ccl backtest --weeks ...`, `ccl sensitivity`.
