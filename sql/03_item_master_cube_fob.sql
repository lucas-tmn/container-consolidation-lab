-- Cube (ft3 per piece), FOB per piece and ContainerVolume for items of one vendor.
-- Reference: round 9/10. ContainerVolume = Cubes / 2400. No weight column in this table.
SELECT TRIM(C.[Item SKU]) AS ITEM, C.[Cubes] AS CUBE_FT3, C.[FOB Price] AS FOB_USD, C.[ContainerVolume] AS CONTAINER_VOLUME
FROM PowerBI_SupplyChain.CurrentProductDetails AS C
WHERE TRIM(C.[Primary Vendor Name]) = 'GRAND WOOD VN CO LTD'
ORDER BY 1;
