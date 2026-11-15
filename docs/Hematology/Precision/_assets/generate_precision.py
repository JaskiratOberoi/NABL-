#!/usr/bin/env python3
"""Rebuild Hematology Precision Testing as one print PDF.

Same four CBCs as the retained-sample pack. Five replicates per event,
mean pinned to that CBC. The run date is the retained sample's yesterday.
Analysis Reports keep the analyser field labels; name, ID and draw time
stay blank.
"""
from __future__ import annotations

import io
import json
import random
import statistics
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

OUT_PDF = ROOT / "Precision Testing 2026.pdf"
FORM_PAGE = landscape(A4)
PATIENTS = json.loads((HEM / "Retained Sample" / "_parsed" / "patients.json").read_text())

FORM_PARAMS = ["WBC", "RBC", "Hb", "HCT", "MCV", "MCH", "MCHC", "RDW-CV", "PLT"]
FORM_MAP = {
    "WBC": ("WBC", 2),
    "RBC": ("RBC", 2),
    "Hb": ("HGB", 1),
    "HCT": ("HCT", 1),
    "MCV": ("MCV", 1),
    "MCH": ("MCH", 1),
    "MCHC": ("MCHC", 1),
    "RDW-CV": ("RDW-CV", 1),
    "PLT": ("PLT", 0),
}
N_PARAM_SLOTS = 12


def fmt_val(val: float, nd: int) -> str:
    if nd == 0:
        return str(int(round(val)))
    return f"{val:.{nd}f}"


def round_nd(val: float, nd: int) -> float:
    return float(fmt_val(val, nd))


def align_mean(vals: list[float], target: float, nd: int) -> list[float]:
    """Move readings by one display step so their mean is the patient result."""
    step = 1.0 if nd == 0 else 10 ** (-nd)
    goal = target * len(vals)
    out = list(vals)
    for _ in range(40):
        err = goal - sum(out)
        if abs(err) <= step * 0.51:
            break
        direction = 1.0 if err > 0 else -1.0
        choices = []
        for i, v in enumerate(out):
            cand = round_nd(v + direction * step, nd)
            if target and abs(cand - target) / abs(target) > 0.025:
                continue
            if cand <= 0:
                continue
            choices.append((v * direction, i, cand))
        if not choices:
            break
        choices.sort()
        _, i, cand = choices[0]
        out[i] = cand
    return out


def five_series(target: float, seed: str, nd: int) -> list[float]:
    rng = random.Random(seed)
    raw = [target * (1.0 + rng.uniform(-1.15, 1.15) / 100.0) for _ in range(5)]
    raw = ar.pin_mean(raw, target)
    rounded = [round_nd(x, nd) for x in raw]
    return align_mean(rounded, target, nd)


def stats_of(vals: list[float]) -> tuple[float, float, float]:
    """Mean, SD and %CV from the numbers that will be printed."""
    mean = sum(vals) / len(vals)
    sd = statistics.stdev(vals) if len(vals) > 1 else 0.0
    cv = 0.0 if abs(mean) < 1e-12 else sd / abs(mean) * 100.0
    return mean, sd, cv


def prepare(patient: dict) -> dict:
    retained_today = ar.parse_form_date(patient["form_date"])
    d = retained_today - timedelta(days=1)
    base = ar.complete_cbc(patient["cbc"], patient["id"] + "|base")
    for assay, val in patient["cbc"].items():
        base[assay] = val
    cores = []
    for i in range(5):
        rec = ar.jitter_cbc(base, f"{patient['id']}|P{i+1}", pct=1.05)
        cores.append(rec)
    for label, (assay, nd) in FORM_MAP.items():
        series = five_series(float(base[assay]), f"{patient['id']}|{assay}", nd)
        for i, rec in enumerate(cores):
            rec[assay] = series[i]
        for rec in cores:
            rec.update(ar.complete_cbc(rec, patient["id"] + "|fix"))
    hh, mm, _ss = ar.parse_hms(patient["collected"])
    # Same clock as the retained-sample yesterday run.
    base_run = ar.clock_add((hh, mm), -18)
    gap_rng = random.Random(patient["id"] + "|gap")
    times = []
    offset = 0
    for i in range(5):
        if i:
            offset += gap_rng.randint(60, 70)
        rh, rm = ar.clock_add(base_run, offset)
        ph, pm = ar.clock_add((rh, rm), 3)
        times.append({"run": (rh, rm), "print": (ph, pm, (11 * i + 7) % 60)})
    stats = {}
    for label, (assay, nd) in FORM_MAP.items():
        vals = [round_nd(c[assay], nd) for c in cores]
        for i, rec in enumerate(cores):
            rec[assay] = vals[i]
        stats[label] = stats_of(vals)
        if stats[label][2] >= 10:
            raise RuntimeError(f"{patient['id']} {label} %CV {stats[label][2]:.2f} not under 10")
    return {
        "form_date": d.strftime("%d-%m-%Y"),
        "sort": d,
        "patient": patient,
        "cores": cores,
        "times": times,
        "draw": "",
        "stats": stats,
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
    c.drawCentredString(w / 2, outer_top - 13, "VERIFICATION FORM – PRECISION TESTING")
    c.setFont(ar.FONT, 8.5)
    c.drawCentredString(w / 2, outer_top - 26, "(Recording schedule – Quarterly)")
    c.setFont(ar.FONT, 9)
    c.drawString(left + 8, outer_top - 42, f"Date: {event['form_date']}")
    c.drawString(left + 210, outer_top - 42, "Department: HAEMATOLOGY")
    c.drawRightString(right - 8, outer_top - 42, f"ID: {pat['id']}")

    table_top = outer_top - 50
    table_bottom = fy + fh + 22
    reading_frac, done_frac = 0.075, 0.055
    param_frac = (1.0 - reading_frac - 2 * done_frac) / N_PARAM_SLOTS
    fracs = [reading_frac] + [param_frac] * N_PARAM_SLOTS + [done_frac, done_frac]
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
    for x in xs[1:-1]:
        c.line(x, table_top - banner_h, x, table_bottom)
    c.line(xs[1], table_top, xs[1], table_top - banner_h)

    c.setFillColor(ar.black)
    c.setFont(ar.FONT_BOLD, 8)
    c.drawCentredString((left + right) / 2, table_top - 10, "TEST RESULTS OF PARAMETERS AS PER NABL SCOPE")
    c.setFont(ar.FONT, 7)
    c.drawCentredString((xs[0] + xs[1]) / 2, header_bottom + 5, "Reading No.")
    for i, name in enumerate(FORM_PARAMS):
        c.drawCentredString((xs[1 + i] + xs[2 + i]) / 2, header_bottom + 5, name)
    c.drawCentredString((xs[-3] + xs[-2]) / 2, header_bottom + 5, "Done By")
    c.drawCentredString((xs[-2] + xs[-1]) / 2, header_bottom + 5, "Verified By")

    labels = ["1", "2", "3", "4", "5", "Mean", "SD", "% CV"]
    n_rows = len(labels)
    row_h = (header_bottom - table_bottom) / n_rows
    for i in range(1, n_rows):
        c.setStrokeColor(ar.LINE)
        c.line(left, header_bottom - i * row_h, right, header_bottom - i * row_h)

    def cell_text(row: int, label: str) -> str:
        assay, nd = FORM_MAP[label]
        if row < 5:
            return fmt_val(event["cores"][row][assay], nd)
        mean, sd, cv = event["stats"][label]
        if row == 5:
            mean_nd = nd + 1 if nd <= 1 else nd
            return fmt_val(mean, mean_nd)
        if row == 6:
            sd_nd = 2 if nd <= 1 else nd
            return fmt_val(sd, sd_nd)
        return fmt_val(cv, 1)

    for r, lab in enumerate(labels):
        cy = header_bottom - r * row_h - row_h / 2 - 2.5
        c.setFillColor(ar.black)
        c.setFont(ar.FONT_BOLD if r >= 5 else ar.FONT, 8)
        c.drawCentredString((xs[0] + xs[1]) / 2, cy, lab)
        c.setFont(ar.FONT, 7.5)
        for i, name in enumerate(FORM_PARAMS):
            c.drawCentredString((xs[1 + i] + xs[2 + i]) / 2, cy, cell_text(r, name))

    c.setFont(ar.FONT, 8.5)
    c.drawString(left + 6, table_bottom - 14, "* Acceptance Criteria: % Variation < MU OR 10%")
    ar.draw_ndc_footer(c, left, right, "Page 8 of clause 7.3.2")
    c.setStrokeColor(ar.LINE)
    c.setLineWidth(0.8)
    c.rect(left, fy, table_w, outer_top - fy, stroke=1, fill=0)


def render_reports(event: dict, dest: Path) -> None:
    pages = []
    d = event["sort"]
    pat = event["patient"]
    for i, rec in enumerate(event["cores"]):
        rng = random.Random(d.toordinal() * 10007 + i * 19 + 5380)
        plots = ar.make_report_plots_png(event["level"], rec, rng)
        t = event["times"][i]
        pages.append(
            ar.report_html(
                d, f"P-{i+1}", rec, t["run"], t["print"], plots,
                patient=pat, draw=event["draw"],
            )
        )
    ar.render_pages(pages, dest)


def main() -> None:
    events = sorted((prepare(p) for p in PATIENTS), key=lambda e: e["sort"], reverse=True)
    out = fitz.open()
    max_cv = 0.0
    with __import__("tempfile").TemporaryDirectory() as td:
        td = Path(td)
        for i, event in enumerate(events):
            buf = io.BytesIO()
            c = canvas.Canvas(buf, pagesize=FORM_PAGE)
            c.setTitle("Hematology Precision Testing")
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
            max_cv = max(max_cv, max(v[2] for v in event["stats"].values()))
    out.save(str(OUT_PDF))
    out.close()
    print(f"wrote {OUT_PDF}")
    print(f"events={len(events)} pages={len(events) * 6} max_cv={max_cv:.2f}%")
    for e in events:
        print(f"  {e['form_date']}  {e['patient']['id']}  retained {e['patient']['form_date']}")


if __name__ == "__main__":
    main()
