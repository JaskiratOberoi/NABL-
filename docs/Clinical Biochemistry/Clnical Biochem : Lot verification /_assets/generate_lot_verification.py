#!/usr/bin/env python3
"""Rebuild Lot verification binder as one print PDF.

Instrument printouts (Current QC + sample slips) keep their data with
years shifted +1. The 07-07, 18-08 and 20-09-2026 forms and their
sample slips carry the corrected new-kit results (the figures written
beside the struck-out values). Other NDC/DI/7.3.2 forms stay blank.
"""
from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path

from reportlab.lib.colors import Color, black, white
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

ROOT = Path(__file__).resolve().parents[1]
PARSED = ROOT / "_parsed"
OUT_PDF = ROOT / "Clinical Biochem Lot Verification 2026.pdf"
BRAND = Path("/Users/jas/Work/NABL 2026/app/public/brand")
PAGE = landscape(A4)  # originals are landscape instrument/form prints

_ARIAL = Path("/System/Library/Fonts/Supplemental/Arial.ttf")
_ARIAL_BD = Path("/System/Library/Fonts/Supplemental/Arial Bold.ttf")
_COURIER = Path("/System/Library/Fonts/Courier.ttc")
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
LIGHT = Color(0.55, 0.55, 0.55)

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
CAL_COLS = [
    ("Date / Time", 0.26),
    ("Item", 0.13),
    ("Specimen", 0.12),
    ("Lot No", 0.11),
    ("Tray", 0.08),
    ("Pos", 0.07),
    ("Result", 0.12),
    ("Cal. Error", 0.11),
]


def shift_year(text: str) -> str:
    return text.replace("2025", "2026").replace("2024", "2025")


def shift_lot(text: str) -> str:
    return (text or "").replace("32312044", "52312044")


def parse_date(text: str) -> datetime | None:
    text = (text or "").strip()
    for fmt in (
        "%Y-%m-%d %H:%M:%S",
        "%d-%m-%Y %H:%M:%S",
        "%d/%m/%Y %H:%M:%S",
        "%Y-%m-%d",
        "%d-%m-%Y",
        "%d/%m/%Y",
    ):
        try:
            return datetime.strptime(text[:19] if len(text) >= 19 and ":" in text else text[:10], fmt)
        except ValueError:
            continue
    m = re.search(r"(\d{1,2})[-/](\d{1,2})[-/](\d{4})", text)
    if m:
        d, mo, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
        try:
            return datetime(y, mo, d)
        except ValueError:
            return None
    m = re.search(r"(\d{4})-(\d{2})-(\d{2})", text)
    if m:
        return datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    return None


def page1(c: canvas.Canvas) -> None:
    w, _ = PAGE
    c.setFillColor(black)
    c.setFont(FONT, 9)
    c.drawRightString(w - 22, 16, "Page 1")


def draw_table(c, left, right, top, cols, rows, row_h=12.4, header_h=14.0, font_size=8):
    table_w = right - left
    xs = [left]
    for _, frac in cols:
        xs.append(xs[-1] + frac * table_w)
    # last column must reach `right` exactly so the right rule closes
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
    w, h = PAGE
    left, right = 22, w - 22
    y = h - 24
    c.setFillColor(black)
    c.setFont(FONT, 13)
    c.drawCentredString(w / 2, y, "Current QC")
    y -= 20

    def block(title: str, rows: list[dict], y: float) -> float:
        lot = shift_lot(page.get("lot") or "")
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
    page1(c)


def draw_cal_page(c: canvas.Canvas, page: dict) -> None:
    w, h = PAGE
    left, right = 22, w - 22
    y = h - 24
    c.setFillColor(black)
    c.setFont(FONT, 13)
    c.drawCentredString(w / 2, y, "Calibration Data")
    data = [
        [
            shift_year(r["datetime"]),
            r.get("item") or "",
            r.get("specimen") or "",
            r.get("lot") or "",
            r.get("tray") or "",
            r.get("pos") or "",
            r.get("result") or "",
            "",
        ]
        for r in page["rows"]
    ]
    draw_table(c, left, right, y - 16, CAL_COLS, data, row_h=13.0, header_h=14.5, font_size=8.5)
    page1(c)


def draw_sample_page(c: canvas.Canvas, slip: dict) -> None:
    w, h = PAGE
    left = 28
    y = h - 32
    dt = shift_year(slip.get("datetime") or "")
    sample = slip.get("sample") or ""
    typ = slip.get("type") or "Serum"
    sid = slip.get("sample_id") or ""

    c.setFillColor(black)
    c.setFont(MONO, 9)
    c.drawString(left, y, f"Sample :  {sample} , Type : {typ}")
    c.drawRightString(w - 28, y, dt)
    y -= 14
    c.drawString(left, y, f"SampleID    : {sid}")
    y -= 10
    c.setStrokeColor(LINE)
    c.setLineWidth(0.5)
    c.line(left, y, w - 28, y)
    y -= 16
    c.setFont(MONO, 8)
    c.drawString(
        left,
        y,
        "Item Name       Result      Dil      NR      C E L P B G < > T W A c S R1 R2 D ------RC------",
    )
    y -= 14
    c.setFont(MONO, 9)
    for r in slip.get("rows") or []:
        item = (r.get("item") or "")[:14].ljust(16)
        result = (r.get("result") or "")[:10].ljust(12)
        rc = r.get("rc") or ""
        c.drawString(left, y, f"{item}{result}")
        c.drawRightString(w - 28, y, rc)
        y -= 13
    page1(c)


def pct_var(old: str, new: str) -> str:
    o = float(old)
    n = float(new)
    if o == 0:
        return "0.00"
    return f"{abs(n - o) / abs(o) * 100.0:.2f}"


# Current QC is the old kit. The new kit is the figure written beside any
# struck-out value, otherwise the sample slip. Each row is Norm then Path.
FILLED_FORMS = {
    "2025-09-20": (
        "20-09-2026",
        [[
            ("SGPT", "33.08", "37.25", "125.62", "128.51"),
            ("CRT", "1.07", "1.18", "4.25", "4.55"),
            ("GLU", "90.5", "93.44", "239.3", "243.2"),
        ]],
    ),
    "2025-08-18": (
        "18-08-2026",
        [[
            ("Chol", "150.9", "153.2", "298.2", "301.1"),
            ("TGL", "144.3", "141.7", "268.4", "265.4"),
            ("BIL T", "0.86", "0.95", "4.52", "5.07"),
            ("BIL D", "0.48", "0.42", "2.12", "2.33"),
        ]],
    ),
    "2025-07-07": (
        "07-07-2026",
        [
    [
        ("ALP", "125.58", "124.12", "341.08", "344.21"),
        ("TP", "5.46", "5.33", "8.16", "7.11"),
        ("ALB", "4.00", "3.79", "4.36", "4.66"),
        ("Ca", "8.39", "8.11", "13.09", "14.52"),
    ],
    [
        ("GGT", "33.94", "32.61", "146.41", "144.32"),
        ("Urea", "28.3", "27.2", "140.9", "143.2"),
        ("UA", "5.0", "4.6", "10.9", "12.1"),
        ],
        ],
    ),
}

# Sample-slip results replaced by the handwritten corrections on the forms,
# keyed by (event date, SampleID, item).
SLIP_CORRECTIONS = {
    ("2025-07-07", "LV-NORM", "ALB"): "3.79",
    ("2025-07-07", "LV-PATH", "ALB"): "4.66",
    ("2025-07-07", "LV-NORM", "UAC"): "4.6",
    ("2025-08-18", "LV-NORM", "BIL T"): "0.95",
    ("2025-08-18", "LV-NORM", "BIL D"): "0.42",
    ("2025-08-18", "LV-PATH", "BIL D"): "2.33",
    ("2025-09-20", "LV-NORM", "CRT J"): "1.18",
}

FORM_TO_SLIP_ITEM = {
    "ALP": "ALP IFCC", "TP": "TPR", "Ca": "CAL", "Urea": "UREA UV", "UA": "UAC",
    "Chol": "CHOL", "CRT": "CRT J",
}


def draw_blank_form(c: canvas.Canvas, tests: list[tuple] | None = None, form_date: str = "") -> None:
    w, h = PAGE
    left, right = 18, w - 18
    y = h - 22
    c.setFillColor(black)
    c.setFont(FONT_BOLD, 12)
    c.drawCentredString(w / 2, y, "VERIFICATION FORM – NEW LOT KIT (BIO/MOL/SER)")
    y -= 13
    c.setFont(FONT, 8.5)
    c.drawCentredString(w / 2, y, "(Recording schedule – Whenever new lot kit is opened)")
    y -= 12

    table_top = y
    table_bottom = 92
    cols = [
        ("Date", 0.08),
        ("Patient ID No.", 0.12),
        ("New Kit Name", 0.13),
        ("OLD KIT", 0.19),
        ("NEW KIT", 0.19),
        ("Variation in results", 0.13),
        ("Done By", 0.08),
        ("Verified By", 0.08),
    ]
    table_w = right - left
    xs = [left]
    for _, frac in cols:
        xs.append(xs[-1] + frac * table_w)

    results_x0, results_x1 = xs[3], xs[6]
    banner_h = 14
    header_h = 16
    c.setStrokeColor(LINE)
    c.setLineWidth(0.7)
    c.rect(left, table_top - banner_h - header_h, table_w, banner_h + header_h, stroke=1, fill=0)
    for x in (xs[1], xs[2], xs[3], xs[6], xs[7]):
        c.line(x, table_top, x, table_top - banner_h - header_h)
    c.line(results_x0, table_top - banner_h, results_x1, table_top - banner_h)
    c.line(xs[4], table_top - banner_h, xs[4], table_top - banner_h - header_h)
    c.line(xs[5], table_top - banner_h, xs[5], table_top - banner_h - header_h)
    c.setFont(FONT_BOLD, 9)
    c.drawCentredString((results_x0 + results_x1) / 2, table_top - 10.5, "RESULTS")
    c.setFont(FONT, 8)
    for i, lab in enumerate([col[0] for col in cols]):
        if i in (3, 4, 5):
            c.drawCentredString((xs[i] + xs[i + 1]) / 2, table_top - banner_h - 11, lab)
        else:
            c.drawCentredString((xs[i] + xs[i + 1]) / 2, table_top - banner_h - 4, lab)

    hy = table_top - banner_h
    n_blocks = 4
    body_h = hy - header_h - table_bottom
    block_h = body_h / n_blocks
    tests = tests or []
    for b in range(n_blocks):
        top = hy - header_h - b * block_h
        bot = top - block_h
        c.setLineWidth(0.7)
        c.setStrokeColor(LINE)
        c.rect(left, bot, table_w, block_h, stroke=1, fill=0)
        for x in xs[1:-1]:
            c.line(x, top, x, bot)
        sub = block_h / 4
        filled = b < len(tests)
        if not filled:
            c.setFont(FONT, 7)
            c.setFillColor(LIGHT)
            for kit_i in (3, 4):
                c.drawString(xs[kit_i] + 4, top - sub + 4, "Lot No.")
                c.drawString(xs[kit_i] + 4, top - 2 * sub + 4, "Expiry")
            c.setFillColor(black)
        for i in range(1, 4):
            yy = top - i * sub
            c.setStrokeColor(LINE)
            c.setLineWidth(0.4)
            c.line(xs[3], yy, xs[6], yy)
        if not filled:
            continue
        name, old_n, new_n, old_p, new_p = tests[b]
        y1 = top - sub / 2 - 3
        y2 = top - 1.5 * sub - 3
        c.setFillColor(black)
        c.setFont(FONT, 8)
        if b == 0 and form_date:
            c.drawCentredString((xs[0] + xs[1]) / 2, (y1 + y2) / 2, form_date)
        c.setFont(FONT, 7.5)
        c.drawCentredString((xs[1] + xs[2]) / 2, y1, "Norm")
        c.drawCentredString((xs[1] + xs[2]) / 2, y2, "Path")
        c.setFont(FONT_BOLD, 8)
        c.drawCentredString((xs[2] + xs[3]) / 2, (y1 + y2) / 2, name)
        c.setFont(FONT, 8)
        for y, old, new in ((y1, old_n, new_n), (y2, old_p, new_p)):
            c.drawCentredString((xs[3] + xs[4]) / 2, y, old)
            c.drawCentredString((xs[4] + xs[5]) / 2, y, new)
            c.drawCentredString((xs[5] + xs[6]) / 2, y, pct_var(old, new))

    c.setStrokeColor(LINE)
    c.setLineWidth(0.7)
    c.setFont(FONT, 8.5)
    c.drawString(
        left,
        table_bottom - 14,
        "Acceptance Criteria: Quantitative Results - % Variation < +/- 1 SD or 10%",
    )

    fy = 14
    fh = 64
    logo = BRAND / "ndc-logo.png"
    qm = BRAND / "sign-quality-manager.png"
    ld = BRAND / "sign-lab-director.png"
    footer_right = right - 56
    c.setLineWidth(0.6)
    c.rect(left, fy, footer_right - left, fh, stroke=1, fill=0)
    c.line(left, fy + 46, footer_right, fy + 46)
    c.line(left, fy + 32, footer_right, fy + 32)
    c.line(left, fy + 18, footer_right, fy + 18)
    mid = left + (footer_right - left) * 0.58
    c.line(mid, fy + 32, mid, fy + fh)
    c.setFont(FONT_BOLD, 10)
    c.drawString(left + 8, fy + 52, "NOBLE DIAGNOSTIC CENTRE")
    c.setFont(FONT, 8)
    c.drawString(mid + 6, fy + 52, "Doc No. NDC / DI / 7.3.2")
    c.drawString(left + 8, fy + 37, "Documented Information – Verification of examination methods")
    c.drawString(mid + 6, fy + 37, "Page 11 of clause 7.3.2")
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


def load() -> tuple[list[dict], list[dict]]:
    qc = json.loads((PARSED / "current_qc.json").read_text())
    samples = json.loads((PARSED / "samples_a.json").read_text())
    samples.extend(json.loads((PARSED / "samples_b.json").read_text()))
    return qc, samples


def event_key(text: str) -> str:
    dt = parse_date(shift_year(text) if False else text)
    if not dt:
        return text[:10]
    # key from original (pre-shift) so grouping still works
    return dt.strftime("%Y-%m-%d")


def main() -> None:
    qc, samples = load()
    for p in qc:
        p["_key"] = event_key(p["norm"][0]["datetime"])
        p["_sort"] = parse_date(p["norm"][0]["datetime"])
    applied = 0
    for s in samples:
        s["_key"] = event_key(s.get("datetime") or "")
        s["_sort"] = parse_date(s.get("datetime") or "")
        for r in s.get("rows") or []:
            fix = SLIP_CORRECTIONS.get((s["_key"], s.get("sample_id"), r.get("item")))
            if fix is not None:
                r["result"] = fix
                applied += 1
    if applied != len(SLIP_CORRECTIONS):
        raise RuntimeError(f"applied {applied} of {len(SLIP_CORRECTIONS)} slip corrections")

    # every form value must match the instrument page it was read from
    slip_by = {(s["_key"], s.get("sample_id")): {r["item"]: r["result"] for r in s["rows"]} for s in samples}
    qc_by = {event_key(p["norm"][0]["datetime"]): p for p in qc}
    for key, (_, pages) in FILLED_FORMS.items():
        qc_page = qc_by[key]
        for name, old_n, new_n, old_p, new_p in (t for page in pages for t in page):
            item = FORM_TO_SLIP_ITEM.get(name, name.upper())
            qc_item = {"CAL": "CAL A", "UAC": "UAC"}.get(item, item)
            for side, old, new, sid in (("norm", old_n, new_n, "LV-NORM"), ("path", old_p, new_p, "LV-PATH")):
                qc_val = next(r["result"] for r in qc_page[side] if r["item"] == qc_item)
                slip_val = slip_by[(key, sid)][item]
                if float(qc_val) != float(old) or float(slip_val) != float(new):
                    raise RuntimeError(f"{key} {name} {side}: form {old}/{new} vs QC {qc_val} / slip {slip_val}")

    by_date: dict[str, dict] = {}
    for p in qc:
        by_date.setdefault(p["_key"], {"qc": None, "slips": []})
        by_date[p["_key"]]["qc"] = p
    for s in samples:
        by_date.setdefault(s["_key"], {"qc": None, "slips": []})
        by_date[s["_key"]]["slips"].append(s)

    keys = sorted(by_date, reverse=True)

    c = canvas.Canvas(str(OUT_PDF), pagesize=PAGE)
    c.setTitle("Lot Verification")
    c.setAuthor("Noble Diagnostic Centre")

    n_form = n_qc = n_slip = 0
    for key in keys:
        packet = by_date[key]
        form_date, pages = FILLED_FORMS.get(key, ("", [None]))
        for tests in pages:
            draw_blank_form(c, tests, form_date if tests else "")
            c.showPage()
            n_form += 1
        if packet["qc"]:
            draw_qc_page(c, packet["qc"])
            c.showPage()
            n_qc += 1
        slips = sorted(packet["slips"], key=lambda s: s.get("sample_id") or "")
        for s in slips:
            draw_sample_page(c, s)
            c.showPage()
            n_slip += 1

    cal_path = PARSED / "calibration.json"
    n_cal = 0
    if cal_path.exists():
        for page in json.loads(cal_path.read_text()):
            draw_cal_page(c, page)
            c.showPage()
            n_cal += 1

    c.save()
    print(f"wrote {OUT_PDF}")
    print(
        f"events={len(keys)}  blank_forms={n_form}  current_qc={n_qc}  "
        f"sample_slips={n_slip}  calibration={n_cal}  pages={n_form+n_qc+n_slip+n_cal}"
    )
    print("event dates (shifted):", ", ".join(shift_year(k) for k in keys))


if __name__ == "__main__":
    main()
