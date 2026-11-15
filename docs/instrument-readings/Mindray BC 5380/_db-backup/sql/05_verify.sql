SELECT RTRIM(FileNo) FileNo, COUNT(*) n, MIN(QcDateTime) mn, MAX(QcDateTime) mx
FROM dbo.QcLjRecord
WHERE RTRIM(FileNo) IN ('43','44','45','46','47','48','49','50','51','52','53','54','55','56','57','58','59','60','61','62','63')
GROUP BY RTRIM(FileNo);
SELECT RTRIM(FileNo) FileNo, RTRIM(LotNo) LotNo, QcLevel, WBC_Ref, WBC_Limit, HasData_Flag
FROM dbo.QcLjRefLimit
WHERE RTRIM(FileNo) IN ('43','44','45','46','47','48','49','50','51','52','53','54','55','56','57','58','59','60','61','62','63');
SELECT COUNT(*) recs FROM dbo.QcLjRecord WHERE RTRIM(FileNo) IN ('43','44','45','46','47','48','49','50','51','52','53','54','55','56','57','58','59','60','61','62','63');
SELECT COUNT(*) bak FROM dbo.QcLjRecord_bak_20261016;
