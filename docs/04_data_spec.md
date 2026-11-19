# 04 – Data specification

All data is read-only, pulled by Claude Code through the query loop (doc 08) and frozen under `snapshots/<YYYY-MM-DD>/` (git-ignored). Row-level data is not committed; only the golden subset in `data/golden/`.

## Inputs
| Input | Source | Key columns | Notes |
|---|---|---|---|
| Planned PO lines | EDW `Wholesale_DemandPlanning_AFI.PlannedRequirementsLogility` | `prqItem`, `prqWarehouse`, `prqVendorNumber`, `prqQuantity`, `prqShipdate`, `prqDuedate` | ~617,896 rows, single load 18 Nov 2026 [V]. `prqShipdate`/`prqDuedate` are **DECIMAL yyyymmdd**: convert with `TRY_CONVERT(date, CAST(CAST(x AS bigint) AS char(8)), 112)`. Order numbers (prefix TQ) are not stable across loads: do not join on them. Planned orders near-term may become real POs between loads. |
| Vendor name | EDW `PowerBI_SupplyChain.VendorMaster` | `VendorNumber`, `VendorName` | Join `TRIM(VendorNumber) = TRIM(prqVendorNumber)`; match vendor by **exact name**. "GRAND WOOD VN CO LTD" and "GRAND WOOD VN 2 CO LTD" are different vendors. Output names only, never ids. |
| Item master | EDW `PowerBI_SupplyChain.CurrentProductDetails` | `[Item SKU]`, `Cubes`, `FOB Price`, `ContainerVolume`, `Primary Vendor Name` | `ContainerVolume` = Cubes / 2400 [V]. No weight column; Databricks `wholesale_item_master.UnitWeightLbs` may have it [?]. |
| Projected inventory / demand | EDW `Wholesale_DemandPlanning_AFI.SupplyPlanDetail` (`spd*`) | shippable inventory, NetForecast | Runs kept: 23 Oct, 24 Oct, 18 Nov [V]. NetForecast = ForecastCommonContainer type F, not M. |
| Forecast by channel | EDW `SupplyChain_Enh.ForecastCommonContainer_Logility` (~495M rows) | `FileDate` (snapshot), `Item-Lvl1`, `Location`, `ForeCastType`, `DfcCustomergroupS` (channel), `Result_Fc_0..11` | Daily snapshots 10 Sep–18 Nov, includes 24 Oct [V]. Filter by `FileDate` first (table is large). `ForeCastType` values: I, M, D, S, F, P, X, N, L; `ForecastLevel` = '2'. 9 channels. Offsets 0..11 are relative months. |
| Actual POs (backtest) | EDW `Wholesale_ProductSourcing_AFI.PoMaster` + `PoDetail` (`pomordernum=podordernum AND pomwarehouse=podwarehouse`) | status `pod`/`pom` codes: 10 on order, 20 in transit, 50 received, 99 cancelled; `podcubes` = line total cube | Prefixes P2/P3/PS (not TQ). 579 of 620 lines for ETD 21–27 Dec were created by the auto-PO job on 16 Nov [V]. |
| Freight | Reference app notes (spot, 22 Oct) | West $8,007, East $10,166 | Config only; replace with contract rates when available. |

## Warehouse facts [V]
Only warehouses 1, 5, 15, 17, 28, 335, ECR appear for the two Grand Wood vendors in the planned table; 3, 12, 19, 20, 201, 49, 101, 42 never do. Warehouse 335 is the largest (VN1 2,282 lines, ~237 container-eq) and is excluded by the reference app. 104 of 124 items in the week of 28 Dec are planned for more than one warehouse.

## Snapshot layout (to implement)
```
snapshots/2026-11-19/
  manifest.json            # table, query id (Q-SC-xxxx), run time, row counts, hash
  planned_lines.csv        # vendor, week, item, wh, qty, due   (no PO numbers)
  item_master.csv          # item, cube, fob, (weight)
  inventory_projection.csv # item, wh, week, shippable
  forecast_m.csv           # snapshot FileDate, item, wh, channel, fc0..fc11
```

## Query rules
Read-only; no PO numbers, vendor ids, user ids in outputs; derived tables via `UNION ALL` (no `FROM (VALUES ...)`); check column types before date logic; run outside Mon–Fri 08:00–18:00 Central; VPN required. Reference queries in `sql/`.
