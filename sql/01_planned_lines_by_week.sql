-- Planned PO lines of one vendor by ship week (Monday) and warehouse, with container-equivalent (cube / 2400).
-- Reference: Q-SC-1051 (UDF round 13). prqShipdate/prqDuedate are DECIMAL yyyymmdd.
SELECT DATEADD(DAY, -(DATEDIFF(DAY, '1900-01-01', TRY_CONVERT(date, CAST(CAST(P.prqShipdate AS bigint) AS char(8)), 112)) % 7),
               TRY_CONVERT(date, CAST(CAST(P.prqShipdate AS bigint) AS char(8)), 112)) AS SHIP_WEEK_MON,
       RTRIM(P.prqWarehouse) AS WHSE, COUNT_BIG(*) AS LINES, SUM(P.prqQuantity) AS QTY,
       CAST(SUM(P.prqQuantity * CAST(C.[Cubes] AS float)) / 2400.0 AS decimal(12,2)) AS CONTAINER_EQ,
       SUM(CASE WHEN C.[Item SKU] IS NULL THEN 1 ELSE 0 END) AS LINES_NO_ITEM_MASTER
FROM Wholesale_DemandPlanning_AFI.PlannedRequirementsLogility AS P
JOIN PowerBI_SupplyChain.VendorMaster AS VM ON TRIM(VM.[VendorNumber]) = TRIM(P.prqVendorNumber)
LEFT JOIN PowerBI_SupplyChain.CurrentProductDetails AS C ON TRIM(C.[Item SKU]) = RTRIM(P.prqItem)
WHERE TRIM(VM.[VendorName]) = 'GRAND WOOD VN CO LTD'
  AND TRY_CONVERT(date, CAST(CAST(P.prqShipdate AS bigint) AS char(8)), 112) >= '2026-12-07'
  AND TRY_CONVERT(date, CAST(CAST(P.prqShipdate AS bigint) AS char(8)), 112) <  '2027-05-10'
GROUP BY DATEADD(DAY, -(DATEDIFF(DAY, '1900-01-01', TRY_CONVERT(date, CAST(CAST(P.prqShipdate AS bigint) AS char(8)), 112)) % 7),
                 TRY_CONVERT(date, CAST(CAST(P.prqShipdate AS bigint) AS char(8)), 112)), RTRIM(P.prqWarehouse)
ORDER BY 1, 2;
