# 06 – Working assumptions and open questions

Working assumptions close open items so work can continue (no business owner is available for this lab).
| # | Assumption | Basis | Revisit when |
|---|---|---|---|
| A1 | Planned PO source = `PlannedRequirementsLogility`, vendor by exact name | weekly line counts match from 18 Jan [V]; first 3 weeks differ [I] | a per-line app export exists |
| A2 | Forecast = `ForecastCommonContainer_Logility`, `ForeCastType` M, channels summed, x 12/52 | magnitude matches D797-02 [V], D642-224 near [I] | AI4/AI6/AI8 defined |
| A3 | Month selection = average of offsets 4, 6, 8 (default) | best single guess at "AI4/AI6/AI8" [?] | tested against more items |
| A4 | Warehouse of a line = `prqWarehouse` mapped by `warehouse_map`; 335 and 42 excluded | reference app exclusion list [V] | assignment rule found |
| A5 | Destination change keeps PO due date (reference behaviour) | inferred from app text [I] | confirmed |
| A6 | Freight = spot West/East benchmark | app notes [V] | contract rates available |
| A7 | Thresholds = app placeholders | app states they are placeholders [V] | business sets own |

## Open questions (for the app builder, only when Lucas agrees to ask)
1. Who built the app, on which platform, and is the planned PO data the Logility Greenfield `PlannedRequirementsLogility` snapshot of 17 Nov?
2. What are AI4, AI6, AI8 and which months do they average? Why snapshot 24 Oct?
3. How is a planned PO assigned to a DC (warehouse 3 and 335, Arcadia 17.5 vs 9.2)?
4. Why a fixed 5-week arrival buffer when due dates are 4–9 weeks after ship?
5. Who owns the thresholds (90%, $25,000, 4 weeks) and are they approved?
6. Can the app export the full line list of a plan (all 622 lines of ship week 28 Dec)?
7. Does the app avoid reusing the same PO across weekly plans?
8. Was the app used to find the B742-57 demand-vs-PO mismatch, or is that separate?

## Known gaps
- No planned-PO history; only one snapshot.
- No weight data; the 44,000 lb limit is not testable.
- `ForeCastType` letter meanings (I, M, D, S, F, P, X, N, L) are not documented in the data seen.

## Findings 20 Nov (round 20b, vendor Grand Wood VN)
- [V] `PoMaster.pometd` is datetime2; `TRY_CONVERT(date, pometd)` reads all 132,747 vendor PO lines (0 NULL).
- [V] Firm POs (all status 10, ordered) by ETD week: 14-Dec 715 lines / 144.24 container-eq; 21-Dec 709 / 150.78; 28-Dec 60 / 7.96 (only warehouses C and CNW, not in the 7 planned DCs). From 28-Dec the 7 planned DCs have no firm PO.
- [V] Week 21-Dec firm POs by DC (container-eq): wh335 31.40, wh1 27.03, ECR 20.14, wh17 19.40, wh5 19.17, wh28 15.23, wh15 10.38. The reference app shows about 10.4 for the whole week (planned lines only).
- [I] Planned lines turn into firm POs about 5 weeks before ETD (21-Dec lines: 48 on 19 Nov, 2 on 20 Nov). So the reference app's week 21-Dec plan optimised lines that were already converted to POs, and its per-DC fill ignored the firm volume.
- [I] The actionable window for consolidation of planned lines is the first week that still has planned lines and no firm PO (28-Dec at 20 Nov). Changes to firm POs (destination, ETD) are a different workflow with the vendor.
- [?] Whether PO ETD week equals the app's ship week, and whether firm POs and planned lines ever overlap (double count).
- Engine consequence: step 1 baseline must add firm POs of the same vendor, DC and week to planned lines (switch `include_firm_pos`), and the tool must show which weeks are planned-only.

## Findings 20 Nov (CHAT_0256 part A, local snapshot 2026-11-19)
- [V] Lead time (due minus ship) is one constant per warehouse in planned lines: wh1 9, wh5 5, wh15 7, wh17 8, wh28 6, ECR 7, wh335 1 weeks. The app text has Redlands 4 weeks (EDW 5) [?].
- [V] Container-eq excluding 335 and 42: 21-Dec 0 (only wh335 left), 28-Dec 73.49, 4-Jan 32.96, 11-Jan 42.61. Planned ship dates run 2026-12-19 to 2027-01-30.
- [V] 105 of 120 items planned at more than one warehouse in week 28-Dec.
- [?] DC assignment: only 6 of 46 golden pull-in lines have an EDW line with the same item and qty; no conclusion. Needs the app line export.
