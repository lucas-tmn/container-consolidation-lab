# 02 – Reference app analysis (Container Overflow Planner, shared 19 Nov 2026)

Evidence labels: [V] seen in data/screens · [I] inferred · [?] unknown. Source: 15 read-only evidence rounds (EDW Synapse + Databricks) run on 19 Nov 2026; full log in the UDF project doc `UDF_Container_Overflow_Planner_App_Review` and its addendum.

## What the app does [V from screenshots]
Per vendor and ship week, on 40' HC (2,400 ft3, 44,000 lb), min fill 90%, max 100%:
1. Spread fill evenly. 2. Find overflow, least-needed item first (highest weeks of supply). 3. Change destination before loading (no cross-dock). 4. Delay one week if the DC does not need it (>= 4 weeks of supply), flag "late" if arrival passes the PO due date. 5. Pull next week's POs forward for DCs that are short, most-needed first. 6. Anything left needs approval.
Approvals: container < 90% always, any destination change, delay that misses the PO due date, pull-forward > $25,000 FOB per to-do. Short = weeks of supply < 4, supply measured at ship week + 5 weeks (fixed), no data = 0 weeks.
Forecast: "Average of AI4, AI6, AI8", snapshot 24 Oct; weekly = monthly channel forecast summed x 12 / 52. Ocean rate: $8,007 (West: Arcadia WI, Mesquite, Redlands, Colton XD) and $10,166 (East: all other DCs incl. Chippewa Falls WI). Data are embedded point-in-time copies (planned POs and inventory 17 Nov, forecast 24 Oct, freight 22 Oct).

## Reference plan used as golden test [V]
Grand Wood VN CO LTD, ship week 21–27 Dec 2026: containers 15 -> 14, avg fill 69% -> 97%, cost avoided $8,007, 8 pcs destination change (D642-224 Redlands -> Leesport), 0 delays, 4/4 to-dos need approval. 47 PO changes (46 pull-ins from ship week 28 Dec to 21 Dec + 1 destination change); pull-in 1,257 pcs: Mesquite 291, Advance 350, Arcadia 322, Leesport 294; FOB $33,711 / $37,509 / $29,103 / $27,583. Next-week containers: Mesquite 9->8, Advance 12->11, Arcadia 18->17, Leesport 7->6.

## Verified against EDW [V]
- Cube and FOB per piece come from `PowerBI_SupplyChain.CurrentProductDetails` (`Cubes`, `FOB Price`); per-to-do ft3 and FOB recomputed match the app (+-$1). 8 x 3.98 = 31.8 ft3.
- Plan arithmetic matches (container texts, totals, Dec 28 plan $18,173 = $10,166 + $8,007).
- App due dates equal ship week + 4/6/7/8/9 weeks for Redlands/Mesquite/Leesport/Advance/Arcadia; consistent with EDW due-ETD gaps by warehouse.
- Planned PO source is very likely `Wholesale_DemandPlanning_AFI.PlannedRequirementsLogility` (one prefix TQ, one load on 18 Nov): lines per ship week of the vendor match the app within 1–24 lines from 18 Jan on; weeks of 2 lines match exactly [V]; the first three weeks are lower in EDW (531/584/705 vs 622/637/768) [I: snapshot 17 vs 18 Nov, planned orders turning into real POs].
- App forecast is in the range of `SupplyChain_Enh.ForecastCommonContainer_Logility`, `ForeCastType = M`, channels summed, snapshot 24 Oct: D797-02 at warehouse 1 about 60/week (avg of offsets 4,6,8 = 61.8; avg of 12 = 59.4); D642-224 at warehouse 5 about 17/week (offsets give 14.9–16.8) [I, medium-high]. It is **not** Logility NetForecast (that is type F: D797-02 warehouse 1 F month-0 = 99 = SupplyPlanDetail NetForecast; M = 129).

## Not reproduced [?]
- How the app assigns a destination warehouse per PO: week 28 Dec container-eq by DC differs (app Arcadia 17.5 vs EDW warehouse 1 = 9.2; Mesquite 8.1 vs 12.9); total is close (66.2 vs 68.6 incl. 335). Only 9 of 47 plan lines have an EDW line with the same item and quantity.
- Meaning of "AI4, AI6, AI8" (no such value in `ForeCastType`, `ForecastLevel`, `Source`, `DfcCustomergroupS`; no such column in EDW or Databricks).
- Who built the app and on what platform; PO numbers (TQ...) do not exist in the 18 Nov table.

## Concerns raised by the analysis [I]
1. Fixed 5-week arrival buffer vs real due lead time of 4–9 weeks by DC: far DCs are measured 1–4 weeks early, so items look short and get pulled.
2. Forecast snapshot 24 Oct vs inventory 17 Nov; type M moved a lot (D797-02 warehouse 1 month-0 raw 129 -> 275, warehouse 5 70 -> 873).
3. Headline saving ($8,007) is one Redlands container; the other four containers are filled by pulling about $127.9k FOB one week earlier.
4. Weekly plans are independent: the same PO can be used in two plans (one item pulled in full in the Dec 21 plan and split in the Dec 28 plan) and the Dec 21 plan already removes the containers the Dec 28 plan counts as saved; $8,007 + $18,173 is not additive.
5. A destination change keeps the old PO due date (no recalculation) [I]. Arcadia WI uses the West rate while Chippewa Falls WI uses East.
6. Thresholds are placeholders and not in any DSI-3261 document.
