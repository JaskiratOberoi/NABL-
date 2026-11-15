/*
Noble Diagnostic Centre - Mindray BC-5380
Point File 43-63 Data/Graph plots at .dat files that already exist.

The .bat failed because this PC has no sqlcmd in PATH.
Do not run the .bat. Run THIS file in SQL Query Analyzer / SSMS
(same way as the insert script), database BC5300DataBase.

It reuses File 1 (Low), File 2 (Normal) and File 3 (High) scatter
files already under C:\Mindray\Auto Hematology Analyzer\dat\
Close the analyser software first, then Execute.
*/

USE [BC5300DataBase];
GO

SET NOCOUNT ON;
SET XACT_ABORT ON;

IF DB_NAME() <> N'BC5300DataBase'
BEGIN
    RAISERROR('Wrong database - expected BC5300DataBase', 16, 1);
    RETURN;
END

IF OBJECT_ID(N'dbo.QcLjDatCopy_2026', N'U') IS NOT NULL
    DROP TABLE dbo.QcLjDatCopy_2026;

SELECT
    n.ID,
    n.FileNo,
    n.QcLevel,
    d.DonorRel
INTO dbo.QcLjDatCopy_2026
FROM (
    SELECT
        r.ID,
        RTRIM(r.FileNo) AS FileNo,
        l.QcLevel,
        ROW_NUMBER() OVER (PARTITION BY l.QcLevel ORDER BY r.ID) AS rn
    FROM dbo.QcLjRecord r
    INNER JOIN dbo.QcLjRefLimit l ON RTRIM(l.FileNo) = RTRIM(r.FileNo)
    WHERE RTRIM(r.FileNo) IN ('43','44','45','46','47','48','49','50','51','52','53','54','55','56','57','58','59','60','61','62','63')
) n
INNER JOIN (
    SELECT
        CASE RTRIM(FileNo) WHEN '1' THEN 0 WHEN '2' THEN 1 WHEN '3' THEN 2 END AS QcLevel,
        RTRIM(ScatterGraphPath) AS DonorRel,
        ROW_NUMBER() OVER (PARTITION BY RTRIM(FileNo) ORDER BY ID) AS rn,
        COUNT(*) OVER (PARTITION BY RTRIM(FileNo)) AS cnt
    FROM dbo.QcLjRecord
    WHERE RTRIM(FileNo) IN ('1','2','3')
      AND ScatterGraphPath IS NOT NULL
      AND RTRIM(ScatterGraphPath) <> ''
) d ON d.QcLevel = n.QcLevel
   AND d.rn = ((n.rn - 1) % d.cnt) + 1;

PRINT 'Mapped rows: ' + CONVERT(varchar(12), @@ROWCOUNT);

BEGIN TRANSACTION;

UPDATE r
SET
    ScatterGraphPath = m.DonorRel,
    WBCLineL = CASE m.QcLevel WHEN 0 THEN 9 WHEN 1 THEN 9 ELSE 11 END,
    WBCLineM = CASE m.QcLevel WHEN 0 THEN 62 WHEN 1 THEN 65 ELSE 69 END,
    WBCLineR = 255,
    RBCLineL = CASE m.QcLevel WHEN 0 THEN 25 WHEN 1 THEN 30 ELSE 30 END,
    RBCLineR = CASE m.QcLevel WHEN 0 THEN 154 WHEN 1 THEN 180 ELSE 202 END,
    PLTLineL = 3,
    PLTLineR = CASE m.QcLevel WHEN 0 THEN 41 ELSE 49 END
FROM dbo.QcLjRecord r
INNER JOIN dbo.QcLjDatCopy_2026 m ON m.ID = r.ID;

PRINT 'Updated records: ' + CONVERT(varchar(12), @@ROWCOUNT);

IF (SELECT COUNT(*) FROM dbo.QcLjRecord r
    INNER JOIN dbo.QcLjDatCopy_2026 m ON m.ID = r.ID
    WHERE r.ScatterGraphPath IS NULL OR RTRIM(r.ScatterGraphPath) = '') > 0
BEGIN
    ROLLBACK TRANSACTION;
    RAISERROR('Some File 43-63 rows still have no ScatterGraphPath', 16, 1);
    RETURN;
END

COMMIT TRANSACTION;
PRINT 'COMMITTED - File 43-63 now point at existing File 1/2/3 .dat files.';

SELECT RTRIM(FileNo) FileNo, COUNT(*) n
FROM dbo.QcLjRecord
WHERE RTRIM(FileNo) IN ('43','44','45','46','47','48','49','50','51','52','53','54','55','56','57','58','59','60','61','62','63')
  AND ScatterGraphPath IS NOT NULL
GROUP BY RTRIM(FileNo)
ORDER BY CONVERT(int, RTRIM(FileNo));
GO
