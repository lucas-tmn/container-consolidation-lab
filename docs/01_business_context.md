# 01 – Business context

## Problem
Ashley imports casegoods and accents from Vietnam/China in 40' HC ocean containers. Planned POs are generated automatically from the forecast and arrive at the vendor by ship week. When a vendor's POs for one ship week do not fill whole containers per destination DC, partial containers ship (cost per container is fixed, so a partial box is expensive freight per cubic foot) or POs are shifted by hand.

A colleague (Amanda) shared a prototype, the **Container Consolidation Optimizer / Container Overflow Planner** (19 Nov 2026), that proposes, per vendor and ship week: change destination, delay a week, or pull forward next week's PO so containers fill to 90–100%.

## Why this lab
- The reference app has no documented owner, no documented data source and placeholder thresholds; it embeds point-in-time data and cannot be re-run or measured.
- UDF (Unified Data Foundation) needs supply-chain decisions that are **decision-ready, AI-ready and optimization-ready**: trusted data, defined business logic, governance. This lab is a small, controlled example of "optimization-ready" on one decision.
- The lab is built like `forecast-accuracy-lab`: local, frozen data, measurable outputs, maturity tracked over time.

## Users and decisions
| Who | Decision | What the lab gives |
|---|---|---|
| Supply planner / buyer | Per vendor-week: ship partial, delay, pull forward, redirect | Ranked recommendation with reasons and approval flags |
| Product Owner (Lucas) | Is the logic right, is the data trustworthy, is it worth productising | Verification vs app, backtest KPIs, sensitivity |
| Approver (business) | Approve pulls above a FOB threshold, destination changes, partial containers | Explicit approval list with the rule that triggered it |

## What "good" means (success criteria)
1. **Correct:** reproduces the reference app on the golden plan, or every difference is explained.
2. **Useful:** fewer partial containers and avoided freight on real historical weeks (backtest).
3. **Safe:** does not increase stock-out risk; weeks of supply at *actual* arrival stays at or above the short threshold for pulled items.
4. **Cheap to trust:** capital pulled forward (FOB x weeks early) and approvals are visible; thresholds are parameters with sensitivity.
5. **Reproducible:** same snapshot, same config, same result.

## Non-goals (for now)
- No write-back to Logility or any ERP; recommendation only.
- No contract freight rates or surcharges (spot benchmark only), no drayage or inland rail.
- No automated scheduling or live data refresh (frozen snapshots only).
- Not a replica of the app UI; the HTML prototype exists only to compare numbers.

## Relationship to other work
- **UDF / Inventory Engine / Forecast tool:** shares data foundations (EDW tables, item master) and the "frozen data + measured output" pattern.
- **DSI-3261 (Destination and Container Optimization):** backlog item without owner or approved thresholds; this lab can inform its thresholds and requirements.
- **B742-57 over-order question:** the reference app is *not* the demand-vs-PO monitor. It is related only in that both depend on forecast version and PO generation timing (see doc 02).
