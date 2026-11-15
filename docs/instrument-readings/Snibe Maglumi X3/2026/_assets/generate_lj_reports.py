"""QCDart LJ Chart Reports for Snibe Maglumi X3, Bio-Rad lots 40471/40472.

Mean and SD are held for every month (first 20 calendar days of Oct 2025).
Only the plotted points, monthly CV, N and cumulative CV change.

    python3 "docs/instrument-readings/Snibe Maglumi X3/2026/_assets/generate_lj_reports.py"
"""
from __future__ import annotations

import base64
import calendar
import json
import re
import statistics
import subprocess
import tempfile
from collections import defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path

import fitz

ASSETS = Path(__file__).resolve().parent
OUT = ASSETS.parent
QCDART = ASSETS / "qdart_logo_tight.png"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
FIXED = json.loads((OUT / "fixed-mean-sd-oct2025-first20.json").read_text())

COPYRIGHT = "© Copyright 2025 Steller Infomatica. All rights reserved."
ORG = "Noble Diagnostic Centre / Noble Diagnostic Centre DELHI"
ADDR = "WZ 409 C HARI NAGAR NEW DELHI,India,Delhi,Delhi,110064"
CONTACT = "SHIPRA | M: 9511018366"
INSTRUMENT = "Snibe | Maglumi X3 | 0101010034012401360"
LOT_LINE = (
    "Bio-Rad | Lyphochek Immunoassay Plus Control | 40471 | 31/01/2028 | "
    "40472 | 31/01/2028 | 40473 | 31/01/2028"
)
METHOD = "CLIA - Chemiluminescence immunoassay"
HOLIDAYS = {
    date(2025, 10, 2),
    date(2025, 10, 20),
    date(2026, 1, 26),
    date(2026, 3, 4),
    date(2026, 8, 15),
}

# assay key, report name, unit, mean/sd display decimals
TESTS = [
    ("HCG/B-HCG", "B-hCG", "mIU/mL", 2, 2),
    ("FSH", "FSH", "mIU/mL", 2, 2),
    ("E2", "Estradiol, E2", "pg/mL", 2, 2),
    ("T3", "T3 Total", "ng/mL", 3, 3),
    ("PRL", "Prolactin", "ng/mL", 2, 2),
    ("TEST", "Testosterone", "ng/dL", 2, 2),
    ("T4", "T4 Total", "µg/dL", 2, 2),
    ("LH", "LH", "mIU/mL", 2, 2),
    ("TSH", "TSH", "µIU/mL", 3, 3),
]
LJ_MONTHS = [
    ("OCTOBER 2025", "OCTOBER 2025", "OCTOBER 2025", "Oct 25"),
    ("NOVEMBER 2025", "NOVEMBER 2025", "NOVEMBER 2025", "Nov 25"),
    ("DECEMBER 2025", "DECEMBER 2025", "DECEMBER 2025", "Dec 25"),
    ("JANUARY 2026", "JANUARY 2026", "JANUARY 2026", "Jan 26"),
    ("FEBRUARY 2026", "FEBRUARY 2026", "FEBRUARY 2026", "Feb 26"),
    ("MARCH 2026", "MARCH 2026", "MARCH 2026", "Mar 26"),
    ("APRIL 2026", "APRIL 2026", "APRIL 2026", "Apr 26"),
    ("MAY 2026", "MAY 2026", "MAY 2026", "May 26"),
    ("JUNE 2026", "JUNE 2026", "JUNE 2026", "Jun 26"),
    ("JULY 2026", "JULY 2026", "JULY 2026", "Jul 26"),
    ("AUGUST 2026", "AUG 2026", "AUG 2026", "Aug 26"),
    ("SEPTEMBER 2026", "SEPTEMBER 2026", "SEPTEMBER 2026", "Sep 26"),
]
C_RED, C_YEL, C_GRN, C_MEAN = "#E53935", "#FBC02D", "#66BB6A", "#212121"
C_LINE, C_PT, C_PT_EDGE = "#1E88E5", "#81C784", "#43A047"
QCDART_B64 = base64.b64encode(QCDART.read_bytes()).decode()
ASSAYS = [t[0] for t in TESTS]


def parse_level(pdf: Path) -> dict[date, dict[str, float]]:
    data: dict[date, dict[str, float]] = defaultdict(dict)
    for pg in fitz.open(pdf):
        t = pg.get_text()
        m = re.search(r"(20\d{2}-\d{2}-\d{2})", t)
        if not m:
            continue
        day = datetime.strptime(m.group(1), "%Y-%m-%d").date()
        for a in ASSAYS:
            mm = re.search(rf"{re.escape(a)}\n\d+\n[\d.]+\n([\d.]+)\s", t)
            if mm:
                data[day][a] = float(mm.group(1))
    return data


def x_tick_dates(start, end):
    n = (end - start).days
    if n <= 0:
        return [start]
    idxs = sorted(set(int(round(i * n / 5)) for i in range(6)))
    return [start + timedelta(days=i) for i in idxs]


def fmt_num(x, mean):
    return f"{x:.3f}" if abs(mean) < 1 else f"{x:.2f}"


def cv_pct(values):
    return statistics.stdev(values) / statistics.mean(values) * 100


def disp(x, nd):
    return f"{x:.{nd}f}"


def svg_chart(points, mean, sd, level_name, n, cv, x_start, x_end, mean_s, sd_s,
              month_cv, cum_cv, cum_n):
    W, H = 720, 132
    ML, MR, MT, MB = 50, 58, 6, 20
    span = max(sd, abs(mean) * 0.01, 1e-6)
    hi = max([3.5] + [(v - mean) / span + 0.4 for _, v in points])
    lo = max([3.5] + [(mean - v) / span + 0.4 for _, v in points])
    H = round(H + (H - MT - MB) * ((hi + lo) / 7 - 1))
    pw, ph = W - ML - MR, H - MT - MB
    y_min, y_max = mean - lo * span, mean + hi * span

    def yx(v):
        return MT + (y_max - v) / (y_max - y_min) * ph

    def xx(d):
        s = max((x_end - x_start).days, 1)
        return ML + ((d - x_start).days / s) * pw

    levels = [
        (mean + 3 * sd, C_RED, "+3SD", "2.2 2.2"),
        (mean + 2 * sd, C_YEL, "+2SD", "2.2 2.2"),
        (mean + 1 * sd, C_GRN, "+1SD", "2.2 2.2"),
        (mean, C_MEAN, "Mean", None),
        (mean - 1 * sd, C_GRN, "-1SD", "2.2 2.2"),
        (mean - 2 * sd, C_YEL, "-2SD", "2.2 2.2"),
        (mean - 3 * sd, C_RED, "-3SD", "2.2 2.2"),
    ]
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">']
    parts.append(
        f'<rect x="{ML}" y="{MT}" width="{pw}" height="{ph}" fill="#fff" stroke="#D6D6D6" stroke-width="1"/>'
    )
    for val, color, lab, dash in levels:
        y = yx(val)
        if dash:
            parts.append(
                f'<line x1="{ML}" y1="{y:.2f}" x2="{ML + pw}" y2="{y:.2f}" '
                f'stroke="{color}" stroke-width="1.15" stroke-dasharray="{dash}"/>'
            )
        else:
            parts.append(
                f'<line x1="{ML}" y1="{y:.2f}" x2="{ML + pw}" y2="{y:.2f}" '
                f'stroke="{color}" stroke-width="1.45"/>'
            )
        parts.append(
            f'<text x="{ML - 5}" y="{y + 3:.1f}" text-anchor="end" '
            f'font-family="Arial,Helvetica,sans-serif" font-size="9.5" fill="#616161">{fmt_num(val, mean)}</text>'
        )
        bw, bh = 38, 13
        parts.append(
            f'<rect x="{ML + pw + 5}" y="{y - bh / 2:.2f}" width="{bw}" height="{bh}" '
            f'rx="2.5" ry="2.5" fill="{color}"/>'
        )
        parts.append(
            f'<text x="{ML + pw + 5 + bw / 2}" y="{y + 3.5:.2f}" text-anchor="middle" '
            f'font-family="Arial,Helvetica,sans-serif" font-size="8" font-weight="700" fill="#fff">{lab}</text>'
        )
    if points:
        coords = " ".join(f"{xx(d):.2f},{yx(v):.2f}" for d, v in points)
        parts.append(
            f'<polyline points="{coords}" fill="none" stroke="{C_LINE}" stroke-width="1.7" '
            f'stroke-linejoin="round" stroke-linecap="round"/>'
        )
        for d, v in points:
            z = abs(v - mean) / sd if sd else 0
            fill, edge = (C_PT, C_PT_EDGE) if z <= 2 else ("#EF9A9A", "#C62828")
            parts.append(
                f'<circle cx="{xx(d):.2f}" cy="{yx(v):.2f}" r="3.3" fill="{fill}" '
                f'stroke="{edge}" stroke-width="0.85"/>'
            )
    for t in x_tick_dates(x_start, x_end):
        x = xx(t)
        parts.append(
            f'<line x1="{x:.2f}" y1="{MT + ph}" x2="{x:.2f}" y2="{MT + ph + 3.5}" '
            f'stroke="#9E9E9E" stroke-width="1"/>'
        )
        parts.append(
            f'<text x="{x:.2f}" y="{H - 3}" text-anchor="middle" '
            f'font-family="Arial,Helvetica,sans-serif" font-size="9.5" fill="#616161">{t.strftime("%d/%m")}</text>'
        )
    hx, hy = ML + pw - 13, MT + 5
    for i in range(3):
        parts.append(
            f'<line x1="{hx}" y1="{hy + i * 3.3}" x2="{hx + 10}" y2="{hy + i * 3.3}" '
            f'stroke="#9E9E9E" stroke-width="1.25" stroke-linecap="round"/>'
        )
    parts.append("</svg>")
    title = (
        f"{level_name} - Mean: {mean_s} | SD: {sd_s} | CV: {cv:.2f} | N: {n}"
        f" | Month CV: {month_cv:.2f}"
    )
    return f'<div class="chart-block"><div class="chart-title">{title}</div>{"".join(parts)}</div>'


CSS = """
@page { size: A4; margin: 10mm 11mm 10mm 11mm; }
* { box-sizing: border-box; }
html, body { margin:0; padding:0; font-family: Arial, Helvetica, sans-serif; color:#212121;
  -webkit-print-color-adjust:exact; print-color-adjust:exact; }
.page { width:188mm; height:277mm; page-break-after:always; position:relative; overflow:hidden; }
.page:last-child { page-break-after:auto; }
.topbar { position:relative; margin-bottom:2px; }
.header-title { text-align:center; font-size:15.5px; font-weight:700; margin:0; padding-top:2px; }
.logo { position:absolute; top:0; right:0; height:18px; width:auto; }
.meta-wrap { position:relative; margin-top:8px; }
.page-num { position:absolute; top:0; right:0; font-size:11px; line-height:1.45; }
.meta { font-size:10px; line-height:1.42; width:calc(100% - 48px); border-collapse:collapse; }
.meta td { vertical-align:top; padding:0; }
.meta .lab { font-weight:700; width:150px; white-space:nowrap; padding-right:8px; }
.meta .val { font-weight:400; }
.charts { margin-top:16px; }
.chart-block { margin-bottom:16px; }
.chart-title { font-size:11.5px; font-weight:700; margin:0 0 3px 0; }
.chart-block svg { display:block; width:100%; height:auto; }
.footer { position:absolute; left:0; right:0; bottom:4mm; }
.signs { display:flex; justify-content:space-between; font-size:11px; margin-bottom:8mm; }
.copy { text-align:center; font-size:9.5px; color:#757575; }
"""

SUMMARY_CSS = """
@page { size: A4 landscape; margin: 10mm 10mm 10mm 10mm; }
* { box-sizing: border-box; }
html, body { margin:0; padding:0; font-family: Arial, Helvetica, sans-serif; color:#212121;
  -webkit-print-color-adjust:exact; print-color-adjust:exact; }
.topbar { position:relative; margin-bottom:6px; }
.header-title { text-align:center; font-size:15.5px; font-weight:700; margin:0; padding-top:2px; }
.logo { position:absolute; top:0; right:0; height:18px; width:auto; }
.meta { font-size:10px; line-height:1.42; border-collapse:collapse; margin-bottom:8px; }
.meta td { padding:0; } .meta .lab { font-weight:700; width:170px; padding-right:8px; }
table.cv { width:100%; border-collapse:collapse; font-size:9.2px; }
table.cv th, table.cv td { border:1px solid #BDBDBD; padding:1.8px 3.5px; text-align:center; }
table.cv tr.nrow td { background:#FAFAFA; font-weight:700; }
table.cv th { background:#EEEEEE; font-weight:700; }
table.cv td.name { text-align:left; white-space:nowrap; }
table.cv tr.l2 td { border-bottom-color:#757575; }
.note { font-size:9px; color:#616161; margin-top:6px; }
.signs { display:flex; justify-content:space-between; font-size:11px; margin-top:8mm; }
.copy { text-align:center; font-size:9.5px; color:#757575; margin-top:4mm; }
"""


def page_html(page_idx, test_name, unit, rf, rt, svg1, svg2):
    return f"""
<section class="page">
  <div class="topbar">
    <img class="logo" src="data:image/png;base64,{QCDART_B64}" alt="QCDart"/>
    <h1 class="header-title">QCDart LJ Chart Report</h1>
  </div>
  <div class="meta-wrap">
    <div class="page-num">Page {page_idx}</div>
    <table class="meta">
      <tr><td class="lab">Data Range</td><td class="val">From: {rf} To: {rt}</td></tr>
      <tr><td class="lab">Oragnization/Lab name</td><td class="val">{ORG}</td></tr>
      <tr><td class="lab">Lab Address</td><td class="val">{ADDR}</td></tr>
      <tr><td class="lab">Contact</td><td class="val">{CONTACT}</td></tr>
      <tr><td class="lab">QC Lot Information</td><td class="val">{LOT_LINE}</td></tr>
      <tr><td class="lab">Instrument Information</td><td class="val">{INSTRUMENT}</td></tr>
      <tr><td class="lab">Test Information</td><td class="val">{test_name} | {unit} | {METHOD}</td></tr>
    </table>
  </div>
  <div class="charts">{svg1}{svg2}</div>
  <div class="footer">
    <div class="signs"><div>Comments ____________________</div><div>Reviewed by ____________________</div><div>Sign &amp; Date ____________________</div></div>
    <div class="copy">{COPYRIGHT}</div>
  </div>
</section>"""


def render_pdf(html, out_pdf):
    with tempfile.TemporaryDirectory() as tdir:
        hp = Path(tdir) / "r.html"
        hp.write_text(html, encoding="utf-8")
        tp = Path(tdir) / "o.pdf"
        r = subprocess.run(
            [CHROME, "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
             f"--print-to-pdf={tp}", f"file://{hp}"],
            capture_output=True, text=True,
        )
        if r.returncode or not tp.exists():
            raise RuntimeError(r.stderr[-400:] if r.stderr else "chrome")
        out_pdf.write_bytes(tp.read_bytes())
    print("OK", out_pdf.name)


def summary_html(title, note, rows, n_by_month, months, shorts, rf, rt, col_header):
    head = "".join(f"<th>{s}</th>" for s in shorts)
    n_row = (
        "<tr class='nrow'><td colspan='3'>N</td>"
        + "".join(f"<td>{n_by_month[m]}</td>" for m in months)
        + "</tr>"
    )
    body = []
    for assay, tname, unit, nd_m, nd_s in TESTS:
        for lv, lname, cls in (("L1", "Level 1", ""), ("L2", "Level 2", "l2")):
            mean = float(FIXED[lv][assay][0])
            sd = float(FIXED[lv][assay][1])
            fixed_cv = sd / mean * 100
            cells = "".join(f"<td>{rows[lv][assay][m]:.2f}</td>" for m in months)
            name = (
                f"<td class='name' rowspan='2'>{tname} "
                f"<span style='color:#757575'>({unit})</span></td>"
                if lv == "L1" else ""
            )
            body.append(
                f"<tr class='{cls}'>{name}<td>{lname}</td><td>{fixed_cv:.2f}</td>{cells}</tr>"
            )
    return f"""<!DOCTYPE html><html><head><meta charset='utf-8'/><style>{SUMMARY_CSS}</style></head><body>
<div class="topbar"><img class="logo" src="data:image/png;base64,{QCDART_B64}" alt="QCDart"/>
<h1 class="header-title">{title}</h1></div>
<table class="meta">
<tr><td class="lab">Data Range</td><td>From: {rf} To: {rt}</td></tr>
<tr><td class="lab">Oragnization/Lab name</td><td>{ORG}</td></tr>
<tr><td class="lab">QC Lot Information</td><td>{LOT_LINE}</td></tr>
<tr><td class="lab">Instrument Information</td><td>{INSTRUMENT} | {METHOD}</td></tr>
</table>
<table class="cv"><tr><th>Test</th><th>Level</th><th>{col_header}</th>{head}</tr>{n_row}{''.join(body)}</table>
<div class="note">{note}</div>
<div class="signs"><div>Comments ____________________</div><div>Reviewed by ____________________</div><div>Sign &amp; Date ____________________</div></div>
<div class="copy">{COPYRIGHT}</div>
</body></html>"""


def main() -> None:
    cum = {"L1": {a: [] for a in ASSAYS}, "L2": {a: [] for a in ASSAYS}}
    month_cv_rows = {"L1": {a: {} for a in ASSAYS}, "L2": {a: {} for a in ASSAYS}}
    month_n = {}
    labels, shorts = [], []
    lot_start = None
    rt = None

    for label, stem, out_stem, short in LJ_MONTHS:
        merged = {"L1": {}, "L2": {}}
        for lv, suf in (("L1", "L1"), ("L2", "L2")):
            parsed = parse_level(OUT / f"{stem} BIO RAD {suf}.pdf")
            for d, items in parsed.items():
                merged[lv].setdefault(d, {}).update(items)
        days = sorted(set(merged["L1"]) | set(merged["L2"]))
        x0, x1 = min(days), max(days)
        cal0 = date(x0.year, x0.month, 1)
        cal1 = date(x0.year, x0.month, calendar.monthrange(x0.year, x0.month)[1])
        a0, a1 = cal0, cal1
        lot_start = lot_start or a0
        rf, rt = a0.strftime("%d/%m/%Y"), a1.strftime("%d/%m/%Y")
        labels.append(label)
        shorts.append(short)
        pages = []
        ns = set()
        for i, (assay, tname, unit, nd_m, nd_s) in enumerate(TESTS, 1):
            svgs = []
            for lv, lname in (("L1", "Level 1"), ("L2", "Level 2")):
                mean = float(FIXED[lv][assay][0])
                sd = float(FIXED[lv][assay][1])
                mean_s, sd_s = disp(mean, nd_m), disp(sd, nd_s)
                pts = [
                    (d, merged[lv][d][assay])
                    for d in sorted(merged[lv])
                    if d not in HOLIDAYS and assay in merged[lv][d]
                ]
                month_vals = [v for _, v in pts]
                month_cv = cv_pct(month_vals)
                ns.add(len(pts))
                cum[lv][assay].extend(month_vals)
                cum_cv, cum_n = cv_pct(cum[lv][assay]), len(cum[lv][assay])
                month_cv_rows[lv][assay][label] = month_cv
                svgs.append(
                    svg_chart(
                        pts, mean, sd, lname, len(pts), sd / mean * 100,
                        a0, a1, mean_s, sd_s, month_cv, cum_cv, cum_n,
                    )
                )
            pages.append(page_html(i, tname, unit, rf, rt, svgs[0], svgs[1]))
        if len(ns) != 1:
            raise RuntimeError(f"{label} N mismatch {ns}")
        month_n[label] = next(iter(ns))
        html = (
            f"<!DOCTYPE html><html><head><meta charset='utf-8'/><style>{CSS}</style></head>"
            f"<body>{''.join(pages)}</body></html>"
        )
        render_pdf(html, OUT / f"QCDart LJ Chart Report - {out_stem}.pdf")

    rf0, rt0 = lot_start.strftime("%d/%m/%Y"), rt
    render_pdf(
        summary_html(
            "QCDart Monthly CV Report",
            "Monthly CV % = SD / mean × 100 of that month's QC results only (holidays excluded). "
            "LJ charts are plotted on the fixed mean and fixed SD from the first 20 days of October 2025. "
            "Fixed CV % = first-20-day SD / first-20-day mean × 100. Points beyond ±2 SD are shown in red.",
            month_cv_rows, month_n, labels, shorts, rf0, rt0, "Fixed CV %",
        ),
        OUT / "QCDart Monthly CV Report - Lot 40471-40472.pdf",
    )
    print("N by month", month_n)


if __name__ == "__main__":
    main()
