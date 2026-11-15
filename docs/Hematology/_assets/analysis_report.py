"""Shared Mindray BC-5380 Hematology Analysis Report renderer."""
from __future__ import annotations

import base64
import importlib.util
import io
import random
import subprocess
import tempfile
from datetime import date, datetime, timedelta
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from reportlab.lib.colors import Color, black
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

LJ_GEN = Path("/Users/jas/Work/NABL 2026/docs/instrument-readings/Mindray BC 5380/_assets/generate_lj_qc.py")
BRAND = Path("/Users/jas/Work/NABL 2026/app/public/brand")
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
PATIENTS = Path("/Users/jas/Work/NABL 2026/docs/Hematology/_parsed/patients.json")

_spec = importlib.util.spec_from_file_location("ljqc", LJ_GEN)
lj = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(lj)

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

REPORT_PARAMS = [
    "WBC", "Neu%", "Lym%", "Mon%", "Eos%", "Bas%",
    "Neu#", "Lym#", "Mon#", "Eos#", "Bas#",
    "RBC", "HGB", "HCT", "MCV", "MCH", "MCHC",
    "RDW-CV", "RDW-SD", "PLT", "MPV", "PDW", "PCT",
]

ADULT = {
    "WBC": (4.00, 10.00), "Neu%": (50.0, 70.0), "Lym%": (20.0, 40.0),
    "Mon%": (3.0, 12.0), "Eos%": (0.5, 5.0), "Bas%": (0.0, 1.0),
    "Neu#": (2.00, 7.00), "Lym#": (0.80, 4.00), "Mon#": (0.12, 1.20),
    "Eos#": (0.02, 0.50), "Bas#": (0.00, 0.10),
    "RBC": (3.50, 5.50), "HGB": (11.0, 16.0), "HCT": (37.0, 54.0),
    "MCV": (80.0, 100.0), "MCH": (27.0, 34.0), "MCHC": (32.0, 36.0),
    "RDW-CV": (11.0, 16.0), "RDW-SD": (35.0, 56.0),
    "PLT": (100.0, 300.0), "MPV": (6.5, 12.0), "PDW": (9.0, 17.0),
    "PCT": (0.108, 0.282),
}

REPORT_CSS = """
@page { size: A4; margin: 0; }
* { box-sizing: border-box; }
html, body {
  margin: 0; padding: 0;
  font-family: "Times New Roman", Times, serif;
  color: #000;
  font-size: 9.5pt;
  -webkit-print-color-adjust: exact;
  print-color-adjust: exact;
}
.page {
  width: 210mm;
  height: 297mm;
  padding: 10mm 12mm 8mm 12mm;
  page-break-after: always;
  position: relative;
  overflow: hidden;
}
.page:last-child { page-break-after: auto; }
.head {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  margin-bottom: 3mm;
}
.title {
  flex: 1;
  text-align: center;
  font-size: 16pt;
  font-weight: 700;
  letter-spacing: 0.2px;
}
.run {
  position: absolute;
  right: 12mm;
  top: 11mm;
  font-size: 9.5pt;
  white-space: nowrap;
}
.body { display: flex; align-items: flex-start; gap: 6mm; }
.params { width: 58%; border-collapse: collapse; table-layout: fixed; }
.params th {
  text-align: left; font-weight: 700;
  padding: 0 1.2mm 1.6mm 0; font-size: 9.5pt;
}
.params td {
  padding: 0.45mm 1.2mm 0.45mm 0;
  vertical-align: baseline; white-space: nowrap; height: 4.5mm;
}
.params .n { width: 20mm; }
.params .flag { width: 9mm; text-align: center; }
.params th.res, .params td.res { width: 38mm; padding-left: 2.5mm; }
.params sup { font-size: 7pt; line-height: 0; }
.meta { width: 42%; border-collapse: collapse; margin-top: 0; }
.meta td { padding: 0.55mm 0; vertical-align: baseline; height: 4.6mm; white-space: nowrap; }
.meta .lab { width: 32mm; padding-right: 3mm; }
.plots-wrap { display: flex; align-items: flex-start; gap: 3mm; margin-top: 5mm; }
.plots-label { font-size: 9.5pt; padding-top: 10mm; flex: 0 0 auto; }
.plots-body { flex: 1; min-width: 0; }
.plots img {
  width: 100%; max-height: 42mm; height: auto; display: block;
  object-fit: contain; object-position: left top;
}
.note { text-align: right; font-size: 8.5pt; margin-top: 1.5mm; }
"""


def parse_form_date(text: str) -> date:
    text = text.strip()
    for fmt in ("%d-%m-%Y", "%d/%m/%Y", "%d-%m-%y", "%d/%m/%y"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    raise ValueError(text)


def clock_add(run: tuple[int, int], mins: int) -> tuple[int, int]:
    t = datetime(2000, 1, 1, run[0], run[1]) + timedelta(minutes=mins)
    return t.hour, t.minute


def parse_hms(text: str) -> tuple[int, int, int]:
    parts = [int(x) for x in text.split(":")]
    return parts[0], parts[1], parts[2] if len(parts) > 2 else 0


def adult_flag(name: str, val: float) -> str:
    lo, hi = ADULT[name]
    if val < lo - 1e-9:
        return "L"
    if val > hi + 1e-9:
        return "H"
    return ""


def html_result(val: float, name: str) -> str:
    text = lj.fmt_result(val, name, lj.UNITS.get(name, ""))
    return text.replace("x10^3/uL", "x10<sup>3</sup>/uL").replace("x10^6/uL", "x10<sup>6</sup>/uL")


def complete_cbc(core: dict, seed: str) -> dict:
    rng = random.Random(seed)
    out = dict(core)
    wbc = float(out["WBC"])
    for pct, absn in (("Neu%", "Neu#"), ("Lym%", "Lym#"), ("Mon%", "Mon#"), ("Eos%", "Eos#"), ("Bas%", "Bas#")):
        out[absn] = wbc * float(out[pct]) / 100.0
    if "MPV" not in out:
        out["MPV"] = round(rng.uniform(9.8, 11.8), 1)
    if "PDW" not in out:
        out["PDW"] = round(rng.uniform(14.8, 16.4), 1)
    out["PCT"] = float(out["PLT"]) * float(out["MPV"]) / 10000.0
    if "RDW-SD" not in out:
        out["RDW-SD"] = float(out["MCV"]) * float(out["RDW-CV"]) / 100.0 * rng.uniform(4.05, 4.35)
    return out


def jitter_cbc(base: dict, seed: str, pct: float = 1.1) -> dict:
    rng = random.Random(seed)
    out = dict(base)
    skip = {"Neu#", "Lym#", "Mon#", "Eos#", "Bas#", "PCT"}
    for name, val in list(out.items()):
        if name in skip or name.startswith("GRAN"):
            continue
        if name in ("Neu%", "Lym%", "Mon%", "Eos%", "Bas%"):
            out[name] = max(0.0, val * (1.0 + rng.uniform(-pct, pct) / 100.0))
            continue
        if name == "PLT":
            delta = rng.choice([-2, -1, 1, 2, 3, -3])
            out[name] = max(1, int(round(val)) + delta)
            continue
        out[name] = val * (1.0 + rng.uniform(-pct, pct) / 100.0)
    total = sum(out[k] for k in ("Neu%", "Lym%", "Mon%", "Eos%", "Bas%"))
    if total > 0:
        for k in ("Neu%", "Lym%", "Mon%", "Eos%", "Bas%"):
            out[k] = out[k] / total * 100.0
    return complete_cbc(out, seed + "|abs")


def pin_mean(series: list[float], target: float) -> list[float]:
    m = sum(series) / len(series)
    if abs(m) < 1e-12:
        return series
    return [x * target / m for x in series]


def _label_font(size: int):
    path = Path("/System/Library/Fonts/Supplemental/Arial.ttf")
    if path.exists():
        return ImageFont.truetype(str(path), size)
    return ImageFont.load_default()


def scatter_to_bw(panel: Image.Image) -> Image.Image:
    arr = np.array(panel.convert("RGB"))
    r = arr[:, :, 0].astype(np.int16)
    g = arr[:, :, 1].astype(np.int16)
    b = arr[:, :, 2].astype(np.int16)
    chroma = np.maximum(np.maximum(np.abs(r - g), np.abs(r - b)), np.abs(g - b))
    out = np.full_like(arr, 255)
    dark = arr.min(axis=2) < 90
    out[dark & (chroma <= 22)] = (0, 0, 0)
    out[chroma > 22] = (18, 18, 18)
    return Image.fromarray(out)


def _hist_amps(n: int, axis_max: float, peaks, rng: random.Random, skew: float) -> np.ndarray:
    xs = np.linspace(0, axis_max, n)
    ys = np.zeros(n)
    for mu, sigma, amp in peaks:
        z = (xs - mu) / max(sigma, 0.4)
        if skew > 0:
            z = np.where(z > 0, z / (1.0 + skew), z)
        ys += amp * np.exp(-0.5 * z * z)
    ys *= 0.97 + rng.uniform(0.0, 0.04)
    peak = float(ys.max()) or 1.0
    return ys / peak


def draw_filled_hist(title, axis_max, ticks, peaks, rng, size, skew=0.0, discriminators=()):
    w, h = size
    img = Image.new("RGB", (w, h), (255, 255, 255))
    dr = ImageDraw.Draw(img)
    font = _label_font(16)
    title_font = _label_font(17)
    left, right, top, bottom = 36, w - 58, 26, h - 40
    dr.text((left + 2, 2), title, fill=(0, 0, 0), font=title_font)
    n = max(2, right - left)
    amps = _hist_amps(n + 1, axis_max, peaks, rng, skew)
    xs = np.linspace(0, 12, n + 1)
    amps = np.clip(amps * (1.0 + 0.035 * np.sin(xs * 3.7)), 0, 1)
    ink = (18, 18, 18)
    for i, amp in enumerate(amps):
        x = left + i
        y = int(round(bottom - amp * (bottom - top - 6)))
        y = max(top + 1, min(bottom - 1, y))
        dr.line([(x, y), (x, bottom - 1)], fill=ink)
    for gate in discriminators:
        x = left + int(round(gate / axis_max * n))
        for y in range(top + 2, bottom - 1, 6):
            dr.line([(x, y), (x, min(y + 3, bottom - 1))], fill=(80, 80, 80))
    dr.line([(left, top), (left, bottom)], fill=(0, 0, 0), width=2)
    dr.line([(left, bottom), (right, bottom)], fill=(0, 0, 0), width=2)
    for t in ticks:
        x = left + int(round(t / axis_max * n))
        dr.line([(x, bottom), (x, bottom + 5)], fill=(0, 0, 0), width=1)
        label = str(t)
        tw = dr.textlength(label, font=font)
        if t == ticks[-1]:
            tx = x - tw - 2
        elif t == ticks[0]:
            tx = x - 2
        else:
            tx = x - tw / 2
        dr.text((tx, bottom + 8), label, fill=(0, 0, 0), font=font)
    dr.text((right + 10, bottom + 8), "fL", fill=(0, 0, 0), font=font)
    return img


def wbc_peaks(level: str, results: dict, rng: random.Random):
    neu = float(results.get("Neu%", 55))
    lym = float(results.get("Lym%", 30))
    total = max(neu + lym, 1.0)
    high = 0.10 if level == "High" else 0.04
    return [
        (22.0, 7.0, 0.14 + rng.uniform(-0.02, 0.02)),
        (58.0, 11.0, lym / total),
        (94.0, 15.0, neu / total),
        (165.0, 28.0, high),
    ]


def make_report_plots_png(level: str, results: dict, rng: random.Random) -> str:
    if level not in lj.TEMPLATES:
        level = "Normal"
    tpl = lj.TEMPLATES[level]
    base = tpl["img"].copy()
    tw, th = base.size
    pw = tw // 4
    scatter = lj._jitter_scatter(base.crop((0, 0, pw, th)), rng, amount=1)
    scatter = scatter_to_bw(scatter)
    target_h = 310
    sw = max(1, int(round(scatter.size[0] * target_h / scatter.size[1])))
    scatter = scatter.resize((sw, target_h), Image.Resampling.LANCZOS)
    hist_size = (380, 310)
    wbc = draw_filled_hist(
        "WBC(BASO)", 400.0, [0, 100, 200, 400],
        wbc_peaks(level, results, rng), rng, hist_size, discriminators=(35.0, 90.0),
    )
    rbc = draw_filled_hist(
        "RBC", 200.0, [0, 100, 200],
        [(float(results["MCV"]), 13.0 + rng.uniform(-1.0, 1.0), 1.0)], rng, hist_size,
    )
    mpv = float(results["MPV"])
    plt = draw_filled_hist(
        "PLT", 30.0, [0, 10, 20, 30],
        [(mpv, 2.5 + rng.uniform(-0.2, 0.2), 1.0), (min(26.0, mpv + 9.0), 4.8, 0.22)],
        rng, hist_size, skew=1.85,
    )
    panels = [scatter, wbc, rbc, plt]
    max_h = max(p.size[1] for p in panels)
    gutter, pad_x, pad_y = 18, 8, 6
    inner_w = sum(p.size[0] for p in panels) + gutter * 3
    strip = Image.new("RGB", (inner_w + 2 * pad_x, max_h + 2 * pad_y), (255, 255, 255))
    x = pad_x
    for i, p in enumerate(panels):
        strip.paste(p, (x, pad_y + (max_h - p.size[1]) // 2))
        x += p.size[0] + (gutter if i < 3 else 0)
    buf = io.BytesIO()
    strip.save(buf, format="PNG", optimize=True)
    return base64.b64encode(buf.getvalue()).decode()


def report_html(
    d: date,
    sample_id: str,
    results: dict,
    run: tuple[int, int],
    prn: tuple[int, int, int],
    plots_b64: str,
    patient: dict | None = None,
    draw: str = "",
) -> str:
    rh, rm = run
    ph, pm, ps = prn
    run_s = f"{d.strftime('%d-%m-%Y')} {rh:02d}:{rm:02d}"
    print_s = f"{d.strftime('%d-%m-%Y')} {ph:02d}:{pm:02d}:{ps:02d}"
    rows = []
    for name in REPORT_PARAMS:
        val = results[name]
        lo, hi = ADULT[name]
        flag = adult_flag(name, val)
        res = html_result(val, name)
        rng = lj.fmt_range(lo, hi, name)
        rows.append(
            f"<tr><td class='n'>{name}</td><td class='flag'>{flag}</td>"
            f"<td class='res'>{res}</td><td>{rng}</td></tr>"
        )
    # Same label list as the analyser print. Values stay blank unless the
    # print itself carries them. Patient name, ID and draw time are not filled.
    meta = [
        ("Sample ID:", sample_id),
        ("Mode:", "WB CBC+DIFF"),
        ("Last Name:", ""),
        ("First Name:", ""),
        ("Gender:", ""),
        ("Age:", ""),
        ("Birthday:", ""),
        ("Patient ID:", ""),
        ("Dept.:", ""),
        ("Bed No.:", ""),
        ("Deliverer:", ""),
        ("Operator:", "Service Engineer"),
        ("Validator:", ""),
        ("Diagnosis:", ""),
        ("Draw Time:", ""),
        ("Delivery Time:", ""),
        ("Print Time:", print_s),
    ]
    meta_html = "".join(f"<tr><td class='lab'>{lab}</td><td>{val}</td></tr>" for lab, val in meta)
    return f"""
<section class="page">
  <div class="head"><div class="title">Hematology Analysis Report</div></div>
  <div class="run">Run Time:&nbsp;&nbsp;{run_s}</div>
  <div class="body">
    <table class="params">
      <tr><th class='n'>Parameter</th><th class='flag'></th><th class='res'>Result Unit</th><th>Ref Range</th></tr>
      {''.join(rows)}
    </table>
    <table class="meta">{meta_html}</table>
  </div>
  <div class="plots-wrap">
    <div class="plots-label">Remarks:</div>
    <div class="plots-body">
      <div class="plots"><img src="data:image/png;base64,{plots_b64}" alt="plots"/></div>
      <div class="note">*This result applies to this sample only</div>
    </div>
  </div>
</section>
"""


def html_to_pdf(html: str, dest: Path) -> None:
    with tempfile.TemporaryDirectory() as td:
        hp = Path(td) / "r.html"
        hp.write_text(html, encoding="utf-8")
        tp = Path(td) / "o.pdf"
        proc = subprocess.run(
            [
                CHROME, "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
                f"--print-to-pdf={tp}", f"file://{hp}",
            ],
            capture_output=True,
            text=True,
        )
        if proc.returncode or not tp.exists():
            raise RuntimeError(proc.stderr[-800:] if proc.stderr else "chrome failed")
        dest.write_bytes(tp.read_bytes())


def render_pages(pages: list[str], dest: Path) -> None:
    html = (
        "<!DOCTYPE html><html><head><meta charset='utf-8'/>"
        f"<style>{REPORT_CSS}</style></head><body>{''.join(pages)}</body></html>"
    )
    html_to_pdf(html, dest)


def draw_ndc_footer(c, left: float, right: float, page_label: str) -> None:
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
    c.drawString(mid + 6, fy + 37, page_label)
    meta_w = (mid - left) / 4
    metas = ["Issue No. IV", "Issue Date: 01 04 2024", "Rev No. 00", "Revision Date: --"]
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
