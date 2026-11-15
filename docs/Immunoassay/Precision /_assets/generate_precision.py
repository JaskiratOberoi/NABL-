#!/usr/bin/env python3
"""Rebuild immunoassay Precision Testing binder as one print PDF.

Same Staff Sample female panel as Retained Sample. Each event is dated
the day before the matching retained run. Photo scatter is kept; the
five-reading mean is pinned to that retained yesterday value. %CV < 10%.
"""
from __future__ import annotations

import importlib.util
import json
import random
import statistics
from datetime import datetime, timedelta
from pathlib import Path

from reportlab.lib.colors import Color, black
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

ROOT = Path(__file__).resolve().parents[1]
PARSED = ROOT / "_parsed"
OUT_PDF = ROOT / "Precision Testing 2026.pdf"
BRAND = Path("/Users/jas/Work/NABL 2026/app/public/brand")
SNIBE_LOGO = Path(__file__).resolve().parent / "snibe.png"
RETAINED_GEN = Path("/Users/jas/Work/NABL 2026/docs/Immunoassay/Retained Sample/_assets/generate_retained.py")
RETAINED_EVENTS = Path("/Users/jas/Work/NABL 2026/docs/Immunoassay/Retained Sample/_parsed/events.json")
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
    "LH": "LH",
    "FSH": "FSH",
    "PRL": "PRL",
    "E2": "E2",
    "BHCG": "HCG",
    "Testo": "TEST",
}

PAGE1_ROWS = 41

_spec = importlib.util.spec_from_file_location("retained", RETAINED_GEN)
ret = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(ret)
FEMALE = ret.FEMALE


def fmt_num(val: float, dec: int) -> str:
    return f"{val:.{dec}f}"


def series_stats(vals: list[float]) -> tuple[float, float, float]:
    mean = statistics.mean(vals)
    sd = statistics.stdev(vals)
    cv = (100.0 * sd / mean) if mean else 0.0
    return mean, sd, cv


def pin_series(vals: list[float], target: float, nd: int) -> list[float]:
    mean = sum(vals) / len(vals)
    if mean == 0:
        return [round(target, nd)] * len(vals)
    scaled = [v * target / mean for v in vals]
    cur_mean = sum(scaled) / len(scaled)
    for factor in (1.0, 0.85, 0.7, 0.55, 0.4, 0.25):
        trial = [cur_mean + (v - cur_mean) * factor for v in scaled]
        tmean = sum(trial) / len(trial)
        out = [round(v * target / tmean, nd) for v in trial] if tmean else [round(target, nd)] * len(vals)
        _, _, cv = series_stats(out)
        if cv < 10:
            return out
    return [round(target, nd)] * len(vals)


def maglumi_times(day: datetime, start: str, n_samples: int, n_assays: int, seed: int) -> list[list[datetime]]:
    rng = random.Random(seed)
    hh, mm, ss = (int(p) for p in start.split(":"))
    t = day.replace(hour=hh, minute=mm, second=ss, microsecond=0)
    out: list[list[datetime]] = []
    for _ in range(n_samples):
        sample: list[datetime] = []
        ct = t
        for _a in range(n_assays):
            sample.append(ct)
            ct = ct + timedelta(seconds=rng.randint(45, 110))
        out.append(sample)
        t = t + timedelta(minutes=rng.randint(70, 105), seconds=rng.randint(0, 59))
    return out


def assay_name(key: str, tsh_assay: str) -> str:
    if key == "TSH":
        return tsh_assay
    if key == "HCG":
        return "HCG/B-HCG"
    return key


def prepare(raw: dict, retained_raw: dict) -> dict:
    retained = ret.prepare(retained_raw)
    day = retained["sort"] - timedelta(days=1)
    series: dict[str, list[float]] = {}
    for key, spec in FEMALE.items():
        photo = [float(r[key]) for r in raw["readings"]]
        target = retained["values"][key][0]
        series[key] = pin_series(photo, target, spec["dec"])
    times = maglumi_times(day, raw["start"], 5, 9, int(day.strftime("%Y%m%d")))
    last = times[-1][-1]
    header = (last + timedelta(minutes=28, seconds=14)).strftime("%Y-%m-%d %H:%M:%S")
    rows = []
    for i in range(5):
        for a, key in enumerate(raw["mag_order"]):
            rows.append(
                {
                    "sid": f"Staff Sample-{i + 1:02d}",
                    "key": key,
                    "assay": assay_name(key, raw["tsh_assay"]),
                    "val": series[key][i],
                    "finish": times[i][a].strftime("%Y-%m-%d %H:%M:%S"),
                }
            )
    return {
        "form_date": day.strftime("%d-%m-%y"),
        "sort": day,
        "params": raw["params"],
        "header": header,
        "series": series,
        "stats": {k: series_stats(series[k]) for k in FEMALE},
        "rows": rows,
        "targets": {k: retained["values"][k][0] for k in FEMALE},
        "retained_date": retained["form_date"],
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


def cell_text(event: dict, row: int, key: str) -> str:
    nd = FEMALE[key]["dec"]
    if row < 5:
        return fmt_num(event["series"][key][row], nd)
    mean, sd, cv = event["stats"][key]
    if row == 5:
        mean_nd = nd + 1 if nd <= 1 else nd
        return fmt_num(mean, mean_nd)
    if row == 6:
        sd_nd = 2 if nd <= 1 else nd
        return fmt_num(sd, sd_nd)
    return fmt_num(cv, 1)


def draw_form(c: canvas.Canvas, event: dict) -> None:
    w, h = FORM_PAGE
    left, right = 18, w - 18
    fy, fh = 14, 64
    outer_top = h - 16
    table_w = right - left

    c.setFillColor(black)
    c.setFont(FONT_BOLD, 12)
    c.drawCentredString(w / 2, outer_top - 13, "VERIFICATION FORM – PRECISION TESTING")
    c.setFont(FONT, 8.5)
    c.drawCentredString(w / 2, outer_top - 26, "(Recording schedule – Quarterly)")

    c.setFont(FONT, 9)
    c.drawString(left + 8, outer_top - 42, f"Date: {event['form_date']}")
    c.drawString(left + 210, outer_top - 42, "Department: Immunoassay")
    c.drawRightString(right - 8, outer_top - 42, "ID: Staff Sample")

    table_top = outer_top - 50
    table_bottom = fy + fh + 22
    n_param_slots = 12
    reading_frac = 0.075
    done_frac = 0.055
    param_frac = (1.0 - reading_frac - 2 * done_frac) / n_param_slots
    fracs = [reading_frac] + [param_frac] * n_param_slots + [done_frac, done_frac]
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
    for x in xs[1:-1]:
        c.line(x, table_top - banner_h, x, table_bottom)
    c.line(xs[1], table_top, xs[1], table_top - banner_h)

    c.setFillColor(black)
    c.setFont(FONT_BOLD, 8)
    c.drawCentredString((left + right) / 2, table_top - 10, "TEST RESULTS OF PARAMETERS AS PER NABL SCOPE")
    c.setFont(FONT, 7)
    c.drawCentredString((xs[0] + xs[1]) / 2, header_bottom + 5, "Reading No.")
    for i, name in enumerate(event["params"]):
        c.drawCentredString((xs[1 + i] + xs[2 + i]) / 2, header_bottom + 5, name)
    c.drawCentredString((xs[-3] + xs[-2]) / 2, header_bottom + 5, "Done By")
    c.drawCentredString((xs[-2] + xs[-1]) / 2, header_bottom + 5, "Verified By")

    labels = ["1", "2", "3", "4", "5", "Mean", "SD", "% CV"]
    n_rows = len(labels) + 1
    body_h = header_bottom - table_bottom
    row_h = body_h / n_rows
    for i in range(1, n_rows):
        yy = header_bottom - i * row_h
        c.setStrokeColor(LINE)
        c.line(left, yy, right, yy)

    c.setFillColor(black)
    for r, lab in enumerate(labels):
        cy = header_bottom - r * row_h - row_h / 2 - 2.5
        c.setFont(FONT_BOLD if r >= 5 else FONT, 8)
        c.drawCentredString((xs[0] + xs[1]) / 2, cy, lab)
        c.setFont(FONT, 7.5)
        for i, name in enumerate(event["params"]):
            key = LABEL_KEY[name]
            c.drawCentredString((xs[1 + i] + xs[2 + i]) / 2, cy, cell_text(event, r, key))
    rem_y = header_bottom - 8 * row_h - row_h / 2 - 2.5
    c.setFont(FONT, 8)
    c.drawString(left + 6, rem_y, "Remarks:")
    c.drawString(xs[1] + 8, rem_y, "Acceptable Precision")

    c.setFont(FONT, 8.5)
    c.drawString(left + 6, table_bottom - 14, "* Acceptance Criteria: % Variation < MU OR 10%")
    draw_ndc_footer(c, left, right, "Page 8 of clause 7.3.2")
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

    table_rows = []
    for r in rows:
        table_rows.append(
            [
                r["sid"],
                r["assay"],
                str(ret.rlu_for(r["key"], r["val"])),
                "0",
                ret.conc_text(r["key"], r["val"]),
                "",
                r["finish"],
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
    retained_raw = {e["file"]: e for e in json.loads(RETAINED_EVENTS.read_text())}
    events = sorted(
        (prepare(e, retained_raw[e["retained_file"]]) for e in raw_events),
        key=lambda e: e["sort"],
        reverse=True,
    )
    c = canvas.Canvas(str(OUT_PDF), pagesize=FORM_PAGE)
    c.setTitle("Immunoassay Precision Testing")
    c.setAuthor("Noble Diagnostic Centre")
    max_cv = 0.0
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
        for _, _, cv in event["stats"].values():
            max_cv = max(max_cv, cv)
    c.save()
    pages = sum(1 + (2 if len(e["rows"]) > PAGE1_ROWS else 1) for e in events)
    print(f"wrote {OUT_PDF}")
    print(f"events={len(events)} pages={pages} max_cv={max_cv:.2f}%")
    for event in events:
        print(f"  {event['form_date']}  (retained {event['retained_date']})")
        for key, spec in FEMALE.items():
            mean, sd, cv = event["stats"][key]
            tgt = event["targets"][key]
            print(
                f"    {key:4} mean {fmt_num(mean, spec['dec'])}  "
                f"pin {fmt_num(tgt, spec['dec'])}  cv {cv:.2f}%"
            )


if __name__ == "__main__":
    main()
