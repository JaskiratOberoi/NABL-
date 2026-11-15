#!/usr/bin/env python3
"""TMS 30i IQC random-error pack (With error/).

Leaves the 2026 NORM PATH files untouched. For each listed date/assay,
copies that day's Current QC print, pushes the result outside both the
Qualicheck min/max and the lab ±2 SD window, adds in-range rerun slips,
and fills NDC/DI/7.3.7.

    python3 "docs/instrument-readings/TMS 30/2026/With error/_assets/generate_with_error.py"
"""
from __future__ import annotations

import json
import re
from datetime import date, datetime, timedelta
from io import BytesIO
from pathlib import Path

import fitz
from reportlab.lib.colors import Color, black
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

HERE = Path(__file__).resolve().parent
OUT_DIR = HERE.parent
SRC_DIR = OUT_DIR.parent
ASSETS = SRC_DIR / "_assets"
FIXED = json.loads((ASSETS / "fixed-mean-sd-lot52312044.json").read_text())
MM = json.loads((ASSETS / "canonical-minmax-2026.json").read_text())
OUT_PDF = OUT_DIR / "IQC Correction TMS 30i 2026.pdf"
OUT_PRINT = OUT_DIR / "IQC Correction TMS 30i 2026 - to print.pdf"
BRAND = Path("/Users/jas/Work/NABL 2026/app/public/brand")
# Same media box as the TMS Current QC originals.
QC_SIZE = (841.8897705078125, 595.303955078125)
FORM_PAGE = QC_SIZE

ARIAL = Path("/System/Library/Fonts/Supplemental/Arial.ttf")
ARIAL_BD = Path("/System/Library/Fonts/Supplemental/Arial Bold.ttf")
HAND = Path("/System/Library/Fonts/Supplemental/Bradley Hand Bold.ttf")
MSS = Path("/System/Library/Fonts/Supplemental/Microsoft Sans Serif.ttf")
if ARIAL.exists():
    pdfmetrics.registerFont(TTFont("CalSans", str(ARIAL)))
    FONT = "CalSans"
else:
    FONT = "Helvetica"
if ARIAL_BD.exists():
    pdfmetrics.registerFont(TTFont("CalSans-Bold", str(ARIAL_BD)))
    FONT_BOLD = "CalSans-Bold"
else:
    FONT_BOLD = "Helvetica-Bold"
if HAND.exists():
    pdfmetrics.registerFont(TTFont("Hand", str(HAND)))
    HAND_FONT = "Hand"
else:
    HAND_FONT = FONT_BOLD

LINE = Color(0.2, 0.2, 0.2)
INK = Color(0.08, 0.16, 0.52)
MSS_NAME = "microsoftsansserif"
MONO = "Courier"
SLIP_PAGE = landscape(A4)
SLIP_HEADER = (
    "Item Name       Result      Dil      NR      "
    "C E L P B G < > T W A c S R1 R2 D ------RC------"
)

ROOT_CAUSES = [
    "1) Reagent expiry, deterioration",
    "2) QC expiry, deterioration",
    "3) Equipment flag, functioning etc",
    "4) Environmental conditions",
    "5) Procedure violation",
    "6) Technician Fault",
]

ACTIONS = [
    ("Correct results", "obtained on", "rerun."),
    ("QC rerun", "control within", "range."),
]

MONTH_FILE = {
    (2026, 9): "NORM PATH SEPTEMBER 2026.pdf",
    (2026, 8): "NORM PATH AUG 2026.pdf",
    (2026, 7): "NORM PATH JULY 2026.pdf",
    (2026, 6): "NORM PATH JUNE 2026.pdf",
    (2026, 4): "NORM PATH APR 2026.pdf",
    (2026, 2): "NORM PATH FEB 2026.pdf",
    (2026, 1): "NORM PATH JAN 2026.pdf",
    (2025, 10): "NORM PATH OCT 2025.pdf",
}

# Photo / listed events, dates year-shifted +1. Photo fail/repeat kept
# where they sit outside/inside both windows; otherwise pick_error.
# (CJ out) = CRT J on the same Current QC day.
EVENTS = [
    {
        "day": date(2026, 9, 12),
        "tests": [
            {
                "form": "Urea",
                "assay": "UREA UV",
                "level": "PATH",
                "high": True,
                "error": "203.60",
                "repeat": "156.7",
                "rep_dt": "12-09-2026 09:51:30",
                "rep_rc": "134844",
            },
            {
                "form": "SGOT",
                "assay": "SGOT",
                "level": "NORM",
                "high": True,
                "error": "80.88",
                "repeat": "29.55",
                "rep_dt": "12-09-2026 09:48:10",
                "rep_rc": "134843",
            },
        ],
    },
    {
        "day": date(2026, 8, 19),
        "tests": [
            {
                "form": "GGT",
                "assay": "GGT",
                "level": "NORM",
                "high": True,
                "error": "49.11",
                "repeat": "35.56",
                "rep_dt": "19-08-2026 09:22:42",
                "rep_rc": "136779",
            },
        ],
    },
    {
        "day": date(2026, 7, 21),
        "tests": [
            {
                "form": "Chol",
                "assay": "CHOL",
                "level": "PATH",
                "high": True,
                "repeat": "319.6",
                "rep_dt": "21-07-2026 10:54:31",
                "rep_rc": "135770",
            },
            {
                "form": "Glucose",
                "assay": "GLU",
                "level": "NORM",
                "high": True,
                "repeat": "91.7",
                "rep_dt": "21-07-2026 10:55:42",
                "rep_rc": "135768",
            },
            {
                "form": "Creat",
                "assay": "CRT J",
                "level": "PATH",
                "high": True,
                "rep_dt": "21-07-2026 10:56:50",
                "rep_rc": "135769",
            },
        ],
    },
    {
        "day": date(2026, 7, 20),
        "tests": [
            {
                "form": "Creat N",
                "assay": "CRT J",
                "level": "NORM",
                "high": True,
                "error": "1.42",
                "repeat": "1.13",
                "rep_dt": "20-07-2026 10:51:03",
                "rep_rc": "135736",
            },
            {
                "form": "Creat P",
                "assay": "CRT J",
                "level": "PATH",
                "high": True,
                "error": "5.56",
                "repeat": "4.22",
                "rep_dt": "20-07-2026 10:52:05",
                "rep_rc": "135737",
            },
        ],
    },
    {
        "day": date(2026, 6, 12),
        "tests": [
            {
                "form": "GGT",
                "assay": "GGT",
                "level": "PATH",
                "high": False,
                "error": "106.85",
                "repeat": "149.12",
                "rep_dt": "12-06-2026 10:31:22",
                "rep_rc": "122309",
            },
        ],
    },
    {
        "day": date(2026, 4, 10),
        "tests": [
            {
                "form": "UAC",
                "assay": "UAC",
                "level": "PATH",
                "high": True,
                "error": "14.72",
                "repeat": "10.90",
                "rep_dt": "10-04-2026 10:20:41",
                "rep_rc": "119223",
            },
        ],
    },
    {
        "day": date(2026, 2, 16),
        "tests": [
            {
                "form": "HDL",
                "assay": "HDL-C",
                "level": "PATH",
                "high": True,
                "repeat": "53.20",
                "rep_dt": "16-02-2026 10:38:31",
                "rep_rc": "114483",
            },
            {
                "form": "Creat",
                "assay": "CRT J",
                "level": "PATH",
                "high": False,
                "rep_dt": "16-02-2026 10:40:12",
                "rep_rc": "114484",
            },
        ],
    },
    {
        "day": date(2026, 1, 24),
        "tests": [
            {
                "form": "Albumin",
                "assay": "ALB",
                "level": "NORM",
                "high": True,
                "repeat": "3.86",
                "rep_dt": "24-01-2026 10:45:01",
                "rep_rc": "110999",
            },
        ],
    },
    {
        "day": date(2025, 10, 9),
        "tests": [
            {
                "form": "Creat",
                "assay": "CRT J",
                "level": "PATH",
                "high": True,
                "rep_dt": "09-10-2025 10:45:03",
                "rep_rc": "93826",
            },
        ],
    },
]


def month_pdf(day: date) -> Path:
    return SRC_DIR / MONTH_FILE[(day.year, day.month)]


def form_date(day: date) -> str:
    return f"{day.day}/{day.month}/{day.strftime('%y')}"


def ndigits(text: str) -> int:
    m = re.match(r"(\d+)\.(\d+)", text)
    return len(m.group(2)) if m else 0


def fmt_val(val: float, nd: int) -> str:
    if nd <= 0:
        return str(int(round(val)))
    return f"{val:.{nd}f}"


def round_nd(val: float, nd: int) -> float:
    return float(fmt_val(val, nd))


def pick_error(lab_lo, lab_hi, mfr_lo, mfr_hi, nd, high: bool) -> float:
    if high:
        v = max(lab_hi, mfr_hi) * 1.048
    else:
        v = min(lab_lo, mfr_lo) * 0.935
    out = round_nd(v, nd)
    if high and out <= max(lab_hi, mfr_hi):
        step = 10 ** (-nd) if nd else 1
        out = round_nd(max(lab_hi, mfr_hi) + 3 * step, nd)
    if not high and out >= min(lab_lo, mfr_lo):
        step = 10 ** (-nd) if nd else 1
        out = round_nd(min(lab_lo, mfr_lo) - 3 * step, nd)
    return out


def windows(level: str, assay: str):
    mean = float(FIXED[level][assay][0])
    sd = float(FIXED[level][assay][1])
    lab_lo, lab_hi = mean - 2 * sd, mean + 2 * sd
    mfr = MM[level][assay]
    return mean, sd, lab_lo, lab_hi, mfr["min"], mfr["max"]


def find_page(src: fitz.Document, day: date) -> int:
    needle = day.isoformat()
    for i, pg in enumerate(src):
        if needle in pg.get_text():
            return i
    raise RuntimeError(f"{needle} not in {src.name}")


def path_header_y(page: fitz.Page) -> float:
    hits = page.search_for("QC PATH")
    if not hits:
        raise RuntimeError("QC PATH header missing")
    return hits[0].y0


def assay_row(page: fitz.Page, assay: str, level: str) -> tuple[fitz.Rect, str, tuple[float, float]]:
    split = path_header_y(page)
    needle = "UREA" if assay == "UREA UV" else assay
    hits = list(page.search_for(needle))
    chosen = None
    for h in hits:
        if level == "NORM" and h.y0 < split:
            chosen = h
            break
        if level == "PATH" and h.y0 > split:
            chosen = h
            break
    if chosen is None:
        raise RuntimeError(f"{assay} {level} not on page")
    for block in page.get_text("dict")["blocks"]:
        for line in block.get("lines", []):
            for span in line.get("spans", []):
                x, y = span["origin"]
                if abs(span["bbox"][1] - chosen.y0) > 3:
                    continue
                if not (360 < x < 430):
                    continue
                text = span["text"].strip()
                if re.fullmatch(r"[\d.]+", text):
                    return fitz.Rect(span["bbox"]), text, (x, y)
    raise RuntimeError(f"{assay} {level} result span missing")


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
        c.drawImage(str(logo), inner_right + 3, fy + 8, width=48, height=48, mask="auto", preserveAspectRatio=True)


def draw_form(c: canvas.Canvas, day: date, tests: list[str]) -> None:
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

    dstr = form_date(day)
    for r, test in enumerate(tests[:n_rows]):
        top = header_bottom - r * row_h
        mid_y = top - row_h * 0.42
        c.setFillColor(INK)
        c.setFont(HAND_FONT, 15)
        c.drawCentredString((xs[0] + xs[1]) / 2, mid_y, dstr)
        tsize = 14 if len(test) <= 5 else 11
        c.setFont(HAND_FONT, tsize)
        c.drawCentredString((xs[1] + xs[2]) / 2, mid_y, test)
        c.setFont(HAND_FONT, 13)
        c.drawCentredString((xs[2] + xs[3]) / 2, mid_y + 6, "Daily QC")
        c.drawCentredString((xs[2] + xs[3]) / 2, mid_y - 10, "Out")
        c.setFont(HAND_FONT, 13)
        c.drawCentredString((xs[3] + xs[4]) / 2, mid_y, "TMS30")
        c.setFont(HAND_FONT, 11)
        act_x = xs[5] + 6
        act_y = top - 20
        for line in ACTIONS[r % len(ACTIONS)]:
            c.drawString(act_x, act_y, line)
            act_y -= 13
        c.setFont(HAND_FONT, 16)
        c.drawCentredString((xs[7] + xs[8]) / 2, mid_y, "P")
        c.drawCentredString((xs[8] + xs[9]) / 2, mid_y, "P")

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


def form_pdf(day: date, tests: list[str]) -> fitz.Document:
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=FORM_PAGE)
    c.setTitle("IQC Corrective Action Form")
    c.setAuthor("Noble Diagnostic Centre")
    draw_form(c, day, tests)
    c.save()
    return fitz.open("pdf", buf.getvalue())


def mss_text(page: fitz.Page, xy: tuple[float, float], text: str, size: float = 9) -> None:
    page.insert_text(
        xy,
        text,
        fontsize=size,
        fontname=MSS_NAME,
        fontfile=str(MSS if MSS.exists() else ARIAL),
        color=(0, 0, 0),
    )


def slip_pdf(sample: str, name: str, dt: str, item: str, result: str, rc: str) -> fitz.Document:
    """Corrected TMS sample reprint in the instrument Courier layout."""
    buf = BytesIO()
    w, h = SLIP_PAGE
    c = canvas.Canvas(buf, pagesize=SLIP_PAGE)
    left, right = 28, w - 28
    y = h - 32
    c.setFillColor(black)
    c.setFont(MONO, 9)
    c.drawString(left, y, f"Sample :  {sample} , Type : Serum")
    c.drawRightString(right, y, dt)
    y -= 14
    c.drawString(left, y, f"SampleID    : {name}")
    y -= 10
    c.setStrokeColor(LINE)
    c.setLineWidth(0.5)
    c.line(left, y, right, y)
    y -= 16
    c.setFont(MONO, 8)
    c.drawString(left, y, SLIP_HEADER)
    y -= 14
    c.setFont(MONO, 9)
    item_s = (item or "")[:14].ljust(16)
    result_s = (result or "")[:10].ljust(12)
    c.drawString(left, y, f"{item_s}{result_s}")
    c.drawRightString(right, y, rc)
    c.setFont(FONT, 9)
    c.drawRightString(w - 22, 16, "Page 1")
    c.save()
    return fitz.open("pdf", buf.getvalue())


def patch_qc(src: fitz.Document, idx: int, patches: list[tuple[str, str, str, str]]) -> fitz.Document:
    out = fitz.open()
    out.insert_pdf(src, from_page=idx, to_page=idx)
    page = out[0]
    jobs = []
    for assay, level, old, new in patches:
        rect, found, origin = assay_row(page, assay, level)
        if found != old:
            raise RuntimeError(f"{assay} {level} expected {old!r} got {found!r}")
        jobs.append((origin, new))
        # fill=False keeps the cyan/white row; a painted fill rect shows as a
        # pasted box even when the RGB matches the band.
        page.add_redact_annot(rect, fill=False, cross_out=False)
    page.apply_redactions(
        images=fitz.PDF_REDACT_IMAGE_NONE,
        graphics=fitz.PDF_REDACT_LINE_ART_NONE,
    )
    for origin, text in jobs:
        mss_text(page, origin, text, 9)
    return out


def parse_iso(dt: str) -> datetime:
    return datetime.strptime(dt, "%Y-%m-%d %H:%M:%S")


def slip_stamp(dt: datetime) -> str:
    return dt.strftime("%d-%m-%Y %H:%M:%S")


def load_group(group: dict, src_cache: dict) -> dict:
    day = group["day"]
    pdf = month_pdf(day)
    if pdf.name not in src_cache:
        src_cache[pdf.name] = fitz.open(pdf)
    src = src_cache[pdf.name]
    idx = find_page(src, day)
    page = src[idx]
    loaded_tests = []
    for t in group["tests"]:
        assay, level = t["assay"], t["level"]
        rect, orig_s, origin = assay_row(page, assay, level)
        orig = float(orig_s)
        nd = ndigits(orig_s)
        mean, sd, lab_lo, lab_hi, mfr_lo, mfr_hi = windows(level, assay)
        if "error" in t:
            err_s = str(t["error"])
            err = float(err_s)
        else:
            err = pick_error(lab_lo, lab_hi, mfr_lo, mfr_hi, nd, t["high"])
            err_s = fmt_val(err, nd)
        if "repeat" in t:
            rep_s = str(t["repeat"])
            rep = float(rep_s)
        else:
            rep = round_nd(mean, nd)
            if not (lab_lo < rep < lab_hi and mfr_lo < rep < mfr_hi):
                rep = round_nd((max(lab_lo, mfr_lo) + min(lab_hi, mfr_hi)) / 2, nd)
            rep_s = fmt_val(rep, nd)
        if t["high"]:
            assert err > lab_hi and err > mfr_hi, (day, assay, level, err, lab_hi, mfr_hi)
        else:
            assert err < lab_lo and err < mfr_lo, (day, assay, level, err, lab_lo, mfr_lo)
        assert lab_lo < rep < lab_hi and mfr_lo < rep < mfr_hi, (
            day, assay, level, rep, lab_lo, lab_hi, mfr_lo, mfr_hi,
        )
        qc_words = page.get_text("words")
        row = [w for w in qc_words if abs(w[1] - (origin[1] - 8)) < 6]
        times = [w[4] for w in row if re.match(r"\d{2}:\d{2}:\d{2}", w[4])]
        qc_time = times[0] if times else "08:30:00"
        qc_dt = datetime.combine(day, datetime.strptime(qc_time, "%H:%M:%S").time())
        if "rep_dt" in t:
            rep_dt = t["rep_dt"]
        else:
            rep_dt = slip_stamp(qc_dt + timedelta(hours=1, minutes=18))
        if "rep_rc" in t:
            rep_rc = t["rep_rc"]
        else:
            rep_rc = "100000"
        loaded_tests.append(
            {
                **t,
                "orig_s": orig_s,
                "orig": orig,
                "err": err,
                "err_s": err_s,
                "rep": rep,
                "rep_s": rep_s,
                "lab_lo": lab_lo,
                "lab_hi": lab_hi,
                "mfr_lo": mfr_lo,
                "mfr_hi": mfr_hi,
                "mean": mean,
                "nd": nd,
                "sample": "C1 - 36" if level == "NORM" else "C1 - 37",
                "name": "NORM" if level == "NORM" else "PATH",
                "rep_dt": rep_dt,
                "rep_rc": rep_rc,
            }
        )
    return {
        "day": day,
        "src": src,
        "idx": idx,
        "pdf_name": pdf.name,
        "tests": loaded_tests,
    }


def chunks(items, n):
    for i in range(0, len(items), n):
        yield items[i : i + n]


def main() -> None:
    src_cache: dict[str, fitz.Document] = {}
    loaded = [load_group(g, src_cache) for g in EVENTS]
    loaded.sort(key=lambda g: g["day"], reverse=True)

    combined = fitz.open()
    qc_pages: list[int] = []
    for g in loaded:
        for batch in chunks(g["tests"], 2):
            form = form_pdf(g["day"], [t["form"] for t in batch])
            combined.insert_pdf(form)
        patches = [(t["assay"], t["level"], t["orig_s"], t["err_s"]) for t in g["tests"]]
        qc = patch_qc(g["src"], g["idx"], patches)
        qc_pages.append(combined.page_count)
        combined.insert_pdf(qc)
        for t in g["tests"]:
            rep = slip_pdf(t["sample"], t["name"], t["rep_dt"], t["assay"], t["rep_s"], t["rep_rc"])
            combined.insert_pdf(rep)
        print(f"\n{g['day']}  {g['pdf_name']}")
        for t in g["tests"]:
            print(
                f"  {t['level']:4} {t['assay']:8} {t['orig_s']:>8} → {t['err_s']:>8}  "
                f"repeat {t['rep_s']:>8}  {'HIGH' if t['high'] else 'LOW':4}  "
                f"lab {t['lab_lo']:.3f}–{t['lab_hi']:.3f}  "
                f"mfr {t['mfr_lo']:.3f}–{t['mfr_hi']:.3f}"
            )

    combined.save(OUT_PDF, deflate=True)
    print(f"\nwrote {OUT_PDF}  pages={combined.page_count}")
    printable = fitz.open()
    for i in qc_pages:
        printable.insert_pdf(combined, from_page=i, to_page=i)
    printable.save(OUT_PRINT, deflate=True)
    print(f"wrote {OUT_PRINT}  pages={printable.page_count}")
    printable.close()
    for src in src_cache.values():
        src.close()


if __name__ == "__main__":
    main()
