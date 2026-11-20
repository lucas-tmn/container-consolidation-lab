-- SNAP-10 Planned lines of one vendor (matched by exact NAME), one row per planned line, no order numbers.
-- Params (in order of the placeholders): vendor name, ship_from (date), ship_to (date, exclusive). Source and conversions: docs/04, Q-SC-1049..1051.
-- prqShipdate / prqDuedate are DECIMAL yyyymmdd. Warehouses are returned as stored; mapping to DCs happens in the lab.
SELECT TRY_CONVERT(date, CAST(CAST(P.prqShipdate AS bigint) AS char(8)), 112) AS SHIP_DATE,
       TRY_CONVERT(date, CAST(CAST(P.prqDuedate AS bigint) AS char(8)), 112) AS DUE_DATE,
       RTRIM(P.prqItem) AS ITEM, RTRIM(P.prqWarehouse) AS WHSE, P.prqQuantity AS QTY,
       CONVERT(date, P.dtea) AS LOAD_DATE
FROM Wholesale_DemandPlanning_AFI.PlannedRequirementsLogility AS P
JOIN PowerBI_SupplyChain.VendorMaster AS VM ON TRIM(VM.[VendorNumber]) = TRIM(P.prqVendorNumber)
WHERE TRIM(VM.[VendorName]) = ?
  AND TRY_CONVERT(date, CAST(CAST(P.prqShipdate AS bigint) AS char(8)), 112) >= CAST(? AS date)
  AND TRY_CONVERT(date, CAST(CAST(P.prqShipdate AS bigint) AS char(8)), 112) <  CAST(? AS date)
ORDER BY 1, 4, 3;
