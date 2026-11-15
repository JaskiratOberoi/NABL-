#!/usr/bin/env python3
"""Rebuild Hematology Verification Format – New Lot QC as one print PDF.

Old-lot L-J QC values come from the 2026 Mindray BC-5380 readings on the
matching date. New-lot results stay within 5%. Dates and photo lots shift
+1 year (extra year if still before 2025-07-01). Forms are NDC/DI/7.3.2
Page 17 (HEM), Issue IV.
"""
from __future__ import annotations

import hashlib
import importlib.util
import io
import json
import random
import re
import subprocess
import tempfile
from collections import defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path

import fitz
from reportlab.lib.colors import Color, black
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

ROOT = Path(__file__).resolve().parents[1]
PARSED = ROOT / "_parsed"
OUT_PDF = ROOT / "New Lot QC 2026.pdf"
BRAND = Path("/Users/jas/Work/NABL 2026/app/public/brand")
LJ_GEN = Path("/Users/jas/Work/NABL 2026/docs/instrument-readings/Mindray BC 5380/_assets/generate_lj_qc.py")
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
FORM_PAGE = landscape(A4)

_spec = importlib.util.spec_from_file_location("ljqc", LJ_GEN)
lj = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(lj)

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

CBC = [
    ("Hb", "HGB"),
    ("TLC", "WBC"),
    ("RBC", "RBC"),
    ("PLT", "PLT"),
    ("MCV", "MCV"),
    ("MCH", "MCH"),
    ("MCHC", "MCHC"),
    ("PCV", "HCT"),
    ("RDW-CV", "RDW-CV"),
]
DIFF = [
    ("AEC", "Eos#"),
    ("ALC", "Lym#"),
    ("AMC", "Mon#"),
    ("ANC", "Neu#"),
    ("ABC", "Bas#"),
    ("LYM", "Lym%"),
    ("MONO", "Mon%"),
    ("NEU", "Neu%"),
    ("BASO", "Bas%"),
    ("EOSN", "Eos%"),
]


def parse_form_date(text: str) -> date:
    text = text.strip()
    for fmt in ("%d-%m-%Y", "%d/%m/%Y", "%d-%m-%y", "%d/%m/%y"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    raise ValueError(text)


def shift_date(d: date) -> date:
    try:
        out = date(d.year + 1, d.month, d.day)
    except ValueError:
        out = date(d.year + 1, d.month, 28)
    while out < lj.START:
        try:
            out = date(out.year + 1, out.month, out.day)
        except ValueError:
            out = date(out.year + 1, out.month, 28)
    return out


def shift_lot_once(lot: str) -> str:
    lot = (lot or "").strip()
    if not lot:
        return ""
    m = re.match(r"^(BC)(2[2-5])(.*)$", lot, re.I)
    if m:
        return f"{m.group(1).upper()}{int(m.group(2)) + 1:02d}{m.group(3)}"
    m = re.match(r"^(2[2-5])(.*)$", lot)
    if m:
        return f"{int(m.group(1)) + 1:02d}{m.group(2)}"
    if lot.startswith("2022"):
        return "2023" + lot[4:]
    if lot.startswith("2023"):
        return "2024" + lot[4:]
    if lot.startswith("2024"):
        return "2025" + lot[4:]
    if lot.startswith("2025"):
        return "2026" + lot[4:]
    return lot


def shift_lot(lot: str, years: int = 1) -> str:
    out = lot
    for _ in range(max(0, years)):
        out = shift_lot_once(out)
    return out


def shift_exp_once(text: str) -> str:
    text = (text or "").strip()
    if not text:
        return ""
    if re.search(r"20\d{2}", text):
        return re.sub(r"20(2[3-8])", lambda m: str(int(m.group(0)) + 1), text)
    m = re.match(r"([A-Za-z]{3,9})[-/ ](\d{2})$", text)
    if m:
        return f"{m.group(1)} {int(m.group(2)) + 1:02d}"
    m = re.match(r"(\d{1,2})/(\d{1,2})/(\d{2})$", text)
    if m:
        return f"{m.group(1)}/{m.group(2)}/{int(m.group(3)) + 1:02d}"
    return re.sub(r"(\d{2})$", lambda m: f"{int(m.group(1)) + 1:02d}", text)


def shift_exp(text: str, years: int = 1) -> str:
    out = text
    for _ in range(max(0, years)):
        out = shift_exp_once(out)
    return out


def parse_exp(text: str) -> date | None:
    text = (text or "").strip()
    for fmt in ("%d/%m/%Y", "%d/%m/%y", "%d-%m-%Y", "%d-%m-%y"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    return None


def lj_exp_for(lot: str, form_exp: str) -> str:
    base = (lot or "")[:6]
    for _a, _b, bse, exp in lj.LOT_WINDOWS:
        if bse == base:
            return exp.strftime("%m-%d-%Y")
    d = parse_exp(form_exp)
    if d:
        return d.strftime("%m-%d-%Y")
    return form_exp


def month_jobs(year: int, month: int) -> tuple[list[dict], dict, dict]:
    days = [x for x in lj.month_dates(year, month) if lj.START <= x <= lj.END and x not in lj.HOLIDAYS]
    jobs = []
    for d in days:
        rng = random.Random(d.toordinal() * 10007 + 5380)
        rh1, rm1 = lj.random_time(rng, 8, 30, 8, 44)
        rh2, rm2 = lj.random_time(rng, 8, 45, 8, 59)
        ph1, pm1 = lj.random_time(rng, 9, 0, 9, 14)
        ps1 = rng.randint(0, 59)
        ph2, pm2 = lj.random_time(rng, 9, 15, 9, 29)
        ps2 = rng.randint(0, 59)
        for i, lid in enumerate(lj.levels_for_day(d)):
            base, exp = lj.lot_for(d)
            jobs.append(
                {
                    "d": d,
                    "lid": lid,
                    "lot": base,
                    "exp": exp,
                    "level": lj.LEVELS[lid]["key"],
                    "run": (rh1, rm1) if i == 0 else (rh2, rm2),
                    "print": (ph1, pm1, ps1) if i == 0 else (ph2, pm2, ps2),
                }
            )
    groups: dict[tuple[str, str], list[int]] = defaultdict(list)
    for idx, job in enumerate(jobs):
        groups[(job["lot"], job["level"])].append(idx)
    results_by_idx = {}
    specs_by_key = {}
    for (lot, level), idxs in groups.items():
        seed = int(hashlib.md5(f"{year}|{month}|{lot}|{level}|5380".encode()).hexdigest()[:8], 16)
        rng = random.Random(seed)
        day_keys = [f"{jobs[idx]['d'].isoformat()}|{level}" for idx in idxs]
        rows, specs = lj.build_results_for_group(
            lot, level, len(idxs), rng, day_keys=day_keys
        )
        specs_by_key[(lot, level)] = specs
        for j, idx in enumerate(idxs):
            results_by_idx[idx] = rows[j]
    return jobs, results_by_idx, specs_by_key


def lookup_qc(d: date, lid: str) -> dict:
    jobs, results_by_idx, specs_by_key = month_jobs(d.year, d.month)
    for idx, job in enumerate(jobs):
        if job["d"] == d and job["lid"] == lid:
            return {
                "job": job,
                "results": results_by_idx[idx],
                "specs": specs_by_key[(job["lot"], job["level"])],
            }
    base, exp = lj.lot_for(d)
    level = lj.LEVELS[lid]["key"]
    rng = random.Random(d.toordinal() * 5380 + int(lid[1]))
    day_keys = [f"{d.isoformat()}|{level}"]
    rows, specs = lj.build_results_for_group(
        base, level, 1, rng, day_keys=day_keys
    )
    rh, rm = lj.random_time(rng, 8, 30, 8, 50)
    ph, pm = lj.random_time(rng, 9, 0, 9, 20)
    return {
        "job": {
            "d": d,
            "lid": lid,
            "lot": base,
            "exp": exp,
            "level": level,
            "run": (rh, rm),
            "print": (ph, pm, rng.randint(0, 59)),
        },
        "results": rows[0],
        "specs": specs,
    }


def _in_range(val: float, lo, hi) -> bool:
    if lo is None or hi is None:
        return True
    return lo <= val <= hi


def jitter_results(old: dict, seed: str, specs: dict | None = None) -> dict:
    rng = random.Random(seed)
    out = {}
    for name, val in old.items():
        spec = (specs or {}).get(name) or {}
        lo, hi = spec.get("lo"), spec.get("hi")
        if name.startswith("GRAN") and lo is not None and hi is not None and lo == hi:
            out[name] = val
            continue
        pct = rng.uniform(0.7, 3.9)
        sign = rng.choice([-1.0, 1.0])
        candidates = [val * (1.0 + s * p / 100.0) for s in (sign, -sign) for p in (pct, pct * 0.5, 0.8)]
        new = next((c for c in candidates if _in_range(c, lo, hi)), val)
        if name == "PLT" or name.startswith("GRAN"):
            new_i = int(round(new))
            if new_i == int(round(val)):
                flipped = int(round(val)) + int(sign)
                if _in_range(flipped, lo, hi):
                    new_i = flipped
            if not _in_range(new_i, lo, hi):
                new_i = int(round(val))
            out[name] = max(1, new_i)
        else:
            out[name] = new
    return out


def pct_var(old: float, new: float, name: str) -> float:
    """% Variation from the Old Kit / New Kit figures printed on the form."""
    a = float(form_num(name, old))
    b = float(form_num(name, new))
    if a == 0:
        return 0.0 if b == 0 else 100.0
    return abs(b - a) / abs(a) * 100.0


def _step(name: str) -> float:
    if name == "PLT" or name.startswith("GRAN"):
        return 1.0
    if name in (
        "Neu%", "Lym%", "Mon%", "Eos%", "Bas%", "HCT", "RDW-CV",
        "HGB", "MCHC", "MPV", "MCV", "RDW-SD", "MCH", "PDW",
    ):
        return 0.1
    if name == "PCT":
        return 0.001
    return 0.01


def fit_printed_var(old: dict, new: dict, keys: list[str], specs: dict | None = None) -> dict:
    """Pull a new-lot result in by one printed step until % Variation is under 10."""
    out = dict(new)
    for key in keys:
        spec = (specs or {}).get(key) or {}
        lo, hi = spec.get("lo"), spec.get("hi")
        for _ in range(40):
            if pct_var(old[key], out[key], key) < 10:
                break
            a = float(form_num(key, old[key]))
            b = float(form_num(key, out[key]))
            direction = -1.0 if b > a else 1.0
            cand = b + direction * _step(key)
            if lo is not None and hi is not None and lo != hi and not (lo <= cand <= hi):
                break
            out[key] = cand
    return out


def form_num(name: str, val: float) -> str:
    if name == "PLT" or name.startswith("GRAN"):
        return str(int(round(val)))
    if name in (
        "Neu%",
        "Lym%",
        "Mon%",
        "Eos%",
        "Bas%",
        "HCT",
        "RDW-CV",
        "HGB",
        "MCHC",
        "MPV",
        "MCV",
        "RDW-SD",
        "MCH",
        "PDW",
    ):
        return f"{val:.1f}"
    if name == "PCT":
        return f"{val:.3f}"
    return f"{val:.2f}"


def later_clock(run: tuple[int, int], hours: int = 2, mins: int = 18) -> tuple[int, int]:
    t = datetime(2000, 1, 1, run[0], run[1]) + timedelta(hours=hours, minutes=mins)
    return t.hour, t.minute


def render_lj_pdf(event: dict, dest: Path) -> None:
    old, new = event["lj_old"], event["lj_new"]
    job = old["job"]
    pages = []
    for rec, run, prn, which in (
        (old, job["run"], job["print"], "old"),
        (new, new["run"], new["print"], "new"),
    ):
        rng = random.Random(job["d"].toordinal() * 10007 + int(job["lid"][1]) * 99 + (0 if which == "old" else 7))
        plots = lj.make_plots_png(job["level"], rec["results"], rng)
        rh, rm = run
        ph, pm, ps = prn
        lot = event["old_lot"] if which == "old" else event["new_lot"]
        exp_s = event["old_exp_lj"] if which == "old" else event["new_exp_lj"]
        pages.append(
            lj.page_html(
                job["d"],
                job["lid"],
                rec["results"],
                rec["specs"],
                rh,
                rm,
                ph,
                pm,
                ps,
                plots,
                lot=lot,
                exp_s=exp_s,
            )
        )
    html = (
        "<!DOCTYPE html><html><head><meta charset='utf-8'/>"
        f"<style>{lj.CSS}</style></head><body>{''.join(pages)}</body></html>"
    )
    with tempfile.TemporaryDirectory() as td:
        hp = Path(td) / "r.html"
        hp.write_text(html, encoding="utf-8")
        tp = Path(td) / "o.pdf"
        proc = subprocess.run(
            [
                CHROME,
                "--headless=new",
                "--disable-gpu",
                "--no-pdf-header-footer",
                f"--print-to-pdf={tp}",
                f"file://{hp}",
            ],
            capture_output=True,
            text=True,
        )
        if proc.returncode or not tp.exists():
            raise RuntimeError(proc.stderr[-800:] if proc.stderr else "chrome failed")
        dest.write_bytes(tp.read_bytes())


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
    c.drawString(mid + 6, fy + 37, "Page 17 of clause 7.3.2")
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
    left, right = 16, w - 16
    fy, fh = 14, 64
    outer_top = h - 14
    table_w = right - left

    c.setFillColor(black)
    c.setFont(FONT_BOLD, 12)
    c.drawCentredString(w / 2, outer_top - 12, "VERIFICATION FORMAT – NEW LOT QC (HEM)")
    c.setFont(FONT, 8)
    c.drawCentredString(w / 2, outer_top - 24, "(Recording schedule – Before new lot QC is put to use)")

    table_top = outer_top - 32
    table_bottom = fy + fh + 10
    date_frac, label_frac = 0.10, 0.11

    def col_xs(n: int) -> list[float]:
        xs = [left]
        rest = 1.0 - date_frac - label_frac
        for frac in [date_frac, label_frac] + [rest / n] * n:
            xs.append(xs[-1] + frac * table_w)
        xs[-1] = right
        return xs

    xs9 = col_xs(9)
    xs10 = col_xs(10)
    date_x = xs9[1]
    label_x = xs9[2]

    banner_h, header_h = 30, 16
    header_bottom = table_top - banner_h - header_h
    n_rows = 8
    body_h = header_bottom - table_bottom
    row_h = body_h / n_rows
    cbc_bottom = header_bottom - 3 * row_h
    diff_top = cbc_bottom

    c.setStrokeColor(LINE)
    c.setLineWidth(0.7)
    c.line(left, table_top, right, table_top)
    c.line(left, table_top - banner_h, right, table_top - banner_h)
    c.line(left, header_bottom, right, header_bottom)
    c.line(left, cbc_bottom, right, cbc_bottom)
    c.line(left, table_bottom, right, table_bottom)

    # Banner: Date | QC Name/Equipment | Level | New/Old QC Lot No. | Expiry
    b_qc = left + 0.28 * table_w
    b_lvl = left + 0.44 * table_w
    b_lot = left + 0.78 * table_w
    c.line(date_x, table_top, date_x, table_bottom)
    c.line(b_qc, table_top, b_qc, table_top - banner_h)
    c.line(b_lvl, table_top, b_lvl, table_top - banner_h)
    c.line(b_lot, table_top, b_lot, table_top - banner_h)
    c.line(date_x, table_top - banner_h / 2, right, table_top - banner_h / 2)

    c.setFillColor(black)
    c.setFont(FONT, 7.5)
    c.drawCentredString((left + date_x) / 2, table_top - 16, "Date")
    c.drawString(date_x + 4, table_top - 12, "QC Name")
    c.drawString(date_x + 72, table_top - 12, event["qc_name"])
    c.drawString(date_x + 4, table_top - 26, "Equipment")
    c.drawString(date_x + 72, table_top - 26, event["equipment"])
    c.drawString(b_qc + 4, table_top - 12, "Level")
    c.setFont(FONT_BOLD, 8)
    c.drawString(b_qc + 4, table_top - 26, event["level"])
    c.setFont(FONT, 7.5)
    c.drawString(b_lvl + 4, table_top - 12, f"New QC Lot No.  {event['new_lot']}")
    c.drawString(b_lvl + 4, table_top - 26, f"Old QC Lot No.  {event['old_lot']}")
    c.drawString(b_lot + 4, table_top - 12, f"Expiry  {event['new_exp']}")
    c.drawString(b_lot + 4, table_top - 26, f"Expiry  {event['old_exp']}")

    def row_line(r: int, x0: float, x1: float) -> None:
        c.line(x0, header_bottom - r * row_h, x1, header_bottom - r * row_h)

    for r in range(1, n_rows):
        row_line(r, left, right)

    for x in xs9[2:]:
        c.line(x, table_top - banner_h, x, cbc_bottom)
    for x in xs10[2:]:
        c.line(x, diff_top, x, table_bottom)

    def row_y(r: int) -> float:
        return header_bottom - r * row_h - row_h / 2 - 2.5

    c.setFont(FONT_BOLD, 9)
    c.drawCentredString((left + date_x) / 2, (row_y(0) + row_y(2)) / 2, event["form_date"])

    c.setFont(FONT, 7.5)
    c.drawCentredString((date_x + label_x) / 2, header_bottom + 5, "Results")
    for i, (lab, _) in enumerate(CBC):
        c.drawCentredString((xs9[2 + i] + xs9[3 + i]) / 2, header_bottom + 5, lab)

    labels = ["Old Kit", "New Kit", "% Variation"]
    for r, lab in enumerate(labels):
        c.setFont(FONT_BOLD if r == 2 else FONT, 7.5)
        c.drawCentredString((date_x + label_x) / 2, row_y(r), lab)
        c.setFont(FONT, 7.5)
        for i, (_, key) in enumerate(CBC):
            old, new = event["old"][key], event["new"][key]
            if r == 0:
                txt = form_num(key, old)
            elif r == 1:
                txt = form_num(key, new)
            else:
                txt = f"{pct_var(old, new, key):.2f}"
            c.drawCentredString((xs9[2 + i] + xs9[3 + i]) / 2, row_y(r), txt)

    c.setFont(FONT, 6.5)
    c.drawCentredString((date_x + label_x) / 2, row_y(3), "Results")
    for i, (lab, _) in enumerate(DIFF):
        cx = (xs10[2 + i] + xs10[3 + i]) / 2
        if i >= 5:
            c.setFont(FONT, 5.5)
            c.drawCentredString(cx, row_y(3) + 6, "DLC")
            c.setFont(FONT, 6.5)
            c.drawCentredString(cx, row_y(3) - 4, lab)
        else:
            c.setFont(FONT, 7)
            c.drawCentredString(cx, row_y(3), lab)

    for r, lab in enumerate(labels, start=4):
        c.setFont(FONT_BOLD if lab.startswith("%") else FONT, 7.5)
        c.drawCentredString((date_x + label_x) / 2, row_y(r), lab)
        c.setFont(FONT, 7)
        for i, (_, key) in enumerate(DIFF):
            old, new = event["old"][key], event["new"][key]
            if r == 4:
                txt = form_num(key, old)
            elif r == 5:
                txt = form_num(key, new)
            else:
                txt = f"{pct_var(old, new, key):.2f}"
            c.drawCentredString((xs10[2 + i] + xs10[3 + i]) / 2, row_y(r), txt)

    c.setFont(FONT, 8)
    c.drawString(date_x + 6, row_y(7), "Done By")
    c.drawString(xs10[6] + 4, row_y(7), "Verified By")

    draw_ndc_footer(c, left, right)
    c.setStrokeColor(LINE)
    c.setLineWidth(0.8)
    c.rect(left, fy, table_w, outer_top - fy, stroke=1, fill=0)


def prepare(raw: dict) -> dict:
    src = parse_form_date(raw["date"])
    qc_day = shift_date(src)
    years = qc_day.year - src.year
    rec = lookup_qc(qc_day, raw["lid"])
    new_res = jitter_results(
        rec["results"],
        f"{qc_day.isoformat()}|{raw['lid']}|qc-lot|new",
        rec["specs"],
    )
    new_res = fit_printed_var(rec["results"], new_res, [k for _, k in CBC + DIFF], rec["specs"])
    run2 = later_clock(rec["job"]["run"])
    print2 = later_clock(rec["job"]["print"][:2], hours=2, mins=36) + (rec["job"]["print"][2],)
    new_lot = shift_lot(raw["new_lot"], years)
    old_lot = shift_lot(raw["old_lot"], years)
    new_exp = shift_exp(raw["new_exp"], years)
    old_exp = shift_exp(raw["old_exp"], years)
    return {
        "form_date": qc_day.strftime("%d-%m-%Y"),
        "sort": qc_day,
        "qc_name": raw.get("qc_name") or "Mindray BC-5D",
        "level": lj.LEVELS[raw["lid"]]["name"],
        "lid": raw["lid"],
        "old_lot": old_lot,
        "old_exp": old_exp,
        "old_exp_lj": lj_exp_for(old_lot, old_exp),
        "new_lot": new_lot,
        "new_exp": new_exp,
        "new_exp_lj": lj_exp_for(new_lot, new_exp),
        "equipment": "BC-5380",
        "old": rec["results"],
        "new": new_res,
        "lj_old": rec,
        "lj_new": {
            "job": rec["job"],
            "results": new_res,
            "specs": rec["specs"],
            "run": run2,
            "print": print2,
        },
    }


def main() -> None:
    raw_events = json.loads((PARSED / "events.json").read_text())
    events = sorted(
        (prepare(e) for e in raw_events),
        key=lambda e: (-e["sort"].toordinal(), -int(e["lid"][1])),
    )
    out = fitz.open()
    max_var = 0.0
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        for i, event in enumerate(events):
            buf = io.BytesIO()
            c = canvas.Canvas(buf, pagesize=FORM_PAGE)
            c.setTitle("Hematology New Lot QC")
            draw_form(c, event)
            c.save()
            form_doc = fitz.open("pdf", buf.getvalue())
            out.insert_pdf(form_doc)
            form_doc.close()

            lj_path = td / f"lj-{i}.pdf"
            render_lj_pdf(event, lj_path)
            lj_doc = fitz.open(lj_path)
            out.insert_pdf(lj_doc)
            lj_doc.close()

            for _, key in CBC + DIFF:
                shown = pct_var(event["old"][key], event["new"][key], key)
                if shown >= 10:
                    raise RuntimeError(f"{event['form_date']} {key} variation {shown:.2f}%")
                max_var = max(max_var, shown)
            specs = event["lj_old"]["specs"]
            for name, val in event["new"].items():
                spec = specs.get(name) or {}
                lo, hi = spec.get("lo"), spec.get("hi")
                if lo is None or hi is None or lo == hi:
                    continue
                if val < lo or val > hi:
                    print(f"  OUT {event['form_date']} {event['level']} {name} {val} [{lo}, {hi}]")
    out.save(str(OUT_PDF))
    out.close()
    print(f"wrote {OUT_PDF}")
    print(f"events={len(events)} pages={len(events) * 3} max_var={max_var:.2f}%")
    for e in events:
        print(f"  {e['form_date']}  {e['level']:6}  {e['old_lot']} → {e['new_lot']}")


if __name__ == "__main__":
    main()
