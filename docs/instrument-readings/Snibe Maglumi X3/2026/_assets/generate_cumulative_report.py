"""QCDart cumulative Mean / SD / CV for Snibe Maglumi X3, Bio-Rad lots 40471/40472.

Fixed mean = first 20 calendar days of October 2025 (the value on every LJ).
Fixed SD  = sample SD of those same 20 points (never applied to the LJ charts).
Cumulative stats exclude the holidays listed in fixed-means-oct2025-first20.json.
"""
from __future__ import annotations

import base64
import json
import re
import statistics
import subprocess
import tempfile
from collections import defaultdict
from datetime import date, datetime
from pathlib import Path

import fitz

ASSETS = Path(__file__).resolve().parent
OUT = ASSETS.parent
QCDART = ASSETS / "qdart_logo_tight.png"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
FIXED_JSON = json.loads((OUT / "fixed-mean-sd-oct2025-first20.json").read_text())

ORG = "Noble Diagnostic Centre / Noble Diagnostic Centre DELHI"
ADDR = "WZ 409 C HARI NAGAR NEW DELHI,India,Delhi,Delhi,110064"
INSTRUMENT = "Snibe | Maglumi X3 | 0101010034012401360"
LOT_LINE = "Bio-Rad | Lyphochek Immunoassay Plus Control | 40471 | 31/01/2028 | 40472 | 31/01/2028"
METHOD = "CLIA - Chemiluminescence immunoassay"
COPYRIGHT = "© Copyright 2025 Steller Infomatica. All rights reserved."
HOLIDAYS = {date(2025, 10, 2), date(2025, 10, 20), date(2026, 1, 26), date(2026, 3, 4), date(2026, 8, 15)}

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
MONTHS = [
    ("OCTOBER 2025", "OCTOBER 2025", "Oct 25"),
    ("NOVEMBER 2025", "NOVEMBER 2025", "Nov 25"),
    ("DECEMBER 2025", "DECEMBER 2025", "Dec 25"),
    ("JANUARY 2026", "JANUARY 2026", "Jan 26"),
    ("FEBRUARY 2026", "FEBRUARY 2026", "Feb 26"),
    ("MARCH 2026", "MARCH 2026", "Mar 26"),
    ("APRIL 2026", "APRIL 2026", "Apr 26"),
    ("MAY 2026", "MAY 2026", "May 26"),
    ("JUNE 2026", "JUNE 2026", "Jun 26"),
    ("JULY 2026", "JULY 2026", "Jul 26"),
    ("AUGUST 2026", "AUG 2026", "Aug 26"),
    ("SEPTEMBER 2026", "SEPTEMBER 2026", "Sep 26"),
]
ASSAYS = [t[0] for t in TESTS]
QCDART_B64 = base64.b64encode(QCDART.read_bytes()).decode()


def parse_level(pdf: Path) -> dict[date, dict[str, float]]:
    data: dict[date, dict[str, float]] = defaultdict(dict)
    doc = fitz.open(pdf)
    for pg in doc:
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


def fmt(x: float, nd: int) -> str:
    return f"{x:.{nd}f}"


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


def page_shell(title: str, rf: str, rt: str, table: str, note: str) -> str:
    return f"""
<section class="page">
<div class="topbar"><img class="logo" src="data:image/png;base64,{QCDART_B64}" alt="QCDart"/>
<h1 class="header-title">{title}</h1></div>
<table class="meta">
<tr><td class="lab">Data Range</td><td>From: {rf} To: {rt}</td></tr>
<tr><td class="lab">Oragnization/Lab name</td><td>{ORG}</td></tr>
<tr><td class="lab">Lab Address</td><td>{ADDR}</td></tr>
<tr><td class="lab">QC Lot Information</td><td>{LOT_LINE}</td></tr>
<tr><td class="lab">Instrument Information</td><td>{INSTRUMENT} | {METHOD}</td></tr>
</table>
{table}
<div class="note">{note}</div>
<div class="signs"><div>Comments ____________________</div><div>Reviewed by ____________________</div><div>Sign &amp; Date ____________________</div></div>
<div class="copy">{COPYRIGHT}</div>
</section>"""


def n_row(n_by_month: dict, shorts: list[str], labels: list[str]) -> str:
    return ("<tr class='nrow'><td colspan='3'>Cumulative N</td>"
            + "".join(f"<td>{n_by_month[m]}</td>" for m in labels) + "</tr>")


def render_pdf(html: str, out_pdf: Path) -> None:
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


def main() -> None:
    series = {"L1": defaultdict(list), "L2": defaultdict(list)}
    for _label, stem, _short in MONTHS:
        for lv, suffix in (("L1", "L1"), ("L2", "L2")):
            parsed = parse_level(OUT / f"{stem} BIO RAD {suffix}.pdf")
            for day in sorted(parsed):
                if day in HOLIDAYS:
                    continue
                for a in ASSAYS:
                    if a in parsed[day]:
                        series[lv][a].append((day, parsed[day][a]))

    labels = [m[0] for m in MONTHS]
    shorts = [m[2] for m in MONTHS]
    month_end = {
        "OCTOBER 2025": date(2025, 10, 31),
        "NOVEMBER 2025": date(2025, 11, 30),
        "DECEMBER 2025": date(2025, 12, 31),
        "JANUARY 2026": date(2026, 1, 31),
        "FEBRUARY 2026": date(2026, 2, 28),
        "MARCH 2026": date(2026, 3, 31),
        "APRIL 2026": date(2026, 4, 30),
        "MAY 2026": date(2026, 5, 31),
        "JUNE 2026": date(2026, 6, 30),
        "JULY 2026": date(2026, 7, 31),
        "AUGUST 2026": date(2026, 8, 31),
        "SEPTEMBER 2026": date(2026, 9, 30),
    }

    cum = {"L1": {a: {} for a in ASSAYS}, "L2": {a: {} for a in ASSAYS}}
    n_by_month = {}
    for label in labels:
        end = month_end[label]
        ns = set()
        for lv in ("L1", "L2"):
            for a in ASSAYS:
                vals = [v for d, v in series[lv][a] if d <= end]
                ns.add(len(vals))
                mean = statistics.mean(vals)
                sd = statistics.stdev(vals)
                cv = sd / mean * 100
                cum[lv][a][label] = (mean, sd, cv, len(vals))
        if len(ns) != 1:
            raise RuntimeError(f"{label} N mismatch {ns}")
        n_by_month[label] = next(iter(ns))

    rf, rt = "01/10/2025", "30/09/2026"
    head = "".join(f"<th>{s}</th>" for s in shorts)

    def body(kind: str) -> str:
        rows = []
        for assay, tname, unit, nd_m, nd_s in TESTS:
            for lv, lname, cls in (("L1", "Level 1", ""), ("L2", "Level 2", "l2")):
                mean_s, sd_s = FIXED_JSON[lv][assay]
                fm, fs = float(mean_s), float(sd_s)
                if kind == "mean":
                    fixed = fmt(fm, nd_m)
                    cells = "".join(f"<td>{fmt(cum[lv][assay][m][0], nd_m)}</td>" for m in labels)
                elif kind == "sd":
                    fixed = fmt(fs, nd_s)
                    cells = "".join(f"<td>{fmt(cum[lv][assay][m][1], nd_s)}</td>" for m in labels)
                else:
                    fixed = f"{fs / fm * 100:.2f}"
                    cells = "".join(f"<td>{cum[lv][assay][m][2]:.2f}</td>" for m in labels)
                name = (f"<td class='name' rowspan='2'>{tname} "
                        f"<span style='color:#757575'>({unit})</span></td>") if lv == "L1" else ""
                rows.append(f"<tr class='{cls}'>{name}<td>{lname}</td><td>{fixed}</td>{cells}</tr>")
        fixed_h = {"mean": "Fixed mean", "sd": "Fixed SD", "cv": "Fixed CV %"}[kind]
        return (f"<table class='cv'><tr><th>Test</th><th>Level</th><th>{fixed_h}</th>{head}</tr>"
                f"{n_row(n_by_month, shorts, labels)}{''.join(rows)}</table>")

    notes = {
        "mean": ("Cumulative mean = arithmetic mean of all QC results from 01/10/2025 to the end of each month, "
                 "holidays excluded. Fixed mean is from the first 20 calendar days of October 2025 and is the "
                 "mean plotted on every LJ chart."),
        "sd": ("Cumulative SD = sample SD of all QC results from 01/10/2025 to the end of each month, "
               "holidays excluded. Fixed SD is the sample SD of those same first 20 days. The LJ charts do "
               "not use this fixed SD; each month's chart uses that month's own SD."),
        "cv": ("Cumulative CV % = cumulative SD / cumulative mean × 100. Fixed CV % = first-20-day SD / "
               "first-20-day mean × 100. LJ chart CV is monthly SD / fixed mean, not this cumulative CV."),
    }
    titles = {
        "mean": "QCDart Cumulative Mean Report",
        "sd": "QCDart Cumulative SD Report",
        "cv": "QCDart Cumulative CV Report",
    }
    CSS = SUMMARY_CSS + ".page { page-break-after:always; } .page:last-child { page-break-after:auto; }"
    pages = [page_shell(titles[k], rf, rt, body(k), notes[k]) for k in ("mean", "sd", "cv")]
    html = (f"<!DOCTYPE html><html><head><meta charset='utf-8'/><style>{CSS}</style></head>"
            f"<body>{''.join(pages)}</body></html>")
    render_pdf(html, OUT / "QCDart Cumulative Mean SD CV Report - Lot 40471-40472.pdf")
    print("N by month", n_by_month)


if __name__ == "__main__":
    main()
