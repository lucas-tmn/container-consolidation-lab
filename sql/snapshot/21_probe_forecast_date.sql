-- PROBE Latest forecast FileDate on or before the given day, looking back 7 days only (the table has about 495M rows).
-- Params (in order of the placeholders): run_date, run_date. Returns one date, or NULL when no snapshot exists in the window.
SELECT MAX(CAST(T.[FileDate] AS date)) AS LATEST_FILE_DATE
FROM SupplyChain_Enh.ForecastCommonContainer_Logility AS T
WHERE T.[FileDate] >= DATEADD(DAY, -7, CAST(? AS date)) AND T.[FileDate] < DATEADD(DAY, 1, CAST(? AS date))
