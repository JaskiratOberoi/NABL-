#!/usr/bin/env python3
"""Build SQL batches for QC LJ insert. Does not talk to the server."""
from __future__ import annotations

import json
from pathlib import Path

ASSETS = Path(__file__).resolve().parent
DRY = ASSETS.parent / "_db-backup" / "dry-run"
SQL_DIR = ASSETS.parent / "_db-backup" / "sql"
SQL_DIR.mkdir(parents=True, exist_ok=True)

FILE_NOS = [str(n) for n in range(43, 64)]
IN_LIST = ",".join(f"'{n}'" for n in FILE_NOS)

REC_COLS = [
    "FileNo",
    "Operator",
    "IsCounting",
    "QcDateTime",
    "QcTime",
    "LoseCtrlCode",
    "LoseCtrlReason",
    "NewBottle",
    "WBC",
    "Bas#",
    "Bas_Percent",
    "Neu#",
    "Neu_Percent",
    "Eos#",
    "Eos_Percent",
    "Lym#",
    "Lym_Percent",
    "Mon#",
    "Mon_Percent",
    "RBC",
    "HGB",
    "MCV",
    "MCH",
    "MCHC",
    "RDW_CV",
    "RDW_SD",
    "HCT",
    "PLT",
    "MPV",
    "PDW",
    "PCT",
    "GRAN_X",
    "GRAN_Y",
    "GRAN_YW",
    "TestSeq",
    "InstrumentSN",
]

LIM_SET_COLS = [
    "LotNo",
    "ValidDate",
    "BloodMode",
    "QcLevel",
    "Setter",
    "OpenScanner",
    "CalType",
    "CalRange",
    "HasSet_Flag",
    "HasData_Flag",
    "HasDoLjAfterSetSampleID",
    "NotPromptOnFull",
    "WBC_Ref",
    "WBC_Limit",
    "Bas#_Ref",
    "Bas#_Limit",
    "Bas_Percent_Ref",
    "Bas_Percent_Limit",
    "Neu#_Ref",
    "Neu#_Limit",
    "Neu_Percent_Ref",
    "Neu_Percent_Limit",
    "Eos#_Ref",
    "Eos#_Limit",
    "Eos_Percent_Ref",
    "Eos_Percent_Limit",
    "Lym#_Ref",
    "Lym#_Limit",
    "Lym_Percent_Ref",
    "Lym_Percent_Limit",
    "Mon#_Ref",
    "Mon#_Limit",
    "Mon_Percent_Ref",
    "Mon_Percent_Limit",
    "ALY#_Ref",
    "ALY#_Limit",
    "ALY_Percent_Ref",
    "ALY_Percent_Limit",
    "LIC#_Ref",
    "LIC#_Limit",
    "LIC_Percent_Ref",
    "LIC_Percent_Limit",
    "RBC_Ref",
    "RBC_Limit",
    "HGB_Ref",
    "HGB_Limit",
    "MCV_Ref",
    "MCV_Limit",
    "MCH_Ref",
    "MCH_Limit",
    "MCHC_Ref",
    "MCHC_Limit",
    "RDW_CV_Ref",
    "RDW_CV_Limit",
    "RDW_SD_Ref",
    "RDW_SD_Limit",
    "HCT_Ref",
    "HCT_Limit",
    "PLT_Ref",
    "PLT_Limit",
    "MPV_Ref",
    "MPV_Limit",
    "PDW_Ref",
    "PDW_Limit",
    "PCT_Ref",
    "PCT_Limit",
    "GRAN_X_Ref",
    "GRAN_X_Limit",
    "GRAN_Y_Ref",
    "GRAN_Y_Limit",
    "GRAN_YW_Ref",
    "GRAN_YW_Limit",
    "WBC_MCV_Ref",
    "WBC_MCV_Limit",
]


def ident(name: str) -> str:
    return f"[{name}]"


def lit(v) -> str:
    if v is None:
        return "NULL"
    if isinstance(v, bool):
        return "1" if v else "0"
    if isinstance(v, int):
        return str(v)
    if isinstance(v, float):
        return str(v)
    return "N'" + str(v).replace("'", "''") + "'"


def main():
    payload = json.loads((DRY / "proposed-inserts.json").read_text())
    batches = []

    batches.append(
        (
            "00_backup_tables",
            f"""
IF OBJECT_ID('dbo.QcLjRecord_bak_20261016','U') IS NOT NULL DROP TABLE dbo.QcLjRecord_bak_20261016;
IF OBJECT_ID('dbo.QcLjRefLimit_bak_20261016','U') IS NOT NULL DROP TABLE dbo.QcLjRefLimit_bak_20261016;
SELECT * INTO dbo.QcLjRecord_bak_20261016
FROM dbo.QcLjRecord
WHERE RTRIM(FileNo) IN ({IN_LIST});
SELECT * INTO dbo.QcLjRefLimit_bak_20261016
FROM dbo.QcLjRefLimit
WHERE RTRIM(FileNo) IN ({IN_LIST});
""".strip(),
        )
    )
    batches.append(
        (
            "01_delete_records",
            f"DELETE FROM dbo.QcLjRecord WHERE RTRIM(FileNo) IN ({IN_LIST});",
        )
    )

    for i, lim in enumerate(payload["limits"], 1):
        fno = lim["FileNo"]
        assigns = []
        for col in LIM_SET_COLS:
            assigns.append(f"{ident(col)} = {lit(lim.get(col))}")
        assigns.append(f"{ident('ModifiedDataTime')} = GETDATE()")
        if lim["action"] == "UPDATE":
            sql = (
                f"UPDATE dbo.QcLjRefLimit SET {', '.join(assigns)} "
                f"WHERE RTRIM(FileNo) = '{fno}';"
            )
        else:
            cols = ["FileNo"] + LIM_SET_COLS + ["ModifiedDataTime"]
            vals = [lit(fno)] + [lit(lim.get(c)) for c in LIM_SET_COLS] + ["GETDATE()"]
            sql = (
                f"INSERT INTO dbo.QcLjRefLimit ({', '.join(ident(c) for c in cols)}) "
                f"VALUES ({', '.join(vals)});"
            )
        batches.append((f"02_limit_{fno}", sql))

    seq = 80387
    recs = payload["records"]
    chunk = 20
    part = 0
    for offset in range(0, len(recs), chunk):
        part += 1
        rows = recs[offset : offset + chunk]
        values = []
        for rec in rows:
            rec = dict(rec)
            rec["TestSeq"] = seq
            seq += 1
            values.append(
                "(" + ", ".join(lit(rec.get(c)) for c in REC_COLS) + ")"
            )
        sql = (
            "INSERT INTO dbo.QcLjRecord ("
            + ", ".join(ident(c) for c in REC_COLS)
            + ") VALUES\n"
            + ",\n".join(values)
            + ";"
        )
        batches.append((f"03_records_{part:02d}", sql))

    batches.append(
        (
            "04_sampleid",
            """
UPDATE r SET SampleID = r.ID
FROM dbo.QcLjRecord r
WHERE RTRIM(r.FileNo) IN ("""
            + IN_LIST
            + """)
  AND r.SampleID IS NULL;
""",
        )
    )
    batches.append(
        (
            "05_verify",
            f"""
SELECT RTRIM(FileNo) FileNo, COUNT(*) n, MIN(QcDateTime) mn, MAX(QcDateTime) mx
FROM dbo.QcLjRecord
WHERE RTRIM(FileNo) IN ({IN_LIST})
GROUP BY RTRIM(FileNo);
SELECT RTRIM(FileNo) FileNo, RTRIM(LotNo) LotNo, QcLevel, WBC_Ref, WBC_Limit, HasData_Flag
FROM dbo.QcLjRefLimit
WHERE RTRIM(FileNo) IN ({IN_LIST});
SELECT COUNT(*) recs FROM dbo.QcLjRecord WHERE RTRIM(FileNo) IN ({IN_LIST});
SELECT COUNT(*) bak FROM dbo.QcLjRecord_bak_20261016;
""",
        )
    )

    manifest = []
    for name, sql in batches:
        path = SQL_DIR / f"{name}.sql"
        path.write_text(sql.strip() + "\n")
        manifest.append({"name": name, "file": path.name, "chars": len(sql)})
    (SQL_DIR / "manifest.json").write_text(json.dumps(manifest, indent=2))
    print(f"{len(batches)} batches -> {SQL_DIR}")
    print("record batches", part, "rows", len(recs))


if __name__ == "__main__":
    main()
