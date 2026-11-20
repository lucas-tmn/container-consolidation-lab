-- PROBE Latest SupplyPlanDetail run day on or before the given day, looking back 7 days only.
-- Params (in order of the placeholders): run_date, run_date. Returns one date, or NULL when no run exists in the window.
SELECT MAX(CAST(S.dtea AS date)) AS LATEST_RUN_DATE
FROM Wholesale_DemandPlanning_AFI.SupplyPlanDetail AS S
WHERE S.dtea >= DATEADD(DAY, -7, CAST(? AS date)) AND S.dtea < DATEADD(DAY, 1, CAST(? AS date))
