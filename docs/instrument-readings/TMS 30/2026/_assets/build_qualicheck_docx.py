"""Editable Word copies of the Agappe Qualicheck NORM / PATH value sheets.

Uses the data in build_qualicheck_softcopy.py. Cells that could not be
identified ("?" in the data) are left blank on a red fill; cells read from a
blurred print ("~") carry the reading on a yellow fill. Clear the fill
(Table Design > Shading > No Color) once a value has been confirmed.

Run with the project venv, which has python-docx and reportlab:
    ../../../../../.venv-docx/bin/python build_qualicheck_docx.py
"""

import sys
from pathlib import Path

from docx import Document
from docx.enum.section import WD_ORIENT
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT, WD_ROW_HEIGHT_RULE, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Mm, Pt, RGBColor

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import build_qualicheck_softcopy as src  # noqa: E402

RED_FILL = "FDE9E9"
CHECK_FILL = "FFF2B3"
GRID = "404040"
PAGE_W, PAGE_H = 297, 210
MARGIN = 8
GAP = 10


def set_fill(cell, hex_fill):
    pr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), hex_fill)
    pr.append(shd)


def set_borders(table, size):
    pr = table._tbl.tblPr
    borders = OxmlElement("w:tblBorders")
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        el = OxmlElement(f"w:{edge}")
        if size:
            el.set(qn("w:val"), "single")
            el.set(qn("w:sz"), str(size if edge.startswith("inside") else size * 2))
            el.set(qn("w:color"), GRID if edge.startswith("inside") else "000000")
        else:
            el.set(qn("w:val"), "nil")
        borders.append(el)
    pr.append(borders)


def set_cell_margins(table, lr_twips):
    pr = table._tbl.tblPr
    mar = OxmlElement("w:tblCellMar")
    for edge, w in (("top", 0), ("left", lr_twips), ("bottom", 0), ("right", lr_twips)):
        el = OxmlElement(f"w:{edge}")
        el.set(qn("w:w"), str(w))
        el.set(qn("w:type"), "dxa")
        mar.append(el)
    pr.append(mar)


TBL_PR_ORDER = ["tblStyle", "tblpPr", "tblOverlap", "bidiVisual", "tblStyleRowBandSize",
                "tblStyleColBandSize", "tblW", "jc", "tblCellSpacing", "tblInd", "tblBorders",
                "shd", "tblLayout", "tblCellMar", "tblLook"]
TC_PR_ORDER = ["cnfStyle", "tcW", "gridSpan", "hMerge", "vMerge", "tcBorders", "shd", "noWrap",
               "tcMar", "textDirection", "tcFitText", "vAlign", "hideMark"]


def schema_order(root):
    """Word rejects tblPr / tcPr children that are out of schema order."""
    for tag, order in (("tblPr", TBL_PR_ORDER), ("tcPr", TC_PR_ORDER)):
        rank = {qn(f"w:{n}"): i for i, n in enumerate(order)}
        for pr in root.iter(qn(f"w:{tag}")):
            kids = sorted(pr, key=lambda el: rank.get(el.tag, len(order)))
            for el in kids:
                pr.append(el)


def fix_layout(table, widths_pt):
    table.autofit = False
    pr = table._tbl.tblPr
    for el in pr.findall(qn("w:tblW")):
        pr.remove(el)
    tw = OxmlElement("w:tblW")
    tw.set(qn("w:w"), str(int(sum(widths_pt) * 20)))
    tw.set(qn("w:type"), "dxa")
    pr.append(tw)
    grid = table._tbl.tblGrid
    for gc, w in zip(grid.findall(qn("w:gridCol")), widths_pt):
        gc.set(qn("w:w"), str(int(w * 20)))
    for row in table.rows:
        for cell, w in zip(row.cells, widths_pt):
            cell.width = Pt(w)


def write(cell, text, size, bold=False, italic=False):
    p = cell.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    fmt = p.paragraph_format
    fmt.space_before = fmt.space_after = Pt(0)
    fmt.line_spacing_rule = WD_LINE_SPACING.EXACTLY
    fmt.line_spacing = Pt(size * 1.12)
    for i, line in enumerate(text.split("\n")):
        if i:
            p.add_run().add_break()
        r = p.add_run(line)
        r.font.name = "Calibri"
        r.font.size = Pt(size)
        r.font.bold = bold
        r.font.italic = italic
        r.font.color.rgb = RGBColor(0, 0, 0)
    cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER


def layout(entries, sheet, side, lot2):
    """Return (rows, spans): rows[r][c] = (text, bold, fill) or None; spans = (r0, c0, r1, c1)."""
    blank = [None] * 9
    rows = [list(blank), list(blank), list(blank)]
    rows[0][0] = ("LOGO", False, None)
    rows[0][2] = ("LOT", True, None)
    rows[0][3] = (src.LOT, True, None)
    rows[0][5] = ("Expiry", True, None)
    rows[0][7] = (f"QUALICHECK {sheet}", True, None)
    rows[1][3] = value(lot2, bold=True)
    rows[1][5] = (src.EXPIRY, True, None)
    rows[1][7] = ("Human Serum", True, "italic")
    for c, h in enumerate(src.COLS):
        rows[2][c] = (h, True, None)
    spans = [(0, 0, 1, 1), (0, 2, 1, 2), (0, 3, 0, 4), (1, 3, 1, 4),
             (0, 5, 0, 6), (1, 5, 1, 6), (0, 7, 0, 8), (1, 7, 1, 8), (2, 3, 2, 4)]

    r = 3
    for sl, analyte, methods in entries:
        a0 = an_start = un_start = r
        for method, mrows in methods:
            m0 = r
            for an, unit, *vals in mrows:
                if an is not None:
                    if r - 1 > an_start:
                        spans.append((an_start, 3, r - 1, 3))
                    an_start = r
                if unit is not None:
                    if r - 1 > un_start:
                        spans.append((un_start, 4, r - 1, 4))
                    un_start = r
                line = list(blank)
                if r == a0:
                    line[0] = (str(sl), False, None)
                    line[1] = (analyte, False, None)
                if r == m0:
                    line[2] = (method, False, None)
                if an:
                    line[3] = (an, False, None)
                if unit:
                    line[4] = (unit, False, None)
                for ci, v in enumerate(vals, start=5):
                    line[ci] = value(v)
                rows.append(line)
                r += 1
            if r - 1 > m0:
                spans.append((m0, 2, r - 1, 2))
        if r - 1 > an_start:
            spans.append((an_start, 3, r - 1, 3))
        if r - 1 > un_start:
            spans.append((un_start, 4, r - 1, 4))
        if r - 1 > a0:
            spans += [(a0, 0, r - 1, 0), (a0, 1, r - 1, 1)]

    if side == "left":
        line = list(blank)
        line[0] = ("SA-Semiauto Analyser", True, None)
        line[4] = ("FAA- Fully Auto Analyser", True, None)
        rows.append(line)
        spans += [(r, 0, r, 3), (r, 4, r, 8)]
    return rows, spans


def value(raw, bold=False):
    if raw.startswith("?"):
        return ("", bold, RED_FILL)
    if raw.startswith("~"):
        return (raw[1:], bold, CHECK_FILL)
    return (raw, bold, None)


def build_side(cell, entries, sheet, side, lot2, row_h, fs):
    rows, spans = layout(entries, sheet, side, lot2)
    t = cell.add_table(rows=len(rows), cols=9)
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_borders(t, 4)
    set_cell_margins(t, 20)
    fix_layout(t, src.COL_W)

    heights = [16, 13, 17] + [row_h] * (len(rows) - 3)
    for tr, h in zip(t.rows, heights):
        tr.height = Pt(h)
        tr.height_rule = WD_ROW_HEIGHT_RULE.EXACTLY

    for r, line in enumerate(rows):
        for c, spec in enumerate(line):
            if spec is None:
                continue
            text, bold, extra = spec
            target = t.cell(r, c)
            if text == "LOGO":
                p = target.paragraphs[0]
                p.alignment = WD_ALIGN_PARAGRAPH.LEFT
                p.paragraph_format.left_indent = Pt(3)
                p.paragraph_format.space_before = p.paragraph_format.space_after = Pt(0)
                p.add_run().add_picture(str(HERE / "agappe-logo@8x.png"), width=Pt(66))
                target.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
                continue
            size = fs + 1.5 if r < 2 else (fs - 0.3 if r == 2 else fs)
            write(target, text, size, bold=bold, italic=extra == "italic")

    for r0, c0, r1, c1 in spans:
        t.cell(r0, c0).merge(t.cell(r1, c1))

    for r, line in enumerate(rows):
        for c, spec in enumerate(line):
            if spec and spec[2] in (RED_FILL, CHECK_FILL):
                set_fill(t.cell(r, c), spec[2])

    # The header's bottom rule is heavier on the printed sheet.
    for c in range(9):
        pr = t.cell(2, c)._tc.get_or_add_tcPr()
        if pr.find(qn("w:tcBorders")) is not None:
            continue
        b = OxmlElement("w:tcBorders")
        el = OxmlElement("w:bottom")
        el.set(qn("w:val"), "single")
        el.set(qn("w:sz"), "8")
        el.set(qn("w:color"), "000000")
        b.append(el)
        pr.append(b)
    # Drop the empty paragraph Word keeps after a nested table.
    p = cell.paragraphs[-1]
    if not p.text:
        p.paragraph_format.space_before = p.paragraph_format.space_after = Pt(0)
        p.paragraph_format.line_spacing_rule = WD_LINE_SPACING.EXACTLY
        p.paragraph_format.line_spacing = Pt(1)


def build(sheet, left, right, lot2):
    doc = Document()
    sec = doc.sections[0]
    sec.orientation = WD_ORIENT.LANDSCAPE
    sec.page_width, sec.page_height = Mm(PAGE_W), Mm(PAGE_H)
    for side in ("left_margin", "right_margin", "top_margin", "bottom_margin"):
        setattr(sec, side, Mm(MARGIN))
    sec.header_distance = sec.footer_distance = Mm(0)

    normal = doc.styles["Normal"]
    normal.font.name = "Calibri"
    normal.font.size = Pt(6)
    normal.paragraph_format.space_after = Pt(0)

    usable = PAGE_H / 25.4 * 72 - 2 * MARGIN / 25.4 * 72 - 16 - 13 - 17 - 12
    n = max(src.n_rows(left) + 1, src.n_rows(right))
    row_h = min(10.5, usable / n)
    fs = 6.4 if row_h < 10 else 6.8

    body = doc.element.body
    for p in list(body.iterchildren(qn("w:p"))):
        body.remove(p)

    outer = doc.add_table(rows=1, cols=3)
    set_borders(outer, 0)
    set_cell_margins(outer, 0)
    fix_layout(outer, [sum(src.COL_W), GAP, sum(src.COL_W)])
    lcell, _, rcell = outer.rows[0].cells
    for c in (lcell, rcell):
        c.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.TOP
        c._tc.remove(c.paragraphs[0]._p)
    build_side(lcell, left, sheet, "left", lot2, row_h, fs)
    build_side(rcell, right, sheet, "right", lot2, row_h, fs)

    tail = doc.add_paragraph()
    tail.paragraph_format.space_before = tail.paragraph_format.space_after = Pt(0)
    tail.paragraph_format.line_spacing_rule = WD_LINE_SPACING.EXACTLY
    tail.paragraph_format.line_spacing = Pt(1)
    schema_order(body)

    doc.core_properties.title = f"Agappe Qualicheck {sheet} — Lot {src.LOT} — Value Sheet"
    doc.core_properties.author = "Noble Diagnostic Centre"
    out = src.OUT_DIR / f"Qualicheck {sheet} Value Sheet - Lot {src.LOT}.docx"
    doc.save(out)
    return out


if __name__ == "__main__":
    for sheet, _prefix, left, right, lot2 in src.SHEETS:
        print(build(sheet, left, right, lot2).name)
