"""Typeset softcopy of the Agappe Qualicheck NORM / PATH value sheets.

Values prefixed with "?" could not be identified from the photographed
sheets. They are printed as red query labels (N-xx / P-xx) and listed, with
the candidate readings, in the companion query sheet. Values prefixed with "~"
were read from a blurred print and close arithmetically (target ± 2SD) but
should be checked against the insert; they print on a yellow fill. Replace
"?<guess>" or "~<value>" with the confirmed value and re-run.

build_qualicheck_docx.py produces editable Word copies from the same data.
"""

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

HERE = Path(__file__).resolve().parent
OUT_DIR = HERE.parent
LOT = "52312044"
EXPIRY = "11/2026"

FONTS = Path("/Applications/Microsoft Word.app/Contents/Resources/DFonts")
pdfmetrics.registerFont(TTFont("Cal", str(FONTS / "Calibri.ttf")))
pdfmetrics.registerFont(TTFont("Cal-B", str(FONTS / "Calibrib.ttf")))

RED = colors.HexColor("#C00000")
RED_BG = colors.HexColor("#FDE9E9")
CHECK_BG = colors.HexColor("#FFF2B3")
GRID = colors.HexColor("#404040")

# --------------------------------------------------------------------------
# Data. Row = (analyser, unit, target, lower, higher, 2SD).
# analyser / unit of None = merged with the cell above (within the analyte).
# --------------------------------------------------------------------------
U = None

NORM_LEFT = [
    (1, "Albumin", [("Bromocresol Green", [
        ("FAA", "g/dL", "3.70", "3.10", "4.30", "0.60"),
        (U, "g/L", "37.00", "31.00", "43.00", "6.00"),
        ("SA", "g/dL", "3.40", "2.90", "3.90", "0.50")])]),
    (2, "Alkaline phosphatase", [
        ("p-Nitrophenyl phosphate DEA/DGKC", [
            ("FAA", "U/L", "194.00", "156.00", "232.00", "38.00"),
            ("SA", U, "208.90", "153.90", "263.90", "55.00")]),
        ("IFCC", [
            ("FAA", U, "137.20", "111.20", "163.20", "26.00"),
            ("SA", U, "116.00", "92.00", "140.00", "24.00")])]),
    (3, "ALT/SGPT", [("IFCC without PSP", [
        ("FAA", "U/L", "35.10", "28.10", "42.10", "7.00"),
        ("SA", U, "34.50", "27.50", "41.50", "7.00")])]),
    (4, "Amylase", [("CNPG3", [
        ("FAA", "U/L", "80.30", "62.30", "98.30", "18.00"),
        ("SA", U, "90", "70.00", "110.00", "20.00")])]),
    (5, "AST/SGOT", [("IFCC without PSP", [
        ("FAA", "U/L", "32.50", "26.00", "39.00", "6.50"),
        ("SA", U, "35.40", "26.90", "43.90", "8.50")])]),
    (6, "Bilirubin Total", [
        ("DMSO", [("SA", "mg/dL", "0.95", "0.60", "1.30", "0.35")]),
        ("TAB", [
            ("SA", U, "0.95", "0.60", "1.30", "0.35"),
            ("FAA", U, "0.85", "0.55", "1.15", "0.30")])]),
    (7, "Bilirubin Direct", [
        ("Diazo", [("SA", "mg/dL", "0.60", "0.42", "0.78", "0.18")]),
        ("Diazo Modified", [("FAA", U, "0.40", "0.25", "0.55", "0.15")])]),
    (8, "Calcium", [
        ("O-Cresolphthalein Complex", [
            ("SA", "mg/dL", "8.40", "7.40", "9.40", "1.00"),
            (U, "mmol/L", "2.10", "1.85", "2.35", "0.25")]),
        ("Arsenazo-III", [
            ("FAA", "mg/dL", "8.80", "7.70", "9.90", "1.10"),
            (U, "mmol/L", "2.20", "1.93", "2.48", "0.28"),
            ("SA", "mg/dL", "8.40", "7.20", "9.60", "1.20")])]),
    (9, "Cholinesterase", [("Butyrylthiocholine", [
        ("SA", "U/L", "6585.00", "5435.00", "7735.00", "1150.00"),
        ("FAA", U, "7305.00", "6295.00", "8315.00", "1010.00")])]),
    (10, "Cholesterol", [
        ("CHOD-PAP (Lypho)", [("SA", "mg/dL", "181.00", "146.00", "216.00", "35.00")]),
        ("CHOD-PAP (SL)", [
            ("SA", U, "181.90", "146.40", "217.40", "35.50"),
            ("FAA", "mg/dL", "163.00", "133.00", "193.00", "30.00"),
            (U, "mmol/L", "4.20", "3.43", "4.97", "0.77")])]),
    (11, "CKNAC", [("DGKCH/IVKC/SEQC/IFCC", [
        ("SA", "U/L", "128.40", "98.40", "158.40", "30.00"),
        ("FAA", U, "147.00", "119.00", "175.00", "28.00")])]),
    (12, "Creatinine", [
        ("Jaffe without Deproteinization", [
            ("SA", "mg/dL", "0.94", "0.59", "1.29", "0.35"),
            ("FAA", "mg/dL", "1.05", "0.75", "1.35", "0.30"),
            (U, "µmol/L", "92.82", "66.30", "119.34", "26.52")]),
        ("Enzymatic", [
            ("FAA", "mg/dL", "0.95", "0.70", "1.20", "0.25"),
            ("SA", U, "1.30", "0.92", "1.68", "0.38")])]),
    (13, "CKMB", [("Immuno-inhibition method", [
        ("FAA/SA", "U/L", "8.50", "4.50", "12.50", "4.00")])]),
    (14, "Gamma GT", [("Szasz method", [
        ("SA", "U/L", "27.50", "21.00", "34.00", "6.50"),
        ("FAA", U, "35.10", "27.10", "43.10", "8.00")])]),
    (15, "Glucose", [
        ("GOD-PAP", [
            ("SA", "mg/dL", "96.00", "82.00", "110.00", "14.00"),
            ("FAA", "mg/dL", "95.00", "82.00", "108.00", "13.00"),
            (U, "mmol/L", "5.30", "4.58", "6.02", "0.72")]),
        ("Hexokinase", [
            ("FAA", "mg/dL", "93.80", "81.30", "106.30", "12.50"),
            (U, "mmol/L", "5.20", "4.51", "5.89", "0.69")])]),
]

NORM_RIGHT = [
    (16, "LDH-P", [("SFBC/SEQC", [
        ("SA", "U/L", "352.00", "282.00", "422.00", "70.00"),
        ("FAA", U, "385.00", "320.00", "450.00", "65.00")])]),
    (17, "Lipase", [("Enzymatic Colorimetric Test", [
        ("SA", "U/L", "39.00", "27.00", "51.00", "12.00"),
        ("FAA", U, "43.70", "32.70", "54.70", "11.00")])]),
    (18, "Magnesium", [("Xylidyl Blue with ATCS", [
        ("SA", "mg/dL", "2.10", "1.65", "2.55", "0.45"),
        ("FAA", "mg/dL", "1.95", "1.55", "2.35", "0.40"),
        (U, "mmol/L", "0.80", "0.64", "0.97", "0.16")])]),
    (19, "Phosphorous", [("Molybdate UV", [
        ("SA", "mg/dL", "3.60", "2.85", "4.35", "0.75"),
        ("FAA", "mg/dL", "3.50", "2.78", "4.22", "0.72"),
        (U, "mmol/L", "1.12", "0.89", "1.35", "0.23")])]),
    (20, "Triglycerides", [("GPO-PAP", [
        ("SA", "mg/dL", "122.80", "97.80", "147.80", "25.00"),
        ("FAA", "mg/dL", "124.50", "102.50", "146.50", "22.00"),
        (U, "mmol/L", "1.40", "1.16", "1.64", "0.24")])]),
    (21, "Total Protein", [("Biuret", [
        ("SA", "g/dL", "5.80", "4.85", "6.75", "0.95"),
        ("FAA", "g/dL", "5.80", "4.85", "6.75", "0.95"),
        (U, "g/L", "58.00", "48.50", "67.50", "9.50")])]),
    (22, "Uric Acid", [
        ("Uricase-PAP (Lypho)", [
            ("SA", "mg/dL", "5.60", "4.70", "6.50", "0.90"),
            (U, "µmol/L", "333.10", "279.57", "386.63", "53.53")]),
        ("Uricase-PAP (S.L)", [
            ("SA", "mg/dL", "5.25", "4.35", "6.15", "0.90"),
            (U, "µmol/L", "312.20", "258.67", "365.73", "53.53"),
            ("FAA", "mg/dL", "5.05", "4.10", "6.00", "0.95"),
            (U, "µmol/L", "300.30", "243.79", "356.81", "56.51")])]),
    (23, "Urea", [
        ("Urease UV", [
            ("SA", "mg/dL", "31.60", "23.10", "40.10", "8.50"),
            ("FAA", "mg/dL", "30.00", "22.00", "38.00", "8.00"),
            (U, "mmol/L", "4.99", "3.66", "6.32", "1.33")]),
        ("Urease Berthelot", [
            ("SA", "mg/dL", "29.70", "21.70", "37.70", "8.00"),
            (U, "mmol/L", "4.94", "3.61", "6.27", "1.33")])]),
    (24, "Chloride", [
        ("Thiocyanate", [("FAA/SA", "mmol/L", "95.51", "81.51", "109.51", "14.00")]),
        ("Direct I.S.E", [("I-SMART", U, "100.30", "84.30", "116.30", "16.00")]),
        ("Indirect I.S.E", [("TBA", U, "101.10", "84.10", "118.10", "17.00")])]),
    (25, "Sodium", [
        ("Direct I.S.E", [("I-SMART", "mmol/L", "115.00", "97.00", "133.00", "18.00")]),
        ("Indirect I.S.E", [("TBA", U, "108.6", "92.50", "121.50", "15.00")])]),
    (26, "Potassium", [
        ("Direct I.S.E", [("I-SMART", "mmol/L", "4.50", "3.60", "5.40", "0.90")]),
        ("Indirect I.S.E", [("TBA", U, "4.15", "3.35", "4.95", "0.80")])]),
    (27, "HDL Cholesterol", [
        ("Precipitation Method", [("SA", "mg/dL", "48.10", "39.10", "57.10", "9.00")]),
        ("Selective Inhibition Method", [
            ("SA", U, "46.40", "37.10", "55.70", "9.30"),
            ("FAA", "mg/dL", "40.00", "32.00", "48.00", "8.00"),
            (U, "mmol/L", "1.03", "0.83", "1.23", "0.20")])]),
    (28, "LDL Cholesterol", [("Selective Solubilization Method", [
        ("SA", "mg/dL", "92.30", "75.30", "109.30", "17.00"),
        ("FAA", "mg/dL", "95.50", "77.50", "113.50", "18.00"),
        (U, "mmol/L", "2.47", "2.11", "2.83", "0.35")])]),
    (29, "IRON", [("Chromazurol", [
        ("FAA", "µmol/L", "14.80", "8.70", "20.90", "6.10"),
        (U, "µg/dL", "82.70", "56.70", "108.70", "26.00"),
        ("SA", "µg/dL", "81.0", "57.00", "105.00", "24.00")])]),
    (30, "TIBC", [
        ("Saturation Method", [("SA", "µg/dL", "260.10", "220.10", "300.10", "40.00")]),
        ("Chromazurol", [("FAA", U, "290.40", "232.40", "348.40", "58.00")])]),
    (31, "ZINC", [("Nitro-PAPS", [("FAA", "µg/dL", "46.60", "34.10", "59.10", "12.50")])]),
]

PATH_LEFT = [
    (1, "Albumin", [("Bromocresol Green", [
        ("FAA", "g/dL", "4.4", "3.55", "5.25", "0.85"),
        (U, "g/L", "44.0", "35.5", "52.5", "8.50"),
        ("SA", "g/dL", "4.40", "3.55", "5.25", "0.85")])]),
    (2, "Alkaline phosphatase", [
        ("p-Nitrophenyl phosphate DEA/DGKC", [
            ("FAA", "U/L", "434.3", "364.3", "504.3", "70.00"),
            ("SA", "U/L", "439.0", "349.0", "529.0", "90.00")]),
        ("IFCC", [
            ("FAA", "U/L", "364.7", "299.7", "429.7", "65.00"),
            ("SA", "U/L", "285.6", "225.6", "345.6", "60.0")])]),
    (3, "ALT/SGPT", [("IFCC without PSP", [
        ("FAA", "U/L", "139.5", "111.5", "167.5", "28.00"),
        ("SA", "U/L", "129.8", "103.8", "155.8", "26.00")])]),
    (4, "Amylase", [("CNPG3", [
        ("FAA", "U/L", "291.4", "241.4", "341.4", "50.00"),
        ("SA", "U/L", "300.0", "240.0", "360.0", "60.00")])]),
    (5, "AST/SGOT", [("IFCC without PSP", [
        ("FAA", "U/L", "140.4", "110.4", "170.4", "30.00"),
        ("SA", "U/L", "142.0", "107.0", "177.0", "35.00")])]),
    (6, "Bilirubin Total", [
        ("DMSO", [("SA", "mg/dL", "4.70", "3.6", "5.80", "1.10")]),
        ("TAB", [
            ("SA", U, "6.20", "4.4", "8.00", "1.80"),
            ("FAA", U, "4.30", "3.4", "5.20", "0.90")])]),
    (7, "Bilirubin Direct", [
        ("Diazo", [("SA", "mg/dL", "2.70", "2.1", "3.30", "0.60")]),
        ("Diazo Modified", [("FAA", U, "2.00", "1.60", "2.40", "0.40")])]),
    (8, "Calcium", [
        ("O-Cresolphthalein Complex", [
            ("SA", "mg/dL", "12.30", "10.60", "14.00", "1.70"),
            (U, "mmol/L", "3.06", "2.64", "3.49", "0.43")]),
        ("Arsenazo-III", [
            ("FAA", "mg/dL", "13.10", "11.10", "15.10", "2.00"),
            (U, "mmol/L", "3.26", "2.77", "3.75", "0.49"),
            ("SA", "mg/dL", "12.40", "10.50", "14.30", "1.90")])]),
    (9, "Cholinesterase", [("Butyrylthiocholine", [
        ("SA/FAA", "U/L", "10965.00", "8765.00", "13165.00", "2200.0")])]),
    (10, "Cholesterol", [
        ("CHOD-PAP (Lypho)", [("SA", "mg/dL", "344.6", "289.6", "399.6", "55.00")]),
        ("CHOD-PAP (SL)", [
            ("SA", U, "342.7", "287.7", "397.7", "55.00"),
            ("FAA", "mg/dL", "309.2", "273.2", "345.2", "36.00"),
            (U, "mmol/L", "7.99", "7.06", "8.92", "0.93")])]),
    (11, "CKNAC", [("DGKCH/NVKC/SEQC/IFCC", [
        ("SA", "U/L", "352.7", "277.7", "427.7", "75.00"),
        ("FAA", U, "475.8", "405.8", "545.8", "70.00")])]),
    (12, "Creatinine", [
        ("Jaffe without Deproteinization", [
            ("SA", "mg/dL", "3.90", "3.15", "4.65", "0.75"),
            ("FAA", "mg/dL", "4.3", "3.5", "5.1", "0.80"),
            (U, "µmol/L", "380.1", "309.4", "450.8", "70.70")]),
        ("Enzymatic", [
            ("FAA", "mg/dL", "5.2", "3.9", "6.5", "1.30"),
            ("SA", U, "4.2", "3.3", "5.1", "0.90")])]),
    (13, "CKMB", [("Immuno-inhibition method", [
        ("FAA", "U/L", "25.2", "15.2", "35.2", "10.00"),
        ("SA", U, "33.9", "19.9", "47.9", "14.00")])]),
    (14, "Gamma GT", [("Szasz method", [
        ("SA", "U/L", "110.5", "88.5", "132.5", "22.00"),
        ("FAA", U, "144.4", "119.4", "169.4", "25.00")])]),
    (15, "Glucose", [
        ("GOD-PAP", [
            ("SA", "mg/dL", "226.0", "192.0", "260.0", "34.00"),
            ("FAA", "mg/dL", "230.0", "200.0", "260.0", "30.00"),
            (U, "mmol/L", "12.7", "11.1", "14.3", "1.60")]),
        ("Hexokinase", [
            ("FAA", "mg/dL", "231.5", "196.5", "266.5", "35.00"),
            (U, "mmol/L", "12.8", "10.9", "14.7", "1.90")])]),
]

PATH_RIGHT = [
    (16, "LDH-P", [("SFBC/SEQC", [
        ("SA", "U/L", "665.0", "580.0", "750.0", "85.00"),
        ("FAA", "U/L", "770", "655.0", "885.0", "115.00")])]),
    (17, "Lipase", [("Enzymatic Colorimetric Test", [
        ("FAA", "U/L", "78.6", "50.6", "106.6", "28.00"),
        ("SA", "U/L", "84.1", "58.1", "110.1", "26.00")])]),
    (18, "Magnesium", [("Xylidyl Blue with ATCS", [
        ("SA", "mg/dL", "3.5", "2.6", "4.4", "0.90"),
        ("FAA", "mg/dL", "3.0", "2.1", "3.9", "0.90"),
        (U, "mmol/L", "1.23", "0.86", "1.60", "0.37")])]),
    (19, "Phosphorous", [("Molybdate UV", [
        ("SA", "mg/dL", "8.8", "7.3", "10.3", "1.50"),
        ("FAA", U, "8.4", "7.1", "9.7", "1.30"),
        (U, "mmol/L", "2.7", "2.3", "3.1", "0.42")])]),
    (20, "Triglycerides", [("GPO-PAP", [
        ("SA", "mg/dL", "261.5", "219.5", "303.5", "42.00"),
        ("FAA", "mg/dL", "262.1", "220.1", "304.1", "42.00"),
        (U, "mmol/L", "2.96", "2.49", "3.43", "0.47")])]),
    (21, "Total Protein", [("Biuret", [
        ("FAA/SA", "g/dL", "8.3", "6.5", "10.1", "1.80"),
        ("FAA/SA", "g/L", "83.0", "65.0", "101.0", "18.00")])]),
    (22, "Uric Acid", [
        ("Uricase-PAP (Lypho)", [
            ("SA", "mg/dL", "11.40", "9.9", "12.9", "1.50"),
            (U, "µmol/L", "678.1", "588.9", "767.3", "89.20")]),
        ("Uricase-PAP (S.L)", [
            ("FAA/SA", "mg/dL", "10.80", "8.2", "13.4", "2.60"),
            (U, "µmol/L", "642.4", "487.8", "797.1", "154.7")])]),
    (23, "Urea", [
        ("Urease UV", [
            ("SA", "mg/dL", "170.5", "135.5", "205.5", "35.00"),
            ("FAA", U, "156.0", "126.0", "186.0", "30.00"),
            ("FAA", "mmol/L", "25.9", "20.9", "30.9", "5.00")]),
        ("Urease Berthelot", [
            ("SA", "mg/dL", "157.0", "127.0", "187.0", "30.00"),
            ("SA", "mmol/L", "26.1", "21.2", "31.0", "4.90")])]),
    (24, "Chloride", [
        ("Thiocyanate", [("FAA/SA", "mmol/L", "105.0", "87.0", "123.0", "18.00")]),
        ("Indirect I.S.E", [("TBA", U, "116.5", "98.5", "134.5", "18.00")]),
        ("Direct I.S.E", [("I-SMART", U, "119.2", "99.2", "139.2", "20.00")])]),
    (25, "Sodium", [
        ("Indirect I.S.E", [("TBA", "mmol/L", "156.1", "137.1", "175.1", "19.00")]),
        ("Direct I.S.E", [("I-SMART", "mmol/L", "163.7", "143.7", "183.7", "20.00")])]),
    (26, "Potassium", [
        ("Indirect I.S.E", [("TBA", "mmol/L", "6.5", "5.3", "7.7", "1.20")]),
        ("Direct I.S.E", [("I-SMART", "mmol/L", "6.7", "5.4", "8.0", "1.30")])]),
    (27, "HDL Cholesterol", [
        ("Precipitation Method", [("SA", "mg/dL", "115.00", "87.0", "143.0", "28.00")]),
        ("Selective Inhibition Method", [
            ("SA", "mg/dL", "65.0", "47.0", "83.0", "18.00"),
            ("FAA", "mg/dL", "56.5", "41.5", "71.5", "15.00"),
            ("FAA", "mmol/L", "1.46", "1.07", "1.85", "0.39")])]),
    (28, "LDL Cholesterol", [("Selective Solubilization Method", [
        ("SA", "mg/dL", "194.0", "162", "226", "32.00"),
        ("FAA", "mg/dL", "203.7", "168.7", "238.7", "35.00"),
        ("FAA", "mmol/L", "5.26", "4.36", "6.16", "0.90")])]),
    (29, "IRON", [("Chromazurol", [
        ("FAA", "µmol/L", "42.4", "32.4", "52.4", "10.00"),
        ("FAA", "µg/dL", "236.7", "180.9", "292.5", "55.80"),
        ("SA", "µg/dL", "195.0", "143.0", "247.0", "52.00")])]),
    (30, "TIBC", [
        ("Saturation Method", [("SA", "µg/dL", "376.7", "301.7", "451.7", "75.00")]),
        ("Chromazurol", [("FAA", "µg/dL", "259.9", "207.9", "311.9", "52.00")])]),
    (31, "ZINC", [("Nitro-PAPS", [("FAA", "µg/dL", "80.0", "60.0", "100.0", "20.00")])]),
]

SHEETS = [
    ("NORM", "N", NORM_LEFT, NORM_RIGHT, "42309221"),
    ("PATH", "P", PATH_LEFT, PATH_RIGHT, "42308259"),
]

COLS = ["SL. NO.", "ANALYTE", "METHODS (AT 37 °C)", "", "UNIT",
        "TARGET\nVALUE", "LOWER\nRANGE", "HIGHER\nRANGE", "2SD"]
COL_NAMES = ["", "", "", "Analyser", "Unit", "Target value", "Lower range", "Higher range", "2SD"]
COL_W = [20, 58, 80, 32, 32, 42, 40, 42, 40]

# --------------------------------------------------------------------------

def logo_png():
    src = HERE / "agappe-logo.svg"
    out = HERE / "agappe-logo@8x.png"
    if not out.exists() or out.stat().st_mtime < src.stat().st_mtime:
        import fitz
        doc = fitz.open(src)
        doc[0].get_pixmap(matrix=fitz.Matrix(8, 8), alpha=True).save(out)
    return out


def style(size, bold=False, color=colors.black, leading=None):
    return ParagraphStyle("s", fontName="Cal-B" if bold else "Cal", fontSize=size,
                          leading=leading or size * 1.08, alignment=TA_CENTER, textColor=color)


class Queries:
    def __init__(self, prefix, sheet):
        self.prefix, self.sheet, self.items, self.seen, self.rows = prefix, sheet, [], {}, []
        self.checks = 0

    def cell(self, raw, where, size):
        if raw.startswith("~"):
            self.checks += 1
            return Paragraph(raw[1:], style(size)), "~"
        if not raw.startswith("?"):
            return Paragraph(raw, style(size)), None
        label = self.seen.get(where)
        if label is None:
            label = f"{self.prefix}-{len(self.items) + 1:02d}"
            self.items.append((label, self.sheet, *where, raw[1:] or "—"))
            if where[0] == "Header":
                self.seen[where] = label
        return Paragraph(f"[{label}]", style(size, bold=True, color=RED)), label


def build_table(entries, sheet, side, q, row_h, fs, lot2):
    logo = Image(str(logo_png()), width=72, height=72 * 368 / 1752)
    lot2_p, lot2_flag = q.cell(lot2, ("Header", "LOT", "second lot line", "", ""), fs + 1.5)

    data = [
        [logo, "", Paragraph("LOT", style(fs + 1.5, True)),
         Paragraph(LOT, style(fs + 1.5, True)), "",
         Paragraph("Expiry", style(fs + 1.5, True)), "",
         Paragraph(f"QUALICHECK {sheet}", style(fs + 1.5, True)), ""],
        ["", "", "", lot2_p, "", Paragraph(EXPIRY, style(fs + 1.5, True)), "",
         Paragraph("Human Serum", style(fs + 1, True)), ""],
        [Paragraph(c.replace("\n", "<br/>"), style(fs - 0.3, True)) for c in COLS],
    ]
    cmds = [
        ("SPAN", (0, 0), (1, 1)), ("SPAN", (2, 0), (2, 1)),
        ("SPAN", (3, 0), (4, 0)), ("SPAN", (3, 1), (4, 1)),
        ("SPAN", (5, 0), (6, 0)), ("SPAN", (5, 1), (6, 1)),
        ("SPAN", (7, 0), (8, 0)), ("SPAN", (7, 1), (8, 1)),
    ]
    if lot2_flag:
        cmds.append(("BACKGROUND", (3, 1), (4, 1), RED_BG))
        if side == "left":
            q.rows.append((sheet, "Header", "LOT — second lot line", "", "", [(lot2_flag, lot2[1:] or "—")]))

    r = len(data)
    for sl, analyte, methods in entries:
        a0 = r
        an_start, un_start = r, r
        for method, rows in methods:
            m0 = r
            for an, unit, *vals in rows:
                if an is not None:
                    if r - 1 > an_start:
                        cmds.append(("SPAN", (3, an_start), (3, r - 1)))
                    an_start = r
                if unit is not None:
                    if r - 1 > un_start:
                        cmds.append(("SPAN", (4, un_start), (4, r - 1)))
                    un_start = r
                if an is not None:
                    cur_an = an
                if unit is not None:
                    cur_unit = unit
                line = [Paragraph(str(sl), style(fs)) if r == a0 else "",
                        Paragraph(analyte, style(fs)) if r == a0 else "",
                        Paragraph(method, style(fs)) if r == m0 else "",
                        Paragraph(an, style(fs)) if an else "",
                        Paragraph(unit, style(fs)) if unit else ""]
                cells = []
                for ci, v in enumerate(vals, start=5):
                    p, flag = q.cell(v, (f"{sl} {analyte}", method, cur_an, cur_unit, COL_NAMES[ci]), fs)
                    line.append(p)
                    cells.append((flag, v.lstrip("?~") or "—"))
                    if flag:
                        cmds.append(("BACKGROUND", (ci, r), (ci, r), CHECK_BG if flag == "~" else RED_BG))
                if any(f for f, _ in cells):
                    q.rows.append((sheet, f"{sl} {analyte}", method, cur_an, cur_unit, cells))
                data.append(line)
                r += 1
            if r - 1 > m0:
                cmds.append(("SPAN", (2, m0), (2, r - 1)))
        if r - 1 > an_start:
            cmds.append(("SPAN", (3, an_start), (3, r - 1)))
        if r - 1 > un_start:
            cmds.append(("SPAN", (4, un_start), (4, r - 1)))
        if r - 1 > a0:
            cmds += [("SPAN", (0, a0), (0, r - 1)), ("SPAN", (1, a0), (1, r - 1))]

    heights = [16, 13, 17] + [row_h] * (r - 3)
    if side == "left":
        data.append([Paragraph("SA-Semiauto Analyser", style(fs, True)), "", "", "",
                     Paragraph("FAA- Fully Auto Analyser", style(fs, True)), "", "", "", ""])
        cmds += [("SPAN", (0, r), (3, r)), ("SPAN", (4, r), (8, r))]
        heights.append(row_h + 1)

    t = Table(data, colWidths=COL_W, rowHeights=heights)
    t.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.45, GRID),
        ("BOX", (0, 0), (-1, -1), 0.9, colors.black),
        ("LINEBELOW", (0, 2), (-1, 2), 0.9, colors.black),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("LEFTPADDING", (0, 0), (-1, -1), 1), ("RIGHTPADDING", (0, 0), (-1, -1), 1),
        ("TOPPADDING", (0, 0), (-1, -1), 0), ("BOTTOMPADDING", (0, 0), (-1, -1), 0.6),
        *cmds,
    ]))
    return t


def n_rows(entries):
    return sum(len(rows) for _, _, ms in entries for _, rows in ms)


def build_sheet(sheet, prefix, left, right, lot2):
    out = OUT_DIR / f"Qualicheck {sheet} Value Sheet - Lot {LOT}.pdf"
    page = landscape(A4)
    margin = 8 * mm
    usable = page[1] - 2 * margin - 12 - 16 - 13 - 17 - 2
    rows = max(n_rows(left) + 1, n_rows(right))
    row_h = min(10.5, usable / rows)
    fs = 6.4 if row_h < 10 else 6.8

    q = Queries(prefix, sheet)
    lt = build_table(left, sheet, "left", q, row_h, fs, lot2)
    rt = build_table(right, sheet, "right", q, row_h, fs, lot2)
    outer = Table([[lt, "", rt]], colWidths=[sum(COL_W), 10, sum(COL_W)])
    outer.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0), ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    doc = SimpleDocTemplate(str(out), pagesize=page, leftMargin=margin, rightMargin=margin,
                            topMargin=margin, bottomMargin=margin,
                            title=f"Agappe Qualicheck {sheet} — Lot {LOT} — Value Sheet",
                            author="Noble Diagnostic Centre")
    doc.build([outer])
    return out, q


def build_queries(queries):
    out = OUT_DIR / f"Qualicheck Value Sheets - Lot {LOT} - values to confirm.pdf"
    doc = SimpleDocTemplate(str(out), pagesize=A4, leftMargin=12 * mm, rightMargin=12 * mm,
                            topMargin=12 * mm, bottomMargin=12 * mm,
                            title=f"Qualicheck Lot {LOT} — values to confirm")
    body = ParagraphStyle("b", fontName="Cal", fontSize=8, leading=9.4)
    cell = ParagraphStyle("c", parent=body, alignment=TA_CENTER)
    head = ParagraphStyle("h", fontName="Cal-B", fontSize=13, leading=16)
    note = ParagraphStyle("n", fontName="Cal", fontSize=9, leading=12)
    total = sum(len(q.items) for q in queries)
    checks = sum(q.checks for q in queries)
    story = [
        Paragraph(f"Agappe Qualicheck NORM / PATH — Lot {LOT} — values to confirm", head),
        Spacer(1, 4),
        Paragraph(f"{total} cells carry a red label: they could not be identified from the "
                  "photographed originals and are left blank in the Word copies. “read” gives the "
                  "candidate readings and must not be used until confirmed against the printed insert. "
                  f"{checks} further cells, on a yellow fill, were read from a blurred part of the print "
                  "and close arithmetically (target ± 2SD) but should still be checked. Each line below "
                  "is one row of a sheet; values in black were read clearly.", note),
        Spacer(1, 8),
    ]
    hdr = ["Sheet", "Analyte", "Method", "Analyser", "Unit",
           "Target value", "Lower range", "Higher range", "2SD"]
    rows = [[Paragraph(f"<b>{h}</b>", cell) for h in hdr]]
    shade = []
    for q in queries:
        for sheet, analyte, method, an, unit, cells in q.rows:
            line = [Paragraph(x or "", body) for x in (sheet, analyte, method, an, unit)]
            vals = []
            for k, (label, v) in enumerate(cells):
                if label == "~":
                    vals.append(Paragraph(f'<b>{v}</b><br/><font size="6.5" color="#666666">check</font>', cell))
                    shade.append((5 + k, len(rows), CHECK_BG))
                elif label:
                    vals.append(Paragraph(f'<font color="#C00000"><b>{label}</b></font><br/>'
                                          f'<font size="6.5" color="#666666">read: {v}</font><br/>'
                                          '<font color="#999999">__________</font>', cell))
                    shade.append((5 + k, len(rows), RED_BG))
                else:
                    vals.append(Paragraph(v, cell))
            if len(vals) == 1:
                line += vals + ["", "", ""]
            else:
                line += vals
            rows.append(line)
    t = Table(rows, colWidths=[34, 74, 94, 44, 40, 58, 58, 58, 58], repeatRows=1)
    t.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.4, GRID),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E8E8E8")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 2), ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ("LEFTPADDING", (0, 0), (-1, -1), 3), ("RIGHTPADDING", (0, 0), (-1, -1), 3),
        *[("BACKGROUND", (c, r), (c, r), bg) for c, r, bg in shade],
    ]))
    story.append(t)
    doc.build(story)
    return out


if __name__ == "__main__":
    queries = []
    for sheet, prefix, left, right, lot2 in SHEETS:
        out, q = build_sheet(sheet, prefix, left, right, lot2)
        print(out.name, "blank:", len(q.items), "check:", q.checks)
        queries.append(q)
    if any(q.items or q.checks for q in queries):
        print(build_queries(queries).name)
    else:
        stale = OUT_DIR / f"Qualicheck Value Sheets - Lot {LOT} - values to confirm.pdf"
        stale.unlink(missing_ok=True)
        print("all values confirmed; no query sheet")
