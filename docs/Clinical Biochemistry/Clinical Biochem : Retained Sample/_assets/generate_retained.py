#!/usr/bin/env python3
"""Rebuild Clinical Biochemistry Retained Sample binder as one print PDF.

Yesterday = precision reading 1 (same reports, same pinning, including HDL).
Today = that value times the photo today/yesterday ratio, so % variation
matches the binder. Glucose is a separate slip. Years on remaining photo
timestamps shift +1.
"""
from __future__ import annotations

import importlib.util
import json
from datetime import datetime
from pathlib import Path

from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfgen import canvas

ROOT = Path(__file__).resolve().parents[1]
PARSED = ROOT / "_parsed"
OUT_PDF = ROOT / "Retained Sample 2026.pdf"
PREC_GEN = Path(
    "/Users/jas/Work/NABL 2026/docs/Clinical Biochem : Precision Testing/_assets/generate_precision.py"
)
PREC_JSON = Path(
    "/Users/jas/Work/NABL 2026/docs/Clinical Biochem : Precision Testing/_parsed/events.json"
)

spec = importlib.util.spec_from_file_location("prec_gen", PREC_GEN)
prec = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(prec)

FORM_PAGE = landscape(A4)
SLIP_PAGE = A4
FONT = prec.FONT
FONT_BOLD = prec.FONT_BOLD
LINE = prec.LINE
DEC = prec.DEC
BIOCHEM_ITEMS = prec.BIOCHEM_ITEMS

PAGE1 = [
    ("Glucose", "Glu"),
    ("Chol", "Chol"),
    ("Albumin", "Alb"),
    ("TGL", "TGL"),
    ("SGOT", "SGOT"),
    ("UAC", "UAC"),
    ("CRT J", "CRT J"),
    ("TPR", "TPR"),
    ("Calcium", "Cal"),
    ("Urea", "Urea"),
]
PAGE2 = [
    ("SGPT", "SGPT"),
    ("GGT", "GGT"),
    ("DBil", "DBil"),
    ("TBil", "TBil"),
    ("ALP", "ALP"),
    ("HDL", "HDL"),
]

SLIP_TO_KEY = {
    "CHOL": "Chol",
    "ALB": "Alb",
    "TGL": "TGL",
    "SGOT": "SGOT",
    "UAC": "UAC",
    "CRT J": "CRT J",
    "TPR": "TPR",
    "CAL A": "Cal",
    "UREA UV": "Urea",
    "SGPT": "SGPT",
    "GGT": "GGT",
    "BIL D": "DBil",
    "BIL T": "TBil",
    "ALP IFCC": "ALP",
}


def shift_year(text: str) -> str:
    return text.replace("2025", "2026").replace("2024", "2025")


def parse_dt(text: str) -> datetime:
    return datetime.strptime(text, "%d/%m/%Y %H:%M:%S")


def photo_pair(raw: dict) -> dict[str, tuple[float, float]]:
    yest = {SLIP_TO_KEY[k]: float(v) for k, v in raw["yesterday_biochem"]["values"].items()}
    today = {SLIP_TO_KEY[k]: float(v) for k, v in raw["today_biochem"]["values"].items()}
    yest["Glu"] = float(raw["yesterday_glu"]["value"])
    today["Glu"] = float(raw["today_glu"]["value"])
    return {k: (yest[k], today[k]) for k in yest}


def scaled_today(yest_new: float, yest_photo: float, today_photo: float, nd: int) -> float:
    if yest_photo == 0:
        return round(yest_new, nd)
    out = round(yest_new * (today_photo / yest_photo), nd)
    tick = 10 ** (-nd)
    for _ in range(20):
        if yest_new == 0:
            break
        pct = abs(out - yest_new) / yest_new * 100
        if pct < 10:
            break
        if out > yest_new:
            out = round(out - tick, nd)
        else:
            out = round(out + tick, nd)
    return out


def pct_var(yest: float, today: float) -> float:
    if yest == 0:
        return 0.0
    return abs(today - yest) / yest * 100


def prepare(raw: dict, prec_by_yest: dict) -> dict:
    yest_key = raw["yesterday_date"]
    prec_ev = prec_by_yest[yest_key]
    r1 = prec_ev["readings"][0]
    pairs = photo_pair(raw)
    values: dict[str, tuple[float, float]] = {}
    for key, nd in DEC.items():
        yest_new = float(r1["values"][key])
        if key == "HDL":
            y_ch, t_ch = pairs["Chol"]
            t_new = scaled_today(yest_new, y_ch, t_ch, nd)
        else:
            y_ph, t_ph = pairs[key]
            t_new = scaled_today(yest_new, y_ph, t_ph, nd)
        values[key] = (yest_new, t_new)
    today_dt = parse_dt(shift_year(raw["today_biochem"]["datetime"]))
    today_glu_dt = parse_dt(shift_year(raw["today_glu"]["datetime"]))
    form_date = datetime.strptime(shift_year(raw["form_date"]), "%d/%m/%Y")
    return {
        "form_date": form_date.strftime("%d/%m/%Y"),
        "form_dept": raw.get("form_dept") or "Biochem",
        "chem_id": prec_ev["chem_id"],
        "glu_id": prec.EVENT_META[yest_key]["glu_id"],
        "sort": form_date,
        "values": values,
        "yest_sample": raw["yesterday_biochem"]["sample"],
        "yest_glu_sample": raw["yesterday_glu"]["sample"],
        "today_sample": raw["today_biochem"]["sample"],
        "today_glu_sample": raw["today_glu"]["sample"],
        "yest_dt": r1["biochem_dt"],
        "yest_glu_dt": r1["glu_dt"],
        "today_dt": today_dt,
        "today_glu_dt": today_glu_dt,
        "yest_rc0": int(raw["yesterday_biochem"]["rc0"]),
        "today_rc0": int(raw["today_biochem"]["rc0"]),
        "yest_pid": f"{prec_ev['chem_id']}-01",
        "today_pid": f"{prec_ev['chem_id']}-02",
        "yest_glu_pid": f"{prec.EVENT_META[yest_key]['glu_id']}-01",
        "today_glu_pid": f"{prec.EVENT_META[yest_key]['glu_id']}-02",
    }


def draw_form(c: canvas.Canvas, event: dict, params: list[tuple[str, str]]) -> None:
    w, h = FORM_PAGE
    left, right = 18, w - 18
    fy, fh = 14, 64
    outer_top = h - 16
    table_w = right - left

    c.setFillColor(prec.black)
    c.setFont(FONT_BOLD, 12)
    c.drawCentredString(w / 2, outer_top - 13, "VERIFICATION FORM – RETAINED SAMPLE")
    c.setFont(FONT, 8.5)
    c.drawCentredString(w / 2, outer_top - 26, "(Recording schedule – Quarterly)")

    table_top = outer_top - 34
    table_bottom = fy + fh + 22
    # Date, Patient ID, Test Parameter, Machine, Yesterday, Today, % Variation, Done By, Verified By
    fracs = [0.10, 0.13, 0.13, 0.10, 0.11, 0.11, 0.12, 0.10, 0.10]
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
    for x in (xs[1], xs[2], xs[3], xs[4], xs[6], xs[7], xs[8]):
        c.line(x, table_top, x, header_bottom)
    c.line(xs[5], table_top - banner_h, xs[5], header_bottom)

    c.setFillColor(prec.black)
    span_y = header_bottom + (banner_h + header_h) / 2 - 3
    c.setFont(FONT, 8)
    c.drawCentredString((xs[0] + xs[1]) / 2, span_y, "Date")
    c.drawCentredString((xs[1] + xs[2]) / 2, span_y, "Patient ID No.")
    c.drawCentredString((xs[2] + xs[3]) / 2, span_y, "Test Parameter")
    c.drawCentredString((xs[3] + xs[4]) / 2, span_y, "Machine")
    c.setFont(FONT, 7.5)
    c.drawCentredString((xs[4] + xs[6]) / 2, table_top - 10.5, "RESULTS")
    c.setFont(FONT, 8)
    c.drawCentredString((xs[4] + xs[5]) / 2, header_bottom + 4.5, "Yesterday")
    c.drawCentredString((xs[5] + xs[6]) / 2, header_bottom + 4.5, "Today")
    c.drawCentredString((xs[6] + xs[7]) / 2, span_y, "% Variation")
    c.drawCentredString((xs[7] + xs[8]) / 2, span_y, "Done By")
    c.drawCentredString((xs[8] + xs[9]) / 2, span_y, "Verified By")

    n_rows = 12
    body_h = header_bottom - table_bottom
    row_h = body_h / n_rows
    c.setStrokeColor(LINE)
    c.setLineWidth(0.7)
    for x in xs[1:-1]:
        c.line(x, header_bottom, x, table_bottom)
    for i in range(1, n_rows):
        c.line(left, header_bottom - i * row_h, right, header_bottom - i * row_h)

    c.setFillColor(prec.black)
    for r, (label, key) in enumerate(params):
        cy = header_bottom - r * row_h - row_h / 2 - 2.5
        yest, today = event["values"][key]
        nd = DEC[key]
        c.setFont(FONT, 8)
        if r == 0:
            c.drawCentredString((xs[0] + xs[1]) / 2, cy, event["form_date"])
            c.drawCentredString((xs[1] + xs[2]) / 2, cy, event["chem_id"])
        c.drawCentredString((xs[2] + xs[3]) / 2, cy, label)
        c.setFont(FONT, 7.5)
        c.drawCentredString((xs[4] + xs[5]) / 2, cy, prec.fmt_val(yest, nd))
        c.drawCentredString((xs[5] + xs[6]) / 2, cy, prec.fmt_val(today, nd))
        c.drawCentredString((xs[6] + xs[7]) / 2, cy, f"{pct_var(yest, today):.2f}")

    c.setFont(FONT, 8.5)
    c.drawString(
        left + 6,
        table_bottom - 14,
        "* Acceptance Criteria for Variation in Results – Variation < MU or 10%",
    )
    prec.draw_footer(c, left, right, fy, fh, "Page 7 of clause 7.3.2")
    c.setStrokeColor(LINE)
    c.setLineWidth(0.8)
    c.rect(left, fy, table_w, outer_top - fy, stroke=1, fill=0)


def biochem_items(vals: dict[str, float]) -> list[tuple[str, str]]:
    return [(name, prec.fmt_val(vals[key], DEC[key])) for name, key in BIOCHEM_ITEMS]


def main() -> None:
    prec_raw = json.loads(PREC_JSON.read_text())
    prec_by_yest = {e["form_date"]: prec.prepare_event(e) for e in prec_raw}
    raw_events = json.loads((PARSED / "events.json").read_text())
    events = sorted((prepare(e, prec_by_yest) for e in raw_events), key=lambda e: e["sort"], reverse=True)

    c = canvas.Canvas(str(OUT_PDF), pagesize=FORM_PAGE)
    c.setTitle("Retained Sample")
    c.setAuthor("Noble Diagnostic Centre")

    n_form = n_slip = 0
    for event in events:
        c.setPageSize(FORM_PAGE)
        draw_form(c, event, PAGE1)
        c.showPage()
        n_form += 1
        c.setPageSize(FORM_PAGE)
        draw_form(c, event, PAGE2)
        c.showPage()
        n_form += 1

        yest_vals = {k: event["values"][k][0] for k in DEC}
        today_vals = {k: event["values"][k][1] for k in DEC}

        for sample, dt, pid, items, rc0 in (
            (
                event["today_sample"],
                event["today_dt"],
                event["today_pid"],
                biochem_items(today_vals),
                event["today_rc0"],
            ),
            (
                event["today_glu_sample"],
                event["today_glu_dt"],
                event["today_glu_pid"],
                [("GLU", prec.fmt_val(today_vals["Glu"], DEC["Glu"]))],
                event["today_rc0"] + len(BIOCHEM_ITEMS),
            ),
            (
                event["yest_sample"],
                event["yest_dt"],
                event["yest_pid"],
                biochem_items(yest_vals),
                event["yest_rc0"],
            ),
            (
                event["yest_glu_sample"],
                event["yest_glu_dt"],
                event["yest_glu_pid"],
                [("GLU", prec.fmt_val(yest_vals["Glu"], DEC["Glu"]))],
                event["yest_rc0"] + len(BIOCHEM_ITEMS),
            ),
        ):
            c.setPageSize(SLIP_PAGE)
            prec.draw_sample_page(c, sample=sample, dt=dt, pid=pid, items=items, rc0=rc0)
            c.showPage()
            n_slip += 1

    c.save()
    print(f"wrote {OUT_PDF}")
    print(f"events={len(events)}  forms={n_form}  sample_slips={n_slip}  pages={n_form + n_slip}")
    print("event dates:", ", ".join(e["form_date"] for e in events))
    for event in events:
        print(f"  {event['form_date']} ID {event['chem_id']}")
        for _, key in PAGE1 + PAGE2:
            y, t = event["values"][key]
            print(f"    {key:6} yest={y}  today={t}  var={pct_var(y, t):.2f}%")


if __name__ == "__main__":
    main()
