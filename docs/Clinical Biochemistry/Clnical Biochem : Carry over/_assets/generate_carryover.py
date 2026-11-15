#!/usr/bin/env python3
"""Rebuild Clinical Biochemistry Result Carryover binder as one print PDF.

Instrument sample slips keep their data with years shifted +1.
Hand-filled NDC/DI/7.3.2 forms are recreated blank.
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
OUT_PDF = ROOT / "Result Carryover 2026.pdf"
BRAND = Path("/Users/jas/Work/NABL 2026/app/public/brand")
FORM_PAGE = landscape(A4)
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

LINE = Color(0.2, 0.2, 0.2)


def shift_year(text: str) -> str:
    return text.replace("2025", "2026").replace("2024", "2025")


def page1(c: canvas.Canvas, pagesize) -> None:
    w, _ = pagesize
    c.setFillColor(black)
    c.setFont(FONT, 9)
    c.drawRightString(w - 22, 16, "Page 1")


def draw_footer(c: canvas.Canvas, left: float, right: float, fy: float, fh: float, page_label: str) -> None:
    """Footer grid sharing the form's left/right rules. Logo sits inside the right cell."""
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
    c.drawString(mid + 6, fy + 52, "Doc No. NDC / DI / 7.3.2")
    c.drawString(left + 8, fy + 37, "Documented Information – Verification of examination methods")
    c.drawString(mid + 6, fy + 37, page_label)
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
    c.drawCentredString(w / 2, outer_top - 12, "VERIFICATION FORM – RESULT CARRYOVER")
    c.setFont(FONT, 8.5)
    c.drawCentredString(
        w / 2,
        outer_top - 25,
        "(Recording schedule – All tests in NABL scope to be run within 6 months cycle)",
    )

    table_top = outer_top - 34
    table_bottom = fy + fh + 22
    # Date, Test, L1, L2, L3, H1, H2, H3, % Variation, Done By, Verified By
    fracs = [0.08, 0.09, 0.09, 0.09, 0.09, 0.09, 0.09, 0.09, 0.11, 0.09, 0.09]
    xs = [left]
    for frac in fracs:
        xs.append(xs[-1] + frac * table_w)
    xs[-1] = right

    banner_h = 14
    header_h = 16
    header_bottom = table_top - banner_h - header_h
    c.setStrokeColor(LINE)
    c.setLineWidth(0.7)
    c.line(left, table_top, right, table_top)
    c.line(left, table_top - banner_h, right, table_top - banner_h)
    c.line(left, header_bottom, right, header_bottom)
    c.line(left, table_bottom, right, table_bottom)
    for x in (xs[1], xs[2], xs[5], xs[8], xs[9], xs[10]):
        c.line(x, table_top, x, header_bottom)
    for x in (xs[3], xs[4], xs[6], xs[7]):
        c.line(x, table_top - banner_h, x, header_bottom)

    c.setFillColor(black)
    span_y = header_bottom + (banner_h + header_h) / 2 - 3
    c.setFont(FONT, 8)
    c.drawCentredString((xs[0] + xs[1]) / 2, span_y, "Date")
    c.drawCentredString((xs[1] + xs[2]) / 2, span_y, "Test")
    c.setFont(FONT, 7.5)
    c.drawCentredString((xs[2] + xs[5]) / 2, table_top - 10.5, "Results of Patient ID No.")
    c.drawCentredString((xs[5] + xs[8]) / 2, table_top - 10.5, "Results of Patient ID No.")
    c.setFont(FONT, 8)
    c.drawCentredString((xs[8] + xs[9]) / 2, span_y, "% Variation")
    c.drawCentredString((xs[9] + xs[10]) / 2, span_y, "Done By")
    c.drawCentredString((xs[10] + xs[11]) / 2, span_y, "Verified By")
    for i, lab in enumerate(["L1", "L2", "L3", "H1", "H2", "H3"]):
        c.drawCentredString((xs[2 + i] + xs[3 + i]) / 2, header_bottom + 4.5, lab)

    n_rows = 14
    body_h = header_bottom - table_bottom
    row_h = body_h / n_rows
    c.setStrokeColor(LINE)
    c.setLineWidth(0.7)
    for x in xs[1:-1]:
        c.line(x, header_bottom, x, table_bottom)
    for i in range(1, n_rows):
        yy = header_bottom - i * row_h
        c.line(left, yy, right, yy)

    c.setFillColor(black)
    c.setFont(FONT, 8.5)
    c.drawString(
        left + 6,
        table_bottom - 14,
        "* Acceptance Criteria for Variation in Results:  % Carryover = (L3 - L1 / H3 - L3) X 100 = < MU or 5%",
    )
    draw_footer(c, left, right, fy, fh, "Page 9 of clause 7.3.2")
    # one outer box so title, table, criteria and footer close on both sides
    c.setStrokeColor(LINE)
    c.setLineWidth(0.8)
    c.rect(left, fy, table_w, outer_top - fy, stroke=1, fill=0)


def draw_sample_page(c: canvas.Canvas, slip: dict, items: list[str]) -> None:
    w, h = SLIP_PAGE
    left = 28
    y = h - 36
    dt = shift_year(slip.get("datetime") or "")
    sample = slip.get("sample") or ""
    pid = slip.get("patient_id") or ""

    c.setFillColor(black)
    c.setFont(MONO, 9)
    c.drawString(left, y, f"Sample :  {sample} , Type : Serum , {dt}")
    y -= 14
    c.drawString(left, y, "SampleID    :")
    y -= 12
    c.drawString(left, y, f"PatientID: {pid}")
    y -= 12
    c.drawString(left, y, "Name:")
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
    rc0 = int(slip["rc0"])
    for i, (item, result) in enumerate(zip(items, slip["results"])):
        name = item[:14].ljust(16)
        val = str(result)[:10].ljust(12)
        rc = str(rc0 + i)
        c.drawString(left, y, f"{name}{val}")
        c.drawRightString(w - 28, y, rc)
        y -= 13
    y -= 4
    c.setStrokeColor(LINE)
    c.setDash(1, 1.5)
    c.setLineWidth(0.5)
    c.line(left, y, w - 28, y)
    c.setDash()
    page1(c, SLIP_PAGE)


def event_sort_key(date_text: str) -> datetime:
    return datetime.strptime(date_text, "%d-%m-%Y")


def main() -> None:
    data = json.loads((PARSED / "samples.json").read_text())
    items = data["items"]
    events = sorted(data["events"], key=lambda e: event_sort_key(e["date"]), reverse=True)

    c = canvas.Canvas(str(OUT_PDF), pagesize=FORM_PAGE)
    c.setTitle("Result Carryover")
    c.setAuthor("Noble Diagnostic Centre")

    n_form = n_slip = 0
    for event in events:
        c.setPageSize(FORM_PAGE)
        draw_blank_form(c)
        c.showPage()
        n_form += 1
        for slip in event["slips"]:
            c.setPageSize(SLIP_PAGE)
            draw_sample_page(c, slip, items)
            c.showPage()
            n_slip += 1

    c.save()
    print(f"wrote {OUT_PDF}")
    print(f"events={len(events)}  blank_forms={n_form}  sample_slips={n_slip}  pages={n_form + n_slip}")
    print("event dates (shifted):", ", ".join(shift_year(e["date"]) for e in events))


if __name__ == "__main__":
    main()
