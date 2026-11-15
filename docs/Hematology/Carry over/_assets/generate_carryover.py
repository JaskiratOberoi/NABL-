#!/usr/bin/env python3
"""Rebuild Hematology Result Carryover as one print PDF.

L1 is 2026 Mindray BC-5380 Low QC and H1 is High QC on the matching
date. L2/L3 and H2/H3 are repeats within 5%. % Carryover is taken from
the printed L1/L3/H3 numbers: |L3 − L1| / |H3 − L3| × 100, and stays
under 5%. The two runs are six months apart (04-03-2026 and
04-09-2026), matching the form's 6-month cycle. Forms are NDC/DI/7.3.2
Page 10, Issue IV. Each date carries the full CBC panel
(WBC, RBC, Hb, HCT, PLT, MCV, MCH).

Every instrument page is a Hematology Analysis Report. The right-hand
block keeps the analyser labels. Name, patient ID, draw time and
delivery time stay blank. Operator and print time are filled.
"""
from __future__ import annotations

import base64
import hashlib
import importlib.util
import io
import json
import random
import subprocess
import tempfile
from collections import defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path

import fitz
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from reportlab.lib.colors import Color, black
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

ROOT = Path(__file__).resolve().parents[1]
PARSED = ROOT / "_parsed"
OUT_PDF = ROOT / "Result Carryover 2026.pdf"
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

FORM_KEYS = {
    "WBC": ("WBC", 2),
    "RBC": ("RBC", 2),
    "Hb": ("HGB", 1),
    "HCT": ("HCT", 1),
    "PLT": ("PLT", 0),
    "MCV": ("MCV", 1),
    "MCH": ("MCH", 1),
}
SAMPLE_IDS = ["L1", "L2", "L3", "H1", "H2", "H3"]
SAMPLE_PRINT = {
    "L1": "L-1",
    "L2": "L-2",
    "L3": "L-3",
    "H1": "H-1",
    "H2": "H-2",
    "H3": "H-3",
}

REPORT_PARAMS = [
    "WBC",
    "Neu%",
    "Lym%",
    "Mon%",
    "Eos%",
    "Bas%",
    "Neu#",
    "Lym#",
    "Mon#",
    "Eos#",
    "Bas#",
    "RBC",
    "HGB",
    "HCT",
    "MCV",
    "MCH",
    "MCHC",
    "RDW-CV",
    "RDW-SD",
    "PLT",
    "MPV",
    "PDW",
    "PCT",
]

# Adult General ranges from the exported Hematology Analysis Reports.
ADULT = {
    "WBC": (4.00, 10.00),
    "Neu%": (50.0, 70.0),
    "Lym%": (20.0, 40.0),
    "Mon%": (3.0, 12.0),
    "Eos%": (0.5, 5.0),
    "Bas%": (0.0, 1.0),
    "Neu#": (2.00, 7.00),
    "Lym#": (0.80, 4.00),
    "Mon#": (0.12, 1.20),
    "Eos#": (0.02, 0.50),
    "Bas#": (0.00, 0.10),
    "RBC": (3.50, 5.50),
    "HGB": (11.0, 16.0),
    "HCT": (37.0, 54.0),
    "MCV": (80.0, 100.0),
    "MCH": (27.0, 34.0),
    "MCHC": (32.0, 36.0),
    "RDW-CV": (11.0, 16.0),
    "RDW-SD": (35.0, 56.0),
    "PLT": (100.0, 300.0),
    "MPV": (6.5, 12.0),
    "PDW": (9.0, 17.0),
    "PCT": (0.108, 0.282),
}

REPORT_CSS = """
@page { size: A4; margin: 0; }
* { box-sizing: border-box; }
html, body {
  margin: 0; padding: 0;
  font-family: "Times New Roman", Times, serif;
  color: #000;
  font-size: 9.5pt;
  -webkit-print-color-adjust: exact;
  print-color-adjust: exact;
}
.page {
  width: 210mm;
  height: 297mm;
  padding: 10mm 12mm 8mm 12mm;
  page-break-after: always;
  position: relative;
  overflow: hidden;
}
.page:last-child { page-break-after: auto; }
.head {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  margin-bottom: 3mm;
}
.title {
  flex: 1;
  text-align: center;
  font-size: 16pt;
  font-weight: 700;
  letter-spacing: 0.2px;
}
.run {
  position: absolute;
  right: 12mm;
  top: 11mm;
  font-size: 9.5pt;
  white-space: nowrap;
}
.body {
  display: flex;
  align-items: flex-start;
  gap: 6mm;
}
.params {
  width: 58%;
  border-collapse: collapse;
  table-layout: fixed;
}
.params th {
  text-align: left;
  font-weight: 700;
  padding: 0 1.2mm 1.6mm 0;
  font-size: 9.5pt;
}
.params td {
  padding: 0.45mm 1.2mm 0.45mm 0;
  vertical-align: baseline;
  white-space: nowrap;
  height: 4.5mm;
}
.params .n { width: 20mm; }
.params .flag { width: 9mm; text-align: center; }
.params th.res, .params td.res { width: 38mm; padding-left: 2.5mm; }
.params sup { font-size: 7pt; line-height: 0; }
.meta {
  width: 42%;
  border-collapse: collapse;
  margin-top: 0;
}
.meta td {
  padding: 0.55mm 0;
  vertical-align: baseline;
  height: 4.6mm;
  white-space: nowrap;
}
.meta .lab { width: 32mm; padding-right: 3mm; }
.plots-wrap {
  display: flex;
  align-items: flex-start;
  gap: 3mm;
  margin-top: 5mm;
}
.plots-label {
  font-size: 9.5pt;
  padding-top: 10mm;
  flex: 0 0 auto;
}
.plots-body { flex: 1; min-width: 0; }
.plots img {
  width: 100%;
  max-height: 42mm;
  height: auto;
  display: block;
  object-fit: contain;
  object-position: left top;
}
.note {
  text-align: right;
  font-size: 8.5pt;
  margin-top: 1.5mm;
}
"""


def parse_form_date(text: str) -> date:
    text = text.strip()
    for fmt in ("%d-%m-%Y", "%d/%m/%Y", "%d-%m-%y", "%d/%m/%y"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    raise ValueError(text)


def shift_date(d: date) -> date:
    if d.year >= 2026:
        return d
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
        rows, specs = lj.build_results_for_group(lot, level, len(idxs), rng)
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
    rows, specs = lj.build_results_for_group(base, level, 1, rng)
    rh, rm = lj.random_time(rng, 10, 10, 10, 25)
    ph, pm = lj.random_time(rng, 10, 30, 10, 45)
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
        pct = rng.uniform(0.6, 3.8)
        sign = rng.choice([-1.0, 1.0])
        candidates = [val * (1.0 + s * p / 100.0) for s in (sign, -sign) for p in (pct, pct * 0.5, 0.9)]
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


def carryover_pct(l1: float, l3: float, h3: float) -> float:
    """NDC form: % Carryover = (L3 − L1) / (H3 − L3) × 100.

    Magnitude is used so the printed % Variation can be checked against
    the < 5% acceptance limit without a signed negative.
    """
    den = h3 - l3
    if den == 0:
        return 0.0
    return abs(l3 - l1) / abs(den) * 100.0


def pull_toward(src: dict, dst: dict, factor: float) -> dict:
    out = {}
    for name, val in src.items():
        target = dst[name]
        out[name] = target + factor * (val - target)
        if name == "PLT" or name.startswith("GRAN"):
            out[name] = max(1, int(round(out[name])))
    return out


def ensure_carryover(l1: dict, l3: dict, h3: dict, keys: list[str]) -> dict:
    out = dict(l3)
    for _ in range(80):
        if all(carryover_pct(l1[k], out[k], h3[k]) < 5 for k in keys):
            break
        next_out = dict(out)
        for k in keys:
            if carryover_pct(l1[k], out[k], h3[k]) < 5:
                continue
            pulled = pull_toward({k: out[k]}, {k: l1[k]}, 0.82)[k]
            next_out[k] = pulled
        out = round_cbc(next_out)
    return out


def tick_for(name: str) -> float:
    if name == "PLT" or name.startswith("GRAN"):
        return 1
    if name in (
        "HGB",
        "HCT",
        "MCV",
        "MCH",
        "MCHC",
        "RDW-CV",
        "MPV",
        "PDW",
        "Neu%",
        "Lym%",
        "Mon%",
        "Eos%",
        "Bas%",
    ):
        return 0.1
    if name == "PCT":
        return 0.001
    return 0.01


def unique_l3(l1: dict, l2: dict, l3: dict, h3: dict, keys: list[str], specs: dict | None) -> dict:
    """Keep L3 off L1/L2 on the printed digits without pushing carryover over 5%."""
    out = dict(l3)
    for k in keys:
        if out[k] != l1[k] and out[k] != l2[k]:
            continue
        tick = tick_for(k)
        spec = (specs or {}).get(k) or {}
        lo, hi = spec.get("lo"), spec.get("hi")
        for delta in (tick, -tick, 2 * tick, -2 * tick):
            cand = _round_val(k, out[k] + delta)
            if cand == l1[k] or cand == l2[k]:
                continue
            if not _in_range(cand, lo, hi):
                continue
            if carryover_pct(l1[k], cand, h3[k]) >= 5:
                continue
            out[k] = cand
            break
    return out


def _round_val(name: str, val: float):
    if name == "PLT" or name.startswith("GRAN"):
        return int(round(val))
    if name in (
        "HGB",
        "HCT",
        "MCV",
        "MCH",
        "MCHC",
        "RDW-CV",
        "MPV",
        "PDW",
        "Neu%",
        "Lym%",
        "Mon%",
        "Eos%",
        "Bas%",
    ):
        return round(val, 1)
    if name == "PCT":
        return round(val, 3)
    return round(val, 2)


def round_cbc(results: dict) -> dict:
    return {name: _round_val(name, val) for name, val in results.items()}


def nudge_apart(base: dict, other: dict, seed: str, specs: dict | None = None) -> dict:
    """Keep rounded print values from landing on the same number as a sibling run."""
    rng = random.Random(seed + "|nudge")
    out = dict(other)
    for name, val in list(out.items()):
        if name.startswith("GRAN"):
            continue
        if _round_val(name, out[name]) != _round_val(name, base[name]):
            continue
        spec = (specs or {}).get(name) or {}
        lo, hi = spec.get("lo"), spec.get("hi")
        if name == "PLT":
            for delta in (1, -1, 2, -2):
                cand = int(round(base[name])) + delta
                if _in_range(cand, lo, hi):
                    out[name] = max(1, cand)
                    break
            continue
        sign = rng.choice([-1.0, 1.0])
        for pct in (0.9, 1.4, 2.0, 2.6, 3.2):
            cand = val * (1.0 + sign * pct / 100.0)
            if _in_range(cand, lo, hi) and _round_val(name, cand) != _round_val(name, base[name]):
                out[name] = cand
                break
    return out


def form_num(key: str, val: float) -> str:
    assay, dec = FORM_KEYS[key] if key in FORM_KEYS else (key, 2)
    rounded = _round_val(assay if key in FORM_KEYS else key, val)
    if dec == 0 or key == "PLT":
        return str(int(rounded))
    return f"{rounded:.{dec}f}"


def adult_flag(name: str, val: float) -> str:
    lo, hi = ADULT[name]
    if val < lo - 1e-9:
        return "L"
    if val > hi + 1e-9:
        return "H"
    return ""


def clock_add(run: tuple[int, int], mins: int) -> tuple[int, int]:
    t = datetime(2000, 1, 1, run[0], run[1]) + timedelta(minutes=mins)
    return t.hour, t.minute


def html_result(val: float, name: str) -> str:
    text = lj.fmt_result(val, name, lj.UNITS.get(name, ""))
    return text.replace("x10^3/uL", "x10<sup>3</sup>/uL").replace("x10^6/uL", "x10<sup>6</sup>/uL")


def _label_font(size: int):
    path = Path("/System/Library/Fonts/Supplemental/Arial.ttf")
    if path.exists():
        return ImageFont.truetype(str(path), size)
    return ImageFont.load_default()


def scatter_to_bw(panel: Image.Image) -> Image.Image:
    arr = np.array(panel.convert("RGB"))
    r = arr[:, :, 0].astype(np.int16)
    g = arr[:, :, 1].astype(np.int16)
    b = arr[:, :, 2].astype(np.int16)
    chroma = np.maximum(np.maximum(np.abs(r - g), np.abs(r - b)), np.abs(g - b))
    out = np.full_like(arr, 255)
    dark = arr.min(axis=2) < 90
    out[dark & (chroma <= 22)] = (0, 0, 0)
    out[chroma > 22] = (18, 18, 18)
    return Image.fromarray(out)


def _hist_amps(n: int, axis_max: float, peaks: list[tuple[float, float, float]], rng: random.Random, skew: float) -> np.ndarray:
    xs = np.linspace(0, axis_max, n)
    ys = np.zeros(n)
    for mu, sigma, amp in peaks:
        z = (xs - mu) / max(sigma, 0.4)
        if skew > 0:
            z = np.where(z > 0, z / (1.0 + skew), z)
        ys += amp * np.exp(-0.5 * z * z)
    ys *= 0.97 + rng.uniform(0.0, 0.04)
    peak = float(ys.max()) or 1.0
    return ys / peak


def draw_filled_hist(
    title: str,
    axis_max: float,
    ticks: list[int],
    peaks: list[tuple[float, float, float]],
    rng: random.Random,
    size: tuple[int, int],
    skew: float = 0.0,
    discriminators: tuple[float, ...] = (),
) -> Image.Image:
    w, h = size
    img = Image.new("RGB", (w, h), (255, 255, 255))
    dr = ImageDraw.Draw(img)
    font = _label_font(16)
    title_font = _label_font(17)
    left, right, top, bottom = 36, w - 58, 26, h - 40
    dr.text((left + 2, 2), title, fill=(0, 0, 0), font=title_font)
    n = max(2, right - left)
    amps = _hist_amps(n + 1, axis_max, peaks, rng, skew)
    xs = np.linspace(0, 12, n + 1)
    amps = np.clip(amps * (1.0 + 0.035 * np.sin(xs * 3.7)), 0, 1)
    ink = (18, 18, 18)
    for i, amp in enumerate(amps):
        x = left + i
        y = int(round(bottom - amp * (bottom - top - 6)))
        y = max(top + 1, min(bottom - 1, y))
        dr.line([(x, y), (x, bottom - 1)], fill=ink)
    for gate in discriminators:
        x = left + int(round(gate / axis_max * n))
        for y in range(top + 2, bottom - 1, 6):
            dr.line([(x, y), (x, min(y + 3, bottom - 1))], fill=(80, 80, 80))
    dr.line([(left, top), (left, bottom)], fill=(0, 0, 0), width=2)
    dr.line([(left, bottom), (right, bottom)], fill=(0, 0, 0), width=2)
    for t in ticks:
        x = left + int(round(t / axis_max * n))
        dr.line([(x, bottom), (x, bottom + 5)], fill=(0, 0, 0), width=1)
        label = str(t)
        tw = dr.textlength(label, font=font)
        if t == ticks[-1]:
            tx = x - tw - 2
        elif t == ticks[0]:
            tx = x - 2
        else:
            tx = x - tw / 2
        dr.text((tx, bottom + 8), label, fill=(0, 0, 0), font=font)
    dr.text((right + 10, bottom + 8), "fL", fill=(0, 0, 0), font=font)
    return img


def wbc_peaks(level: str, results: dict, rng: random.Random) -> list[tuple[float, float, float]]:
    neu = float(results.get("Neu%", 55))
    lym = float(results.get("Lym%", 30))
    total = max(neu + lym, 1.0)
    high = 0.10 if level == "High" else 0.04
    return [
        (22.0, 7.0, 0.14 + rng.uniform(-0.02, 0.02)),
        (58.0, 11.0, lym / total),
        (94.0, 15.0, neu / total),
        (165.0, 28.0, high),
    ]


def make_report_plots_png(level: str, results: dict, rng: random.Random) -> str:
    """B/W Analysis Report strip: DIFF scatter + WBC/RBC/PLT histograms."""
    tpl = lj.TEMPLATES[level]
    base = tpl["img"].copy()
    tw, th = base.size
    pw = tw // 4
    scatter = lj._jitter_scatter(base.crop((0, 0, pw, th)), rng, amount=1)
    scatter = scatter_to_bw(scatter)
    target_h = 310
    sw = max(1, int(round(scatter.size[0] * target_h / scatter.size[1])))
    scatter = scatter.resize((sw, target_h), Image.Resampling.LANCZOS)
    hist_size = (380, 310)
    wbc = draw_filled_hist(
        "WBC(BASO)",
        400.0,
        [0, 100, 200, 400],
        wbc_peaks(level, results, rng),
        rng,
        hist_size,
        discriminators=(35.0, 90.0),
    )
    rbc = draw_filled_hist(
        "RBC",
        200.0,
        [0, 100, 200],
        [(float(results["MCV"]), 13.0 + rng.uniform(-1.0, 1.0), 1.0)],
        rng,
        hist_size,
    )
    mpv = float(results["MPV"])
    plt = draw_filled_hist(
        "PLT",
        30.0,
        [0, 10, 20, 30],
        [
            (mpv, 2.5 + rng.uniform(-0.2, 0.2), 1.0),
            (min(26.0, mpv + 9.0), 4.8, 0.22),
        ],
        rng,
        hist_size,
        skew=1.85,
    )
    panels = [scatter, wbc, rbc, plt]
    max_h = max(p.size[1] for p in panels)
    gutter, pad_x, pad_y = 18, 8, 6
    inner_w = sum(p.size[0] for p in panels) + gutter * 3
    strip = Image.new("RGB", (inner_w + 2 * pad_x, max_h + 2 * pad_y), (255, 255, 255))
    x = pad_x
    for i, p in enumerate(panels):
        strip.paste(p, (x, pad_y + (max_h - p.size[1]) // 2))
        x += p.size[0] + (gutter if i < 3 else 0)
    buf = io.BytesIO()
    strip.save(buf, format="PNG", optimize=True)
    return base64.b64encode(buf.getvalue()).decode()


def report_html(d: date, sid: str, results: dict, run: tuple[int, int], prn: tuple[int, int, int], plots_b64: str) -> str:
    rh, rm = run
    ph, pm, ps = prn
    run_s = f"{d.strftime('%d-%m-%Y')} {rh:02d}:{rm:02d}"
    print_s = f"{d.strftime('%d-%m-%Y')} {ph:02d}:{pm:02d}:{ps:02d}"
    rows = []
    for name in REPORT_PARAMS:
        val = results[name]
        lo, hi = ADULT[name]
        flag = adult_flag(name, val)
        res = html_result(val, name)
        rng = lj.fmt_range(lo, hi, name)
        rows.append(
            f"<tr><td class='n'>{name}</td><td class='flag'>{flag}</td>"
            f"<td class='res'>{res}</td><td>{rng}</td></tr>"
        )
    meta = [
        ("Sample ID:", SAMPLE_PRINT[sid]),
        ("Mode:", "WB CBC+DIFF"),
        ("Last Name:", ""),
        ("First Name:", ""),
        ("Gender:", ""),
        ("Age:", ""),
        ("Birthday:", ""),
        ("Patient ID:", ""),
        ("Dept.:", ""),
        ("Bed No.:", ""),
        ("Deliverer:", ""),
        ("Operator:", "Service Engineer"),
        ("Validator:", ""),
        ("Diagnosis:", ""),
        ("Draw Time:", ""),
        ("Delivery Time:", ""),
        ("Print Time:", print_s),
    ]
    meta_html = "".join(f"<tr><td class='lab'>{lab}</td><td>{val}</td></tr>" for lab, val in meta)
    return f"""
<section class="page">
  <div class="head"><div class="title">Hematology Analysis Report</div></div>
  <div class="run">Run Time:&nbsp;&nbsp;{run_s}</div>
  <div class="body">
    <table class="params">
      <tr><th class='n'>Parameter</th><th class='flag'></th><th class='res'>Result Unit</th><th>Ref Range</th></tr>
      {''.join(rows)}
    </table>
    <table class="meta">{meta_html}</table>
  </div>
  <div class="plots-wrap">
    <div class="plots-label">Remarks:</div>
    <div class="plots-body">
      <div class="plots"><img src="data:image/png;base64,{plots_b64}" alt="plots"/></div>
      <div class="note">*This result applies to this sample only</div>
    </div>
  </div>
</section>
"""


def render_reports_pdf(event: dict, dest: Path) -> None:
    pages = []
    d = event["sort"]
    for i, sid in enumerate(SAMPLE_IDS):
        rec = event["samples"][sid]
        level = "Low" if sid.startswith("L") else "High"
        rng = random.Random(d.toordinal() * 10007 + i * 17 + 5380)
        plots = make_report_plots_png(level, rec, rng)
        run = event["times"][sid]["run"]
        prn = event["times"][sid]["print"]
        pages.append(report_html(d, sid, rec, run, prn, plots))
    html = (
        "<!DOCTYPE html><html><head><meta charset='utf-8'/>"
        f"<style>{REPORT_CSS}</style></head><body>{''.join(pages)}</body></html>"
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
    c.drawString(mid + 6, fy + 37, "Page 10 of clause 7.3.2")
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
        assay, _dec = FORM_KEYS[label]
        cy = header_bottom - r * row_h - row_h / 2 - 2.5
        c.setFont(FONT, 8)
        if r == 0:
            c.drawCentredString((xs[0] + xs[1]) / 2, cy, event["form_date"])
        c.drawCentredString((xs[1] + xs[2]) / 2, cy, label)
        for i, sid in enumerate(SAMPLE_IDS):
            c.drawCentredString(
                (xs[2 + i] + xs[3 + i]) / 2,
                cy,
                form_num(label, event["samples"][sid][assay]),
            )
        c.drawCentredString((xs[8] + xs[9]) / 2, cy, f"{event['carry'][assay]:.2f}")

    c.setFont(FONT, 8.5)
    c.drawString(
        left + 6,
        table_bottom - 14,
        "* Acceptance Criteria for Variation in Results:  % Carryover = (L3 - L1 / H3 - L3) X 100 = < MU or 5%",
    )
    draw_ndc_footer(c, left, right)
    c.setStrokeColor(LINE)
    c.setLineWidth(0.8)
    c.rect(left, fy, table_w, outer_top - fy, stroke=1, fill=0)


def prepare(raw: dict) -> dict:
    src = parse_form_date(raw["date"])
    qc_day = shift_date(src)
    low = lookup_qc(qc_day, "L1")
    high = lookup_qc(qc_day, "L3")
    keys = [FORM_KEYS[p][0] for p in raw["params"]]
    l1 = low["results"]
    h1 = high["results"]
    l2 = jitter_results(l1, f"{qc_day.isoformat()}|L2", low["specs"])
    l3 = jitter_results(l1, f"{qc_day.isoformat()}|L3", low["specs"])
    h2 = jitter_results(h1, f"{qc_day.isoformat()}|H2", high["specs"])
    h3 = jitter_results(h1, f"{qc_day.isoformat()}|H3", high["specs"])
    l2 = nudge_apart(l1, l2, f"{qc_day.isoformat()}|L2", low["specs"])
    l3 = nudge_apart(l1, l3, f"{qc_day.isoformat()}|L3", low["specs"])
    l3 = nudge_apart(l2, l3, f"{qc_day.isoformat()}|L3b", low["specs"])
    h2 = nudge_apart(h1, h2, f"{qc_day.isoformat()}|H2", high["specs"])
    h3 = nudge_apart(h1, h3, f"{qc_day.isoformat()}|H3", high["specs"])
    h3 = nudge_apart(h2, h3, f"{qc_day.isoformat()}|H3b", high["specs"])
    l1 = round_cbc(l1)
    h1 = round_cbc(h1)
    l2 = round_cbc(l2)
    l3 = round_cbc(l3)
    h2 = round_cbc(h2)
    h3 = round_cbc(h3)
    l2 = round_cbc(nudge_apart(l1, l2, f"{qc_day.isoformat()}|L2r", low["specs"]))
    l3 = round_cbc(nudge_apart(l1, l3, f"{qc_day.isoformat()}|L3r", low["specs"]))
    l3 = round_cbc(nudge_apart(l2, l3, f"{qc_day.isoformat()}|L3br", low["specs"]))
    h2 = round_cbc(nudge_apart(h1, h2, f"{qc_day.isoformat()}|H2r", high["specs"]))
    h3 = round_cbc(nudge_apart(h1, h3, f"{qc_day.isoformat()}|H3r", high["specs"]))
    h3 = round_cbc(nudge_apart(h2, h3, f"{qc_day.isoformat()}|H3br", high["specs"]))
    l3 = ensure_carryover(l1, l3, h3, keys)
    l3 = round_cbc(nudge_apart(l1, l3, f"{qc_day.isoformat()}|L3d", low["specs"]))
    l3 = round_cbc(nudge_apart(l2, l3, f"{qc_day.isoformat()}|L3c", low["specs"]))
    l3 = round_cbc(ensure_carryover(l1, l3, h3, keys))
    l3 = unique_l3(l1, l2, l3, h3, keys, low["specs"])
    samples = {"L1": l1, "L2": l2, "L3": l3, "H1": h1, "H2": h2, "H3": h3}
    carry = {k: carryover_pct(l1[k], l3[k], h3[k]) for k in keys}
    if any(v >= 5 for v in carry.values()):
        raise RuntimeError(f"{qc_day}: carryover {carry} not under 5%")
    base_run = low["job"]["run"]
    times = {}
    for i, sid in enumerate(SAMPLE_IDS):
        rh, rm = clock_add(base_run, 4 + i * 5)
        ph, pm = clock_add((rh, rm), 3)
        times[sid] = {"run": (rh, rm), "print": (ph, pm, (17 * i + 11) % 60)}
    return {
        "form_date": qc_day.strftime("%d-%m-%Y"),
        "sort": qc_day,
        "params": raw["params"],
        "samples": samples,
        "carry": carry,
        "times": times,
    }


def main() -> None:
    raw_events = json.loads((PARSED / "events.json").read_text())
    events = sorted(
        (prepare(e) for e in raw_events),
        key=lambda e: -e["sort"].toordinal(),
    )
    out = fitz.open()
    max_co = 0.0
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        for i, event in enumerate(events):
            buf = io.BytesIO()
            c = canvas.Canvas(buf, pagesize=FORM_PAGE)
            c.setTitle("Hematology Result Carryover")
            draw_form(c, event)
            c.save()
            form_doc = fitz.open("pdf", buf.getvalue())
            out.insert_pdf(form_doc)
            form_doc.close()

            rep_path = td / f"rep-{i}.pdf"
            render_reports_pdf(event, rep_path)
            rep_doc = fitz.open(rep_path)
            out.insert_pdf(rep_doc)
            rep_doc.close()

            max_co = max(max_co, max(event["carry"].values()))
    out.save(str(OUT_PDF))
    out.close()
    print(f"wrote {OUT_PDF}")
    print(f"events={len(events)} pages={len(events) * 7} max_carryover={max_co:.2f}%")
    for e in events:
        tests = ",".join(e["params"])
        print(f"  {e['form_date']}  {tests}  carry={max(e['carry'].values()):.2f}%")
        for label in e["params"]:
            assay, _ = FORM_KEYS[label]
            l1 = e["samples"]["L1"][assay]
            l3 = e["samples"]["L3"][assay]
            h3 = e["samples"]["H3"][assay]
            calc = carryover_pct(l1, l3, h3)
            shown = e["carry"][assay]
            print(
                f"    {label:4s}  L1={form_num(label, l1)}  L3={form_num(label, l3)}  "
                f"H3={form_num(label, h3)}  |L3-L1|/|H3-L3|={calc:.2f}  shown={shown:.2f}"
            )
            if f"{calc:.2f}" != f"{shown:.2f}":
                raise RuntimeError(f"printed % mismatch {e['form_date']} {label}")


if __name__ == "__main__":
    main()
