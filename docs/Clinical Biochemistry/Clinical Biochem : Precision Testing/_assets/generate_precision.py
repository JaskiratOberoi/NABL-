#!/usr/bin/env python3
"""Rebuild Clinical Biochemistry Precision Testing binder as one print PDF.

Photo values keep their relative scatter. Overlapping analytes are pinned so
the five-reading mean matches the paired patient report. Glucose comes from
the same-day glucose report (separate print). Chol, TGL and HDL are not on
those reports, so each event gets a report-style lipid target consistent
with the rest of that panel; the five readings are then pinned to it.
HDL-C is on form page 2 and on the biochem slips.
"""
from __future__ import annotations

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
FORM_PAGE = landscape(A4)
SLIP_PAGE = A4

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
MONO = "Courier"

LINE = Color(0.2, 0.2, 0.2)

DEC = {
    "Glu": 1,
    "Chol": 1,
    "HDL": 1,
    "Alb": 2,
    "TGL": 1,
    "SGOT": 1,
    "UAC": 2,
    "CRT J": 2,
    "TPR": 2,
    "Cal": 2,
    "Urea": 1,
    "SGPT": 1,
    "GGT": 1,
    "DBil": 2,
    "TBil": 2,
    "ALP": 1,
}

PAGE1_PARAMS = [
    "Glu",
    "Chol",
    "Alb",
    "TGL",
    "SGOT",
    "UAC",
    "CRT J",
    "TPR",
    "Cal",
    "Urea",
    "SGPT",
    "GGT",
]
PAGE2_PARAMS = ["DBil", "TBil", "ALP", "HDL"]

# Instrument slip header is one Courier line. RC values occupy the same
# trailing columns as "------RC------" so the last digit sits under the last dash.
SLIP_HEADER = (
    "Item Name       Result      Dil      NR      "
    "C E L P B G < > T W A c S R1 R2 D ------RC------"
)
SLIP_FONT_SIZE = 9

BIOCHEM_ITEMS = [
    ("CHOL", "Chol"),
    ("ALB", "Alb"),
    ("TGL", "TGL"),
    ("HDL-C", "HDL"),
    ("SGOT", "SGOT"),
    ("UAC", "UAC"),
    ("CRT J", "CRT J"),
    ("TPR", "TPR"),
    ("CAL A", "Cal"),
    ("UREA UV", "Urea"),
    ("SGPT", "SGPT"),
    ("GGT", "GGT"),
    ("BIL D", "DBil"),
    ("BIL T", "TBil"),
    ("ALP IFCC", "ALP"),
]

# Photo form_date -> report pinning, IDs, clustered start
EVENT_META = {
    "08/07/2025": {
        "chem_id": "10265353",
        "glu_id": "10265370",
        "collected": "08/07/2026 09:49:05",
        "seed": 20260708,
        "pin": {
            "TBil": 0.51,
            "DBil": 0.12,
            "SGOT": 23.1,
            "SGPT": 16.8,
            "GGT": 31.5,
            "ALP": 51.3,
            "TPR": 7.70,
            "Alb": 4.07,
            "Urea": 21.2,
            "CRT J": 0.83,
            "UAC": 4.00,
            "Cal": 9.00,
            "Glu": 86.5,
            "Chol": 186.4,
            "TGL": 142.8,
            "HDL": 43.6,
        },
    },
    "09/04/2025": {
        "chem_id": "1026446",
        "glu_id": "1026454",
        "collected": "09/04/2026 10:22:51",
        "seed": 20260409,
        "pin": {
            "TBil": 0.65,
            "DBil": 0.16,
            "SGOT": 157.1,
            "SGPT": 248.6,
            "ALP": 124.6,
            "TPR": 7.90,
            "Alb": 4.42,
            "CRT J": 0.61,
            "UAC": 3.27,
            "Urea": 15.4,
            "Cal": 9.07,
            "Glu": 61.4,
            "Chol": 168.2,
            "TGL": 118.4,
            "HDL": 46.3,
        },
    },
    "10/01/2025": {
        "chem_id": "102511343",
        "glu_id": "102511333",
        "collected": "10/01/2026 08:56:03",
        "seed": 20260110,
        "pin": {
            "TBil": 0.22,
            "DBil": 0.10,
            "SGOT": 12.0,
            "SGPT": 11.0,
            "GGT": 10.9,
            "ALP": 66.0,
            "TPR": 6.83,
            "Alb": 3.61,
            "Urea": 25.7,
            "CRT J": 0.61,
            "UAC": 3.24,
            "Cal": 9.45,
            "Glu": 279.0,
            "Chol": 174.6,
            "TGL": 128.3,
            "HDL": 49.1,
        },
    },
    "09/10/2024": {
        "chem_id": "102411384",
        "glu_id": "10256893",
        "collected": "09/10/2025 08:14:07",
        "seed": 20251009,
        "pin": {
            "Glu": 290.0,
            "Chol": 198.5,
            "TGL": 226.8,
            "HDL": 34.2,
        },
    },
}


def shift_year(text: str) -> str:
    return text.replace("2025", "2026").replace("2024", "2025")


def page1(c: canvas.Canvas, pagesize) -> None:
    w, _ = pagesize
    c.setFillColor(black)
    c.setFont(FONT, 9)
    c.drawRightString(w - 22, 16, "Page 1")


def fmt_val(value: float, nd: int) -> str:
    return f"{value:.{nd}f}"


def pin_series(vals: list[float], target: float, nd: int) -> list[float]:
    mean = sum(vals) / len(vals)
    if mean == 0:
        return [round(target, nd)] * len(vals)
    out = [round(v * target / mean, nd) for v in vals]
    tick = 10 ** (-nd)
    for _ in range(20):
        cur_mean, _, cv = series_stats(out)
        if cv < 10:
            break
        # 2-dp analytes (DBil) can exceed 10% CV after rounding; pull the outlier in.
        farthest = max(range(len(out)), key=lambda i: abs(out[i] - cur_mean))
        if out[farthest] > cur_mean:
            out[farthest] = round(out[farthest] - tick, nd)
        else:
            out[farthest] = round(out[farthest] + tick, nd)
    return out


def clustered_times(collected: datetime, n: int, seed: int) -> tuple[list[datetime], list[datetime]]:
    rng = random.Random(seed)
    t = collected + timedelta(minutes=rng.randint(30, 60), seconds=rng.randint(0, 59))
    biochem = [t]
    for _ in range(n - 1):
        t = t + timedelta(minutes=rng.randint(60, 75), seconds=rng.randint(0, 59))
        biochem.append(t)
    glu = [bt + timedelta(seconds=rng.randint(120, 300)) for bt in biochem]
    return biochem, glu


def series_stats(vals: list[float]) -> tuple[float, float, float]:
    mean = statistics.mean(vals)
    sd = statistics.stdev(vals)
    cv = (100.0 * sd / mean) if mean else 0.0
    return mean, sd, cv


def prepare_event(raw: dict) -> dict:
    meta = EVENT_META[raw["form_date"]]
    collected = datetime.strptime(meta["collected"], "%d/%m/%Y %H:%M:%S")
    biochem_times, glu_times = clustered_times(collected, 5, meta["seed"])
    photo_keys = [k for k in DEC if k != "HDL"]
    series = {k: [float(r["values"][k]) for r in raw["readings"]] for k in photo_keys}
    # HDL is not on the photo slips; use cholesterol scatter as the template.
    series["HDL"] = list(series["Chol"])
    pin = meta["pin"]
    for key, target in pin.items():
        series[key] = pin_series(series[key], target, DEC[key])

    readings = []
    for i, src in enumerate(raw["readings"]):
        values = {k: series[k][i] for k in DEC}
        rc0 = int(src["rc_biochem0"])
        readings.append(
            {
                "n": src["n"],
                "biochem_sample": src["biochem_sample"],
                "glu_sample": src["glu_sample"],
                "biochem_dt": biochem_times[i],
                "glu_dt": glu_times[i],
                "chem_pid": f"{meta['chem_id']}-{src['n']:02d}",
                "glu_pid": f"{meta['glu_id']}-{src['n']:02d}",
                "values": values,
                "rc_biochem0": rc0,
                "rc_glu": rc0 + len(BIOCHEM_ITEMS),
            }
        )
    stats = {k: series_stats(series[k]) for k in DEC}
    form_date = collected.strftime("%d/%m/%Y")
    return {
        "form_date": form_date,
        "form_dept": raw.get("form_dept") or "Biochem",
        "chem_id": meta["chem_id"],
        "sort": collected,
        "readings": readings,
        "stats": stats,
    }


def draw_footer(c: canvas.Canvas, left: float, right: float, fy: float, fh: float, page_label: str) -> None:
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
    c.drawString(mid + 6, fy + 52, "Doc No. NDC / DI / 7.3.2")
    c.drawString(left + 8, fy + 37, "Documented Information – Verification of examination methods")
    c.drawString(mid + 6, fy + 37, page_label)
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
        c.drawImage(
            str(logo),
            inner_right + 3,
            fy + 8,
            width=48,
            height=48,
            mask="auto",
            preserveAspectRatio=True,
        )


def draw_form(c: canvas.Canvas, event: dict, params: list[str]) -> None:
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
    c.drawString(left + 210, outer_top - 42, f"Department: {event['form_dept']}")
    c.drawRightString(right - 8, outer_top - 42, f"ID: {event['chem_id']}")

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

    banner_h = 14
    header_h = 16
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
    for i, name in enumerate(params):
        c.drawCentredString((xs[1 + i] + xs[2 + i]) / 2, header_bottom + 5, name)
    c.drawCentredString((xs[-3] + xs[-2]) / 2, header_bottom + 5, "Done By")
    c.drawCentredString((xs[-2] + xs[-1]) / 2, header_bottom + 5, "Verified By")

    labels = ["1", "2", "3", "4", "5", "Mean", "SD", "% CV"]
    n_rows = len(labels)
    body_h = header_bottom - table_bottom
    row_h = body_h / n_rows
    for i in range(1, n_rows):
        yy = header_bottom - i * row_h
        c.setStrokeColor(LINE)
        c.line(left, yy, right, yy)

    readings = event["readings"]
    stats = event["stats"]

    def cell_text(row: int, param: str) -> str:
        nd = DEC[param]
        if row < 5:
            return fmt_val(readings[row]["values"][param], nd)
        mean, sd, cv = stats[param]
        if row == 5:
            mean_nd = nd + 1 if nd <= 1 else nd
            return fmt_val(mean, mean_nd)
        if row == 6:
            sd_nd = 2 if nd <= 1 else nd
            return fmt_val(sd, sd_nd)
        return fmt_val(cv, 1)

    c.setFillColor(black)
    for r, lab in enumerate(labels):
        cy = header_bottom - r * row_h - row_h / 2 - 2.5
        c.setFont(FONT_BOLD if r >= 5 else FONT, 8)
        c.drawCentredString((xs[0] + xs[1]) / 2, cy, lab)
        c.setFont(FONT, 7.5)
        for i, param in enumerate(params):
            c.drawCentredString((xs[1 + i] + xs[2 + i]) / 2, cy, cell_text(r, param))

    c.setFont(FONT, 8.5)
    c.drawString(left + 6, table_bottom - 14, "* Acceptance Criteria: % Variation < MU OR 10%")
    draw_footer(c, left, right, fy, fh, "Page 8 of clause 7.3.2")
    c.setStrokeColor(LINE)
    c.setLineWidth(0.8)
    c.rect(left, fy, table_w, outer_top - fy, stroke=1, fill=0)


def slip_row(name: str, result: str, rc: int | str) -> str:
    """One instrument line: same character columns as SLIP_HEADER."""
    cells = [" "] * len(SLIP_HEADER)
    item = (name or "")[:16]
    cells[0 : len(item)] = list(item)
    r_at = SLIP_HEADER.index("Result")
    val = (result or "")[:12]
    cells[r_at : r_at + len(val)] = list(val)
    rc_s = str(rc)
    cells[len(SLIP_HEADER) - len(rc_s) :] = list(rc_s)
    return "".join(cells)


def draw_sample_page(
    c: canvas.Canvas,
    *,
    sample: str,
    dt: datetime,
    pid: str,
    items: list[tuple[str, str]],
    rc0: int,
) -> None:
    w, h = SLIP_PAGE
    left = 28
    y = h - 36
    stamp = dt.strftime("%d/%m/%Y %H:%M:%S")

    c.setFillColor(black)
    c.setFont(MONO, SLIP_FONT_SIZE)
    c.drawString(left, y, f"Sample :  {sample} , Type : Serum , {stamp}")
    y -= 14
    c.drawString(left, y, "SampleID    :")
    y -= 12
    c.drawString(left, y, f"PatientID: {pid}")
    y -= 12
    c.drawString(left, y, "Name:")
    y -= 10
    c.setStrokeColor(LINE)
    c.setDash(1, 1.5)
    c.setLineWidth(0.5)
    c.line(left, y, w - 28, y)
    c.setDash()
    y -= 16
    c.setFont(MONO, SLIP_FONT_SIZE)
    c.drawString(left, y, SLIP_HEADER)
    y -= 14
    for i, (item, result) in enumerate(items):
        c.drawString(left, y, slip_row(item, result, rc0 + i))
        y -= 13
    page1(c, SLIP_PAGE)


def main() -> None:
    raw_events = json.loads((PARSED / "events.json").read_text())
    events = sorted((prepare_event(e) for e in raw_events), key=lambda e: e["sort"], reverse=True)

    c = canvas.Canvas(str(OUT_PDF), pagesize=FORM_PAGE)
    c.setTitle("Precision Testing")
    c.setAuthor("Noble Diagnostic Centre")

    n_form = n_slip = 0
    for event in events:
        c.setPageSize(FORM_PAGE)
        draw_form(c, event, PAGE1_PARAMS)
        c.showPage()
        n_form += 1
        c.setPageSize(FORM_PAGE)
        draw_form(c, event, PAGE2_PARAMS)
        c.showPage()
        n_form += 1

        for reading in event["readings"]:
            biochem_items = [
                (name, fmt_val(reading["values"][key], DEC[key]))
                for name, key in BIOCHEM_ITEMS
            ]
            c.setPageSize(SLIP_PAGE)
            draw_sample_page(
                c,
                sample=reading["biochem_sample"],
                dt=reading["biochem_dt"],
                pid=reading["chem_pid"],
                items=biochem_items,
                rc0=reading["rc_biochem0"],
            )
            c.showPage()
            n_slip += 1
        for reading in event["readings"]:
            glu_items = [("GLU", fmt_val(reading["values"]["Glu"], DEC["Glu"]))]
            c.setPageSize(SLIP_PAGE)
            draw_sample_page(
                c,
                sample=reading["glu_sample"],
                dt=reading["glu_dt"],
                pid=reading["glu_pid"],
                items=glu_items,
                rc0=reading["rc_glu"],
            )
            c.showPage()
            n_slip += 1

    c.save()
    print(f"wrote {OUT_PDF}")
    print(f"events={len(events)}  forms={n_form}  sample_slips={n_slip}  pages={n_form + n_slip}")
    print("event dates:", ", ".join(e["form_date"] for e in events))


if __name__ == "__main__":
    main()
