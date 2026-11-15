#!/usr/bin/env python3
"""Clean Organo Biotech pH confirmation letters.

Handwritten notes are set in type. Struck-out figures are dropped:
Ref. No. OBL-COA-35-26 (not 25-26), current-dated and letter dates in
2026 (not 2025), manufacture year 2025 (not 2024), expiry year 2029
(not 2028). The printed specification table is unchanged.
"""
from __future__ import annotations

from pathlib import Path

from reportlab.lib.colors import Color, black, white
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "Organo pH Confirmation Letters 2026.pdf"
LOGO = Path(__file__).resolve().parent / "organo-logo.png"
GILL = Path("/System/Library/Fonts/Supplemental/GillSans.ttc")

_TIMES = Path("/System/Library/Fonts/Supplemental/Times New Roman.ttf")
_TIMES_BD = Path("/System/Library/Fonts/Supplemental/Times New Roman Bold.ttf")
_TIMES_BI = Path("/System/Library/Fonts/Supplemental/Times New Roman Bold Italic.ttf")
_ARIAL = Path("/System/Library/Fonts/Supplemental/Arial.ttf")
pdfmetrics.registerFont(TTFont("TNR", str(_TIMES)))
pdfmetrics.registerFont(TTFont("TNR-Bold", str(_TIMES_BD)))
pdfmetrics.registerFont(TTFont("TNR-BI", str(_TIMES_BI)))
pdfmetrics.registerFont(TTFont("Arial", str(_ARIAL)))
pdfmetrics.registerFont(TTFont("Arial-Bold", "/System/Library/Fonts/Supplemental/Arial Bold.ttf"))
pdfmetrics.registerFont(TTFont("Gill", str(GILL), subfontIndex=0))
pdfmetrics.registerFont(TTFont("Gill-Bold", str(GILL), subfontIndex=1))

INK = Color(0.12, 0.12, 0.12)
BROWN = Color(0.55, 0.28, 0.16)
GREEN = Color(0.36, 0.48, 0.20)

ROWS = [
    ("1", "pH", "6.6"),
    ("2", "Specific Conductivity at 25 C", "<33 Microsiemens/cm"),
    ("3", "Silica", "Nil"),
    ("4", "Chloride (Cl)", "<5 mg/l"),
    ("5", "Sulphate (SO4)", "<10 mg/l"),
    ("6", "Calcium (Ca)", "Nil"),
    ("7", "Ammonium (NH4)", "Nil"),
    ("8", "Magnesium (Mg)", "Nil"),
    ("9", "Alkalinity", "Nil"),
    ("10", "Iron", "Nil"),
    ("11", "Sodium (Na)", "Nil"),
    ("12", "Potassium (K)", "Nil"),
    ("13", "Microbes", "Nil"),
    ("14", "Bacteria", "Nil"),
    ("15", "Resistivity", ">30 kohm/cm²"),
    ("16", "Oxidizable Matter Oxygen", "0.29mg/Ltr"),
    ("17", "Residue After Evaporation", "1.2mg/kg"),
]

# dated, lot line, spec lot, mfg, exp
LETTERS = [
    ("05/04/2026", "U2364/1600", "05-04-2026", "1600", "APRIL, 2025", "MARCH, 2029"),
    ("05/05/2026", "U2364/1650", "05-05-2026", "1650", "MAY, 2025", "APRIL, 2029"),
    ("05/06/2026", "U2364/1700", "05-06-2026", "1700", "JUNE, 2025", "MAY, 2029"),
    ("05/07/2026", "U2364/1720", "05-07-2026", "1720", "JULY, 2025", "JUNE, 2029"),
    ("19/09/2026", "U2361/2370", "19-09-2026", "1600", "APRIL, 2025", "MARCH, 2029"),
]


def draw_logo(c: canvas.Canvas, right: float, bottom: float) -> None:
    """High-resolution Organo wordmark (brush ring, rgano, Biotech)."""
    logo_w = 138
    logo_h = logo_w * 864 / 2720
    c.drawImage(
        str(LOGO),
        right + 1.4 - logo_w,
        bottom,
        width=logo_w,
        height=logo_h,
        mask="auto",
        preserveAspectRatio=True,
    )


ICON_UNIT = 0.0556


def icon_phone(c: canvas.Canvas, x: float, y: float) -> None:
    """Filled desk telephone; drawn in reference-crop units (x 68-248, y 62-195)."""

    def P(zx: float, zy: float) -> tuple[float, float]:
        return x + (zx - 68) * ICON_UNIT, y + (195 - zy) * ICON_UNIT

    c.saveState()
    c.setFillColor(INK)
    p = c.beginPath()
    p.moveTo(*P(68, 116))
    p.curveTo(*P(68, 72), *P(110, 62), *P(158, 62))
    p.curveTo(*P(206, 62), *P(248, 72), *P(248, 116))
    p.curveTo(*P(248, 124), *P(244, 127), *P(236, 127))
    p.lineTo(*P(216, 127))
    p.curveTo(*P(210, 127), *P(207, 122), *P(208, 114))
    p.curveTo(*P(196, 94), *P(178, 88), *P(158, 88))
    p.curveTo(*P(138, 88), *P(120, 94), *P(108, 114))
    p.curveTo(*P(109, 122), *P(106, 127), *P(100, 127))
    p.lineTo(*P(80, 127))
    p.curveTo(*P(72, 127), *P(68, 124), *P(68, 116))
    p.close()
    c.drawPath(p, stroke=0, fill=1)
    b = c.beginPath()
    b.moveTo(*P(112, 92))
    b.lineTo(*P(134, 92))
    b.lineTo(*P(134, 112))
    b.lineTo(*P(182, 112))
    b.lineTo(*P(182, 92))
    b.lineTo(*P(204, 92))
    b.lineTo(*P(230, 188))
    b.curveTo(*P(231, 193), *P(229, 195), *P(225, 195))
    b.lineTo(*P(91, 195))
    b.curveTo(*P(87, 195), *P(85, 193), *P(86, 188))
    b.close()
    c.drawPath(b, stroke=0, fill=1)
    c.restoreState()


def icon_mail(c: canvas.Canvas, x: float, y: float) -> None:
    c.saveState()
    c.setStrokeColor(INK)
    c.setLineWidth(0.7)
    c.rect(x, y + 1.2, 9, 6.2, stroke=1, fill=0)
    p = c.beginPath()
    p.moveTo(x, y + 7.4)
    p.lineTo(x + 4.5, y + 4.2)
    p.lineTo(x + 9, y + 7.4)
    c.drawPath(p, stroke=1, fill=0)
    c.restoreState()


def icon_laptop(c: canvas.Canvas, x: float, y: float) -> None:
    """Filled laptop with globe; drawn in reference-crop units (x 25-278, y 8-150)."""
    u = ICON_UNIT

    def P(zx: float, zy: float) -> tuple[float, float]:
        return x + (zx - 25) * u, y + (150 - zy) * u

    c.saveState()
    c.setFillColor(INK)
    c.roundRect(*P(55, 118), 190 * u, 110 * u, 6 * u, stroke=0, fill=1)
    c.setFillColor(white)
    c.rect(*P(73, 102), 154 * u, 78 * u, stroke=0, fill=1)
    c.setFillColor(INK)
    gx, gy = P(150, 60)
    c.circle(gx, gy, 37 * u, stroke=0, fill=1)
    c.setStrokeColor(white)
    c.setLineWidth(5 * u)
    c.ellipse(gx - 14 * u, gy - 30 * u, gx + 14 * u, gy + 30 * u, stroke=1, fill=0)
    c.line(gx, gy - 30 * u, gx, gy + 30 * u)
    c.roundRect(*P(25, 150), 253 * u, 22 * u, 8 * u, stroke=0, fill=1)
    c.restoreState()


FOOTER_GAP = 60


def draw_footer(c: canvas.Canvas, cx: float, top: float) -> None:
    """Footer block; `top` is the baseline of the company name."""
    name_a = "Organo"
    name_b = " Biotech Laboratories Pvt. Ltd."
    c.setFont("Arial-Bold", 19.7)
    wa = c.stringWidth(name_a, "Arial-Bold", 19.7)
    wb = c.stringWidth(name_b, "Arial-Bold", 19.7)
    x0 = cx - (wa + wb) / 2
    c.setFillColor(BROWN)
    c.drawString(x0, top, name_a)
    c.setFillColor(GREEN)
    c.drawString(x0 + wa, top, name_b)
    c.setFillColor(INK)
    c.setFont("Arial", 7)
    c.drawRightString(x0 + wa + wb, top - 9, "An ISO 9001: 2015 & ISO 14001: 2015 Certified Company")
    c.setFont("Arial-Bold", 10.3)
    c.drawCentredString(cx, top - 22.7, "MANUFACTURER OF : LAB CHEMICALS, REAGENTS, TRIPLE REAGENTS")
    c.setFont("Arial-Bold", 10.5)
    c.drawCentredString(cx, top - 39.7, "GRADE DEIONIZED WATER & HOUSEKEEPING CHEMICALS")
    c.setFont("Arial", 9.15)
    c.drawCentredString(
        cx,
        top - 54.4,
        "H.O.: Plot No.7, Phase-1, Community Centre, Industrial Area, Mayapuri, New Delhi-110064",
    )
    c.setFont("Arial", 7.5)
    phone = "011-28113908/45680909"
    mail = "rjndrchopra@yahoo.com"
    web = "www.organobiotech.in"
    gap = 16
    phone_w = 12 + c.stringWidth(phone, "Arial", 7.5)
    mail_w = 18.5 + c.stringWidth(mail, "Arial", 7.5)
    web_w = 12 + c.stringWidth(web, "Arial", 7.5)
    total = phone_w + mail_w + web_w + gap * 2
    x = cx - total / 2
    base = top - 71.4
    y = base - 1.5
    icon_phone(c, x, base + 1.3)
    c.setFillColor(INK)
    c.drawString(x + 12, base, phone)
    x += phone_w + gap
    icon_laptop(c, x, base + 3.3)
    c.setFillColor(INK)
    c.drawString(x + 18.5, base, mail)
    x += mail_w + gap
    icon_mail(c, x, y)
    c.drawString(x + 12, y + 1.5, web)


def underline(c: canvas.Canvas, text: str, font: str, size: float, y: float, cx: float) -> None:
    c.setFont(font, size)
    c.drawCentredString(cx, y, text)
    w = c.stringWidth(text, font, size)
    c.setStrokeColor(black)
    c.setLineWidth(0.8)
    c.line(cx - w / 2, y - 2, cx + w / 2, y - 2)


def draw_letter(c: canvas.Canvas, dated: str, lot: str, current: str, spec_lot: str, mfg: str, exp: str) -> None:
    w, h = A4
    cx = w / 2
    left, right = 42, w - 42

    c.setFillColor(INK)
    c.setFont("Arial", 8)
    c.drawString(left, h - 78, "GSTIN No.:07AABCO0245P1ZB")
    draw_logo(c, right, h - 99.2)

    c.setFont("TNR", 11)
    c.drawString(left, h - 102, "26-27")
    c.drawString(left, h - 122, "Ref. No. OBL-COA-35-26")
    c.drawRightString(right, h - 122, f"Dated  {dated}")

    underline(c, "C- CONFIRMATION LETTER, DETERMING pH SCALE", "TNR-Bold", 13, h - 180, cx)

    c.setFont("TNR", 11)
    c.drawCentredString(cx, h - 202, "This is to certify that the Reagent Grade Diagnosed water (ULTRA PURE)")
    c.drawCentredString(cx, h - 225, f"Lot No. {lot} Current Dated {current} is determined by")
    c.drawCentredString(cx, h - 248, "The under mentioned specifications.")

    y = h - 279
    c.setFont("TNR-Bold", 12)
    c.drawCentredString(cx, y, "SPECIFICATION'S")
    y -= 18
    underline(c, f"(LOT NO. – {spec_lot})", "TNR-Bold", 12, y, cx)
    y -= 19
    underline(c, f"MFG – {mfg}", "TNR-Bold", 12, y, cx)
    y -= 19
    underline(c, f"EXP – {exp}", "TNR-Bold", 12, y, cx)
    y -= 22
    underline(c, "Type – III Grade – III", "TNR-Bold", 12, y, cx)

    y -= 39
    c.setStrokeColor(black)
    c.setLineWidth(0.6)
    c.line(left, y + 14, right, y + 14)
    c.setFont("TNR-Bold", 11)
    c.drawString(left, y, "S.No.")
    c.drawString(left + 70, y, "Test Value")
    c.drawRightString(right, y, "Result")
    c.line(left, y - 4, right, y - 4)

    c.setFont("TNR", 11)
    y -= 28
    for sno, test, result in ROWS:
        c.drawString(left + 8, y, sno)
        c.drawString(left + 70, y, test)
        c.drawRightString(right, y, result)
        y -= 14
        if sno == "17":
            c.drawString(left + 70, y, "On Heating at 110C")
            y -= 14

    draw_footer(c, cx, y + 14 - FOOTER_GAP)


def main() -> None:
    c = canvas.Canvas(str(OUT), pagesize=A4)
    c.setTitle("Organo Biotech pH Confirmation Letters")
    c.setAuthor("Organo Biotech Laboratories Pvt. Ltd.")
    for dated, lot, current, spec_lot, mfg, exp in LETTERS:
        draw_letter(c, dated, lot, current, spec_lot, mfg, exp)
        c.showPage()
    c.save()
    print(f"wrote {OUT}")
    print(f"pages={len(LETTERS)}")


if __name__ == "__main__":
    main()
