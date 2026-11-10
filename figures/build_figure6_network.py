# Figure 6 (17.5 cm, native PowerPoint shapes, Times New Roman):
#   (a) MNIST digit -> multilayer perceptron 784-H-10 (sigmoid)
#   (b) mapping of one weight layer onto a crossbar of differential device pairs (w = G+ - G-),
#       with the measured Pt/La-Sc:BFO/ITO cell as the zoomed cross-point
#   (c) accuracy vs epoch (ideal / nonlinearity / nonlinearity + write noise): Origin panel pasted by paste_fig6c.ps1
# usage: python build_figure6.py [--hidden 200]   then fig6c_geom.py and paste_fig6c.ps1 add panel (c) and write the preview PNG
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.normpath(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..")))
import config

import argparse, os, copy
import numpy as np
from PIL import Image
from pptx import Presentation
from pptx.util import Cm, Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE, MSO_CONNECTOR
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.oxml.ns import qn
from lxml import etree

ap = argparse.ArgumentParser()
ap.add_argument("--hidden", default="200")
args = ap.parse_args()
H = args.hidden

ROOT = config.PROJECT
OUT = config.PAPER_FIG
PAN = os.path.join(config.WORK, "fig7_panels"); os.makedirs(PAN, exist_ok=True)
MNIST = os.path.join(config.PKG, "crosssim", "data", "mnist.npz")
CELL = os.path.join(config.FIG1, "renders", "device alpha.png")

FONT = "Times New Roman"
FS = 7.5            # body labels (Origin panels print at 6-7 pt in Figs 2-5)
BLACK = RGBColor(0, 0, 0); GREY = RGBColor(150, 150, 150); RED = RGBColor(230, 0, 0); BLUE = RGBColor(0, 0, 230)
NODE = RGBColor(255, 255, 255)

# ------------------------------------------------------------------ images
d = np.load(MNIST)
img = d["xte"][0]                       # first MNIST test image (a "7")
lab = int(d["yte"][0])
Image.fromarray(img.astype(np.uint8)).resize((280, 280), Image.NEAREST).save(os.path.join(PAN, "digit.png"))
cell = Image.open(CELL).convert("RGBA")
bb = cell.getchannel("A").point(lambda a: 255 if a > 8 else 0).getbbox()
cell.crop(bb).save(os.path.join(PAN, "cell.png"))

prs = Presentation()
prs.slide_width, prs.slide_height = Cm(17.5), Cm(11.7)
s = prs.slides.add_slide(prs.slide_layouts[6])
sh = s.shapes

# ------------------------------------------------------------------ helpers
def _runs(tf, parts, size, bold, color, align):
    """parts: str or list of (text, mode) with mode '', 'sub', 'sup', 'i' (italic), 'isub' ..."""
    if isinstance(parts, str): parts = [(parts, "")]
    p = tf.paragraphs[0]; p.alignment = align
    for t, m in parts:
        r = p.add_run(); r.text = t
        f = r.font; f.name = FONT; f.size = Pt(size); f.bold = bold; f.color.rgb = color
        if "i" in m: f.italic = True
        if "sub" in m: r._r.get_or_add_rPr().set("baseline", "-25000")
        if "sup" in m: r._r.get_or_add_rPr().set("baseline", "30000")

def text(x, y, parts, size=FS, bold=True, color=BLACK, anchor="cc", w=4.0, h=0.5):
    """(x, y) is the anchor point in cm; anchor = [l|c|r][t|c|b]"""
    ax, ay = anchor[0], anchor[1]
    left = x - (0 if ax == "l" else w / 2 if ax == "c" else w)
    top = y - (0 if ay == "t" else h / 2 if ay == "c" else h)
    tb = sh.add_textbox(Cm(left), Cm(top), Cm(w), Cm(h)); tf = tb.text_frame
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    tf.word_wrap = False
    tf.vertical_anchor = {"t": MSO_ANCHOR.TOP, "c": MSO_ANCHOR.MIDDLE, "b": MSO_ANCHOR.BOTTOM}[ay]
    _runs(tf, parts, size, bold, color, {"l": PP_ALIGN.LEFT, "c": PP_ALIGN.CENTER, "r": PP_ALIGN.RIGHT}[ax])
    return tb

def _arrowhead(conn, end="tail", kind="triangle", size="sm"):
    ln = conn.line._get_or_add_ln()
    e = etree.SubElement(ln, qn(f"a:{end}End")); e.set("type", kind); e.set("w", size); e.set("len", size)

def line(x1, y1, x2, y2, w=0.75, color=BLACK, arrow=None, dash=None):
    c = sh.add_connector(MSO_CONNECTOR.STRAIGHT, Cm(x1), Cm(y1), Cm(x2), Cm(y2))
    c.line.width = Pt(w); c.line.color.rgb = color
    if dash:
        ln = c.line._get_or_add_ln(); pd = etree.SubElement(ln, qn("a:prstDash")); pd.set("val", dash)
    if arrow in ("end", "both"): _arrowhead(c, "tail")
    if arrow in ("start", "both"): _arrowhead(c, "head")
    return c

def circle(x, y, r, fill=NODE, lw=1.0, color=BLACK):
    c = sh.add_shape(MSO_SHAPE.OVAL, Cm(x - r), Cm(y - r), Cm(2 * r), Cm(2 * r))
    if fill is None: c.fill.background()
    else: c.fill.solid(); c.fill.fore_color.rgb = fill
    c.line.width = Pt(lw); c.line.color.rgb = color; c.shadow.inherit = False
    return c

def rect(x, y, w, h, fill=None, lw=0.75, color=BLACK, dash=None):
    r = sh.add_shape(MSO_SHAPE.RECTANGLE, Cm(x), Cm(y), Cm(w), Cm(h))
    if fill is None: r.fill.background()
    else: r.fill.solid(); r.fill.fore_color.rgb = fill
    r.line.width = Pt(lw); r.line.color.rgb = color; r.shadow.inherit = False
    if dash:
        ln = r.line._get_or_add_ln(); pd = etree.SubElement(ln, qn("a:prstDash")); pd.set("val", dash)
    return r

def vdots(x, y, gap=0.12, r=0.025):
    for k in (-1, 0, 1): circle(x, y + k * gap, r, fill=BLACK, lw=0.25)

def hdots(x, y, gap=0.12, r=0.025):
    for k in (-1, 0, 1): circle(x + k * gap, y, r, fill=BLACK, lw=0.25)

def letter(x, y, t):
    text(x, y, t, size=10, bold=True, anchor="lt", w=1.0, h=0.45)

# ------------------------------------------------------------------ (a) network
letter(0.05, 0.05, "(a)")
R = 0.17
XI, XH, XO = 3.15, 5.55, 7.85
yin = [1.25, 1.95, 2.65, 4.25]; yin_dots = 3.45
yhid = [1.6, 2.3, 3.0, 4.2]; yhid_dots = 3.42
yout = [1.95, 2.65, 3.75]; yout_dots = 3.2
for a in yin:
    for b in yhid:
        line(XI + R, a, XH - R, b, w=0.4, color=GREY)
for a in yhid:
    for b in yout:
        line(XH + R, a, XO - R, b, w=0.4, color=GREY)
line(XI + R, yin[1], XH - R, yhid[1], w=1.25, color=RED)          # one highlighted weight
for y in yin: circle(XI, y, R)
for y in yhid: circle(XH, y, R)
for y in yout: circle(XO, y, R)
vdots(XI, yin_dots); vdots(XH, yhid_dots); vdots(XO, yout_dots)
for y, sfx in zip(yin, ["1", "2", "3", "784"]):
    text(XI - R - 0.06, y, [("x", "i"), (sfx, "sub")], anchor="rc", w=0.9)
for y, sfx in zip(yhid, ["1", "2", "3", H]):
    text(XH, y - R - 0.02, [("h", "i"), (sfx, "sub")], anchor="cb", w=0.9, h=0.32, size=FS - 0.5)
for y, sfx in zip(yout, ["0", "1", "9"]):
    text(XO + R + 0.06, y, [("y", "i"), (sfx, "sub")], anchor="lc", w=0.9)
text((XI + XH) / 2, 0.75, [("W", "i"), ("1", "sub"), (f" (784 × {H})", "")], anchor="cc", w=3.0)
text((XH + XO) / 2, 0.75, [("W", "i"), ("2", "sub"), (f" ({H} × 10)", "")], anchor="cc", w=3.0)
text((XI + XH) / 2, 1.92, [("w", "i"), ("ij", "isub")], anchor="cb", w=0.6, color=RED)
text(XI, 4.85, "Input", anchor="ct", w=2.0); text(XI, 5.2, "(784)", anchor="ct", w=2.0, bold=False)
text(XH, 4.85, "Hidden", anchor="ct", w=2.0); text(XH, 5.2, f"({H}, sigmoid)", anchor="ct", w=2.4, bold=False)
text(XO, 4.85, "Output", anchor="ct", w=2.0); text(XO, 5.2, "(10, sigmoid)", anchor="ct", w=2.4, bold=False)
# digit
DX, DY, DW = 0.25, 1.75, 1.55
sh.add_picture(os.path.join(PAN, "digit.png"), Cm(DX), Cm(DY), Cm(DW), Cm(DW)).line.color.rgb = BLACK
text(DX + DW / 2, DY - 0.1, "MNIST", anchor="cb", w=2.0)
text(DX + DW / 2, DY + DW + 0.1, "28 × 28 pixels", anchor="ct", w=2.2, bold=False)
line(DX + DW + 0.1, DY + DW / 2, XI - R - 0.55, DY + DW / 2, w=1.0, arrow="end")
text((DX + DW + XI - R - 0.45) / 2, DY + DW / 2 - 0.08, "flatten", anchor="cb", w=1.2, bold=False, size=FS - 0.5)

# ------------------------------------------------------------------ (b) crossbar mapping
letter(8.95, 0.05, "(b)")
X0, Y0 = 10.15, 1.1                          # top-left cross-point
NR, NP = 4, 3                                 # rows shown, column pairs shown
DYR, DXC, PAIR = 0.72, 0.36, 1.12             # row pitch, G+/G- spacing, pair pitch
rows = [Y0 + i * DYR for i in range(NR)]
rows[-1] += 0.32                              # gap for the dots before row 784
cols = []
for j in range(NP):
    xp = X0 + j * PAIR + (0.35 if j == NP - 1 else 0)
    cols += [(xp, "+", j), (xp + DXC, "−", j)]
XEND = cols[-1][0] + 0.35
YEND = rows[-1] + 0.45
for i, y in enumerate(rows):
    line(X0 - 0.75, y, XEND, y, w=1.0)
    sfx = ["1", "2", "3", "784"][i]
    text(X0 - 0.8, y, [("V", "i"), (sfx, "sub")], anchor="rc", w=0.8)
for x, sgn, j in cols:
    line(x, Y0 - 0.35, x, YEND, w=1.0, color=(RED if sgn == "+" else BLUE))
for i, y in enumerate(rows):
    for x, sgn, j in cols:
        rect(x - 0.075, y - 0.075, 0.15, 0.15, fill=RGBColor(40, 40, 40), lw=0.5)
vdots(X0 - 0.95, (rows[2] + rows[3]) / 2, gap=0.1); hdots(cols[3][0] + 0.38, Y0 - 0.2, gap=0.1)
for x, sgn, j in cols:
    text(x, Y0 - 0.4, [("G", "i"), (sgn, "sup")], anchor="cb", w=0.5, size=FS - 0.5, color=(RED if sgn == "+" else BLUE))
# column read-out: differential pair -> neuron
for j in range(NP):
    xp = [c[0] for c in cols if c[2] == j]
    xc = (xp[0] + xp[1]) / 2
    line(xp[0], YEND, xc - 0.05, YEND + 0.28, w=0.75, color=RED); line(xp[1], YEND, xc + 0.05, YEND + 0.28, w=0.75, color=BLUE)
    circle(xc, YEND + 0.42, 0.14, lw=0.75)
    text(xc, YEND + 0.42, "Σ", anchor="cc", w=0.3, size=FS - 1)
    sfx = ["1", "2", H][j]
    text(xc, YEND + 0.62, [("h", "i"), (sfx, "sub")], anchor="ct", w=0.8, size=FS - 0.5)
text(X0 - 0.6, 5.3, [("I", "i"), ("j", "isub"), (" = Σ", ""), ("i", "isub"), (" V", "i"), ("i", "isub"),
                     (" (", ""), ("G", "i"), ("ij", "isub"), ("+", "sup"), (" − ", ""), ("G", "i"), ("ij", "isub"), ("−", "sup"), (")", "")],
     anchor="lc", w=4.6, bold=False)
text(X0 - 0.6, 5.72, [("w", "i"), ("ij", "isub"), (" ∝ ", ""), ("G", "i"), ("ij", "isub"), ("+", "sup"), (" − ", ""), ("G", "i"), ("ij", "isub"), ("−", "sup"),
                      (";  ", ""), ("V", "i"), ("i", "isub"), (" ∝ ", ""), ("x", "i"), ("i", "isub")], anchor="lc", w=4.6, bold=False)
# zoom to the measured cell
hx, hy = cols[2][0], rows[1]
circle(hx, hy, 0.17, fill=None, lw=1.0, color=BLACK)
CX, CY, CW = 14.55, 0.85, 2.8
pic = sh.add_picture(os.path.join(PAN, "cell.png"), Cm(CX), Cm(CY), Cm(CW))
ch = pic.height / 360000
line(hx + 0.17, hy, CX + 0.15, CY + ch * 0.55, w=0.75, dash="dash")
text(CX + CW / 2, CY + ch + 0.1, "Measured cell", anchor="ct", w=3.0)
text(CX + CW / 2, CY + ch + 0.45, "Pt/La-Sc:BFO/ITO", anchor="ct", w=3.0, bold=False)
text(CX + CW / 2, CY + ch + 0.95, [("Update: power-law mean", "")], anchor="ct", w=3.0, bold=False, size=FS - 0.5)
text(CX + CW / 2, CY + ch + 1.27, [("+ Gaussian scatter (Table 2)", "")], anchor="ct", w=3.0, bold=False, size=FS - 0.5)

# ------------------------------------------------------------------ (c) Origin panel (accuracy vs epoch), pasted by paste_fig6c.ps1
letter(5.75, 6.35, "(c)")

out = os.path.join(OUT, "Figure 6.pptx")
prs.save(out)
print("saved", out, "| hidden =", H, "| digit label =", lab)
