-- SNAP-14 Firm PO volume of one vendor (exact NAME) by ETD week (Monday) and warehouse. Aggregates only: no order numbers.
-- Params (in order of the placeholders): vendor name, ship_from (date), ship_to (date, exclusive). ETD is read from 14 days before ship_from.
-- pometd is datetime2 [V, Q-SC-1081]. Columns used are verified in Q-SC-1083 [V]; pomAutoPO is a bit column.
SELECT DATEADD(DAY, -(DATEDIFF(DAY, '1900-01-01', TRY_CONVERT(date, M.pometd)) % 7), TRY_CONVERT(date, M.pometd)) AS ETD_WEEK,
       RTRIM(D.podwarehouse) AS WHSE,
       COUNT_BIG(*) AS PO_LINES,
       SUM(CASE WHEN M.pomAutoPO = 1 THEN 1 ELSE 0 END) AS AUTO_PO_LINES,
       SUM(D.podqtyordered) AS QTY,
       CAST(SUM(CAST(D.podcubes AS float)) / 2400.0 AS decimal(12,3)) AS CONTAINER_EQ
FROM Wholesale_ProductSourcing_AFI.PoMaster AS M
JOIN Wholesale_ProductSourcing_AFI.PoDetail AS D ON M.pomordernum = D.podordernum AND M.pomwarehouse = D.podwarehouse
JOIN PowerBI_SupplyChain.VendorMaster AS VM ON TRIM(VM.[VendorNumber]) = TRIM(M.pomvendornum)
WHERE TRIM(VM.[VendorName]) = ? AND M.pomstatuscode <> '99' AND D.podstatuscode <> '99'
  AND TRY_CONVERT(date, M.pometd) >= DATEADD(DAY, -14, CAST(? AS date))
  AND TRY_CONVERT(date, M.pometd) <  CAST(? AS date)
GROUP BY DATEADD(DAY, -(DATEDIFF(DAY, '1900-01-01', TRY_CONVERT(date, M.pometd)) % 7), TRY_CONVERT(date, M.pometd)), RTRIM(D.podwarehouse)
ORDER BY 1, 2;
