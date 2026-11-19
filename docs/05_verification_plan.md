# 05 – Verification and measurement plan

## Layer 1 – Golden tests (reproduce the reference app)
Data: `data/golden/`. The Dec 21 plan is the answer key.
| Test | Expected (app) | Status |
|---|---|---|
| Pull-in pcs per to-do | 291 / 350 / 322 / 294, total 1,257 | automated (passes) |
| ft3 per to-do | 2,138 / 2,068 / 1,771 / 1,531 | automated (passes) |
| FOB per to-do | $33,711 / $37,509 / $29,103 / $27,583 (+-$1) | automated (passes) |
| PO changes | 47 (46 pull-in + 1 destination) | automated (passes) |
| Destination change cube | 8 x 3.98 = 31.8 ft3 | automated (passes) |
| Cost avoided | $8,007 (1 West container) | automated (passes) |
| Approvals | 4 of 4 to-dos | automated (passes) |
| Containers 15 -> 14, avg fill 69% -> 97% | needs all lines of 21 Dec and 28 Dec weeks | pending snapshot |
| Next-week containers 9->8, 12->11, 18->17, 7->6 | needs the 28 Dec week lines | pending snapshot |
Rule: a golden test may only be marked "explained difference" with a written cause in doc 06.

## Layer 2 – Data checks (trust the inputs)
Row counts per ship week vs the reference counts (46/622/637/768/861/851/845/741/897/914/915/942/915/890/920/910/940 for Dec 21 .. Apr 26); item master coverage = 100% of lines; vendor exact-name filter; snapshot ages printed.

## Layer 3 – Backtest on history (does it help?)
Planned lines have no history (single snapshot), so the backtest uses **actual POs** (`PoMaster/PoDetail`): for past ship weeks by vendor and DC, measure real container fill (cube / 2,400), partial containers, and what the engine would have recommended with data as of the PO creation date. Outputs: partial containers avoided, freight avoided (spot rate), pulled FOB x weeks early, approvals count.
Honest limits: planned-vs-actual differences; projected inventory history is only 3 runs; freight is spot.

## Layer 4 – Outcome risk
After applying a plan to history: weeks of supply at **actual** arrival for pulled items vs threshold; stock-out events within N weeks; capital tied (FOB x weeks early); count of pulled items later cancelled or rescheduled.

## Layer 5 – Forecast quality (links to forecast-accuracy-lab)
Compare forecast type M vs F (and month-offset averaging) on actual demand over the pilot SKUs; record which one best predicts the arrival-period demand. Forecast age is a reported field in every run.

## KPIs (per run, appended to `runs/kpi_history.csv`)
containers before/after; avg fill; freight avoided (this week only); pulled pcs/cube/FOB; delayed pcs and late count; destination changes; approvals; next-week container delta (reported separately); % of lines with WOS = 0 (missing data); snapshot age (days) for planned, inventory, forecast.

## Acceptance criteria
- Phase 1: all automated golden tests pass; engine matches 15 -> 14 containers and 69% -> 97% on a frozen 21 Dec + 28 Dec snapshot, or each gap is explained.
- Phase 2: backtest on >= 8 historical weeks of the pilot vendor with the KPI table above.
- Phase 3: improved variant shows no worse stock-out risk at actual arrival and equal or better containers than the reference variant on the same weeks.
