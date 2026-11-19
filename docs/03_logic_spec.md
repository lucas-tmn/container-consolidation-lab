# 03 – Logic specification (v0)

Scope: one vendor, one ship week at a time (phase 1), then multi-week (phase 3). All thresholds come from `config/params.yaml`.

## Definitions
- **Line**: planned PO line (item, warehouse/DC, quantity, ship week, PO due date). Identified by SEQ in outputs, never by PO number.
- **cube(line)** = quantity x `Cubes` (ft3 per piece, item master). **fob(line)** = quantity x `FOB Price`.
- **container-eq(DC, week)** = sum(cube) / 2,400. **containers(DC, week)** = ceil(container-eq) (a partial container still ships as one). **fill of a container**: full containers are 100%; the last one = remainder / 2,400.
- **avg fill(week)** = total cube / (containers x 2,400) over all DCs.
- **weeks of supply (WOS)** of item at DC at time t = projected shippable inventory(t) / weekly forecast. WOS = 0 when data is missing. Short = WOS < `supply.short_below_weeks`.
- **weekly forecast** = sum over channels of monthly forecast x 12 / 52 (reference app). Lab default: `ForeCastType = M`, snapshot date recorded in every run.
- **supply measurement time** = ship week + `arrival_buffer_weeks` (reference app, fixed). Lab option: ship week + DC `lead_time_weeks`.

## Planning steps (order matters, copy of the reference app)
1. **Baseline.** Group lines by DC. Compute containers, fill, freight (`containers x rate(region of DC)`).
2. **Spread.** If a DC's cube is between k and k+1 containers, try to even the fill across its containers.
3. **Find overflow.** For each DC whose last container is below `fill.min`, the overflow candidates are lines in that last container, ordered by WOS descending (least needed first).
4. **Change destination** (before loading, no cross-dock): move a candidate to another DC that (a) is short for the item or needs it, (b) has room in a container below `fill.max`, (c) is allowed (not excluded / container-direct). Always needs approval. PO due date is kept (reference app behaviour [I]); lab option: recompute from the new DC lead time.
5. **Delay one week**: if the DC is not short for the item (WOS >= short threshold after arrival). Delay is always exactly one week, and next week's plan is not re-run (reference app limitation). Flag `late` if the new arrival is after the PO due date; late delays need approval.
6. **Pull forward**: for DCs whose last container is still under `fill.min`, take next-week lines for that DC, short items first (lowest WOS), until the container reaches `fill.min`..`fill.max`. Approval per to-do if pulled FOB > `approvals.pull_forward_fob_usd`.
7. **Leftover.** Any container still below `fill.min` ships as is and needs approval.
8. **Rank options.** Compare: as scheduled; all levers; no destination change; no pull-forward. Report containers, avg fill, cost avoided, moved/delayed/pulled pcs, late pcs, approvals, next-week container change.

## Approvals (per to-do)
A to-do needs approval when any of: container below `fill.min`; any destination change; delay that misses the PO due date; pull-forward FOB above the threshold. (Reference plan: 4 of 4 to-dos need approval.)

## Cost avoided
`cost avoided = (baseline containers - plan containers) per DC x rate(region)`; the reference plan's $8,007 is one West container (Redlands). Report next-week container reductions separately, never added to this week's saving.

## Lab improvements over the reference app (phase 3, switchable)
| Switch | Reference behaviour | Lab option |
|---|---|---|
| `use_dc_lead_time` | fixed 5-week buffer | measure supply at ship week + DC lead time (4–9 weeks) |
| multi-week planning | independent weeks | plan N weeks jointly; a line is used once; savings counted once |
| forecast freshness | snapshot 24 Oct | newest snapshot; print age on every output |
| weight | cube only, weight warning | enforce 44,000 lb when unit weight is available |
| destination due date | kept | recomputed from new DC lead time |
| sensitivity | none | run grid on fill min, approval threshold, short threshold, buffer |

## Determinism
Given snapshot id + config + code version, output is identical. Ties are broken by (WOS, item code, SEQ). Every run writes a `run.json` (snapshot id, config hash, git commit, timestamps).

## Open decisions (see doc 06)
How the reference app assigns a warehouse to a planned PO; exact forecast month selection ("AI4/AI6/AI8"); whether warehouse 335 should be included.
