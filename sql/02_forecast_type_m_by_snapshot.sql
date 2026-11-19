-- Forecast by type and snapshot, summed over channels (weekly = SUM_FCx * 12 / 52).
-- Reference: Q-SC-1069 (UDF round 18). The table is ~495M rows: always filter FileDate first.
SELECT CAST(T.[FileDate] AS date) AS FILE_DATE, RTRIM(T.[Item-Lvl1]) AS ITEM, RTRIM(T.[Location]) AS LOC,
       CAST(T.[ForeCastType] AS varchar(10)) AS FC_TYPE, COUNT_BIG(*) AS ROWS_N,
       CAST(SUM(T.[Result_Fc_0]) AS decimal(18,3)) AS SUM_FC0, CAST(SUM(T.[Result_Fc_1]) AS decimal(18,3)) AS SUM_FC1,
       CAST(SUM(T.[Result_Fc_2]) AS decimal(18,3)) AS SUM_FC2, CAST(SUM(T.[Result_Fc_3]) AS decimal(18,3)) AS SUM_FC3,
       CAST(SUM(T.[Result_Fc_4]) AS decimal(18,3)) AS SUM_FC4, CAST(SUM(T.[Result_Fc_5]) AS decimal(18,3)) AS SUM_FC5,
       CAST(SUM(T.[Result_Fc_6]) AS decimal(18,3)) AS SUM_FC6, CAST(SUM(T.[Result_Fc_7]) AS decimal(18,3)) AS SUM_FC7,
       CAST(SUM(T.[Result_Fc_8]) AS decimal(18,3)) AS SUM_FC8, CAST(SUM(T.[Result_Fc_9]) AS decimal(18,3)) AS SUM_FC9,
       CAST(SUM(T.[Result_Fc_10]) AS decimal(18,3)) AS SUM_FC10, CAST(SUM(T.[Result_Fc_11]) AS decimal(18,3)) AS SUM_FC11
FROM SupplyChain_Enh.ForecastCommonContainer_Logility AS T
WHERE ((T.[FileDate] >= '2026-10-24' AND T.[FileDate] < '2026-10-25') OR (T.[FileDate] >= '2026-11-18' AND T.[FileDate] < '2026-11-19'))
  AND RTRIM(T.[Item-Lvl1]) IN ('D642-224','D797-02') AND RTRIM(T.[Location]) IN ('5','1')
GROUP BY CAST(T.[FileDate] AS date), RTRIM(T.[Item-Lvl1]), RTRIM(T.[Location]), CAST(T.[ForeCastType] AS varchar(10))
ORDER BY 1, 2, 3, 4;
