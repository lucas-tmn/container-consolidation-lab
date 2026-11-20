-- SNAP-13 Monthly channel forecast, type M, for the vendor's planned items; one snapshot day.
-- Params (in order of the placeholders): vendor name, ship_from, ship_to, forecast_date (FileDate day). Source: ForecastCommonContainer_Logility [I, best candidate].
-- Filter by FileDate first: the table has about 495M rows (docs/04). Channel column is kept (9 channels); summing happens in the lab.
WITH items AS (
    SELECT DISTINCT RTRIM(P.prqItem) AS ITEM
    FROM Wholesale_DemandPlanning_AFI.PlannedRequirementsLogility AS P
    JOIN PowerBI_SupplyChain.VendorMaster AS VM ON TRIM(VM.[VendorNumber]) = TRIM(P.prqVendorNumber)
    WHERE TRIM(VM.[VendorName]) = ?
      AND TRY_CONVERT(date, CAST(CAST(P.prqShipdate AS bigint) AS char(8)), 112) >= CAST(? AS date)
      AND TRY_CONVERT(date, CAST(CAST(P.prqShipdate AS bigint) AS char(8)), 112) <  CAST(? AS date)
)
SELECT CAST(T.[FileDate] AS date) AS FILE_DATE, RTRIM(T.[Item-Lvl1]) AS ITEM, RTRIM(T.[Location]) AS LOC,
       CAST(T.[DfcCustomergroupS] AS varchar(20)) AS CHANNEL,
       CAST(T.[Result_Fc_0] AS decimal(18,3)) AS FC0, CAST(T.[Result_Fc_1] AS decimal(18,3)) AS FC1,
       CAST(T.[Result_Fc_2] AS decimal(18,3)) AS FC2, CAST(T.[Result_Fc_3] AS decimal(18,3)) AS FC3,
       CAST(T.[Result_Fc_4] AS decimal(18,3)) AS FC4, CAST(T.[Result_Fc_5] AS decimal(18,3)) AS FC5,
       CAST(T.[Result_Fc_6] AS decimal(18,3)) AS FC6, CAST(T.[Result_Fc_7] AS decimal(18,3)) AS FC7,
       CAST(T.[Result_Fc_8] AS decimal(18,3)) AS FC8, CAST(T.[Result_Fc_9] AS decimal(18,3)) AS FC9,
       CAST(T.[Result_Fc_10] AS decimal(18,3)) AS FC10, CAST(T.[Result_Fc_11] AS decimal(18,3)) AS FC11
FROM SupplyChain_Enh.ForecastCommonContainer_Logility AS T
JOIN items AS I ON I.ITEM = RTRIM(T.[Item-Lvl1])
WHERE T.[FileDate] >= CAST(? AS date) AND T.[FileDate] < DATEADD(DAY, 1, CAST(? AS date))
  AND CAST(T.[ForeCastType] AS varchar(10)) = 'M'
  AND RTRIM(T.[Location]) IN ('1', '5', '15', '17', '28', '335', 'ECR')
ORDER BY 2, 3, 4;
