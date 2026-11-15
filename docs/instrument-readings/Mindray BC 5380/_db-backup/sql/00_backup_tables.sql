IF OBJECT_ID('dbo.QcLjRecord_bak_20261016','U') IS NOT NULL DROP TABLE dbo.QcLjRecord_bak_20261016;
IF OBJECT_ID('dbo.QcLjRefLimit_bak_20261016','U') IS NOT NULL DROP TABLE dbo.QcLjRefLimit_bak_20261016;
SELECT * INTO dbo.QcLjRecord_bak_20261016
FROM dbo.QcLjRecord
WHERE RTRIM(FileNo) IN ('43','44','45','46','47','48','49','50','51','52','53','54','55','56','57','58','59','60','61','62','63');
SELECT * INTO dbo.QcLjRefLimit_bak_20261016
FROM dbo.QcLjRefLimit
WHERE RTRIM(FileNo) IN ('43','44','45','46','47','48','49','50','51','52','53','54','55','56','57','58','59','60','61','62','63');
