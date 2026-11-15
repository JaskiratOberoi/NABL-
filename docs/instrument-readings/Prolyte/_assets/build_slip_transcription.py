"""Typed transcription of three Prolyte thermal printouts (Aug 2024) for legibility.

Line breaks follow the printer's own wrapping so each line can be checked
against the photographed original.
"""
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

OUT = Path(__file__).resolve().parent.parent / "Prolyte Sample Report slips - Aug 2024 (transcription).pdf"

pdfmetrics.registerFont(TTFont("Menlo", "/System/Library/Fonts/Menlo.ttc", subfontIndex=0))
pdfmetrics.registerFont(TTFont("Menlo-Bold", "/System/Library/Fonts/Menlo.ttc", subfontIndex=1))


def report(date, time_hm, time_s, info, pid, k, na, cl, flags):
    fk, fna, fcl = flags
    return [
        ("c", "Sample Report"),
        ("gap", None),
        ("l", f"Time:   {date}  {time_hm}:"),
        ("l", time_s),
        ("l", f"Info:   {info}"),
        ("l", "Type:   Serum"),
        ("gap", None),
        ("l", f"PID  {pid} mmol/L   Norma"),
        ("l", "l"),
        ("l", f"    K:  {k}   (3.50--5"),
        ("a", (".50)", fk)),
        ("l", f"   Na:  {na}   (135.0--"),
        ("a", ("145.0)", fna)),
        ("l", f"   Cl:  {cl}   (98.0--1"),
        ("a", ("06.0)", fcl)),
    ]


SLIPS = [
    ("19-08-2024", "Photo: WhatsApp 2026-09-29 21.34.23", [
        report("19-08-24", "08:04", "22", "1 1 0 0 1 91", "0001", "4.31", "114.0", "93.1", (None, "d", "d")),
        report("19-08-24", "08:05", "26", "1 1 0 0 1 92", "0002", "6.88", "158.3", "119.4", ("u", "u", "u")),
    ]),
    ("20-08-2024", "Photo: WhatsApp 2026-09-29 21.34.22", [
        report("20-08-24", "08:01", "31", "1 1 0 0 1 89", "0001", "4.31", "113.1", "92.7", (None, "d", "d")),
        report("20-08-24", "08:02", "32", "1 1 0 0 1 90", "0002", "7.01", "161.0", "121.4", ("u", "u", "u")),
    ]),
    ("24-08-2024", "Photo: WhatsApp 2026-09-29 21.34.22 (1)", [
        report("24-08-24", "08:05", "01", "1 1 0 0 1 81", "0001", "4.26", "111.1", "92.1", (None, "d", "d")),
        report("24-08-24", "08:06", "03", "1 1 0 0 1 82", "0002", "7.44", "172.2", "130.3", ("u", "u", "u")),
    ]),
]

FONT, SIZE, LEAD = "Menlo", 9.2, 13.2
SLIP_W = 58 * mm
PAD = 4 * mm


def arrow(c, x, y, direction):
    bottom, top = y - 1.2, y + SIZE * 0.92
    head_h, half_w = SIZE * 0.36, SIZE * 0.2
    tip, base = (top, top - head_h) if direction == "u" else (bottom, bottom + head_h)
    c.setLineWidth(0.75)
    c.line(x, base, x, bottom if direction == "u" else top)
    p = c.beginPath()
    p.moveTo(x, tip)
    p.lineTo(x - half_w, base)
    p.lineTo(x + half_w, base)
    p.close()
    c.drawPath(p, stroke=0, fill=1)


def draw_slip(c, x0, top, reports):
    lines = []
    for i, r in enumerate(reports):
        if i:
            lines += [("gap", None)] * 3
        lines += r
    height = PAD * 2 + sum(LEAD * (0.6 if k == "gap" else 1) for k, _ in lines)
    c.setLineWidth(0.6)
    c.setStrokeGray(0.55)
    c.rect(x0, top - height, SLIP_W, height)
    c.setStrokeGray(0)
    y = top - PAD - SIZE
    c.setFont(FONT, SIZE)
    for kind, val in lines:
        if kind == "gap":
            y -= LEAD * 0.6
            continue
        if kind == "c":
            c.setFont("Menlo-Bold", SIZE)
            c.drawCentredString(x0 + SLIP_W / 2, y, val)
            c.setFont(FONT, SIZE)
        elif kind == "a":
            text, flag = val
            c.drawString(x0 + PAD, y, text)
            if flag:
                arrow(c, x0 + PAD + pdfmetrics.stringWidth(text + " ", FONT, SIZE) + 2, y, flag)
        else:
            c.drawString(x0 + PAD, y, val)
        y -= LEAD
    return top - height


def main():
    c = canvas.Canvas(str(OUT), pagesize=A4)
    c.setTitle("Prolyte Sample Report slips - Aug 2024 (transcription)")
    W, H = A4
    c.setFont("Helvetica-Bold", 12)
    c.drawString(15 * mm, H - 18 * mm, "Prolyte electrolyte analyser - Sample Report printouts")
    c.setFont("Helvetica", 9)
    c.drawString(15 * mm, H - 23.5 * mm,
                 "Typed transcription of thermal slips dated 19, 20 and 24 August 2024. Units mmol/L, sample type Serum.")

    gap = (W - 30 * mm - 3 * SLIP_W) / 2
    top = H - 34 * mm
    bottom = top
    for i, (label, src, reports) in enumerate(SLIPS):
        x = 15 * mm + i * (SLIP_W + gap)
        c.setFont("Helvetica-Bold", 9)
        c.drawString(x, top + 2.5 * mm, label)
        b = draw_slip(c, x, top, reports)
        c.setFont("Helvetica", 7)
        c.setFillGray(0.35)
        c.drawString(x, b - 4 * mm, src)
        c.setFillGray(0)
        bottom = min(bottom, b)

    notes = [
        "Line breaks reproduce the printer's own wrapping (e.g. \"(3.50--5\" / \".50)\" is the range 3.50-5.50).",
        "Arrows are the analyser's flags against the printed reference range. PID 0001 / 0002 are the two runs on each slip.",
        "Slip of 24-08-2024: day digits are faint on the original; both timestamps read \"24\". Check against the paper slip.",
        "This page is a transcription for readability, not an instrument printout. The original slips are the primary record.",
    ]
    y = bottom - 14 * mm
    c.setFont("Helvetica-Bold", 8.5)
    c.drawString(15 * mm, y, "Notes")
    c.setFont("Helvetica", 8)
    for n in notes:
        y -= 4.6 * mm
        c.drawString(15 * mm, y, "- " + n)

    c.setFont("Helvetica", 7.5)
    c.drawString(15 * mm, 15 * mm, "Transcribed by: ____________________   Checked against originals by: ____________________   Date: ___________")
    c.save()
    print(OUT)


if __name__ == "__main__":
    main()
