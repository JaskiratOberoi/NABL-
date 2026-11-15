#!/usr/bin/env python3
"""Rebuild Hematology Retained Sample as one print PDF.

Today is the issued CBC from RS_DEC_25, RS_MARCH_26, RS_JUNE_26 and
RS_SEP_26. Yesterday is the next-day repeat of that CBC. Analysis
Reports keep the analyser field labels; name, ID and draw time stay blank.
"""
from __future__ import annotations

import io
import json
import random
import sys
from datetime import timedelta
from pathlib import Path

import fitz
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfgen import canvas

ROOT = Path(__file__).resolve().parents[1]
HEM = ROOT.parent
sys.path.insert(0, str(HEM / "_assets"))
import analysis_report as ar  # noqa: E402

OUT_PDF = ROOT / "Retained Sample 2026.pdf"
FORM_PAGE = landscape(A4)
PATIENTS = json.loads((ROOT / "_parsed" / "patients.json").read_text())

FORM_PARAMS = [
    ("WBC", "WBC", 2),
    ("RBC", "RBC", 2),
    ("Hb", "HGB", 1),
    ("HCT", "HCT", 1),
    ("MCV", "MCV", 1),
    ("MCH", "MCH", 1),
    ("MCHC", "MCHC", 1),
    ("RDW-CV", "RDW-CV", 1),
    ("PLT", "PLT", 0),
]


def fmt_val(val: float, nd: int) -> str:
    if nd == 0:
        return str(int(round(val)))
    return f"{val:.{nd}f}"


def pct_var(yest: float, today: float, nd: int) -> float:
    """% Variation from the Yesterday / Today figures printed on the form."""
    a = float(fmt_val(yest, nd))
    b = float(fmt_val(today, nd))
    if a == 0:
        return 0.0
    return abs(b - a) / abs(a) * 100.0


def prepare(patient: dict) -> dict:
    today_d = ar.parse_form_date(patient["form_date"])
    yest_d = today_d - timedelta(days=1)
    today = ar.complete_cbc(patient["cbc"], patient["id"] + "|today")
    for assay, val in patient["cbc"].items():
        today[assay] = val
    yest = ar.jitter_cbc(today, patient["id"] + "|yest", pct=1.35)
    # keep yesterday close enough that every form key is < 10%
    for _label, assay, nd in FORM_PARAMS:
        for _ in range(20):
            if pct_var(yest[assay], today[assay], nd) < 9.5:
                break
            yest[assay] = today[assay] * 0.7 + yest[assay] * 0.3
        yest = ar.complete_cbc(yest, patient["id"] + "|yabs")
    hh, mm, ss = ar.parse_hms(patient["collected"])
    yrun = ar.clock_add((hh, mm), -18)
    trun = (hh, mm)
    yprn = (*ar.clock_add(yrun, 3), (ss + 11) % 60)
    tprn = (*ar.clock_add(trun, 3), ss)
    draw_y = f"{yest_d.strftime('%m/%d/%Y')} {yrun[0]:02d}:{yrun[1]:02d}:00"
    draw_t = f"{today_d.strftime('%m/%d/%Y')} {hh:02d}:{mm:02d}:{ss:02d}"
    return {
        "form_date": today_d.strftime("%d-%m-%Y"),
        "sort": today_d,
        "patient": patient,
        "yest_d": yest_d,
        "today_d": today_d,
        "yest": yest,
        "today": today,
        "y_times": {"run": yrun, "print": yprn},
        "t_times": {"run": trun, "print": tprn},
        "draw_y": draw_y,
        "draw_t": draw_t,
        "level": patient.get("plot_level") or "Normal",
    }


def draw_form(c: canvas.Canvas, event: dict) -> None:
    w, h = FORM_PAGE
    left, right = 18, w - 18
    fy, fh = 14, 64
    outer_top = h - 16
    table_w = right - left
    pat = event["patient"]

    c.setFillColor(ar.black)
    c.setFont(ar.FONT_BOLD, 12)
    c.drawCentredString(w / 2, outer_top - 13, "VERIFICATION FORM – RETAINED SAMPLE")
    c.setFont(ar.FONT, 8.5)
    c.drawCentredString(w / 2, outer_top - 26, "(Recording schedule – Quarterly)")

    table_top = outer_top - 34
    table_bottom = fy + fh + 22
    fracs = [0.10, 0.13, 0.13, 0.12, 0.11, 0.11, 0.12, 0.09, 0.09]
    xs = [left]
    for frac in fracs:
        xs.append(xs[-1] + frac * table_w)
    xs[-1] = right

    banner_h, header_h = 14, 16
    header_bottom = table_top - banner_h - header_h
    c.setStrokeColor(ar.LINE)
    c.setLineWidth(0.7)
    c.line(left, table_top, right, table_top)
    c.line(left, table_top - banner_h, right, table_top - banner_h)
    c.line(left, header_bottom, right, header_bottom)
    c.line(left, table_bottom, right, table_bottom)
    for x in (xs[1], xs[2], xs[3], xs[4], xs[6], xs[7], xs[8]):
        c.line(x, table_top, x, header_bottom)
    c.line(xs[5], table_top - banner_h, xs[5], header_bottom)

    c.setFillColor(ar.black)
    span_y = header_bottom + (banner_h + header_h) / 2 - 3
    c.setFont(ar.FONT, 8)
    c.drawCentredString((xs[0] + xs[1]) / 2, span_y, "Date")
    c.drawCentredString((xs[1] + xs[2]) / 2, span_y, "Patient ID No.")
    c.drawCentredString((xs[2] + xs[3]) / 2, span_y, "Test Parameter")
    c.drawCentredString((xs[3] + xs[4]) / 2, span_y, "Machine")
    c.setFont(ar.FONT, 7.5)
    c.drawCentredString((xs[4] + xs[6]) / 2, table_top - 10.5, "RESULTS")
    c.setFont(ar.FONT, 8)
    c.drawCentredString((xs[4] + xs[5]) / 2, header_bottom + 4.5, "Yesterday")
    c.drawCentredString((xs[5] + xs[6]) / 2, header_bottom + 4.5, "Today")
    c.drawCentredString((xs[6] + xs[7]) / 2, span_y, "% Variation")
    c.drawCentredString((xs[7] + xs[8]) / 2, span_y, "Done By")
    c.drawCentredString((xs[8] + xs[9]) / 2, span_y, "Verified By")

    n_rows = 12
    row_h = (header_bottom - table_bottom) / n_rows
    c.setStrokeColor(ar.LINE)
    for x in xs[1:-1]:
        c.line(x, header_bottom, x, table_bottom)
    for i in range(1, n_rows):
        c.line(left, header_bottom - i * row_h, right, header_bottom - i * row_h)

    c.setFillColor(ar.black)
    for r, (label, assay, nd) in enumerate(FORM_PARAMS):
        cy = header_bottom - r * row_h - row_h / 2 - 2.5
        yest, today = event["yest"][assay], event["today"][assay]
        c.setFont(ar.FONT, 8)
        if r == 0:
            c.drawCentredString((xs[0] + xs[1]) / 2, cy, event["form_date"])
            c.setFont(ar.FONT, 7)
            c.drawCentredString((xs[1] + xs[2]) / 2, cy, pat["id"])
            c.setFont(ar.FONT, 7)
            c.drawCentredString((xs[3] + xs[4]) / 2, cy, "Mindray BC-5380")
        c.setFont(ar.FONT, 8)
        c.drawCentredString((xs[2] + xs[3]) / 2, cy, label)
        c.setFont(ar.FONT, 7.5)
        c.drawCentredString((xs[4] + xs[5]) / 2, cy, fmt_val(yest, nd))
        c.drawCentredString((xs[5] + xs[6]) / 2, cy, fmt_val(today, nd))
        c.drawCentredString((xs[6] + xs[7]) / 2, cy, f"{pct_var(yest, today, nd):.2f}")

    c.setFont(ar.FONT, 8.5)
    c.drawString(
        left + 6,
        table_bottom - 14,
        "* Acceptance Criteria for Variation in Results – Variation < MU or 10%",
    )
    ar.draw_ndc_footer(c, left, right, "Page 7 of clause 7.3.2")
    c.setStrokeColor(ar.LINE)
    c.setLineWidth(0.8)
    c.rect(left, fy, table_w, outer_top - fy, stroke=1, fill=0)


def render_reports(event: dict, dest: Path) -> None:
    pages = []
    pat = event["patient"]
    for sid, day, rec, times, draw in (
        ("RET-Y", event["yest_d"], event["yest"], event["y_times"], event["draw_y"]),
        ("RET-T", event["today_d"], event["today"], event["t_times"], event["draw_t"]),
    ):
        rng = random.Random(day.toordinal() * 5380 + (0 if sid.endswith("Y") else 1))
        plots = ar.make_report_plots_png(event["level"], rec, rng)
        pages.append(
            ar.report_html(day, sid, rec, times["run"], times["print"], plots, patient=pat, draw=draw)
        )
    ar.render_pages(pages, dest)


def main() -> None:
    events = sorted((prepare(p) for p in PATIENTS), key=lambda e: e["sort"], reverse=True)
    out = fitz.open()
    max_v = 0.0
    with __import__("tempfile").TemporaryDirectory() as td:
        td = Path(td)
        for i, event in enumerate(events):
            buf = io.BytesIO()
            c = canvas.Canvas(buf, pagesize=FORM_PAGE)
            c.setTitle("Hematology Retained Sample")
            draw_form(c, event)
            c.save()
            form_doc = fitz.open("pdf", buf.getvalue())
            out.insert_pdf(form_doc)
            form_doc.close()
            rep = td / f"rep-{i}.pdf"
            render_reports(event, rep)
            rep_doc = fitz.open(rep)
            out.insert_pdf(rep_doc)
            rep_doc.close()
            for _label, assay, nd in FORM_PARAMS:
                shown = pct_var(event["yest"][assay], event["today"][assay], nd)
                if shown >= 10:
                    raise RuntimeError(f"{event['form_date']} {assay} variation {shown:.2f}%")
                max_v = max(max_v, shown)
    out.save(str(OUT_PDF))
    out.close()
    print(f"wrote {OUT_PDF}")
    print(f"events={len(events)} pages={len(events) * 3} max_var={max_v:.2f}%")
    for e in events:
        print(f"  {e['form_date']}  {e['patient']['id']}  {e['patient'].get('source', '')}")


if __name__ == "__main__":
    main()
