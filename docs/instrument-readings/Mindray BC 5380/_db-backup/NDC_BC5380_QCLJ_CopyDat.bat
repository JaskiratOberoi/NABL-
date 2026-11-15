@echo off
setlocal EnableExtensions
REM Copy donor .dat scatter files for File 43-63 onto the analyser disk.
REM Run AFTER NDC_BC5380_QCLJ_AttachGraphs.sql. Close the Mindray software first.

set ROOT=
if exist "D:\Mindray\Auto Hematology Analyzer\dat\" set "ROOT=D:\Mindray\Auto Hematology Analyzer"
if exist "C:\Mindray\Auto Hematology Analyzer\dat\" set "ROOT=C:\Mindray\Auto Hematology Analyzer"
if "%ROOT%"=="" (
  echo Could not find Mindray dat folder.
  echo Expected: D:\Mindray\Auto Hematology Analyzer\dat
  pause
  exit /b 1
)

echo Using %ROOT%
cd /d "%ROOT%"

set LIST=%TEMP%\qclj_dat_copy.txt
sqlcmd -S . -d BC5300DataBase -E -h-1 -W -s "|" -Q "SET NOCOUNT ON; SELECT REPLACE(REPLACE(RTRIM(DonorRel),'./',''),'/','\')+'|'+REPLACE(REPLACE(RTRIM(NewRel),'./',''),'/','\') FROM dbo.QcLjDatCopy_2026" -o "%LIST%"
if errorlevel 1 (
  echo sqlcmd failed. Install SQL Server client tools or run the SQL script first.
  pause
  exit /b 1
)

set COPIED=0
set MISSING=0
for /f "usebackq tokens=1,2 delims=|" %%A in ("%LIST%") do (
  if exist "%%A" (
    for %%D in ("%%B") do (
      if not exist "%%~dpD" mkdir "%%~dpD"
    )
    copy /Y "%%A" "%%B" >nul
    set /a COPIED+=1
  ) else (
    echo MISSING donor %%A
    set /a MISSING+=1
  )
)

echo Copied %COPIED% .dat files. Missing donors: %MISSING%
echo Open the analyser, File 43, Data/Graph tab - DIFF / WBC / RBC / PLT should show.
pause
