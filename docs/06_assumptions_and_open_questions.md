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
