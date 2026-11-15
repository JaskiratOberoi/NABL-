#!/usr/bin/env python3
"""
Generate Mindray BC-5380 QCDart LJ Chart Report monthly PDFs.

Mean, SD, CV and N are all from that month's points only (dominant lot per
level). Same value engine as the L-J QC Run pack.
"""
from __future__ import annotations

import base64
import calendar
import hashlib
import json
import math
import random
import re
import subprocess
import sys
import tempfile
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path

# Import shared schedule / value engine from QC Run generator
sys.path.insert(0, str(Path(__file__).resolve().parent))
import generate_lj_qc as qc  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "2026"
ASSETS = Path(__file__).resolve().parent
OUT.mkdir(exist_ok=True)
FIXED_JSON = ASSETS / "fixed-mean-sd-by-lot.json"

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
LOGO = ASSETS / "qdart_logo_tight.png"
LOGO_B64 = base64.b64encode(LOGO.read_bytes()).decode()

COPYRIGHT = "© Copyright 2025 Steller Infomatica. All rights reserved."
ORG = "Noble Diagnostic Centre / Noble Diagnostic Centre DELHI"
ADDR = "WZ 409 C HARI NAGAR NEW DELHI,India,Delhi,Delhi,110064"
CONTACT = "SHIPRA | M: 9511018366"
INSTRUMENT = "Mindray | BC-5380"
METHOD = "Haematology - CBC"

TESTS = [
    ("WBC", "WBC", "x10^3/uL"),
    ("RBC", "RBC", "x10^6/uL"),
    ("HGB", "HGB", "g/dL"),
    ("HCT", "HCT", "%"),
    ("MCV", "MCV", "fL"),
    ("MCH", "MCH", "pg"),
    ("MCHC", "MCHC", "g/dL"),
    ("PLT", "PLT", "x10^3/uL"),
    ("MPV", "MPV", "fL"),
    ("RDW-CV", "RDW-CV", "%"),
    ("RDW-SD", "RDW-SD", "fL"),
    ("Neu%", "Neu%", "%"),
    ("Lym%", "Lym%", "%"),
    ("Mon%", "Mon%", "%"),
    ("Eos%", "Eos%", "%"),
    ("Bas%", "Bas%", "%"),
    ("Neu#", "Neu#", "x10^3/uL"),
    ("Lym#", "Lym#", "x10^3/uL"),
    ("Mon#", "Mon#", "x10^3/uL"),
    ("Eos#", "Eos#", "x10^3/uL"),
    ("Bas#", "Bas#", "x10^3/uL"),
]

C_RED, C_YEL, C_GRN = "#E53935", "#FBC02D", "#43A047"
C_MEAN = "#212121"
C_LINE = "#1E88E5"
C_PT, C_PT_EDGE = "#66BB6A", "#43A047"

LEVEL_LABEL = {"Low": "Level 1", "Normal": "Level 2", "High": "Level 3"}
# Distinct from mean/SD colours — vial-open event marker on the plot
C_VIAL = "#EF6C00"


def sample_sd(vals, mean):
    if len(vals) < 2:
        return 0.0
    return math.sqrt(sum((v - mean) ** 2 for v in vals) / (len(vals) - 1))


def cv_pct(vals):
    if len(vals) < 2:
        return 0.0
    m = sum(vals) / len(vals)
    if abs(m) < 1e-12:
        return 0.0
    return sample_sd(vals, m) / abs(m) * 100.0


def month_window(year, month):
    days = [
        d
        for d in qc.month_dates(year, month)
        if qc.START <= d <= qc.END and d not in qc.HOLIDAYS
    ]
    if not days:
        return None
    cal0 = date(year, month, 1)
    last = calendar.monthrange(year, month)[1]
    cal1 = date(year, month, last)
    a0 = max(cal0, qc.START)
    a1 = min(cal1, qc.END)
    return days, a0, a1


def lot_line_for_days(days):
    """Build QC lot information string for lots used in this month."""
    seen = []
    for d in days:
        base, exp = qc.lot_for(d)
        key = (base, exp)
        if key not in seen:
            seen.append(key)
    parts = [f"{base}B | {exp.strftime('%d/%m/%Y')}" for base, exp in seen]
    return "Mindray | BC-5D Hematology Control | " + " | ".join(parts)


def vial_open_dates_for_level(level_key: str) -> list[tuple[date, str]]:
    """Vial-change markers: first working day of each half-month (1–15 / 16–end)
    when this level is in the active pair, labelled with the lot in use.
    """
    opens: list[tuple[date, str]] = []
    seen: set[tuple[int, int, int]] = set()  # year, month, half
    d = qc.START
    while d <= qc.END:
        if d not in qc.HOLIDAYS:
            lids = qc.levels_for_day(d)
            if any(qc.LEVELS[lid]["key"] == level_key for lid in lids):
                half = 0 if d.day <= 15 else 1
                key = (d.year, d.month, half)
                if key not in seen:
                    seen.add(key)
                    base, _ = qc.lot_for(d)
                    opens.append((d, base))
        d += timedelta(days=1)
    return opens


def _month_jobs_and_results(year, month, days):
    """Same value engine as L-J QC Run (including Baso-only preservation)."""
    jobs = []
    for d in days:
        for lid in qc.levels_for_day(d):
            base, _ = qc.lot_for(d)
            jobs.append(
                {
                    "d": d,
                    "lid": lid,
                    "lot": base,
                    "level": qc.LEVELS[lid]["key"],
                }
            )

    groups = defaultdict(list)
    for idx, job in enumerate(jobs):
        groups[(job["lot"], job["level"])].append(idx)

    results_by_idx = {}
    for (lot, level), idxs in groups.items():
        seed = int(
            hashlib.md5(f"{year}|{month}|{lot}|{level}|5380".encode()).hexdigest()[:8],
            16,
        )
        day_keys = [f"{jobs[idx]['d'].isoformat()}|{level}" for idx in idxs]
        rows, _specs = qc.build_results_for_group(
            lot, level, len(idxs), random.Random(seed), day_keys=day_keys
        )
        for j, idx in enumerate(idxs):
            results_by_idx[idx] = rows[j]
    return jobs, results_by_idx


def build_universe():
    """All (date, level) → result row across START..END."""
    universe = {}
    y, m = qc.START.year, qc.START.month
    while date(y, m, 1) <= qc.END:
        win = month_window(y, m)
        if win:
            days, _a0, _a1 = win
            jobs, results_by_idx = _month_jobs_and_results(y, m, days)
            for idx, job in enumerate(jobs):
                universe[(job["d"], job["level"])] = {
                    "lot": job["lot"],
                    "row": results_by_idx[idx],
                }
        m += 1
        if m > 12:
            m = 1
            y += 1
    return universe


def compute_lot_fixed(universe):
    """
    Cumulative mean/SD for each lot × level × parameter over the full lot window.
    Held constant on every monthly LJ chart for that lot.
    """
    buckets = defaultdict(list)  # (lot, level, param) -> [values]
    for (d, level), rec in universe.items():
        lot = rec["lot"]
        row = rec["row"]
        for name, _t, _u in TESTS:
            if name in row:
                buckets[(lot, level, name)].append(float(row[name]))

    fixed = {}
    serializable = {}
    for (lot, level, name), vals in sorted(buckets.items()):
        mean = sum(vals) / len(vals)
        sd = sample_sd(vals, mean)
        fixed[(lot, level, name)] = (mean, sd, len(vals))
        serializable.setdefault(lot, {}).setdefault(level, {})[name] = {
            "mean": round(mean, 6),
            "sd": round(sd, 6),
            "n": len(vals),
            "cv": round((sd / abs(mean) * 100.0) if abs(mean) > 1e-12 else 0.0, 4),
        }
    FIXED_JSON.write_text(json.dumps(serializable, indent=2))
    return fixed


def collect_month_series(days, universe):
    """
    Month plot points for every scheduled level on every day, plus the
    dominant lot per level (most run days) for Mean/SD/CV.

    Always two levels per day (PAIR_CYCLE). When a lot changes mid-month,
    both lots' points are plotted so two controls remain visible daily;
    Mean/SD/CV use the dominant lot only so bands are not inflated.
    """
    lot_counts = defaultdict(lambda: defaultdict(int))
    series = {lv: defaultdict(list) for lv in ("Low", "Normal", "High")}
    lots_by_point = {lv: defaultdict(list) for lv in ("Low", "Normal", "High")}
    for d in days:
        for lid in qc.levels_for_day(d):
            level = qc.LEVELS[lid]["key"]
            rec = universe.get((d, level))
            if not rec:
                continue
            lot_counts[level][rec["lot"]] += 1
            row = rec["row"]
            for name, _t, _u in TESTS:
                if name in row:
                    series[level][name].append((d, float(row[name])))
                    lots_by_point[level][name].append(rec["lot"])
    dominant = {
        lv: max(counts.items(), key=lambda kv: kv[1])[0]
        for lv, counts in lot_counts.items()
        if counts
    }
    return series, dominant, lots_by_point


def x_tick_dates(start, end):
    n = (end - start).days
    if n <= 0:
        return [start]
    idxs = sorted(set(int(round(i * n / 5)) for i in range(6)))
    return [start + timedelta(days=i) for i in idxs]


def fmt_num(x, mean):
    if abs(mean) >= 100:
        return f"{x:.1f}"
    if abs(mean) >= 10:
        return f"{x:.2f}"
    return f"{x:.3f}"


def svg_chart(
    points,
    mean,
    sd,
    level_name,
    n,
    month_cv,
    x_start,
    x_end,
    vial_opens=None,
    height=118,
):
    W, H = 720, height
    ML, MR, MT, MB = 56, 78, 8, 22
    pw, ph = W - ML - MR, H - MT - MB
    X_PAD = 10.0
    PT_R = 3.4
    LEGEND_GAP = 20
    span = max(sd, abs(mean) * 0.01, 1e-6)
    y_min, y_max = mean - 3.5 * span, mean + 3.5 * span
    vial_opens = vial_opens or []
    open_days = {d for d, _lot in vial_opens}

    def yx(v):
        return MT + (y_max - v) / (y_max - y_min) * ph

    def xx(d):
        s = max((x_end - x_start).days + 1, 1)
        return ML + X_PAD + ((d - x_start).days / s) * (pw - 2 * X_PAD)

    levels = [
        (mean + 3 * sd, C_RED, "+3SD", "2.2 2.2"),
        (mean + 2 * sd, C_YEL, "+2SD", "2.2 2.2"),
        (mean + 1 * sd, C_GRN, "+1SD", "2.2 2.2"),
        (mean, C_MEAN, "Mean", None),
        (mean - 1 * sd, C_GRN, "-1SD", "2.2 2.2"),
        (mean - 2 * sd, C_YEL, "-2SD", "2.2 2.2"),
        (mean - 3 * sd, C_RED, "-3SD", "2.2 2.2"),
    ]
    clip_id = f"plotClip-{abs(hash((level_name, round(mean, 6), round(sd, 6), n))) % 10_000_000}"
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">']
    parts.append(
        f'<defs><clipPath id="{clip_id}">'
        f'<rect x="{ML}" y="{MT}" width="{pw}" height="{ph}"/>'
        f"</clipPath></defs>"
    )
    parts.append(
        f'<rect x="{ML}" y="{MT}" width="{pw}" height="{ph}" fill="#fff" stroke="#BDBDBD" stroke-width="1"/>'
    )
    # Vial-open markers (behind data): dashed vertical + top label
    for od, lot in vial_opens:
        if not (x_start <= od <= x_end):
            continue
        x = xx(od)
        parts.append(
            f'<line x1="{x:.2f}" y1="{MT}" x2="{x:.2f}" y2="{MT+ph}" stroke="{C_VIAL}" '
            f'stroke-width="1.35" stroke-dasharray="3.5 2.5" opacity="0.95"/>'
        )
        # Small downward triangle at top of plot
        parts.append(
            f'<polygon points="{x-4.2:.2f},{MT+1} {x+4.2:.2f},{MT+1} {x:.2f},{MT+8}" '
            f'fill="{C_VIAL}"/>'
        )
        parts.append(
            f'<text x="{x:.2f}" y="{MT+18}" text-anchor="middle" '
            f'font-family="Arial,Helvetica,sans-serif" font-size="7.5" font-weight="700" '
            f'fill="{C_VIAL}">Open {lot}</text>'
        )
    sd_pitch = abs(yx(mean + sd) - yx(mean)) if sd > 0 else ph / 7.0
    PILL_GAP = 3.0
    bw = 40
    bh = float(min(11.0, max(7.0, sd_pitch - PILL_GAP)))
    pill_rx = 1.8 if bh < 10 else 2.2
    lx = ML + pw + LEGEND_GAP
    for val, color, lab, dash in levels:
        y = yx(val)
        if dash:
            parts.append(
                f'<line x1="{ML}" y1="{y:.2f}" x2="{ML+pw}" y2="{y:.2f}" stroke="{color}" '
                f'stroke-width="1.15" stroke-dasharray="{dash}"/>'
            )
        else:
            parts.append(
                f'<line x1="{ML}" y1="{y:.2f}" x2="{ML+pw}" y2="{y:.2f}" stroke="{color}" stroke-width="1.5"/>'
            )
        parts.append(
            f'<text x="{ML-7}" y="{y+3:.1f}" text-anchor="end" font-family="Arial,Helvetica,sans-serif" '
            f'font-size="9.5" fill="#212121">{fmt_num(val, mean)}</text>'
        )
        parts.append(
            f'<rect x="{lx}" y="{y-bh/2:.2f}" width="{bw}" height="{bh:.2f}" '
            f'rx="{pill_rx}" ry="{pill_rx}" fill="{color}"/>'
        )
        parts.append(
            f'<text x="{lx+bw/2}" y="{y+2.8:.2f}" text-anchor="middle" '
            f'font-family="Arial,Helvetica,sans-serif" font-size="7.5" font-weight="700" fill="#fff">{lab}</text>'
        )
    if points:
        parts.append(f'<g clip-path="url(#{clip_id})">')
        coords = " ".join(f"{xx(d):.2f},{yx(v):.2f}" for d, v in points)
        parts.append(
            f'<polyline points="{coords}" fill="none" stroke="{C_LINE}" stroke-width="1.7" '
            f'stroke-linejoin="round" stroke-linecap="round"/>'
        )
        for d, v in points:
            if d in open_days:
                # Diamond marker on the open-day point
                cx, cy = xx(d), yx(v)
                r = 5.0
                parts.append(
                    f'<polygon points="{cx:.2f},{cy-r:.2f} {cx+r:.2f},{cy:.2f} '
                    f'{cx:.2f},{cy+r:.2f} {cx-r:.2f},{cy:.2f}" '
                    f'fill="{C_VIAL}" stroke="#E65100" stroke-width="0.9"/>'
                )
            else:
                parts.append(
                    f'<circle cx="{xx(d):.2f}" cy="{yx(v):.2f}" r="{PT_R}" fill="{C_PT}" '
                    f'stroke="{C_PT_EDGE}" stroke-width="0.9"/>'
                )
        parts.append("</g>")
    for t in x_tick_dates(x_start, x_end):
        x = xx(t)
        parts.append(
            f'<line x1="{x:.2f}" y1="{MT+ph}" x2="{x:.2f}" y2="{MT+ph+3.5}" stroke="#9E9E9E" stroke-width="1"/>'
        )
        parts.append(
            f'<text x="{x:.2f}" y="{H-3}" text-anchor="middle" font-family="Arial,Helvetica,sans-serif" '
            f'font-size="9.5" fill="#424242">{t.strftime("%d/%m")}</text>'
        )
    hx, hy = ML + pw - 13, MT + 5
    for i in range(3):
        parts.append(
            f'<line x1="{hx}" y1="{hy+i*3.3}" x2="{hx+10}" y2="{hy+i*3.3}" stroke="#9E9E9E" '
            f'stroke-width="1.25" stroke-linecap="round"/>'
        )
    parts.append("</svg>")
    title = (
        f"{level_name} - Mean: {fmt_num(mean, mean)} | SD: {fmt_num(sd, mean)} | "
        f"CV: {month_cv:.2f} | N: {n}"
    )
    if any(x_start <= od <= x_end for od, _ in vial_opens):
        title += " | ◆ = vial open"
    return f'<div class="chart-block"><div class="chart-title">{title}</div>{"".join(parts)}</div>'


CSS = """
@page { size: A4; margin: 10mm 11mm 10mm 11mm; }
* { box-sizing: border-box; }
html, body { margin:0; padding:0; font-family: Arial, Helvetica, sans-serif; color:#212121;
  -webkit-print-color-adjust:exact; print-color-adjust:exact; }
.page { width:188mm; height:277mm; page-break-after:always; position:relative; overflow:hidden; }
.page:last-child { page-break-after:auto; }
.topbar { position:relative; margin-bottom:4px; }
.header-title { text-align:center; font-size:15.5px; font-weight:700; margin:0; padding-top:2px; }
.logo { position:absolute; top:0; right:0; height:18px; width:auto; }
.meta-wrap { position:relative; margin-top:10px; }
.page-num { position:absolute; top:0; right:0; font-size:11px; line-height:1.45; }
.meta { font-size:10px; line-height:1.48; width:calc(100% - 48px); border-collapse:collapse; }
.meta td { vertical-align:top; padding:1px 0; }
.meta .lab { font-weight:700; width:150px; white-space:nowrap; padding-right:8px; }
.meta .val { font-weight:400; }
.charts { margin-top:18px; }
.chart-block { margin-bottom:16px; }
.chart-title { font-size:11px; font-weight:700; margin:0 0 4px 0; }
.chart-block svg { display:block; width:100%; height:auto; }
.footer { position:absolute; left:0; right:0; bottom:3mm; }
.signs { display:flex; justify-content:space-between; font-size:11px; margin-bottom:6mm; }
.copy { text-align:center; font-size:9.5px; color:#757575; }
"""


def page_html(page_idx, test_name, unit, rf, rt, lot_line, chart_html):
    return f"""
<section class="page">
  <div class="topbar">
    <img class="logo" src="data:image/png;base64,{LOGO_B64}" alt="QCDart"/>
    <h1 class="header-title">QCDart LJ Chart Report</h1>
  </div>
  <div class="meta-wrap">
    <div class="page-num">Page {page_idx}</div>
    <table class="meta">
      <tr><td class="lab">Data Range</td><td class="val">From: {rf} To: {rt}</td></tr>
      <tr><td class="lab">Oragnization/Lab name</td><td class="val">{ORG}</td></tr>
      <tr><td class="lab">Lab Address</td><td class="val">{ADDR}</td></tr>
      <tr><td class="lab">Contact</td><td class="val">{CONTACT}</td></tr>
      <tr><td class="lab">QC Lot Information</td><td class="val">{lot_line}</td></tr>
      <tr><td class="lab">Instrument Information</td><td class="val">{INSTRUMENT}</td></tr>
      <tr><td class="lab">Test Information</td><td class="val">{test_name} | {unit} | {METHOD}</td></tr>
    </table>
  </div>
  <div class="charts">{chart_html}</div>
  <div class="footer">
    <div class="signs">
      <div>Comments ____________________</div>
      <div>Reviewed by ____________________</div>
      <div>Sign &amp; Date ____________________</div>
    </div>
    <div class="copy">{COPYRIGHT}</div>
  </div>
</section>"""


def generate_month(year, month, universe, fixed=None):
    win = month_window(year, month)
    if not win:
        return None
    days, a0, a1 = win
    series, dominant, lots_by_point = collect_month_series(days, universe)
    lot_line = lot_line_for_days(days)
    rf, rt = a0.strftime("%d/%m/%Y"), a1.strftime("%d/%m/%Y")
    opens_by_level = {
        lv: vial_open_dates_for_level(lv) for lv in ("Low", "Normal", "High")
    }
    pages = []
    max_month_cv = 0.0
    for i, (param, tname, unit) in enumerate(TESTS, 1):
        blocks = []
        for lv in ("Low", "Normal", "High"):
            pts = series[lv].get(param, [])
            if not pts:
                continue
            dom = dominant.get(lv)
            point_lots = lots_by_point[lv].get(param, [])
            # Stats from dominant lot only; N = all plotted points that month
            stat_vals = [
                v
                for (d, v), lot in zip(pts, point_lots)
                if lot == dom
            ]
            if not stat_vals:
                stat_vals = [v for _, v in pts]
            mean = sum(stat_vals) / len(stat_vals)
            sd = sample_sd(stat_vals, mean)
            month_cv = cv_pct(stat_vals)
            max_month_cv = max(max_month_cv, month_cv)
            blocks.append(
                svg_chart(
                    pts,
                    mean,
                    sd,
                    LEVEL_LABEL[lv],
                    len(pts),
                    month_cv,
                    a0,
                    a1,
                    vial_opens=opens_by_level[lv],
                    height=116,
                )
            )
        if not blocks:
            continue
        pages.append(page_html(i, tname, unit, rf, rt, lot_line, "".join(blocks)))

    html = (
        "<!DOCTYPE html><html><head><meta charset='utf-8'/>"
        f"<style>{CSS}</style></head><body>{''.join(pages)}</body></html>"
    )
    label = f"{qc.MONTH_NAMES[month]} {year}"
    out_pdf = OUT / f"QCDart LJ Chart Report - {label}.pdf"
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
        out_pdf.write_bytes(tp.read_bytes())
    return out_pdf, len(pages), max_month_cv


def main():
    print("Generating Mindray BC-5380 QCDart LJ Chart Reports (monthly mean/SD/CV)")
    print("  building universe…")
    universe = build_universe()
    print(f"  runs={len(universe)}")
    # Keep lot stats file for reference; charts use monthly mean/SD.
    fixed = compute_lot_fixed(universe)
    print(f"  lot stats (reference only) → {FIXED_JSON.name} ({len(fixed)} series)")

    for p in OUT.glob("QCDart LJ Chart Report*.pdf"):
        p.unlink()

    results = []
    y, m = 2025, 7
    while date(y, m, 1) <= qc.END:
        info = generate_month(y, m, universe)
        if info:
            pdf, npages, max_cv = info
            print(f"  OK {pdf.name}: {npages} pages, maxMonthCV={max_cv:.2f}")
            results.append(pdf.name)
        m += 1
        if m > 12:
            m = 1
            y += 1

    print("\n=== VERIFY ===")
    bad = []
    for name in results:
        text = subprocess.check_output(["pdftotext", str(OUT / name), "-"], text=True)
        if "Mindray | BC-5380" not in text:
            bad.append(f"{name}: instrument")
        if "Steller Infomatica" not in text:
            bad.append(f"{name}: copyright")
        if "Service Engineer" in text or "Agappe" in text or "Maglumi" in text:
            bad.append(f"{name}: wrong branding")
        month_cvs = [
            float(x)
            for x in re.findall(r"Mean:.*?\| CV:\s*([\d.]+)\s*\|\s*N:", text)
        ]
        if month_cvs and max(month_cvs) > 5.05:
            bad.append(f"{name}: month CV={max(month_cvs)}")
    print("PASS" if not bad else "FAIL\n" + "\n".join(bad))
    print("LJ PDFs:", len(results))


if __name__ == "__main__":
    main()
