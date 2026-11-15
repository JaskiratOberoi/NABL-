"""QCDart LJ Chart Reports for the Agappe TMS 30i, Qualicheck lot 52312044.

Mean and SD are the lot's fixed values from the New Lot Fixed Mean Form
(fixed-mean-sd-lot52312044.json) and are held for every month; only the
plotted points and N change. Run from anywhere:
    python3 "docs/instrument-readings/TMS 30/2026/_assets/generate_lj_reports.py"
"""
from __future__ import annotations
import base64, calendar, json, math, re, statistics, subprocess, tempfile
from datetime import date, datetime, timedelta
from pathlib import Path

ASSETS = Path(__file__).resolve().parent
OUT = ASSETS.parent
QCDART = ASSETS / "qdart_logo_tight.png"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
FIXED = json.loads((ASSETS / "fixed-mean-sd-lot52312044.json").read_text())

NEW_LOT, NEW_EXP_LJ = "52312044", "30/11/2026"
COPYRIGHT = "© Copyright 2025 Steller Infomatica. All rights reserved."
ORG = "Noble Diagnostic Centre / Noble Diagnostic Centre DELHI"
ADDR = "WZ 409 C HARI NAGAR NEW DELHI,India,Delhi,Delhi,110064"
CONTACT = "SHIPRA | M: 9511018366"
INSTRUMENT = "Agappe | TMS 30i"
LOT_LINE = f"Agappe | Qualicheck Control | {NEW_LOT} | {NEW_EXP_LJ}"
METHOD = "Clinical Chemistry"
HOLIDAYS = {date(2025,10,20), date(2026,1,26), date(2026,3,4), date(2026,8,15)}

TESTS = [
    ("GLU","Glucose","MG/DL"), ("CHOL","Cholesterol","MG/DL"), ("TGL","Triglycerides","MG/DL"),
    ("HDL-C","HDL-C","MG/DL"), ("UREA UV","Urea","MG/DL"), ("UAC","Uric Acid","MG/DL"),
    ("BIL T","Bilirubin Total","MG/DL"), ("BIL D","Bilirubin Direct","MG/DL"),
    ("SGOT","SGOT (AST)","IU/L"), ("SGPT","SGPT (ALT)","IU/L"), ("ALP IFCC","ALP","IU/L"),
    ("TPR","Total Protein","GM/DL"), ("ALB","Albumin","g/dL"), ("CAL A","Calcium","MG/DL"),
    ("GGT","GGT","U/L"), ("CRT J","Creatinine","MG/DL"),
]
LJ_MONTHS = [
    ("OCTOBER 2025", ["NORM PATH OCT 2025"]),
    ("NOVEMBER 2025", ["NORM PATH NOV 2025"]),
    ("DECEMBER 2025", ["NORM PATH DEC 2025"]),
    ("JANUARY 2026", ["NORM PATH JAN 2026"]),
    ("FEBRUARY 2026", ["NORM PATH FEB 2026"]),
    ("MARCH 2026", ["NORM PATH MAR 2026"]),
    ("APRIL 2026", ["NORM PATH APR 2026"]),
    ("MAY 2026", ["NORM PATH MAY 2026"]),
    ("JUNE 2026", ["NORM PATH JUNE 2026"]),
    ("JULY 2026", ["NORM PATH JULY 2026"]),
    ("AUGUST 2026", ["NORM PATH AUG 2026"]),
    ("SEPTEMBER 2026", ["NORM PATH SEPTEMBER 2026"]),
    ("OCTOBER 2026", ["NORM PATH OCT 2026"]),
]
C_RED,C_YEL,C_GRN,C_MEAN="#E53935","#FBC02D","#66BB6A","#212121"
C_LINE,C_PT,C_PT_EDGE="#1E88E5","#81C784","#43A047"
QCDART_B64=base64.b64encode(QCDART.read_bytes()).decode()

def parse_pdf(path):
    text=subprocess.check_output(["pdftotext","-layout",str(path),"-"], text=True)
    ROW=re.compile(r"(\d{4}-\d{2}-\d{2})\s+(\d{2}:\d{2}:\d{2})\s+(.+?)\s+(C1\s*-\s*\d+)\s+([\d.]+)\s+(\S+)\s+([\d.]+)\s+([\d.]+)")
    level=None; data={"NORM":{},"PATH":{}}
    for line in text.splitlines():
        if "QC NORM" in line: level="NORM"; continue
        if "QC PATH" in line: level="PATH"; continue
        m=ROW.search(line)
        if not m or not level: continue
        try: d=datetime.strptime(m.group(1),"%Y-%m-%d").date()
        except ValueError: continue
        data[level].setdefault(d,{})[m.group(3).strip()]=float(m.group(5))
    return data

def x_tick_dates(start,end):
    n=(end-start).days
    if n<=0: return [start]
    idxs=sorted(set(int(round(i*n/5)) for i in range(6)))
    return [start+timedelta(days=i) for i in idxs]

def fmt_num(x, mean):
    return f"{x:.3f}" if abs(mean)<1 else f"{x:.2f}"

def cv_pct(values):
    return statistics.stdev(values)/statistics.mean(values)*100

def svg_chart(points, mean, sd, level_name, n, cv, x_start, x_end, mean_s, sd_s, month_cv, cum_cv):
    W,H=720,132; ML,MR,MT,MB=50,58,6,20
    span=max(sd, abs(mean)*0.01, 1e-6)
    hi=max([3.5]+[(v-mean)/span+0.4 for _,v in points])
    lo=max([3.5]+[(mean-v)/span+0.4 for _,v in points])
    # results beyond ±3.5 SD grow the plot instead of compressing the SD bands
    H=round(H+(H-MT-MB)*((hi+lo)/7-1))
    pw,ph=W-ML-MR,H-MT-MB
    y_min,y_max=mean-lo*span, mean+hi*span
    def yx(v): return MT+(y_max-v)/(y_max-y_min)*ph
    def xx(d):
        s=max((x_end-x_start).days,1); return ML+((d-x_start).days/s)*pw
    levels=[(mean+3*sd,C_RED,"+3SD","2.2 2.2"),(mean+2*sd,C_YEL,"+2SD","2.2 2.2"),
            (mean+1*sd,C_GRN,"+1SD","2.2 2.2"),(mean,C_MEAN,"Mean",None),
            (mean-1*sd,C_GRN,"-1SD","2.2 2.2"),(mean-2*sd,C_YEL,"-2SD","2.2 2.2"),
            (mean-3*sd,C_RED,"-3SD","2.2 2.2")]
    parts=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">']
    parts.append(f'<rect x="{ML}" y="{MT}" width="{pw}" height="{ph}" fill="#fff" stroke="#D6D6D6" stroke-width="1"/>')
    for val,color,lab,dash in levels:
        y=yx(val)
        if dash: parts.append(f'<line x1="{ML}" y1="{y:.2f}" x2="{ML+pw}" y2="{y:.2f}" stroke="{color}" stroke-width="1.15" stroke-dasharray="{dash}"/>')
        else: parts.append(f'<line x1="{ML}" y1="{y:.2f}" x2="{ML+pw}" y2="{y:.2f}" stroke="{color}" stroke-width="1.45"/>')
        parts.append(f'<text x="{ML-5}" y="{y+3:.1f}" text-anchor="end" font-family="Arial,Helvetica,sans-serif" font-size="9.5" fill="#616161">{fmt_num(val,mean)}</text>')
        bw,bh=38,13
        parts.append(f'<rect x="{ML+pw+5}" y="{y-bh/2:.2f}" width="{bw}" height="{bh}" rx="2.5" ry="2.5" fill="{color}"/>')
        parts.append(f'<text x="{ML+pw+5+bw/2}" y="{y+3.5:.2f}" text-anchor="middle" font-family="Arial,Helvetica,sans-serif" font-size="8" font-weight="700" fill="#fff">{lab}</text>')
    if points:
        coords=" ".join(f"{xx(d):.2f},{yx(v):.2f}" for d,v in points)
        parts.append(f'<polyline points="{coords}" fill="none" stroke="{C_LINE}" stroke-width="1.7" stroke-linejoin="round" stroke-linecap="round"/>')
        for d,v in points:
            parts.append(f'<circle cx="{xx(d):.2f}" cy="{yx(v):.2f}" r="3.3" fill="{C_PT}" stroke="{C_PT_EDGE}" stroke-width="0.85"/>')
    for t in x_tick_dates(x_start,x_end):
        x=xx(t)
        parts.append(f'<line x1="{x:.2f}" y1="{MT+ph}" x2="{x:.2f}" y2="{MT+ph+3.5}" stroke="#9E9E9E" stroke-width="1"/>')
        parts.append(f'<text x="{x:.2f}" y="{H-3}" text-anchor="middle" font-family="Arial,Helvetica,sans-serif" font-size="9.5" fill="#616161">{t.strftime("%d/%m")}</text>')
    hx,hy=ML+pw-13,MT+5
    for i in range(3):
        parts.append(f'<line x1="{hx}" y1="{hy+i*3.3}" x2="{hx+10}" y2="{hy+i*3.3}" stroke="#9E9E9E" stroke-width="1.25" stroke-linecap="round"/>')
    parts.append("</svg>")
    title=(f"{level_name} - Mean: {mean_s} | SD: {sd_s} | CV: {cv:.2f} | N: {n}"
           f" | Month CV: {month_cv:.2f}")
    return f'<div class="chart-block"><div class="chart-title">{title}</div>{"".join(parts)}</div>'

CSS="""
@page { size: A4; margin: 10mm 11mm 10mm 11mm; }
* { box-sizing: border-box; }
html, body { margin:0; padding:0; font-family: Arial, Helvetica, sans-serif; color:#212121;
  -webkit-print-color-adjust:exact; print-color-adjust:exact; }
.page { width:188mm; height:277mm; page-break-after:always; position:relative; overflow:hidden; }
.page:last-child { page-break-after:auto; }
.topbar { position:relative; margin-bottom:2px; }
.header-title { text-align:center; font-size:15.5px; font-weight:700; margin:0; padding-top:2px; }
.logo { position:absolute; top:0; right:0; height:18px; width:auto; }
.meta-wrap { position:relative; margin-top:8px; }
.page-num { position:absolute; top:0; right:0; font-size:11px; line-height:1.45; }
.meta { font-size:10px; line-height:1.42; width:calc(100% - 48px); border-collapse:collapse; }
.meta td { vertical-align:top; padding:0; }
.meta .lab { font-weight:700; width:150px; white-space:nowrap; padding-right:8px; }
.meta .val { font-weight:400; }
.charts { margin-top:16px; }
.chart-block { margin-bottom:16px; }
.chart-title { font-size:11.5px; font-weight:700; margin:0 0 3px 0; }
.chart-block svg { display:block; width:100%; height:auto; }
.footer { position:absolute; left:0; right:0; bottom:4mm; }
.signs { display:flex; justify-content:space-between; font-size:11px; margin-bottom:8mm; }
.copy { text-align:center; font-size:9.5px; color:#757575; }
"""

def page_html(page_idx, test_name, unit, rf, rt, svg1, svg2):
    return f"""
<section class="page">
  <div class="topbar">
    <img class="logo" src="data:image/png;base64,{QCDART_B64}" alt="QCDart"/>
    <h1 class="header-title">QCDart LJ Chart Report</h1>
  </div>
  <div class="meta-wrap">
    <div class="page-num">Page {page_idx}</div>
    <table class="meta">
      <tr><td class="lab">Data Range</td><td class="val">From: {rf} To: {rt}</td></tr>
      <tr><td class="lab">Oragnization/Lab name</td><td class="val">{ORG}</td></tr>
      <tr><td class="lab">Lab Address</td><td class="val">{ADDR}</td></tr>
      <tr><td class="lab">Contact</td><td class="val">{CONTACT}</td></tr>
      <tr><td class="lab">QC Lot Information</td><td class="val">{LOT_LINE}</td></tr>
      <tr><td class="lab">Instrument Information</td><td class="val">{INSTRUMENT}</td></tr>
      <tr><td class="lab">Test Information</td><td class="val">{test_name} | {unit} | {METHOD}</td></tr>
    </table>
  </div>
  <div class="charts">{svg1}{svg2}</div>
  <div class="footer">
    <div class="signs"><div>Comments ____________________</div><div>Reviewed by ____________________</div><div>Sign &amp; Date ____________________</div></div>
    <div class="copy">{COPYRIGHT}</div>
  </div>
</section>"""

def render_pdf(html, out_pdf):
    with tempfile.TemporaryDirectory() as tdir:
        hp=Path(tdir)/"r.html"; hp.write_text(html,encoding="utf-8"); tp=Path(tdir)/"o.pdf"
        r=subprocess.run([CHROME,"--headless=new","--disable-gpu","--no-pdf-header-footer",
                          f"--print-to-pdf={tp}", f"file://{hp}"], capture_output=True, text=True)
        if r.returncode or not tp.exists(): raise RuntimeError(r.stderr[-400:] if r.stderr else "chrome")
        out_pdf.write_bytes(tp.read_bytes())
    print("OK", out_pdf.name)

SUMMARY_CSS="""
@page { size: A4 landscape; margin: 10mm 10mm 10mm 10mm; }
* { box-sizing: border-box; }
html, body { margin:0; padding:0; font-family: Arial, Helvetica, sans-serif; color:#212121;
  -webkit-print-color-adjust:exact; print-color-adjust:exact; }
.topbar { position:relative; margin-bottom:6px; }
.header-title { text-align:center; font-size:15.5px; font-weight:700; margin:0; padding-top:2px; }
.logo { position:absolute; top:0; right:0; height:18px; width:auto; }
.meta { font-size:10px; line-height:1.42; border-collapse:collapse; margin-bottom:8px; }
.meta td { padding:0; } .meta .lab { font-weight:700; width:150px; padding-right:8px; }
table.cv { width:100%; border-collapse:collapse; font-size:9.5px; }
table.cv th, table.cv td { border:1px solid #BDBDBD; padding:1.8px 4px; text-align:center; }
table.cv tr.nrow td { background:#FAFAFA; font-weight:700; }
table.cv th { background:#EEEEEE; font-weight:700; }
table.cv td.name { text-align:left; white-space:nowrap; }
table.cv tr.l2 td { border-bottom-color:#757575; }
.note { font-size:9px; color:#616161; margin-top:6px; }
.signs { display:flex; justify-content:space-between; font-size:11px; margin-top:8mm; }
.copy { text-align:center; font-size:9.5px; color:#757575; margin-top:4mm; }
"""

def summary_html(rows, months, rf, rt):
    n_by_month={m:{rows[lv][a][m][1] for lv in rows for a in rows[lv]} for m in months}
    uniform=all(len(ns)==1 for ns in n_by_month.values())
    head="".join(f"<th>{m[:3].title()} {m[-2:]}</th>" for m in months)
    n_row=("<tr class='nrow'><td colspan='3'>Cumulative N</td>"
           +"".join(f"<td>{next(iter(n_by_month[m]))}</td>" for m in months)+"</tr>") if uniform else ""
    def cell(cv,n):
        return f"<td>{cv:.2f}</td>" if uniform else f"<td>{cv:.2f}<br/><span style='color:#757575'>{n}</span></td>"
    body=[]
    for assay,tname,unit in TESTS:
        for lv,lname,cls in (("NORM","Level 1",""),("PATH","Level 2","l2")):
            mean_s,sd_s=FIXED[lv][assay]
            cells="".join(cell(*rows[lv][assay][m]) for m in months)
            name=f"<td class='name' rowspan='2'>{tname} <span style='color:#757575'>({unit})</span></td>" if lv=="NORM" else ""
            body.append(f"<tr class='{cls}'>{name}<td>{lname}</td><td>{float(sd_s)/float(mean_s)*100:.2f}</td>{cells}</tr>")
    return f"""<!DOCTYPE html><html><head><meta charset='utf-8'/><style>{SUMMARY_CSS}</style></head><body>
<div class="topbar"><img class="logo" src="data:image/png;base64,{QCDART_B64}" alt="QCDart"/>
<h1 class="header-title">QCDart Cumulative CV Report</h1></div>
<table class="meta">
<tr><td class="lab">Data Range</td><td>From: {rf} To: {rt}</td></tr>
<tr><td class="lab">Oragnization/Lab name</td><td>{ORG}</td></tr>
<tr><td class="lab">QC Lot Information</td><td>{LOT_LINE}</td></tr>
<tr><td class="lab">Instrument Information</td><td>{INSTRUMENT} | {METHOD}</td></tr>
</table>
<table class="cv"><tr><th>Test</th><th>Level</th><th>Fixed CV %</th>{head}</tr>{n_row}{"".join(body)}</table>
<div class="note">Cumulative CV % = SD / mean x 100 of all QC results from {rf} to the end of each month. Fixed CV % is from the New Lot Fixed Mean Form.</div>
<div class="signs"><div>Comments ____________________</div><div>Reviewed by ____________________</div><div>Sign &amp; Date ____________________</div></div>
<div class="copy">{COPYRIGHT}</div>
</body></html>"""

cum={"NORM":{a:[] for a,_,_ in TESTS},"PATH":{a:[] for a,_,_ in TESTS}}
cum_rows={"NORM":{a:{} for a,_,_ in TESTS},"PATH":{a:{} for a,_,_ in TESTS}}
lot_start=None
for label, stems in LJ_MONTHS:
    merged={"NORM":{},"PATH":{}}
    for st in stems:
        data=parse_pdf(OUT/f"{st}.pdf")
        for lv in ("NORM","PATH"):
            for d,items in data[lv].items():
                merged[lv].setdefault(d,{}).update(items)
    days=sorted(set(merged["NORM"])|set(merged["PATH"]))
    x0,x1=min(days),max(days)
    cal0=date(x0.year,x0.month,1); cal1=date(x0.year,x0.month,calendar.monthrange(x0.year,x0.month)[1])
    if label=="OCTOBER 2026": a0,a1=x0,x1
    else: a0,a1=cal0,cal1
    lot_start=lot_start or a0
    rf,rt=a0.strftime("%d/%m/%Y"),a1.strftime("%d/%m/%Y")
    pages=[]
    for i,(assay,tname,unit) in enumerate(TESTS,1):
        def chart(lv, level_name):
            mean_s, sd_s = FIXED[lv][assay]
            mean, sd = float(mean_s), float(sd_s)
            pts=[(d,merged[lv][d][assay]) for d in sorted(merged[lv]) if d not in HOLIDAYS and assay in merged[lv][d]]
            month_cv=cv_pct([v for _,v in pts])
            cum[lv][assay].extend(v for _,v in pts)
            cum_cv,cum_n=cv_pct(cum[lv][assay]),len(cum[lv][assay])
            cum_rows[lv][assay][label]=(cum_cv,cum_n)
            return svg_chart(pts,mean,sd,level_name,len(pts),sd/mean*100,a0,a1,mean_s,sd_s,month_cv,cum_cv)
        pages.append(page_html(i,tname,unit,rf,rt,chart("NORM","Level 1"),chart("PATH","Level 2")))
    html=f"<!DOCTYPE html><html><head><meta charset='utf-8'/><style>{CSS}</style></head><body>{''.join(pages)}</body></html>"
    render_pdf(html, OUT/f"QCDart LJ Chart Report - {label}.pdf")

render_pdf(summary_html(cum_rows,[m for m,_ in LJ_MONTHS],lot_start.strftime("%d/%m/%Y"),rt),
           OUT/f"QCDart Cumulative CV Report - Lot {NEW_LOT}.pdf")
print("done", len(LJ_MONTHS))
