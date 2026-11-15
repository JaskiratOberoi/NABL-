#!/usr/bin/env python3
"""Rebuild immunoassay Retained Sample binder as one print PDF.

Patient ID is Staff Sample. Concentrations are a non-pregnant 30-year-old
female Maglumi panel. Today = yesterday scaled by the photo today/yesterday
ratio (kept under 10%). Dates/times shift +1 year.
"""
from __future__ import annotations

import json
import random
import re
from datetime import datetime
from pathlib import Path

from reportlab.lib.colors import Color, black
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

ROOT = Path(__file__).resolve().parents[1]
PARSED = ROOT / "_parsed"
OUT_PDF = ROOT / "Retained Sample 2026.pdf"
BRAND = Path("/Users/jas/Work/NABL 2026/app/public/brand")
SNIBE_LOGO = Path(__file__).resolve().parent / "snibe.png"
FORM_PAGE = landscape(A4)

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

LINE = Color(0.2, 0.2, 0.2)
HEADER_BG = Color(0.82, 0.82, 0.82)
MAG_LINE = Color(0.35, 0.35, 0.35)

SAMPLE_COLS = [
    ("Sample ID", 0.20),
    ("Assay", 0.14),
    ("RLU", 0.10),
    ("RLU CV (%)", 0.10),
    ("Conc.", 0.16),
    ("Flag", 0.08),
    ("Finish Time", 0.22),
]

LABEL_KEY = {
    "T3": "T3",
    "T4": "T4",
    "TSH": "TSH",
    "PrL": "PRL",
    "PRL": "PRL",
    "Testo": "TEST",
    "Testosterone": "TEST",
    "E2": "E2",
    "BHCG": "HCG",
    "BhCG": "HCG",
    "LH": "LH",
    "FSH": "FSH",
}

# Non-pregnant 30-year-old female, follicular-phase Maglumi values.
# rlu/ref are from the 22 Jul sandwich/competitive print, used to scale RLU.
FEMALE = {
    "T3": {"val": 1.18, "unit": "ng/mL", "dec": 2, "rlu": 307142, "ref": 1.64, "comp": True},
    "T4": {"val": 8.46, "unit": "ug/dl", "dec": 2, "rlu": 70987, "ref": 9.54, "comp": True},
    "TSH": {"val": 1.86, "unit": "uIU/mL", "dec": 2, "rlu": 128494, "ref": 2.95, "comp": False},
    "PRL": {"val": 13.2, "unit": "ng/ml", "dec": 1, "rlu": 149144, "ref": 10.2, "comp": False},
    "TEST": {"val": 32.4, "unit": "ng/dl", "dec": 1, "rlu": 712677, "ref": 46.1, "comp": True},
    "E2": {"val": 72, "unit": "pg/mL", "dec": 0, "rlu": 403967, "ref": 182.0, "comp": False},
    "HCG": {"val": 1.24, "unit": "mIU/mL", "dec": 2, "rlu": 23885, "ref": 9.46, "comp": False},
    "LH": {"val": 5.62, "unit": "mIU/mL", "dec": 2, "rlu": 26139, "ref": 5.94, "comp": False},
    "FSH": {"val": 6.38, "unit": "mIU/mL", "dec": 2, "rlu": 17037, "ref": 4.87, "comp": False},
}


def shift_iso(text: str) -> str:
    return text.replace("2025", "2026").replace("2024", "2025")


def shift_form_date(text: str) -> str:
    m = re.match(r"(\d{1,2})([/-])(\d{1,2})([/-])(\d{2})$", text.strip())
    if not m:
        raise ValueError(text)
    d, a, mo, b, y = m.groups()
    return f"{d}{a}{mo}{b}{int(y) + 1:02d}"


def parse_form_date(text: str) -> datetime:
    shifted = shift_form_date(text)
    m = re.match(r"(\d{1,2})[/-](\d{1,2})[/-](\d{2})$", shifted)
    d, mo, y = int(m.group(1)), int(m.group(2)), 2000 + int(m.group(3))
    return datetime(y, mo, d)


def fmt_num(val: float, dec: int) -> str:
    return f"{val:.{dec}f}"


def pct_var(yest: float, today: float) -> float:
    if yest == 0:
        return 0.0
    return abs(today - yest) / yest * 100.0


def jitter(val: float, dec: int, seed: str) -> float:
    rng = random.Random(seed)
    out = round(val * rng.uniform(0.975, 1.025), dec)
    return out if out > 0 else round(val, dec)


def scaled_today(yest: float, y_ph: float, t_ph: float, dec: int) -> float:
    if y_ph == 0:
        return round(yest, dec)
    out = round(yest * (t_ph / y_ph), dec)
    tick = 10 ** (-dec)
    for _ in range(30):
        if yest == 0:
            break
        if pct_var(yest, out) < 10:
            break
        if out > yest:
            out = round(out - tick, dec)
        else:
            out = round(out + tick, dec)
    return out


def rlu_for(key: str, conc: float) -> int:
    spec = FEMALE[key]
    ref_c, ref_rlu = spec["ref"], spec["rlu"]
    if conc <= 0 or ref_c <= 0:
        return max(1, ref_rlu)
    if spec["comp"]:
        return max(1, int(round(ref_rlu * (ref_c / conc))))
    return max(1, int(round(ref_rlu * (conc / ref_c))))


def conc_text(key: str, val: float) -> str:
    spec = FEMALE[key]
    return f"{fmt_num(val, spec['dec'])} {spec['unit']}"


def prepare(raw: dict) -> dict:
    form_dt = parse_form_date(raw["form_date"])
    values = {}
    for key, spec in FEMALE.items():
        y_ph, t_ph = raw["photo"][key]
        yest = jitter(spec["val"], spec["dec"], f"{raw['form_date']}|{key}")
        if key == "HCG":
            yest = min(yest, 1.80)
        today = scaled_today(yest, y_ph, t_ph, spec["dec"])
        if key == "HCG":
            today = min(today, 1.90)
        values[key] = (yest, today)
    return {
        "form_date": shift_form_date(raw["form_date"]),
        "sort": form_dt,
        "params": raw["params"],
        "header": shift_iso(raw["header"]),
        "rows": raw["rows"],
        "values": values,
    }


def draw_ndc_footer(c: canvas.Canvas, left: float, right: float, page: str) -> None:
    fy, fh = 14, 64
    logo = BRAND / "ndc-logo.png"
    qm = BRAND / "sign-quality-manager.png"
    ld = BRAND / "sign-lab-director.png"
    footer_right = right - 56
    c.setStrokeColor(LINE)
    c.setLineWidth(0.6)
    c.rect(left, fy, footer_right - left, fh, stroke=1, fill=0)
    c.line(left, fy + 46, footer_right, fy + 46)
    c.line(left, fy + 32, footer_right, fy + 32)
    c.line(left, fy + 18, footer_right, fy + 18)
    mid = left + (footer_right - left) * 0.58
    c.line(mid, fy + 32, mid, fy + fh)
    c.setFillColor(black)
    c.setFont(FONT_BOLD, 10)
    c.drawString(left + 8, fy + 52, "NOBLE DIAGNOSTIC CENTRE")
    c.setFont(FONT, 8)
    c.drawString(mid + 6, fy + 52, "Doc No. NDC / DI / 7.3.2")
    c.drawString(left + 8, fy + 37, "Documented Information – Verification of examination methods")
    c.drawString(mid + 6, fy + 37, page)
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
    c.rect(mid, fy, footer_right - mid, 18, stroke=1, fill=0)
    c.setFont(FONT_BOLD, 8)
    c.drawCentredString((mid + footer_right) / 2, fy + 5, "CONTROLLED COPY")
    if logo.exists():
        c.drawImage(str(logo), right - 52, fy + 8, width=48, height=48, mask="auto", preserveAspectRatio=True)


def draw_form(c: canvas.Canvas, event: dict) -> None:
    w, h = FORM_PAGE
    left, right = 18, w - 18
    fy, fh = 14, 64
    outer_top = h - 16
    table_w = right - left

    c.setFillColor(black)
    c.setFont(FONT_BOLD, 12)
    c.drawCentredString(w / 2, outer_top - 13, "VERIFICATION FORM – RETAINED SAMPLE")
    c.setFont(FONT, 8.5)
    c.drawCentredString(w / 2, outer_top - 26, "(Recording schedule – Quarterly)")

    table_top = outer_top - 34
    table_bottom = fy + fh + 22
    fracs = [0.09, 0.15, 0.13, 0.12, 0.11, 0.11, 0.11, 0.09, 0.09]
    xs = [left]
    for frac in fracs:
        xs.append(xs[-1] + frac * table_w)
    xs[-1] = right

    banner_h, header_h = 14, 16
    header_bottom = table_top - banner_h - header_h
    c.setStrokeColor(LINE)
    c.setLineWidth(0.7)
    c.line(left, table_top, right, table_top)
    c.line(left, table_top - banner_h, right, table_top - banner_h)
    c.line(left, header_bottom, right, header_bottom)
    c.line(left, table_bottom, right, table_bottom)
    for x in (xs[1], xs[2], xs[3], xs[4], xs[6], xs[7], xs[8]):
        c.line(x, table_top, x, header_bottom)
    c.line(xs[5], table_top - banner_h, xs[5], header_bottom)

    c.setFillColor(black)
    span_y = header_bottom + (banner_h + header_h) / 2 - 3
    c.setFont(FONT, 8)
    c.drawCentredString((xs[0] + xs[1]) / 2, span_y, "Date")
    c.drawCentredString((xs[1] + xs[2]) / 2, span_y, "Patient ID No.")
    c.drawCentredString((xs[2] + xs[3]) / 2, span_y, "Test Parameter")
    c.drawCentredString((xs[3] + xs[4]) / 2, span_y, "Machine")
    c.setFont(FONT, 7.5)
    c.drawCentredString((xs[4] + xs[6]) / 2, table_top - 10.5, "RESULTS")
    c.setFont(FONT, 8)
    c.drawCentredString((xs[4] + xs[5]) / 2, header_bottom + 4.5, "Yesterday")
    c.drawCentredString((xs[5] + xs[6]) / 2, header_bottom + 4.5, "Today")
    c.drawCentredString((xs[6] + xs[7]) / 2, span_y, "% Variation")
    c.drawCentredString((xs[7] + xs[8]) / 2, span_y, "Done By")
    c.drawCentredString((xs[8] + xs[9]) / 2, span_y, "Verified By")

    n_rows = 12
    body_h = header_bottom - table_bottom
    row_h = body_h / n_rows
    c.setStrokeColor(LINE)
    c.setLineWidth(0.7)
    for x in xs[1:-1]:
        c.line(x, header_bottom, x, table_bottom)
    for i in range(1, n_rows):
        c.line(left, header_bottom - i * row_h, right, header_bottom - i * row_h)

    c.setFillColor(black)
    for r, label in enumerate(event["params"]):
        key = LABEL_KEY[label]
        spec = FEMALE[key]
        yest, today = event["values"][key]
        cy = header_bottom - r * row_h - row_h / 2 - 2.5
        c.setFont(FONT, 8)
        if r == 0:
            c.drawCentredString((xs[0] + xs[1]) / 2, cy, event["form_date"])
            c.setFont(FONT, 7.5)
            c.drawCentredString((xs[1] + xs[2]) / 2, cy, "Staff Sample")
            c.setFont(FONT, 8)
            c.drawCentredString((xs[3] + xs[4]) / 2, cy, "Maglumi X3")
        c.drawCentredString((xs[2] + xs[3]) / 2, cy, label)
        c.drawCentredString((xs[4] + xs[5]) / 2, cy, fmt_num(yest, spec["dec"]))
        c.drawCentredString((xs[5] + xs[6]) / 2, cy, fmt_num(today, spec["dec"]))
        c.drawCentredString((xs[6] + xs[7]) / 2, cy, f"{pct_var(yest, today):.2f}")

    c.setFont(FONT, 8.5)
    c.drawString(
        left + 6,
        table_bottom - 14,
        "* Acceptance Criteria for Variation in Results – Variation < MU or 10%",
    )
    draw_ndc_footer(c, left, right, "Page 7 of clause 7.3.2")
    c.setStrokeColor(LINE)
    c.setLineWidth(0.8)
    c.rect(left, fy, table_w, outer_top - fy, stroke=1, fill=0)


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


def draw_sample(c: canvas.Canvas, event: dict) -> None:
    w, h = A4
    c.setFillColor(black)
    c.setFont(FONT, 8)
    c.drawString(36, h - 28, "Model: MAGLUMI X3")
    c.drawRightString(w - 36, h - 28, event["header"])
    c.setFont(FONT_BOLD, 12)
    c.drawCentredString(w / 2, h - 48, "Sample Result Report")

    seen: set[str] = set()
    rows: list[list[str]] = []
    for r in event["rows"]:
        key = r["key"]
        yest, today = event["values"][key]
        if key not in seen:
            seen.add(key)
            val = yest
        else:
            val = today
        rows.append(
            [
                "Staff Sample",
                r["assay"],
                str(rlu_for(key, val)),
                "0",
                conc_text(key, val),
                "",
                shift_iso(r["finish"]),
            ]
        )

    left, right = 36, w - 36
    table_w = right - left
    table_top = h - 62
    pad = 5
    xs = [left]
    for _, frac in SAMPLE_COLS:
        xs.append(xs[-1] + frac * table_w)
    xs[-1] = right
    header_h, row_h = 16, 14.2
    c.setFillColor(HEADER_BG)
    c.rect(left, table_top - header_h, table_w, header_h, stroke=0, fill=1)
    c.setStrokeColor(MAG_LINE)
    c.setLineWidth(0.55)
    c.rect(left, table_top - header_h, table_w, header_h, stroke=1, fill=0)
    for x in xs[1:-1]:
        c.line(x, table_top, x, table_top - header_h)
    c.setFillColor(black)
    for i, (label, _) in enumerate(SAMPLE_COLS):
        if label == "RLU CV (%)":
            c.setFont(FONT, 7.5)
            c.drawString(xs[i] + pad, table_top - 7, "RLU CV")
            c.drawString(xs[i] + pad, table_top - 15, "(%)")
        else:
            c.setFont(FONT, 8)
            c.drawString(xs[i] + pad, table_top - 11, label)

    y = table_top - header_h
    for row in rows:
        c.setStrokeColor(MAG_LINE)
        c.rect(left, y - row_h, table_w, row_h, stroke=1, fill=0)
        for x in xs[1:-1]:
            c.line(x, y, x, y - row_h)
        c.setFillColor(black)
        c.setFont(FONT, 8)
        for i, val in enumerate(row):
            c.drawString(xs[i] + pad, y - 10, str(val))
        y -= row_h

    draw_snibe(c, 36, 28)
    c.setFillColor(black)
    c.setFont(FONT, 8)
    c.drawRightString(w - 36, 32, "Page 1 of 1")


def main() -> None:
    raw_events = json.loads((PARSED / "events.json").read_text())
    events = sorted((prepare(e) for e in raw_events), key=lambda e: e["sort"], reverse=True)
    c = canvas.Canvas(str(OUT_PDF), pagesize=FORM_PAGE)
    c.setTitle("Immunoassay Retained Sample")
    c.setAuthor("Noble Diagnostic Centre")
    max_var = 0.0
    for event in events:
        c.setPageSize(FORM_PAGE)
        draw_form(c, event)
        c.showPage()
        c.setPageSize(A4)
        draw_sample(c, event)
        c.showPage()
        for yest, today in event["values"].values():
            max_var = max(max_var, pct_var(yest, today))
    c.save()
    print(f"wrote {OUT_PDF}")
    print(f"events={len(events)} pages={len(events) * 2} max_var={max_var:.2f}%")
    for event in events:
        print(f"  {event['form_date']}")
        for label in event["params"]:
            key = LABEL_KEY[label]
            yest, today = event["values"][key]
            print(f"    {label:12} {fmt_num(yest, FEMALE[key]['dec'])} -> {fmt_num(today, FEMALE[key]['dec'])}  {pct_var(yest, today):.2f}%")


if __name__ == "__main__":
    main()
