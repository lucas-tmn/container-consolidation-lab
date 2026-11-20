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
- [?] Whether PO ETD week equals the app's ship week, and whether firm POs and planned lines ever overlap (double count): see findings of rounds 21-22 below.
- Engine consequence: step 1 baseline must add firm POs of the same vendor, DC and week to planned lines (switch `include_firm_pos`), and the tool must show which weeks are planned-only.

## Findings 20 Nov (CHAT_0256 part A, local snapshot 2026-11-19)
- [V] Lead time (due minus ship) is one constant per warehouse in planned lines: wh1 9, wh5 5, wh15 7, wh17 8, wh28 6, ECR 7, wh335 1 weeks. The app text has Redlands 4 weeks (EDW 5) [?].
- [V] Container-eq excluding 335 and 42: 21-Dec 0 (only wh335 left), 28-Dec 73.49, 4-Jan 32.96, 11-Jan 42.61. Planned ship dates run 2026-12-19 to 2027-01-30.
- [V] 105 of 120 items planned at more than one warehouse in week 28-Dec.
- [?] DC assignment: only 6 of 46 golden pull-in lines have an EDW line with the same item and qty; no conclusion. Needs the app line export.

## Findings 20 Nov (rounds 21-22: PO vs planned alignment)
- [V] Auto-PO share of firm lines: 93-94% for ETD weeks 7, 14, 21 Dec (206/222, 664/715, 668/709); none of these has its ETD moved. Non-auto POs are mostly pushed later (33 of 41 lines in week 21-Dec). From ETD week 28-Dec there is no auto-PO. Firm PO lines of the 7 DCs end at ETD week 21-Dec.
- [V] Week-to-week recurrence of item+warehouse keys (share of next week's keys also in the previous week): PO 7->14 Dec 14%, PO 14->21 Dec 56%, PO 21-Dec -> planned 28-Dec 73%, planned 28-Dec -> 4-Jan 79%, 4->11 Jan 82%, 11->18 Jan 84%, 18->25 Jan 98%. The 73% at the PO/planned boundary is normal recurrence, so the key overlap is NOT evidence of double counting.
- [V] On the 381 common keys, planned qty is below 75% of PO qty on 63% of keys and within +/-25% on 13%: planned lines are not copies of the POs.
- [V] PO due minus ETD (days) vs planned due minus ship: wh15 48 vs 49, wh17 55 vs 56, wh28 41 vs 42, ECR 48 vs 49 (ship is about ETD, same week); wh1 57 vs 63, wh5 30 vs 35, wh335 1 vs 7 (PO about 5-6 days shorter). No uniform one-week offset: do not shift weeks.
- [I] Timing: round 10 shows the auto-PO job created the 21-27 Dec POs on 16 Nov, yet planned lines of week 21-Dec still existed on 17 Nov (46 in the app) and 19 Nov (48) and fell to 2 on 20 Nov. So the planned table lags the PO creation by a few days, and the app's 17 Nov plan for week 21-Dec probably optimised lines that were already firm POs. Needs Amanda's confirmation (question 1).
- Engine rule: a ship week is plannable only if it has no firm POs of the vendor for those DCs (use PO coverage by ETD week); show the plannable weeks in the UI. Add PO volume as context, not as double count.
