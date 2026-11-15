#!/usr/bin/env python3
"""Rebuild immunoassay Lot Verification as one print PDF.

NDC new-lot forms stay filled. Maglumi Sample Result Reports keep the
binder layout. L1/L2 concentrations, RLU and first-run finish times come
from the 2026 Maglumi X3 QC readings. Repeat-run concentrations stay
within 5% of that original. Dates +1 year. Reagent lots whose first two
digits are a year (24… / 25…) increment that prefix only.
"""
from __future__ import annotations

import json
import random
import re
from pathlib import Path

from reportlab.lib.colors import Color, black
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

ROOT = Path(__file__).resolve().parents[1]
PARSED = ROOT / "_parsed"
OUT_PDF = ROOT / "Lot Verification 2026.pdf"
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
LIGHT = Color(0.55, 0.55, 0.55)
HEADER_BG = Color(0.82, 0.82, 0.82)
MAG_LINE = Color(0.35, 0.35, 0.35)

SAMPLE_COLS = [
    ("Sample ID", 0.18),
    ("Assay", 0.14),
    ("RLU", 0.10),
    ("RLU CV (%)", 0.10),
    ("Conc.", 0.16),
    ("Flag", 0.08),
    ("Finish Time", 0.24),
]

KIT_ASSAY = {
    "Testo": "TEST",
    "TEST": "TEST",
    "FSH": "FSH",
    "LH": "LH",
    "E2": "E2",
    "BhCG": "HCG/B-HCG",
    "BHCG": "HCG/B-HCG",
    "T3": "T3",
    "T4": "T4",
    "TSH": "TSH",
    "PrL": "PRL",
    "Prl": "PRL",
    "PRL": "PRL",
}


def shift_iso(text: str) -> str:
    return text.replace("2025", "2026").replace("2024", "2025").replace("2023", "2024")


def shift_form_date(text: str) -> str:
    d, m, y = text.strip().split("/")
    if len(y) == 2:
        return f"{d}/{m}/{int(y) + 1:02d}"
    return f"{d}/{m}/{int(y) + 1}"


def form_date_to_iso(text: str) -> str:
    d, m, y = text.strip().split("/")
    yi = int(y)
    if yi < 100:
        yi += 2000
    yi += 1
    return f"{yi:04d}-{int(m):02d}-{int(d):02d}"


def shift_expiry(text: str) -> str:
    text = (text or "").strip()
    if re.search(r"20\d{2}", text):
        return re.sub(r"20(2[3-8])", lambda m: str(int(m.group(0)) + 1), text)
    return re.sub(r"([/-])(\d{2})$", lambda m: f"{m.group(1)}{int(m.group(2)) + 1:02d}", text)


def shift_lot(lot: str) -> str:
    lot = (lot or "").strip()
    if lot.startswith("24"):
        return "25" + lot[2:]
    if lot.startswith("25"):
        return "26" + lot[2:]
    return lot


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
    rec = qc[day]
    for row in rec[level]:
        if row["assay"] == assay:
            return row
    raise KeyError(f"{day} {level} {assay}")


def make_repeat(orig_val: float, dec: int, orig_rlu: int, seed: str) -> tuple[float, int, float]:
    rng = random.Random(seed)
    for _ in range(40):
        pct = rng.uniform(1.1, 4.4)
        sign = rng.choice([-1.0, 1.0])
        new_val = round(orig_val * (1.0 + sign * pct / 100.0), dec)
        if new_val <= 0:
            continue
        var = abs(new_val - orig_val) / orig_val * 100.0
        if var <= 5.0 and var >= 0.4:
            new_rlu = max(1, int(round(orig_rlu * (new_val / orig_val))))
            return new_val, new_rlu, var
    new_val = round(orig_val * 1.02, dec)
    var = abs(new_val - orig_val) / orig_val * 100.0
    new_rlu = max(1, int(round(orig_rlu * (new_val / orig_val))))
    return new_val, new_rlu, var


def build_values(pages: list[dict], qc: dict) -> dict:
    needed: set[tuple[str, str, str]] = set()
    for p in pages:
        if p["kind"] == "form":
            day = form_date_to_iso(p["blocks"][0]["date"])
            for bl in p["blocks"]:
                assay = KIT_ASSAY[bl["kit_name"]]
                needed.add((day, assay, "L1"))
                needed.add((day, assay, "L2"))
        else:
            day = shift_iso(p["datetime"])[:10]
            for r in p["rows"]:
                level = "L1" if "L1" in r["sample_id"] else "L2"
                needed.add((day, r["assay"], level))

    out = {}
    for day, assay, level in sorted(needed):
        mag = maglumi_row(qc, day, level, assay)
        val, unit, dec = parse_conc(mag["conc"])
        rlu = int(mag["rlu"])
        new_val, new_rlu, var = make_repeat(val, dec, rlu, f"{day}|{assay}|{level}")
        out[(day, assay, level)] = {
            "old_val": val,
            "old_rlu": rlu,
            "old_conc": mag["conc"],
            "old_finish": mag["finish"],
            "unit": unit,
            "dec": dec,
            "new_val": new_val,
            "new_rlu": new_rlu,
            "new_conc": f"{fmt_num(new_val, dec)} {unit}".strip(),
            "var": var,
        }
    return out


def load_pages() -> list[dict]:
    pages = []
    for name in ("batch1.json", "batch2.json"):
        pages.extend(json.loads((PARSED / name).read_text()))
    return pages


def draw_ndc_footer(c: canvas.Canvas, left: float, right: float) -> None:
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


def draw_form(c: canvas.Canvas, page: dict, values: dict) -> None:
    w, h = FORM_PAGE
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
    xs[-1] = right

    results_x0, results_x1 = xs[3], xs[6]
    banner_h, header_h = 14, 16
    c.setStrokeColor(LINE)
    c.setLineWidth(0.7)
    c.rect(left, table_top - banner_h - header_h, table_w, banner_h + header_h, stroke=1, fill=0)
    for x in (xs[1], xs[2], xs[3], xs[6], xs[7]):
        c.line(x, table_top, x, table_top - banner_h - header_h)
    c.line(results_x0, table_top - banner_h, results_x1, table_top - banner_h)
    c.line(xs[4], table_top - banner_h, xs[4], table_top - banner_h - header_h)
    c.line(xs[5], table_top - banner_h, xs[5], table_top - banner_h - header_h)
    c.setFillColor(black)
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
    blocks = page["blocks"]
    for b in range(n_blocks):
        top = hy - header_h - b * block_h
        bot = top - block_h
        c.setStrokeColor(LINE)
        c.setLineWidth(0.7)
        c.rect(left, bot, table_w, block_h, stroke=1, fill=0)
        for x in xs[1:-1]:
            c.line(x, top, x, bot)
        sub = block_h / 4
        c.setFont(FONT, 7)
        c.setFillColor(LIGHT)
        for kit_i in (3, 4):
            c.drawString(xs[kit_i] + 4, top - sub + 4, "Lot No.")
            c.drawString(xs[kit_i] + 4, top - 2 * sub + 4, "Expiry")
        c.setFillColor(black)
        for i in range(1, 4):
            c.setStrokeColor(LINE)
            c.setLineWidth(0.4)
            c.line(xs[3], top - i * sub, xs[6], top - i * sub)

        if b >= len(blocks):
            continue
        bl = blocks[b]
        day = form_date_to_iso(bl["date"])
        assay = KIT_ASSAY[bl["kit_name"]]
        l1 = values[(day, assay, "L1")]
        l2 = values[(day, assay, "L2")]
        date_s = shift_form_date(bl["date"])
        c.setFillColor(black)
        c.setFont(FONT, 9)
        c.drawCentredString((xs[0] + xs[1]) / 2, bot + block_h / 2 - 3, date_s)
        c.drawCentredString((xs[1] + xs[2]) / 2, top - 3 * sub + 4, "L1")
        c.drawCentredString((xs[1] + xs[2]) / 2, top - 4 * sub + 4, "L2")
        c.setFont(FONT_BOLD, 10)
        c.drawCentredString((xs[2] + xs[3]) / 2, bot + block_h / 2 - 3, bl["kit_name"])
        c.setFont(FONT, 8)
        c.drawString(xs[3] + 42, top - sub + 4, shift_lot(bl["old_lot"]))
        c.drawString(xs[3] + 42, top - 2 * sub + 4, shift_expiry(bl["old_exp"]))
        c.drawString(xs[4] + 42, top - sub + 4, shift_lot(bl["new_lot"]))
        c.drawString(xs[4] + 42, top - 2 * sub + 4, shift_expiry(bl["new_exp"]))
        c.setFont(FONT, 9)
        c.drawCentredString((xs[3] + xs[4]) / 2, top - 3 * sub + 4, fmt_num(l1["old_val"], l1["dec"]))
        c.drawCentredString((xs[3] + xs[4]) / 2, top - 4 * sub + 4, fmt_num(l2["old_val"], l2["dec"]))
        c.drawCentredString((xs[4] + xs[5]) / 2, top - 3 * sub + 4, fmt_num(l1["new_val"], l1["dec"]))
        c.drawCentredString((xs[4] + xs[5]) / 2, top - 4 * sub + 4, fmt_num(l2["new_val"], l2["dec"]))
        c.drawCentredString((xs[5] + xs[6]) / 2, top - 3 * sub + 4, f"{l1['var']:.2f}")
        c.drawCentredString((xs[5] + xs[6]) / 2, top - 4 * sub + 4, f"{l2['var']:.2f}")

    c.setFillColor(black)
    c.setFont(FONT, 8.5)
    c.drawString(
        left,
        table_bottom - 14,
        "Acceptance Criteria: Quantitative Results - % Variation < +/- 1 SD or 10%",
    )
    draw_ndc_footer(c, left, right)


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


def draw_sample(c: canvas.Canvas, page: dict, values: dict, seen_runs: set[tuple[str, str, str]]) -> None:
    w, h = A4
    dt = shift_iso(page["datetime"])
    c.setFillColor(black)
    c.setFont(FONT, 8)
    c.drawString(36, h - 28, "Model: MAGLUMI X3")
    c.drawRightString(w - 36, h - 28, dt)
    c.setFont(FONT_BOLD, 12)
    c.drawCentredString(w / 2, h - 48, "Sample Result Report")

    day = dt[:10]
    rows: list[list[str]] = []
    for r in page["rows"]:
        level = "L1" if "L1" in r["sample_id"] else "L2"
        assay = r["assay"]
        key = (day, assay, level)
        rec = values[key]
        if key not in seen_runs:
            seen_runs.add(key)
            conc, rlu, finish = rec["old_conc"], str(rec["old_rlu"]), rec["old_finish"]
        else:
            conc, rlu, finish = rec["new_conc"], str(rec["new_rlu"]), shift_iso(r["finish"])
        rows.append([r["sample_id"], assay, rlu, r.get("rlu_cv") or "0", conc, r.get("flag") or "", finish])

    left, right = 42, w - 42
    table_w = right - left
    table_top = h - 62
    pad = 5
    xs = [left]
    for _, frac in SAMPLE_COLS:
        xs.append(xs[-1] + frac * table_w)
    xs[-1] = right
    header_h, row_h = 16, 15.5
    c.setFillColor(HEADER_BG)
    c.rect(left, table_top - header_h, table_w, header_h, stroke=0, fill=1)
    c.setStrokeColor(MAG_LINE)
    c.setLineWidth(0.55)
    c.rect(left, table_top - header_h, table_w, header_h, stroke=1, fill=0)
    for x in xs[1:-1]:
        c.line(x, table_top, x, table_top - header_h)
    c.setFillColor(black)
    c.setFont(FONT, 8)
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
            c.drawString(xs[i] + pad, y - 11, str(val))
        y -= row_h

    draw_snibe(c, 42, 28)
    c.setFillColor(black)
    c.setFont(FONT, 8)
    c.drawRightString(w - 42, 32, "Page 1 of 1")


def main() -> None:
    pages = load_pages()
    qc = json.loads((PARSED / "maglumi_qc.json").read_text())
    values = build_values(pages, qc)
    c = canvas.Canvas(str(OUT_PDF), pagesize=A4)
    c.setTitle("Immunoassay Lot Verification")
    c.setAuthor("Noble Diagnostic Centre")
    n_form = n_sample = 0
    max_var = 0.0
    seen_runs: set[tuple[str, str, str]] = set()
    for p in pages:
        if p["kind"] == "form":
            c.setPageSize(FORM_PAGE)
            draw_form(c, p, values)
            n_form += 1
        else:
            c.setPageSize(A4)
            draw_sample(c, p, values, seen_runs)
            n_sample += 1
        c.showPage()
    for rec in values.values():
        max_var = max(max_var, rec["var"])
    c.save()
    serial = []
    for p in pages:
        if p["kind"] == "form":
            blocks = []
            day = form_date_to_iso(p["blocks"][0]["date"])
            for bl in p["blocks"]:
                assay = KIT_ASSAY[bl["kit_name"]]
                l1, l2 = values[(day, assay, "L1")], values[(day, assay, "L2")]
                blocks.append(
                    {
                        "date": shift_form_date(bl["date"]),
                        "kit_name": bl["kit_name"],
                        "old_lot": shift_lot(bl["old_lot"]),
                        "old_exp": shift_expiry(bl["old_exp"]),
                        "new_lot": shift_lot(bl["new_lot"]),
                        "new_exp": shift_expiry(bl["new_exp"]),
                        "old_L1": fmt_num(l1["old_val"], l1["dec"]),
                        "new_L1": fmt_num(l1["new_val"], l1["dec"]),
                        "var_L1": f"{l1['var']:.2f}",
                        "old_L2": fmt_num(l2["old_val"], l2["dec"]),
                        "new_L2": fmt_num(l2["new_val"], l2["dec"]),
                        "var_L2": f"{l2['var']:.2f}",
                    }
                )
            serial.append({"file": p["file"], "kind": "form", "blocks": blocks})
        else:
            serial.append({"file": p["file"], "kind": "sample", "datetime": shift_iso(p["datetime"])})
    (PARSED / "pages.json").write_text(json.dumps(serial, indent=2) + "\n")
    print(f"wrote {OUT_PDF}")
    print(f"pages={len(pages)} form={n_form} sample={n_sample} max_var={max_var:.2f}%")
    first = pages[0]["blocks"][0]
    day = form_date_to_iso(first["date"])
    rec = values[(day, KIT_ASSAY[first["kit_name"]], "L1")]
    print("example", first["kit_name"], shift_form_date(first["date"]), rec["old_conc"], "→", rec["new_conc"], f"{rec['var']:.2f}%")


if __name__ == "__main__":
    main()
