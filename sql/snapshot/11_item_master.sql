-- SNAP-11 Cube and FOB per item for the items planned for the vendor in the ship window.
-- Params (in order of the placeholders): vendor name, ship_from, ship_to. Columns verified in round 9 (docs/04). Weight is not in this table.
WITH items AS (
    SELECT DISTINCT RTRIM(P.prqItem) AS ITEM
    FROM Wholesale_DemandPlanning_AFI.PlannedRequirementsLogility AS P
    JOIN PowerBI_SupplyChain.VendorMaster AS VM ON TRIM(VM.[VendorNumber]) = TRIM(P.prqVendorNumber)
    WHERE TRIM(VM.[VendorName]) = ?
      AND TRY_CONVERT(date, CAST(CAST(P.prqShipdate AS bigint) AS char(8)), 112) >= CAST(? AS date)
      AND TRY_CONVERT(date, CAST(CAST(P.prqShipdate AS bigint) AS char(8)), 112) <  CAST(? AS date)
)
SELECT TRIM(C.[Item SKU]) AS ITEM, CAST(C.[Cubes] AS float) AS CUBES, CAST(C.[FOB Price] AS float) AS FOB_PRICE,
       CAST(C.[ContainerVolume] AS float) AS CONTAINER_VOLUME
FROM PowerBI_SupplyChain.CurrentProductDetails AS C
JOIN items AS I ON I.ITEM = TRIM(C.[Item SKU])
ORDER BY 1;
