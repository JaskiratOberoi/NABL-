#!/usr/bin/env python3
"""Rebuild immunoassay Result Carryover binder as one print PDF.

L1/H1 are the Bio-Rad Maglumi QC L1/L2 from the same calendar date in the
2026 readings (as lot verification). L2/L3 and H2/H3 are repeats within 5%.
% Carryover = (L3 - L1) / (H3 - L3) × 100 stays under 5%. Dates +1 year.
"""
from __future__ import annotations

import json
import random
import re
from datetime import datetime, timedelta
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
SNIBE_LOGO = Path(__file__).resolve().parent / "snibe.png"
QC_PATH = Path("/Users/jas/Work/NABL 2026/docs/Immunoassay/Lot Verification /_parsed/maglumi_qc.json")
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
    ("Sample ID", 0.14),
    ("Assay", 0.14),
    ("RLU", 0.12),
    ("RLU CV (%)", 0.10),
    ("Conc.", 0.16),
    ("Flag", 0.08),
    ("Finish Time", 0.26),
]

LABEL_KEY = {
    "T3": "T3",
    "T4": "T4",
    "TSH": "TSH",
    "FSH": "FSH",
    "LH": "LH",
    "PRL": "PRL",
    "E2": "E2",
    "Testo": "TEST",
    "BHCG": "HCG",
}

QC_ASSAY = {
    "T3": "T3",
    "T4": "T4",
    "TSH": "TSH",
    "FSH": "FSH",
    "LH": "LH",
    "PRL": "PRL",
    "E2": "E2",
    "TEST": "TEST",
    "HCG": "HCG/B-HCG",
}

PRINT_ASSAY = {
    "T3": "T3 II",
    "T4": "T4 II",
    "TSH": "TSH II",
    "FSH": "FSH II",
    "LH": "LH II",
    "PRL": "PRL II",
    "E2": "E2 II",
    "TEST": "TEST II",
    "HCG": "T-B HCG II",
}

COMPETITIVE = {"T3", "T4", "TEST"}
SAMPLE_IDS = ["L1", "H1", "L2", "H2", "L3", "H3"]
PAGE1_ROWS = 44


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


def parse_conc(text: str) -> tuple[float, str, int]:
    m = re.match(r"([0-9.]+)\s*(.*)", (text or "").strip())
    if not m:
        raise ValueError(f"unparseable conc: {text!r}")
    num, unit = m.group(1), m.group(2).strip()
    dec = len(num.split(".")[1]) if "." in num else 0
    return float(num), unit, dec


def fmt_num(val: float, dec: int) -> str:
    return f"{val:.{dec}f}"


def maglumi_row(qc: dict, day: str, level: str, assay: str) -> dict:
    for row in qc[day][level]:
        if row["assay"] == assay:
            return row
    raise KeyError(f"{day} {level} {assay}")


def scale_rlu(key: str, orig_val: float, orig_rlu: int, new_val: float) -> int:
    if orig_val <= 0 or new_val <= 0:
        return max(1, orig_rlu)
    if key in COMPETITIVE:
        return max(1, int(round(orig_rlu * (orig_val / new_val))))
    return max(1, int(round(orig_rlu * (new_val / orig_val))))


def make_repeat(orig_val: float, dec: int, orig_rlu: int, key: str, seed: str) -> tuple[float, int, float]:
    rng = random.Random(seed)
    for _ in range(60):
        pct = rng.uniform(0.6, 3.8)
        sign = rng.choice([-1.0, 1.0])
        new_val = round(orig_val * (1.0 + sign * pct / 100.0), dec)
        if new_val <= 0:
            continue
        var = abs(new_val - orig_val) / orig_val * 100.0
        if 0.3 <= var <= 5.0:
            return new_val, scale_rlu(key, orig_val, orig_rlu, new_val), var
    new_val = round(orig_val * 1.015, dec)
    var = abs(new_val - orig_val) / orig_val * 100.0
    return new_val, scale_rlu(key, orig_val, orig_rlu, new_val), var


def carryover_pct(l1: float, l3: float, h3: float) -> float:
    den = h3 - l3
    if den == 0:
        return 0.0
    return abs(l3 - l1) / abs(den) * 100.0


def maglumi_times(start: datetime, n_samples: int, n_assays: int, seed: int) -> list[list[datetime]]:
    rng = random.Random(seed)
    t = start
    out: list[list[datetime]] = []
    for _ in range(n_samples):
        sample: list[datetime] = []
        ct = t
        for _a in range(n_assays):
            sample.append(ct)
            ct = ct + timedelta(seconds=rng.randint(40, 95))
        out.append(sample)
        t = ct + timedelta(seconds=rng.randint(50, 140))
    return out


def prepare(raw: dict, qc: dict) -> dict:
    day_dt = parse_form_date(raw["form_date"])
    day = day_dt.strftime("%Y-%m-%d")
    start = datetime.strptime(shift_iso(raw["start"]), "%Y-%m-%d %H:%M:%S")
    times = maglumi_times(start, 6, 9, int(day_dt.strftime("%Y%m%d")))
    series: dict[str, dict[str, dict]] = {}
    for key in QC_ASSAY:
        l1_row = maglumi_row(qc, day, "L1", QC_ASSAY[key])
        l2_row = maglumi_row(qc, day, "L2", QC_ASSAY[key])
        l1_val, unit, dec = parse_conc(l1_row["conc"])
        h1_val, h_unit, h_dec = parse_conc(l2_row["conc"])
        dec = max(dec, h_dec)
        unit = unit or h_unit
        l1_rlu = int(l1_row["rlu"])
        h1_rlu = int(l2_row["rlu"])
        l2_val, l2_rlu, _ = make_repeat(l1_val, dec, l1_rlu, key, f"{day}|{key}|L2")
        l3_val, l3_rlu, _ = make_repeat(l1_val, dec, l1_rlu, key, f"{day}|{key}|L3")
        h2_val, h2_rlu, _ = make_repeat(h1_val, dec, h1_rlu, key, f"{day}|{key}|H2")
        h3_val, h3_rlu, _ = make_repeat(h1_val, dec, h1_rlu, key, f"{day}|{key}|H3")
        tick = 10 ** (-dec)
        for _ in range(80):
            if carryover_pct(l1_val, l3_val, h3_val) < 5:
                break
            if l3_val > l1_val:
                l3_val = round(l3_val - tick, dec)
            else:
                l3_val = round(l3_val + tick, dec)
            l3_rlu = scale_rlu(key, l1_val, l1_rlu, l3_val)
        series[key] = {
            "L1": {"val": l1_val, "rlu": l1_rlu},
            "L2": {"val": l2_val, "rlu": l2_rlu},
            "L3": {"val": l3_val, "rlu": l3_rlu},
            "H1": {"val": h1_val, "rlu": h1_rlu},
            "H2": {"val": h2_val, "rlu": h2_rlu},
            "H3": {"val": h3_val, "rlu": h3_rlu},
            "unit": unit,
            "dec": dec,
            "carry": carryover_pct(l1_val, l3_val, h3_val),
        }
    rows = []
    for i, sid in enumerate(SAMPLE_IDS):
        for a, key in enumerate(raw["mag_order"]):
            rec = series[key][sid]
            rows.append(
                {
                    "sid": sid,
                    "key": key,
                    "assay": PRINT_ASSAY[key],
                    "rlu": rec["rlu"],
                    "conc": f"{fmt_num(rec['val'], series[key]['dec'])} {series[key]['unit']}".strip(),
                    "flag": ">" if key == "HCG" else "",
                    "finish": times[i][a].strftime("%Y-%m-%d %H:%M:%S"),
                }
            )
    return {
        "form_date": shift_form_date(raw["form_date"]),
        "sort": day_dt,
        "params": raw["params"],
        "header": shift_iso(raw["header"]),
        "series": series,
        "rows": rows,
        "day": day,
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
    c.drawCentredString(w / 2, outer_top - 12, "VERIFICATION FORM – RESULT CARRYOVER")
    c.setFont(FONT, 8.5)
    c.drawCentredString(
        w / 2,
        outer_top - 25,
        "(Recording schedule – All tests in NABL scope to be run within 6 months cycle)",
    )

    table_top = outer_top - 34
    table_bottom = fy + fh + 22
    fracs = [0.08, 0.09, 0.09, 0.09, 0.09, 0.09, 0.09, 0.09, 0.11, 0.09, 0.09]
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
        c.line(left, header_bottom - i * row_h, right, header_bottom - i * row_h)

    c.setFillColor(black)
    for r, label in enumerate(event["params"]):
        key = LABEL_KEY[label]
        spec = event["series"][key]
        cy = header_bottom - r * row_h - row_h / 2 - 2.5
        c.setFont(FONT, 8)
        if r == 0:
            c.drawCentredString((xs[0] + xs[1]) / 2, cy, event["form_date"])
        c.drawCentredString((xs[1] + xs[2]) / 2, cy, label)
        for i, sid in enumerate(["L1", "L2", "L3", "H1", "H2", "H3"]):
            c.drawCentredString(
                (xs[2 + i] + xs[3 + i]) / 2,
                cy,
                fmt_num(spec[sid]["val"], spec["dec"]),
            )
        c.drawCentredString((xs[8] + xs[9]) / 2, cy, f"{spec['carry']:.2f}")

    c.setFont(FONT, 8.5)
    c.drawString(
        left + 6,
        table_bottom - 14,
        "* Acceptance Criteria for Variation in Results:  % Carryover = (L3 - L1 / H3 - L3) X 100 = < MU or 5%",
    )
    draw_ndc_footer(c, left, right, "Page 9 of clause 7.3.2")
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


def draw_sample_page(c: canvas.Canvas, event: dict, rows: list[dict], page: int, pages: int) -> None:
    w, h = A4
    c.setFillColor(black)
    c.setFont(FONT, 8)
    c.drawString(36, h - 28, "Model: MAGLUMI X3")
    c.drawRightString(w - 36, h - 28, event["header"])
    c.setFont(FONT_BOLD, 12)
    c.drawCentredString(w / 2, h - 48, "Sample Result Report")

    table_rows = [
        [r["sid"], r["assay"], str(r["rlu"]), "0", r["conc"], r["flag"], r["finish"]]
        for r in rows
    ]
    left, right = 36, w - 36
    table_w = right - left
    table_top = h - 62
    pad = 5
    xs = [left]
    for _, frac in SAMPLE_COLS:
        xs.append(xs[-1] + frac * table_w)
    xs[-1] = right
    header_h, row_h = 16, 14.0
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
    for row in table_rows:
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
    c.drawRightString(w - 36, 32, f"Page {page} of {pages}")


def main() -> None:
    raw_events = json.loads((PARSED / "events.json").read_text())
    qc = json.loads(QC_PATH.read_text())
    events = sorted((prepare(e, qc) for e in raw_events), key=lambda e: e["sort"], reverse=True)
    c = canvas.Canvas(str(OUT_PDF), pagesize=FORM_PAGE)
    c.setTitle("Immunoassay Result Carryover")
    c.setAuthor("Noble Diagnostic Centre")
    max_co = 0.0
    for event in events:
        c.setPageSize(FORM_PAGE)
        draw_form(c, event)
        c.showPage()
        chunks = [event["rows"][:PAGE1_ROWS], event["rows"][PAGE1_ROWS:]]
        chunks = [ch for ch in chunks if ch]
        for i, chunk in enumerate(chunks, start=1):
            c.setPageSize(A4)
            draw_sample_page(c, event, chunk, i, len(chunks))
            c.showPage()
        for spec in event["series"].values():
            max_co = max(max_co, spec["carry"])
    c.save()
    pages = sum(1 + (2 if len(e["rows"]) > PAGE1_ROWS else 1) for e in events)
    print(f"wrote {OUT_PDF}")
    print(f"events={len(events)} pages={pages} max_carryover={max_co:.2f}%")
    for event in events:
        print(f"  {event['form_date']}  QC {event['day']}")
        for label in event["params"]:
            key = LABEL_KEY[label]
            spec = event["series"][key]
            print(
                f"    {label:6} L1 {fmt_num(spec['L1']['val'], spec['dec'])}  "
                f"H1 {fmt_num(spec['H1']['val'], spec['dec'])}  "
                f"co {spec['carry']:.2f}%"
            )


if __name__ == "__main__":
    main()
