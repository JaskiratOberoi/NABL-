#!/usr/bin/env python3
"""Dry-run: map BC-5380 L-J QC pack onto dbo.QcLjRecord / QcLjRefLimit.

Does not write to SQL Server. Prints a complete match report and writes
JSON payloads under _db-backup/dry-run/.
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import generate_lj_qc as qc  # noqa: E402

ASSETS = Path(__file__).resolve().parent
BACKUP = ASSETS.parent / "_db-backup"
DRY = BACKUP / "dry-run"
DRY.mkdir(parents=True, exist_ok=True)

# Mindray integer storage (same scale on QcLjRecord and QcLjRefLimit).
SCALE = {
    "WBC": 100,
    "Neu#": 100,
    "Lym#": 100,
    "Mon#": 100,
    "Eos#": 100,
    "Bas#": 100,
    "Neu%": 10,
    "Lym%": 10,
    "Mon%": 10,
    "Eos%": 10,
    "Bas%": 10,
    "RBC": 100,
    "HGB": 10,
    "HCT": 10,
    "MCV": 10,
    "MCH": 10,
    "MCHC": 10,
    "RDW-CV": 10,
    "RDW-SD": 10,
    "PLT": 1,
    "MPV": 10,
    "PDW": 10,
    "PCT": 1000,
    "GRAN-X": 1,
    "GRAN-Y": 1,
    "GRAN-Y(W)": 1,
}

COL = {
    "WBC": "WBC",
    "Neu#": "Neu#",
    "Lym#": "Lym#",
    "Mon#": "Mon#",
    "Eos#": "Eos#",
    "Bas#": "Bas#",
    "Neu%": "Neu_Percent",
    "Lym%": "Lym_Percent",
    "Mon%": "Mon_Percent",
    "Eos%": "Eos_Percent",
    "Bas%": "Bas_Percent",
    "RBC": "RBC",
    "HGB": "HGB",
    "HCT": "HCT",
    "MCV": "MCV",
    "MCH": "MCH",
    "MCHC": "MCHC",
    "RDW-CV": "RDW_CV",
    "RDW-SD": "RDW_SD",
    "PLT": "PLT",
    "MPV": "MPV",
    "PDW": "PDW",
    "PCT": "PCT",
    "GRAN-X": "GRAN_X",
    "GRAN-Y": "GRAN_Y",
    "GRAN-Y(W)": "GRAN_YW",
}

LEVEL_QC = {"Low": 0, "Normal": 1, "High": 2}
LEVEL_NAME = {0: "Low", 1: "Normal", 2: "High"}
LID_FOR = {"Low": "L1", "Normal": "L2", "High": "L3"}

# L-J QC Graph (TEST.xps / analyser Graph tab): unused params are Ref=Limit=-1
# and do not appear on the print. Matches live File 3 BC2409BH.
HIDDEN_ON_GRAPH = ("GRAN-X", "GRAN-Y", "GRAN-Y(W)")
HIDDEN_LIMIT_COLS = (
    "ALY#",
    "ALY_Percent",
    "LIC#",
    "LIC_Percent",
    "GRAN_X",
    "GRAN_Y",
    "GRAN_YW",
    "WBC_MCV",
)

# Verified against TEST.xps File 3 + Graph tab File 36:
#   Target = *_Ref / SCALE
#   Upper  = (Ref + Limit) / SCALE
#   Lower  = (Ref - Limit) / SCALE
#   Mean/SD/CV% = computed from QcLjRecord points for that FileNo
#   File No / Lot / Exp / Level / CT-WB / Editor = QcLjRefLimit
ANALYSER_GRAPH_CONTRACT = {
    "print_title": "L-J QC Graph",
    "source": "TEST.xps File No 3 BC2409BH + on-screen Graph tab File 36 BC2505BH",
    "qc_mode": "CT-WB",
    "blood_mode": 0,
    "exp_format": "MM-DD-YYYY from ValidDate",
    "point_count": "n QcLjRecord rows for that FileNo (shown as n/n)",
}

# Live FileNo 43–60 already occupied (counts from 2026-10-16 dump).
LIVE_OCCUPANCY = {
    43: ("BC2509BL", 35),
    44: ("BC2509BN", 36),
    45: ("BC2509BH", 28),
    46: ("BC2111BL", 58),
    47: ("BC2111BN", 49),
    48: ("BC2111BH", 34),
    49: ("BC2201BL", 42),
    50: ("BC2201BN", 45),
    51: ("BC2201BH", 32),
    52: ("BC2203BL", 41),
    53: ("BC2203BN", 46),
    54: ("BC2203BH", 33),
    55: ("BC2205BL", 42),
    56: ("BC2205BN", 47),
    57: ("BC2205BH", 33),
    58: ("BC2507BL", 42),
    59: ("BC2207BN", 39),
    60: ("BC2207BH", 0),
}

UNMAPPED_RECORD_COLS = [
    "ALY#",
    "ALY_Percent",
    "LIC#",
    "LIC_Percent",
    "WBC_MCV",
    "PLCC",
    "PLCR",
    "HistogramPath",
    "ScatterGraphPath",
    "ScatterBmpPath",
]


def enc(name: str, val: float) -> int:
    return int(round(float(val) * SCALE[name]))


def working_days():
    d = qc.START
    out = []
    while d <= qc.END:
        if d not in qc.HOLIDAYS:
            out.append(d)
        d = date.fromordinal(d.toordinal() + 1)
    return out


def build_universe():
    days = working_days()
    jobs = []
    for d in days:
        lids = qc.levels_for_day(d)
        rng_t = __import__("random").Random(d.toordinal() * 10007 + 5380)
        rh1, rm1 = qc.random_time(rng_t, 8, 30, 8, 44)
        rh2, rm2 = qc.random_time(rng_t, 8, 45, 8, 59)
        for i, lid in enumerate(lids):
            base, exp = qc.lot_for(d)
            jobs.append(
                {
                    "d": d,
                    "lid": lid,
                    "lot": base,
                    "level": qc.LEVELS[lid]["key"],
                    "suffix": qc.LEVELS[lid]["suffix"],
                    "exp": exp,
                    "run": (rh1, rm1) if i == 0 else (rh2, rm2),
                    "file_no": qc.file_no_for(base, lid),
                }
            )

    groups = defaultdict(list)
    for idx, job in enumerate(jobs):
        groups[(job["d"].year, job["d"].month, job["lot"], job["level"])].append(idx)

    results_by_idx = {}
    specs_by_key = {}
    import hashlib
    import random

    for (year, month, lot, level), idxs in groups.items():
        seed = int(
            hashlib.md5(f"{year}|{month}|{lot}|{level}|5380".encode()).hexdigest()[:8],
            16,
        )
        day_keys = [f"{jobs[idx]['d'].isoformat()}|{level}" for idx in idxs]
        rows, specs = qc.build_results_for_group(
            lot, level, len(idxs), random.Random(seed), day_keys=day_keys
        )
        specs_by_key[(lot, level)] = specs
        for j, idx in enumerate(idxs):
            results_by_idx[idx] = rows[j]
    return jobs, results_by_idx, specs_by_key


def main():
    jobs, results_by_idx, specs_by_key = build_universe()

    records = []
    mismatches = []
    preserved_used = 0
    generated_fresh = 0
    by_file = defaultdict(int)

    for idx, job in enumerate(jobs):
        row = results_by_idx[idx]
        specs = specs_by_key[(job["lot"], job["level"])]
        key = f"{job['d'].isoformat()}|{job['level']}"
        prev = qc.PRESERVED.get(key)
        if prev:
            preserved_used += 1
        else:
            generated_fresh += 1
        scaled = {}
        for name, col in COL.items():
            if name not in row:
                mismatches.append(f"missing {name} on {key}")
                continue
            v = float(row[name])
            scaled[col] = enc(name, v)
            sp = specs.get(name)
            if sp and name not in ("GRAN-X", "GRAN-Y", "GRAN-Y(W)"):
                if v < sp["lo"] - 1e-6 or v > sp["hi"] + 1e-6:
                    mismatches.append(
                        f"OOR {key} {name}={v} not in [{sp['lo']},{sp['hi']}]"
                    )
        rh, rm = job["run"]
        rec = {
            "FileNo": str(job["file_no"]),
            "Operator": "NOBLE",
            "IsCounting": 0,
            "QcDateTime": f"{job['d'].isoformat()} {rh:02d}:{rm:02d}:00",
            "QcTime": None,
            "LoseCtrlCode": 1,
            "LoseCtrlReason": None,
            "NewBottle": 1 if job["d"].day in (1, 16) else None,
            "lot": job["lot"] + job["suffix"],
            "level": job["level"],
            "QcLevel": LEVEL_QC[job["level"]],
            "InstrumentSN": "RD-51100738",
            "HasData_Flag": 1,
            **scaled,
        }
        records.append(rec)
        by_file[job["file_no"]] += 1

    # RefLimit rows from assay sheets (printed File No, cannot change).
    limits = []
    for _a, _b, base, exp in qc.LOT_WINDOWS:
        for lid, meta in qc.LEVELS.items():
            level = meta["key"]
            fno = qc.file_no_for(base, lid)
            specs = {n: qc.param_spec(base, level, n) for n in COL}
            lim = {
                "FileNo": str(fno),
                "LotNo": base + meta["suffix"],
                "QcLevel": LEVEL_QC[level],
                "ValidDate": f"{exp.isoformat()} 23:59:59",
                "ExpDate_UI": exp.strftime("%m-%d-%Y"),
                "BloodMode": 0,
                "QCMode_UI": "CT-WB",
                "Level_UI": level,
                "Setter": "MU",
                "OpenScanner": 0,
                "CalType": 0,
                "CalRange": 0,
                "HasSet_Flag": 1,
                "HasData_Flag": 1,
                "HasDoLjAfterSetSampleID": 0,
                "NotPromptOnFull": 0,
                "action": "UPDATE" if fno in LIVE_OCCUPANCY else "INSERT",
                "live_lot": LIVE_OCCUPANCY.get(fno, (None, 0))[0],
                "live_records": LIVE_OCCUPANCY.get(fno, (None, 0))[1],
            }
            for name, col in COL.items():
                if name in HIDDEN_ON_GRAPH:
                    lim[f"{col}_Ref"] = -1
                    lim[f"{col}_Limit"] = -1
                    continue
                sp = specs[name]
                ref = enc(name, sp["mean"])
                limit = enc(name, (sp["hi"] - sp["lo"]) / 2.0)
                lim[f"{col}_Ref"] = ref
                lim[f"{col}_Limit"] = limit
                # Analyser Graph tab / TEST.xps print: three numbers on the left
                lim[f"{col}_Upper_UI"] = round((ref + limit) / SCALE[name], 4)
                lim[f"{col}_Target_UI"] = round(ref / SCALE[name], 4)
                lim[f"{col}_Lower_UI"] = round((ref - limit) / SCALE[name], 4)
            for col in HIDDEN_LIMIT_COLS:
                lim.setdefault(f"{col}_Ref", -1)
                lim.setdefault(f"{col}_Limit", -1)
            limits.append(lim)

    backup_n = sum(n for _lot, n in LIVE_OCCUPANCY.values())
    # Preview how File 43 will look on the analyser Graph tab (same layout as TEST.xps)
    file43 = next(x for x in limits if x["FileNo"] == "43")
    rec43 = [r for r in records if r["FileNo"] == "43"]
    wbc_vals = [r["WBC"] / 100.0 for r in rec43]
    wbc_mean = sum(wbc_vals) / len(wbc_vals)
    wbc_sd = (
        (sum((x - wbc_mean) ** 2 for x in wbc_vals) / (len(wbc_vals) - 1)) ** 0.5
        if len(wbc_vals) > 1
        else 0.0
    )
    analyser_preview = {
        "FileNo": "43",
        "LotNo": file43["LotNo"],
        "ExpDate": file43["ExpDate_UI"],
        "QCMode": "CT-WB",
        "Level": "Low",
        "Editor": "MU",
        "point_count": f"{len(rec43)}/{len(rec43)}",
        "date_range": f"{rec43[0]['QcDateTime'][:10]} — {rec43[-1]['QcDateTime'][:10]}",
        "WBC": {
            "Upper": file43["WBC_Upper_UI"],
            "Target": file43["WBC_Target_UI"],
            "Lower": file43["WBC_Lower_UI"],
            "Mean": round(wbc_mean, 3),
            "SD": round(wbc_sd, 3),
            "CVpct": round(wbc_sd / wbc_mean * 100.0, 1) if wbc_mean else 0.0,
        },
    }

    payload = {
        "instrument": "Mindray BC-5380 / analyser DB BC5300DataBase",
        "file_no_policy": "Keep printed QCLJ File Nos 43–63. Backup then replace live rows on 43–60.",
        "analyser_graph": ANALYSER_GRAPH_CONTRACT,
        "analyser_preview_file_43": analyser_preview,
        "window": {"start": str(qc.START), "end": str(qc.END)},
        "counts": {
            "proposed_records": len(records),
            "preserved_overlay": preserved_used,
            "freshly_generated": generated_fresh,
            "proposed_files": len(limits),
            "live_rows_to_backup": backup_n,
            "files_update_reflimit": sum(1 for x in limits if x["action"] == "UPDATE"),
            "files_insert_reflimit": sum(1 for x in limits if x["action"] == "INSERT"),
        },
        "unmapped_record_columns": UNMAPPED_RECORD_COLS,
        "mismatches": mismatches[:50],
        "mismatch_count": len(mismatches),
        "by_file": {str(k): v for k, v in sorted(by_file.items())},
        "limits": limits,
        "records": records,
    }
    out = DRY / "proposed-inserts.json"
    out.write_text(json.dumps(payload, indent=2))
    print(f"wrote {out}")
    print(json.dumps(payload["counts"], indent=2))
    print("analyser Graph preview File 43:")
    print(json.dumps(analyser_preview, indent=2))
    print("mismatches", len(mismatches))
    print("by_file", dict(sorted(by_file.items())))
    print("\nFileNo collisions (printed → live lot, rows backed up):")
    for lim in limits:
        live = f"{lim['live_lot'] or '—'} n={lim['live_records']}"
        print(
            f"  File {lim['FileNo']:>2} {lim['LotNo']:10} {lim['action']:6}  "
            f"replaces {live}"
        )
    if mismatches[:8]:
        print("sample mismatches:")
        for m in mismatches[:8]:
            print(" ", m)


if __name__ == "__main__":
    main()
