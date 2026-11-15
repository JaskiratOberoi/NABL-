#!/usr/bin/env python3
"""Rebuild Maglumi X3 Test Calibration printouts as one PDF.

Dates shift +1 year (2025→2026, then 2024→2025, then 2023→2024).
Lot numbers whose first two digits are a year (24… / 25…) increment that
prefix only (24→25, 25→26). Kit numbers and 00/01 lots are unchanged.
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from reportlab.lib.colors import Color, black
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

ROOT = Path(__file__).resolve().parents[1]
PARSED = ROOT / "_parsed"
OUT_PDF = ROOT / "Test Calibration 2026.pdf"

_ARIAL = Path("/System/Library/Fonts/Supplemental/Arial.ttf")
_ARIAL_BD = Path("/System/Library/Fonts/Supplemental/Arial Bold.ttf")
if _ARIAL.exists():
    pdfmetrics.registerFont(TTFont("CalSans", str(_ARIAL)))
    FONT = "CalSans"
else:
    FONT = "Helvetica"
if _ARIAL_BD.exists():
    pdfmetrics.registerFont(TTFont("CalSans-Bold", str(_ARIAL_BD)))
    FONT_BOLD = "CalSans-Bold"
else:
    FONT_BOLD = "Helvetica-Bold"

LINE = Color(0.35, 0.35, 0.35)
HEADER_BG = Color(0.82, 0.82, 0.82)
SNIBE_LOGO = Path(__file__).resolve().parent / "snibe.png"

CAL_COLS = [
    ("Reagent", 0.22),
    ("Lot-No.", 0.20),
    ("Kit-No.", 0.16),
    ("Calibrator 1 Mean", 0.21),
    ("Calibrator 2 Mean", 0.21),
]
SAMPLE_COLS = [
    ("Sample ID", 0.18),
    ("Assay", 0.14),
    ("RLU", 0.10),
    ("RLU CV (%)", 0.10),
    ("Conc.", 0.16),
    ("Flag", 0.08),
    ("Finish Time", 0.24),
]


def shift_year(text: str) -> str:
    return text.replace("2025", "2026").replace("2024", "2025").replace("2023", "2024")


def shift_lot(lot: str) -> str:
    lot = (lot or "").strip()
    if lot.startswith("24"):
        return "25" + lot[2:]
    if lot.startswith("25"):
        return "26" + lot[2:]
    return lot


def reagent_name(name: str) -> str:
    name = (name or "").strip()
    if name == "TESTOST II":
        return "TEST II"
    return name


def load_pages() -> list[dict]:
    pages = []
    for batch in ("batch1.json", "batch2.json", "batch3.json"):
        pages.extend(json.loads((PARSED / batch).read_text()))
    out = []
    for p in pages:
        if p.get("skip"):
            continue
        file = str(p.get("file") or "").replace(".jpg", "")
        kind = p["kind"]
        dt = shift_year(p["datetime"])
        rows = []
        if kind == "calibration":
            for r in p.get("rows") or []:
                rows.append(
                    {
                        "reagent": reagent_name(r.get("reagent") or ""),
                        "lot": shift_lot(r.get("lot") or ""),
                        "kit": (r.get("kit") or "").strip(),
                        "cal1": (r.get("cal1") or "").strip(),
                        "cal2": (r.get("cal2") or "").strip(),
                    }
                )
        else:
            for r in p.get("rows") or []:
                rows.append(
                    {
                        "sample_id": r.get("sample_id") or "",
                        "assay": r.get("assay") or "",
                        "rlu": r.get("rlu") or "",
                        "rlu_cv": r.get("rlu_cv") or "",
                        "conc": r.get("conc") or "",
                        "flag": r.get("flag") or "",
                        "finish": shift_year(r.get("finish") or ""),
                    }
                )
        sort = datetime.strptime(dt[:19], "%Y-%m-%d %H:%M:%S")
        out.append({"file": file, "kind": kind, "datetime": dt, "rows": rows, "sort": sort})
    out.sort(key=lambda p: p["sort"], reverse=True)
    return out


def draw_snibe(c: canvas.Canvas, x: float, y: float) -> None:
    logo_w = 56
    logo_h = logo_w * 165 / 341
    c.drawImage(
        str(SNIBE_LOGO),
        x,
        y,
        width=logo_w,
        height=logo_h,
        mask="auto",
        preserveAspectRatio=True,
    )


def draw_header(c: canvas.Canvas, dt: str, title: str) -> None:
    w, h = A4
    c.setFillColor(black)
    c.setFont(FONT, 8)
    c.drawString(36, h - 28, "Model: MAGLUMI X3")
    c.drawRightString(w - 36, h - 28, dt)
    c.setFont(FONT_BOLD, 12)
    c.drawCentredString(w / 2, h - 48, title)


def draw_table(
    c: canvas.Canvas,
    cols: list[tuple[str, float]],
    rows: list[list[str]],
    header_two_line: bool,
) -> None:
    w, h = A4
    left, right = 42, w - 42
    table_w = right - left
    table_top = h - 62
    pad = 5
    xs = [left]
    for _, frac in cols:
        xs.append(xs[-1] + frac * table_w)
    xs[-1] = right
    header_h = 26 if header_two_line else 16
    row_h = 15.5

    c.setFillColor(HEADER_BG)
    c.rect(left, table_top - header_h, table_w, header_h, stroke=0, fill=1)
    c.setStrokeColor(LINE)
    c.setLineWidth(0.55)
    c.rect(left, table_top - header_h, table_w, header_h, stroke=1, fill=0)
    for x in xs[1:-1]:
        c.line(x, table_top, x, table_top - header_h)

    c.setFillColor(black)
    if header_two_line:
        for i, (label, _) in enumerate(cols):
            if "Calibrator" in label:
                c.setFont(FONT, 7.5)
                c.drawString(xs[i] + pad, table_top - 10, label.replace(" Mean", ""))
                c.drawString(xs[i] + pad, table_top - 20, "Mean")
            else:
                c.setFont(FONT, 8)
                c.drawString(xs[i] + pad, table_top - 16, label)
    else:
        c.setFont(FONT, 8)
        for i, (label, _) in enumerate(cols):
            if label == "RLU CV (%)":
                c.setFont(FONT, 7.5)
                c.drawString(xs[i] + pad, table_top - 7, "RLU CV")
                c.drawString(xs[i] + pad, table_top - 15, "(%)")
            else:
                c.drawString(xs[i] + pad, table_top - 11, label)

    y = table_top - header_h
    for row in rows:
        c.setStrokeColor(LINE)
        c.rect(left, y - row_h, table_w, row_h, stroke=1, fill=0)
        for x in xs[1:-1]:
            c.line(x, y, x, y - row_h)
        c.setFillColor(black)
        c.setFont(FONT, 8)
        for i, val in enumerate(row):
            c.drawString(xs[i] + pad, y - 11, str(val))
        y -= row_h

    draw_snibe(c, 42, 28)
    c.setFillColor(black)
    c.setFont(FONT, 8)
    c.drawRightString(w - 42, 32, "Page 1 of 1")


def draw_calibration(c: canvas.Canvas, page: dict) -> None:
    draw_header(c, page["datetime"], "Calibration Result Report")
    rows = [[r["reagent"], r["lot"], r["kit"], r["cal1"], r["cal2"]] for r in page["rows"]]
    draw_table(c, CAL_COLS, rows, header_two_line=True)


def draw_sample(c: canvas.Canvas, page: dict) -> None:
    draw_header(c, page["datetime"], "Sample Result Report")
    rows = [
        [r["sample_id"], r["assay"], r["rlu"], r["rlu_cv"], r["conc"], r["flag"], r["finish"]]
        for r in page["rows"]
    ]
    draw_table(c, SAMPLE_COLS, rows, header_two_line=False)


def main() -> None:
    pages = load_pages()
    c = canvas.Canvas(str(OUT_PDF), pagesize=A4)
    c.setTitle("Immunoassay Test Calibration")
    c.setAuthor("Noble Diagnostic Centre")
    n_cal = n_sample = 0
    lots_shifted = 0
    for p in pages:
        if p["kind"] == "calibration":
            draw_calibration(c, p)
            n_cal += 1
            for r in p["rows"]:
                if r["lot"].startswith(("25", "26")):
                    lots_shifted += 1
        else:
            draw_sample(c, p)
            n_sample += 1
        c.showPage()
    c.save()
    canonical = [
        {"file": p["file"], "kind": p["kind"], "datetime": p["datetime"], "rows": p["rows"]}
        for p in pages
    ]
    (PARSED / "pages.json").write_text(json.dumps(canonical, indent=2) + "\n")
    print(f"wrote {OUT_PDF}")
    print(f"pages={len(pages)}  calibration={n_cal}  sample={n_sample}")
    print("newest", pages[0]["datetime"], pages[0]["file"])
    print("oldest", pages[-1]["datetime"], pages[-1]["file"])
    # show a few shifted lots
    print("example lots:")
    for p in pages[:3]:
        if p["kind"] == "calibration":
            print(" ", p["datetime"], [(r["reagent"], r["lot"]) for r in p["rows"][:4]])
            break


if __name__ == "__main__":
    main()
