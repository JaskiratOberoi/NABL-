#!/usr/bin/env python3
"""Rebuild Biolis 30i Calibration Data printouts as a single PDF.

Each sheet is a 1-page instrument-style report. The footer is always
"Page 1" (the originals print "1Page"). Years are shifted +1 so the
binder covers Sep 2025 through Sep 2026 (2025→2026, 2024→2025).
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from reportlab.lib.colors import Color, black, white
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

ROOT = Path(__file__).resolve().parents[1]
PARSED = ROOT / "_parsed"
OUT_PDF = ROOT / "Calibration Data 2026.pdf"
CANONICAL = PARSED / "canonical-pages.json"

SKIP_FILES = {
    "20260908_123713",  # accidental desk photo
    "20260908_123113",  # retake of 123109
    "20260908_124542",  # retake of 123859
}

# Arial matches the analyser print closer than Helvetica.
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

GRAY = Color(0.91, 0.91, 0.91)
LINE = Color(0.15, 0.15, 0.15)

# Column fractions of table width (Date/Time is the wide left column).
COLS = [
    ("Date / Time", 0.26),
    ("Item", 0.13),
    ("Specimen", 0.12),
    ("Lot No", 0.11),
    ("Tray", 0.08),
    ("Pos", 0.07),
    ("Result", 0.12),
    ("Cal. Error", 0.11),
]


def shift_year(dt: str) -> str:
    """Shift the printed year by one. 2025 must be replaced first so that
    2024→2025 does not then get bumped to 2026."""
    return dt.replace("2025", "2026").replace("2024", "2025")


def load_pages() -> list[dict]:
    pages = []
    for i in range(1, 7):
        pages.extend(json.loads((PARSED / f"batch{i}.json").read_text()))
    kept = []
    for p in pages:
        if p.get("skip") or p["file"] in SKIP_FILES:
            continue
        rows = []
        for r in p.get("rows") or []:
            rows.append(
                {
                    "datetime": shift_year(r["datetime"]),
                    "item": r["item"] or "",
                    "specimen": r["specimen"] or "",
                    "lot": r["lot"] or "",
                    "tray": r["tray"] or "",
                    "pos": r["pos"] or "",
                    "result": r["result"] or "",
                }
            )
        if not rows:
            continue
        first = datetime.strptime(rows[0]["datetime"], "%d-%m-%Y %H:%M:%S")
        kept.append({"file": p["file"], "rows": rows, "sort": first})
    kept.sort(key=lambda p: p["sort"], reverse=True)
    return kept


def draw_page(c: canvas.Canvas, rows: list[dict]) -> None:
    w, h = A4
    left = 18
    right = w - 18
    table_w = right - left
    title_y = h - 28

    c.setFillColor(black)
    c.setFont(FONT, 13)
    c.drawCentredString(w / 2, title_y, "Calibration Data")

    # Compact enough that a 38-row sheet still sits on one A4 page
    # the way the analyser prints it.
    row_h = 12.2
    header_h = 14.0
    table_top = title_y - 16

    xs = [left]
    for _, frac in COLS:
        xs.append(xs[-1] + frac * table_w)

    def col_left(i: int) -> float:
        return xs[i] + 4

    # Header rules
    c.setStrokeColor(LINE)
    c.setLineWidth(0.6)
    c.line(left, table_top, right, table_top)
    c.line(left, table_top - header_h, right, table_top - header_h)

    c.setFont(FONT, 8)
    header_baseline = table_top - header_h + 4.2
    for i, (label, _) in enumerate(COLS):
        c.drawString(col_left(i), header_baseline, label)

    y = table_top - header_h
    for idx, row in enumerate(rows):
        y_bottom = y - row_h
        if idx % 2 == 1:
            c.setFillColor(GRAY)
            c.rect(left, y_bottom, table_w, row_h, stroke=0, fill=1)
        c.setFillColor(black)
        c.setFont(FONT, 8)
        vals = [
            row["datetime"],
            row["item"],
            row["specimen"],
            row["lot"],
            row["tray"],
            row["pos"],
            row["result"],
            "",
        ]
        baseline = y_bottom + 3.6
        for i, val in enumerate(vals):
            c.drawString(col_left(i), baseline, str(val))
        y = y_bottom

    # Footer always reads Page 1 — each sheet is a 1-page instrument print.
    c.setFont(FONT, 9)
    c.drawRightString(right, 22, "Page 1")


def main() -> None:
    pages = load_pages()
    CANONICAL.parent.mkdir(exist_ok=True)
    serial = [{"file": p["file"], "rows": p["rows"]} for p in pages]
    CANONICAL.write_text(json.dumps(serial, indent=2) + "\n")

    c = canvas.Canvas(str(OUT_PDF), pagesize=A4)
    c.setTitle("Calibration Data")
    c.setAuthor("Noble Diagnostic Centre")
    for p in pages:
        draw_page(c, p["rows"])
        c.showPage()
    c.save()
    print(f"wrote {OUT_PDF}  pages={len(pages)}  rows={sum(len(p['rows']) for p in pages)}")


if __name__ == "__main__":
    main()
