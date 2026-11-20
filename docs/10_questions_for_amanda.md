# 10 – Questions for Amanda (only what data cannot answer)

Status 20 Nov. Lucas decides whether and how to send. Tone: curious, to help the tool, not to audit. Check the numbers again before sending (data change daily).

## Already answered by investigation (do not ask)
- Platform: Microsoft 365 Copilot Cowork managed app; data are embedded copies [V].
- Source of planned POs: `PlannedRequirementsLogility`, same counts per ship week from 18 Jan on [V].
- Why data differ between 17 Nov and now: planned lines convert to firm POs about 5 weeks before ETD and the table reloads daily [I].

## Questions
1. **Firm POs (priority).** Does the tool include POs that were already created for the same vendor, DC and week? In EDW, week 21-Dec has 709 firm PO lines (about 151 container-eq) for Grand Wood VN, while the app shows about 10.4 container-eq of planned lines. The auto-PO job created these POs on 16 Nov, but week 21-Dec still showed 48 planned lines on 19 Nov and 2 on 20 Nov. Were the 46 lines in the 17 Nov plan already firm POs when the plan was made?
2. **Forecast.** What are AI4, AI6 and AI8 (which months, which column)? Why the 24 Oct snapshot, and is it meant to be refreshed?
3. **DC assignment.** How is a planned line assigned to a DC? The app shows Arcadia 17.5 container-eq for ship week 28-Dec, EDW warehouse 1 shows 10.45. A line-level test on the 19 Nov data could not settle it (only 6 of 46 app lines match an EDW line on item and qty), so we need her export or rule.
4. **Arrival buffer.** Why a fixed 5 weeks when EDW due minus ship is a constant per warehouse (Arcadia 9, Advance 8, Leesport 7, Ecru 7, Mesquite 6, Redlands 5 weeks)? The app text uses 4 weeks for Redlands; which is right?
5. **Thresholds.** Who owns 90% fill, $25,000 pull-forward, 4 weeks of supply? Are they approved or placeholders?
6. **Export.** Can the app export the full line list of a plan (all lines of ship week 28-Dec) so we can verify line by line?
7. **Reuse.** Does the plan avoid using the same line in two weekly plans?
8. **Warehouse 335.** Why excluded (largest source in EDW for this vendor, about 18 container-eq in week 28-Dec)? Is it a business rule or a data limit?
9. **Decision log.** Planners still take the actions: is there a record of which recommendations were followed? That would let us back-test.
10. **Platform and credits.** What does the "not enough credits" banner mean for other users, and who can get access?
11. **Freight and lead times.** Source of the $8,007 / $10,166 spot rates and of DC lead times; are contract rates available?
12. **Projected inventory.** Does the projected shippable inventory used for weeks of supply already include the planned receipts that the tool is moving? And how does the tool treat an item with no forecast (we see 13% of lines)?
13. **B742-57.** Was the app used to find the demand-versus-PO mismatch, or is that separate?
