-- SNAP-12 Projected shippable inventory, net forecast and safety stock per item, warehouse and week ending, for one planning run.
-- Params (in order of the placeholders): vendor name, ship_from, ship_to, inventory_run_date (the dtea day of the run), week_from, week_to (week-ending window).
-- Run days kept in the table so far: 23 Oct, 24 Oct, 18 Nov [V]; if 0 rows come back, pick another run day.
WITH items AS (
    SELECT DISTINCT RTRIM(P.prqItem) AS ITEM
    FROM Wholesale_DemandPlanning_AFI.PlannedRequirementsLogility AS P
    JOIN PowerBI_SupplyChain.VendorMaster AS VM ON TRIM(VM.[VendorNumber]) = TRIM(P.prqVendorNumber)
    WHERE TRIM(VM.[VendorName]) = ?
      AND TRY_CONVERT(date, CAST(CAST(P.prqShipdate AS bigint) AS char(8)), 112) >= CAST(? AS date)
      AND TRY_CONVERT(date, CAST(CAST(P.prqShipdate AS bigint) AS char(8)), 112) <  CAST(? AS date)
)
SELECT CAST(S.dtea AS date) AS RUN_DATE, RTRIM(S.spdItem) AS ITEM, RTRIM(S.spdWarehouse) AS WHSE,
       CAST(S.spdWeekEnding AS date) AS WEEK_ENDING, S.spdShippableInventory AS SHIPPABLE_INV,
       S.spdNetForecast AS NET_FCST, S.spdSafetyStock AS SAFETY_STK
FROM Wholesale_DemandPlanning_AFI.SupplyPlanDetail AS S
JOIN items AS I ON I.ITEM = RTRIM(S.spdItem)
WHERE CAST(S.dtea AS date) = CAST(? AS date)
  AND RTRIM(S.spdWarehouse) IN ('1', '5', '15', '17', '28', '335', 'ECR')
  AND CAST(S.spdWeekEnding AS date) >= CAST(? AS date)
  AND CAST(S.spdWeekEnding AS date) <= CAST(? AS date)
ORDER BY 2, 3, 4;
