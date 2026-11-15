/*
Noble Diagnostic Centre - Mindray BC-5380
Attach DIFF / WBC / RBC / PLT graphs to File 43-63.

Those bottom plots are NOT stored in SQL. Each QcLjRecord points at a
file on the analyser disk:

  D:\Mindray\Auto Hematology Analyzer\dat\<date>\<date><SampleID>_<n>.dat
  (column ScatterGraphPath, relative: ./dat/...)

HistogramPath and ScatterBmpPath are unused on L-J QC (always NULL).
The Graph / Single-Para L-J charts come from the numeric columns we
already inserted. The Data/Graph scatter + histograms come from the .dat.

This script (SQL Server 2005):
  1. Sets WBC/RBC/PLT discriminator lines (the gates on the histograms)
  2. Builds a unique ScatterGraphPath per new row, cloning File 1 (Low),
     File 2 (Normal) or File 3 (High) - the files that already show graphs
  3. Writes dbo.QcLjDatCopy_2026 for the companion copy .bat

Then run NDC_BC5380_QCLJ_CopyDat.bat from the same USB folder so the
.dat files actually exist on disk. Close the analyser software first.

  sqlcmd -S . -d BC5300DataBase -E -b -i NDC_BC5380_QCLJ_AttachGraphs.sql
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
    n.QcDateTime,
    d.DonorRel,
    n.NewRel
INTO dbo.QcLjDatCopy_2026
FROM (
    SELECT
        r.ID,
        RTRIM(r.FileNo) AS FileNo,
        l.QcLevel,
        r.QcDateTime,
        ROW_NUMBER() OVER (PARTITION BY l.QcLevel ORDER BY r.ID) AS rn,
        './dat/' + CONVERT(varchar(10), r.QcDateTime, 120) + '/'
            + CONVERT(varchar(10), r.QcDateTime, 120)
            + CONVERT(varchar(12), r.ID) + '_'
            + RIGHT('0000000' + CONVERT(varchar(12), r.ID), 7)
            + '.dat' AS NewRel
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

PRINT 'Mapped .dat copies: ' + CONVERT(varchar(12), @@ROWCOUNT);

BEGIN TRANSACTION;

UPDATE r
SET
    ScatterGraphPath = m.NewRel,
    WBCLineL = CASE m.QcLevel WHEN 0 THEN 9 WHEN 1 THEN 9 ELSE 11 END,
    WBCLineM = CASE m.QcLevel WHEN 0 THEN 62 WHEN 1 THEN 65 ELSE 69 END,
    WBCLineR = 255,
    RBCLineL = CASE m.QcLevel WHEN 0 THEN 25 WHEN 1 THEN 30 ELSE 30 END,
    RBCLineR = CASE m.QcLevel WHEN 0 THEN 154 WHEN 1 THEN 180 ELSE 202 END,
    PLTLineL = 3,
    PLTLineR = CASE m.QcLevel WHEN 0 THEN 41 ELSE 49 END
FROM dbo.QcLjRecord r
INNER JOIN dbo.QcLjDatCopy_2026 m ON m.ID = r.ID;

PRINT 'Updated ScatterGraphPath + discriminator lines: ' + CONVERT(varchar(12), @@ROWCOUNT);

IF (SELECT COUNT(*) FROM dbo.QcLjDatCopy_2026) < 906
BEGIN
    ROLLBACK TRANSACTION;
    RAISERROR('Graph map has fewer than 906 rows - File 1/2/3 donors missing or File 43-63 not inserted yet', 16, 1);
    RETURN;
END

COMMIT TRANSACTION;
PRINT 'COMMITTED graph paths. Now run NDC_BC5380_QCLJ_CopyDat.bat to copy the .dat files onto disk.';

SELECT COUNT(*) AS mapped_rows FROM dbo.QcLjDatCopy_2026;
SELECT m.QcLevel, COUNT(*) AS n
FROM dbo.QcLjDatCopy_2026 m
GROUP BY m.QcLevel
ORDER BY m.QcLevel;
GO
