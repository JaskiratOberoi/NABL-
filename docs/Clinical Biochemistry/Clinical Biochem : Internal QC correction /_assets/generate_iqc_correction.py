#!/usr/bin/env python3
"""Rebuild Clinical Biochemistry Internal QC correction binder as one print PDF.

Instrument printouts (Current QC + rerun slips) keep their data with years
shifted +1. Hand-filled NDC/DI/7.3.7 forms are recreated blank.
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from reportlab.lib.colors import Color, black
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

ROOT = Path(__file__).resolve().parents[1]
PARSED = ROOT / "_parsed"
OUT_PDF = ROOT / "Internal QC Correction 2026.pdf"
BRAND = Path("/Users/jas/Work/NABL 2026/app/public/brand")
FORM_PAGE = landscape(A4)
QC_PAGE = landscape(A4)
SLIP_PAGE = A4

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
MONO = "Courier"

GRAY = Color(0.91, 0.91, 0.91)
LINE = Color(0.2, 0.2, 0.2)

QC_COLS = [
    ("Date/Time", 0.26),
    ("Item", 0.13),
    ("Pos. No.", 0.12),
    ("Result", 0.11),
    ("Unit", 0.10),
    ("Min", 0.11),
    ("Max", 0.11),
    ("Error Code", 0.06),
]

ROOT_CAUSES = [
    "1) Reagent expiry, deterioration",
    "2) QC expiry, deterioration",
    "3) Equipment flag, functioning etc",
    "4) Environmental conditions",
    "5) Procedure violation",
    "6) Technician Fault",
]


def shift_year(text: str) -> str:
    return text.replace("2025", "2026").replace("2024", "2025")


def page1(c: canvas.Canvas, pagesize) -> None:
    w, _ = pagesize
    c.setFillColor(black)
    c.setFont(FONT, 9)
    c.drawRightString(w - 22, 16, "Page 1")


def draw_footer(c: canvas.Canvas, left: float, right: float, fy: float, fh: float) -> None:
    logo = BRAND / "ndc-logo.png"
    qm = BRAND / "sign-quality-manager.png"
    ld = BRAND / "sign-lab-director.png"
    logo_slot = 54
    inner_right = right - logo_slot
    c.setStrokeColor(LINE)
    c.setFillColor(black)
    c.setLineWidth(0.7)
    c.line(left, fy + fh, right, fy + fh)
    c.line(left, fy + 46, inner_right, fy + 46)
    c.line(left, fy + 32, inner_right, fy + 32)
    c.line(left, fy + 18, right, fy + 18)
    c.line(inner_right, fy, inner_right, fy + fh)
    mid = left + (inner_right - left) * 0.58
    c.line(mid, fy + 32, mid, fy + fh)
    c.setFont(FONT_BOLD, 10)
    c.drawString(left + 8, fy + 52, "NOBLE DIAGNOSTIC CENTRE")
    c.setFont(FONT, 8)
    c.drawString(mid + 6, fy + 52, "Doc No. NDC / DI / 7.3.7")
    c.drawString(left + 8, fy + 37, "Documented Information – Ensuring validity of examination results")
    c.drawString(mid + 6, fy + 37, "Page 17 of clause 7.3.7")
    meta_w = (mid - left) / 4
    metas = [
        "Issue No. IV",
        "Issue Date: 01 04 2024",
        "Rev No. 00",
        "Revision Date: --",
    ]
    for i, m in enumerate(metas):
        x = left + i * meta_w
        if i:
            c.line(x, fy + 18, x, fy + 32)
        c.setFont(FONT, 7)
        c.drawString(x + 4, fy + 22, m)
    if qm.exists():
        c.drawImage(str(qm), left + 10, fy + 5, width=46, height=12, mask="auto", preserveAspectRatio=True)
    if ld.exists():
        c.drawImage(str(ld), left + 160, fy + 5, width=52, height=12, mask="auto", preserveAspectRatio=True)
    c.setFont(FONT, 6.5)
    c.drawString(left + 8, fy + 2, "Prepared By Quality Manager")
    c.drawString(left + 158, fy + 2, "Approved By Lab Director")
    c.line(mid, fy, mid, fy + 18)
    c.setFont(FONT_BOLD, 8)
    c.drawCentredString((mid + inner_right) / 2, fy + 5, "CONTROLLED COPY")
    if logo.exists():
        c.drawImage(
            str(logo),
            inner_right + 3,
            fy + 8,
            width=48,
            height=48,
            mask="auto",
            preserveAspectRatio=True,
        )


def draw_blank_form(c: canvas.Canvas) -> None:
    w, h = FORM_PAGE
    left, right = 18, w - 18
    fy, fh = 14, 64
    outer_top = h - 16
    table_w = right - left

    c.setFillColor(black)
    c.setFont(FONT_BOLD, 12)
    c.drawCentredString(w / 2, outer_top - 12, "IQC CORRECTIVE ACTION FORM")
    c.setFont(FONT, 8.5)
    c.drawCentredString(
        w / 2,
        outer_top - 25,
        "(Recording schedule – Whenever there is IQC outlier OR Westgard Rules violation)",
    )

    table_top = outer_top - 34
    table_bottom = fy + fh + 36
    fracs = [0.08, 0.11, 0.14, 0.08, 0.22, 0.13, 0.10, 0.07, 0.07]
    xs = [left]
    for frac in fracs:
        xs.append(xs[-1] + frac * table_w)
    xs[-1] = right

    header_h = 28
    header_bottom = table_top - header_h
    c.setStrokeColor(LINE)
    c.setLineWidth(0.7)
    c.line(left, table_top, right, table_top)
    c.line(left, header_bottom, right, header_bottom)
    c.line(left, table_bottom, right, table_bottom)
    for x in xs[1:-1]:
        c.line(x, table_top, x, table_bottom)

    labels = [
        "Date",
        "Test Parameter",
        "OUTLIER",
        "EQPT",
        "Root Cause – Please tick the reason",
        "Corrective Action Taken",
        "Preventive Action Taken",
        "Taken By (Sign of Tech)",
        "Verified By",
    ]
    c.setFillColor(black)
    for i, lab in enumerate(labels):
        cx = (xs[i] + xs[i + 1]) / 2
        if i == 2:
            c.setFont(FONT, 7.5)
            c.drawCentredString(cx, table_top - 11, "OUTLIER")
            c.setFont(FONT, 6)
            c.drawCentredString(cx, table_top - 21, "Daily QC Out / Monthly % CV")
            c.drawCentredString(cx, table_top - 29, "high Or Westgard Rule")
        elif i == 4:
            c.setFont(FONT, 7)
            c.drawCentredString(cx, table_top - 16, lab)
        elif i in (5, 6, 7):
            c.setFont(FONT, 7)
            words = lab.split()
            if len(words) > 2:
                c.drawCentredString(cx, table_top - 12, " ".join(words[:2]))
                c.drawCentredString(cx, table_top - 22, " ".join(words[2:]))
            else:
                c.drawCentredString(cx, table_top - 16, lab)
        else:
            c.setFont(FONT, 8)
            c.drawCentredString(cx, table_top - 16, lab)

    n_rows = 2
    body_h = header_bottom - table_bottom
    row_h = body_h / n_rows
    c.setStrokeColor(LINE)
    c.setLineWidth(0.7)
    for i in range(1, n_rows):
        c.line(left, header_bottom - i * row_h, right, header_bottom - i * row_h)
    c.setFont(FONT, 6.5)
    c.setFillColor(black)
    for r in range(n_rows):
        top = header_bottom - r * row_h
        for j, line in enumerate(ROOT_CAUSES):
            c.drawString(xs[4] + 4, top - 10 - j * 9.2, line)

    c.setFillColor(black)
    c.setFont(FONT, 8)
    c.drawString(
        left + 6,
        table_bottom - 12,
        "Acceptance Criteria: Daily QC value within range specified by manufacturer for that control OR Westgard rule violation.",
    )
    c.drawString(
        left + 6,
        table_bottom - 24,
        "Monthly % CV: < MU OR 5 % for Hematology and < 10 % for Biochemistry whichever is higher.",
    )
    draw_footer(c, left, right, fy, fh)
    c.setStrokeColor(LINE)
    c.setLineWidth(0.8)
    c.rect(left, fy, table_w, outer_top - fy, stroke=1, fill=0)


def draw_table(c, left, right, top, cols, rows, row_h=12.4, header_h=14.0, font_size=8):
    table_w = right - left
    xs = [left]
    for _, frac in cols:
        xs.append(xs[-1] + frac * table_w)
    xs[-1] = right

    y = top - header_h
    for idx, row in enumerate(rows):
        yb = y - row_h
        if idx % 2 == 1:
            c.setFillColor(GRAY)
            c.rect(left, yb, table_w, row_h, stroke=0, fill=1)
        c.setFillColor(black)
        c.setFont(FONT, font_size)
        for i, val in enumerate(row):
            c.drawString(xs[i] + 4, yb + 3.4, str(val))
        y = yb
    bottom = y

    c.setFillColor(black)
    c.setFont(FONT, font_size)
    for i, (label, _) in enumerate(cols):
        c.drawString(xs[i] + 4, top - header_h + 4.0, label)

    c.setStrokeColor(LINE)
    c.setLineWidth(0.7)
    c.rect(left, bottom, table_w, top - bottom, stroke=1, fill=0)
    c.line(left, top - header_h, right, top - header_h)
    for x in xs[1:-1]:
        c.line(x, top, x, bottom)
    return bottom


def draw_qc_page(c: canvas.Canvas, page: dict) -> None:
    w, h = QC_PAGE
    left, right = 22, w - 22
    y = h - 24
    c.setFillColor(black)
    c.setFont(FONT, 13)
    c.drawCentredString(w / 2, y, "Current QC")
    y -= 20

    def block(title: str, rows: list[dict], y: float) -> float:
        lot = page.get("lot") or ""
        exp = shift_year(page.get("exp") or "")
        c.setFont(FONT, 8.5)
        c.drawString(left, y, f"Control Name: {title}")
        c.drawString(left + 220, y, f"Lot No.: {lot}")
        c.drawString(left + 420, y, f"Exp. Date: {exp}")
        y -= 6
        data = [
            [
                shift_year(r["datetime"]),
                r.get("item") or "",
                r.get("pos") or "",
                r.get("result") or "",
                r.get("unit") or "",
                r.get("min") or "",
                r.get("max") or "",
                "",
            ]
            for r in rows
        ]
        return draw_table(c, left, right, y, QC_COLS, data, row_h=12.6, header_h=14.0, font_size=8) - 14

    y = block("QC NORM", page["norm"], y)
    block("QC PATH", page["path"], y)
    page1(c, QC_PAGE)


def draw_sample_page(c: canvas.Canvas, slip: dict) -> None:
    w, h = SLIP_PAGE
    left = 28
    y = h - 36
    dt = shift_year(slip.get("datetime") or "")
    sample = slip.get("sample") or ""
    name = slip.get("name") or ""

    c.setFillColor(black)
    c.setFont(MONO, 9)
    c.drawString(left, y, f"Sample :  {sample} , Type : Serum , {dt}")
    y -= 14
    c.drawString(left, y, "SampleID    :")
    y -= 12
    c.drawString(left, y, f"Name: {name}")
    y -= 10
    c.setStrokeColor(LINE)
    c.setDash(1, 1.5)
    c.setLineWidth(0.5)
    c.line(left, y, w - 28, y)
    c.setDash()
    y -= 16
    c.setFont(MONO, 7.5)
    c.drawString(
        left,
        y,
        "Item Name       Result      Dil      NR      C E L P B G < > T W A c S R1 R2 D ------RC------",
    )
    y -= 14
    c.setFont(MONO, 9)
    item = (slip.get("item") or "")[:14].ljust(16)
    result = (slip.get("result") or "")[:10].ljust(12)
    c.drawString(left, y, f"{item}{result}")
    c.drawRightString(w - 28, y, slip.get("rc") or "")
    y -= 17
    c.setStrokeColor(LINE)
    c.setDash(1, 1.5)
    c.setLineWidth(0.5)
    c.line(left, y, w - 28, y)
    c.setDash()
    page1(c, SLIP_PAGE)


def main() -> None:
    qc_pages = json.loads((PARSED / "current_qc.json").read_text())
    slips = json.loads((PARSED / "samples.json").read_text())

    by_date: dict[str, dict] = {}
    for p in qc_pages:
        key = p["date"]
        by_date.setdefault(key, {"qc": None, "slips": []})
        by_date[key]["qc"] = p
    for s in slips:
        key = s["event"]
        by_date.setdefault(key, {"qc": None, "slips": []})
        by_date[key]["slips"].append(s)

    keys = sorted(by_date, key=lambda d: datetime.strptime(d, "%Y-%m-%d"), reverse=True)

    c = canvas.Canvas(str(OUT_PDF), pagesize=FORM_PAGE)
    c.setTitle("Internal QC Correction")
    c.setAuthor("Noble Diagnostic Centre")

    n_form = n_qc = n_slip = 0
    for key in keys:
        packet = by_date[key]
        c.setPageSize(FORM_PAGE)
        draw_blank_form(c)
        c.showPage()
        n_form += 1
        if packet["qc"]:
            c.setPageSize(QC_PAGE)
            draw_qc_page(c, packet["qc"])
            c.showPage()
            n_qc += 1
        for s in packet["slips"]:
            c.setPageSize(SLIP_PAGE)
            draw_sample_page(c, s)
            c.showPage()
            n_slip += 1

    c.save()
    print(f"wrote {OUT_PDF}")
    print(f"events={len(keys)}  blank_forms={n_form}  current_qc={n_qc}  sample_slips={n_slip}  pages={n_form + n_qc + n_slip}")
    print("event dates (shifted):", ", ".join(shift_year(k) for k in keys))


if __name__ == "__main__":
    main()
