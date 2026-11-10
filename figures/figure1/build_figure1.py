# Build Figure 1 (5 Blender renders, native editable labels) as a PowerPoint slide at journal size.
# Double-column width 17.5 cm. Labels Times New Roman bold, leader lines with small triangle heads.
# Run: python build_figure1.py   -> Figure 1\Figure 1.pptx  (+ cropped panels in Figure 1\panels)
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.normpath(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..", "..")))
import config

import json, os
from PIL import Image
from pptx import Presentation
from pptx.util import Cm, Pt, Emu
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_CONNECTOR
from pptx.dml.color import RGBColor
from pptx.oxml.ns import qn

ROOT = config.FIG1
R = os.path.join(ROOT, "renders")
P = os.path.join(ROOT, "panels")
os.makedirs(P, exist_ok=True)
FONT = "Times New Roman"
LBL, LETTER = 8, 12            # pt at print size
FIG_W = 17.5                   # cm

# render name, crop box (px), anchors file (None -> inline dict)
DEVICE_ANCH = {"pt": [819.4, 495.5], "film_front": [326.2, 480.0], "ito_front": [329.1, 542.4],
               "glass_front": [332.5, 583.5], "vo": [721.3, 569.8], "gnd_tip": [208.3, 403.4]}
PANELS = {
    "overview": dict(img="overview alpha.png", crop=(120, 0, 1830, 1380), anch="overview anchors.json"),
    "device": dict(img="device alpha.png", crop=(0, 0, 1110, 840), anch=DEVICE_ANCH),
    "closeup": dict(img="closeup alpha.png", crop=(0, 0, 1500, 1500), anch="closeup anchors.json"),
    "synapse": dict(img="synapse alpha.png", crop=(330, 0, 1070, 1640), anch="synapse anchors.json"),
    "artificial": dict(img="artificial synapse alpha.png", crop=None, anch="artificial synapse anchors.json"),
}

def prep(key):
    d = PANELS[key]
    im = Image.open(os.path.join(R, d["img"]))
    if d["crop"] is None:          # crop to object + shadow, small margin
        bb = im.getchannel("A").point(lambda v: 255 if v > 25 else 0).getbbox()
        m = 20
        d["crop"] = (max(bb[0] - m, 0), max(bb[1] - m, 0), min(bb[2] + m, im.width), min(bb[3] + m, im.height))
    c = im.crop(d["crop"])
    A = c.getchannel("A").point(lambda v: 0 if v < 10 else min(255, int((v - 10) * 255 / 235)))
    fw, fh = int(c.width * 0.06), int(c.height * 0.06)
    ramp = Image.new("L", c.size, 255)
    px_ = ramp.load()
    for yy in range(c.height):
        for xx in range(c.width):
            f = min(1, xx / fw, (c.width - 1 - xx) / fw, yy / fh, (c.height - 1 - yy) / fh)
            if f < 1: px_[xx, yy] = int(255 * max(f, 0))
    if key not in ("closeup", "synapse"):
        from PIL import ImageChops
        A = ImageChops.multiply(A, ramp)
    c.putalpha(A)
    out = os.path.join(P, f"{key}.png")
    c.save(out, dpi=(600, 600))
    a = d["anch"]
    if isinstance(a, str):
        a = json.load(open(os.path.join(R, a)))
    d["anchors"] = {k: v for k, v in a.items() if k != "size"}
    d["file"], d["w"], d["h"] = out, c.width, c.height
    return d

prs = Presentation()
prs.slide_width = Cm(FIG_W)
prs.slide_height = Cm(12.5)
s = prs.slides.add_slide(prs.slide_layouts[6])

def place(key, left, top, width=None, height=None):
    d = prep(key)
    if width is None:
        width = height * d["w"] / d["h"]
    d["L"], d["T"], d["s"] = left, top, width / d["w"]
    s.shapes.add_picture(d["file"], Cm(left), Cm(top), Cm(width))
    return d

def pt_of(d, k_or_xy):
    x, y = d["anchors"][k_or_xy] if isinstance(k_or_xy, str) else k_or_xy
    return d["L"] + (x - d["crop"][0]) * d["s"], d["T"] + (y - d["crop"][1]) * d["s"]

def runs_into(p, runs, size):
    for t in runs:
        txt, kind = (t, None) if isinstance(t, str) else t
        r = p.add_run(); r.text = txt
        f = r.font; f.name = FONT; f.bold = True; f.size = Pt(size); f.color.rgb = RGBColor(0, 0, 0)
        rpr = r._r.get_or_add_rPr()
        for tag in ("a:latin", "a:cs"):
            e = rpr.find(qn(tag))
            if e is None:
                e = rpr.makeelement(qn(tag), {}); rpr.append(e)
            e.set("typeface", FONT)
        if kind == "sub": rpr.set("baseline", "-25000")
        if kind == "sup": rpr.set("baseline", "30000")

def text(x, y, runs, size=LBL, align="l", w=4.0, color=None):
    """x,y = cm of the anchor edge of the text: align l -> left edge, r -> right edge, c -> centre; y = vertical centre."""
    h = size * 0.0353 * 1.35
    left = {"l": x, "r": x - w, "c": x - w / 2}[align]
    tb = s.shapes.add_textbox(Cm(left), Cm(y - h / 2), Cm(w), Cm(h))
    tf = tb.text_frame; tf.word_wrap = False; tf.auto_size = None
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tf.paragraphs[0]
    p.alignment = {"l": PP_ALIGN.LEFT, "r": PP_ALIGN.RIGHT, "c": PP_ALIGN.CENTER}[align]
    if isinstance(runs, str): runs = [runs]
    lines, cur = [], []
    for t in runs:
        if t == "BR": lines.append(cur); cur = []
        else: cur.append(t)
    lines.append(cur)
    if len(lines) > 1:
        tb.top = Cm(y - h * len(lines) / 2); tb.height = Cm(h * len(lines))
    for i, ln in enumerate(lines):
        pp = p if i == 0 else tf.add_paragraph()
        pp.alignment = p.alignment
        runs_into(pp, ln, size)
    return tb

def leader(x1, y1, x2, y2, head=True):
    c = s.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Cm(x1), Cm(y1), Cm(x2), Cm(y2))
    c.line.color.rgb = RGBColor(0, 0, 0); c.line.width = Pt(0.75)
    if head:
        ln = c.line._get_or_add_ln()
        te = ln.makeelement(qn("a:tailEnd"), {"type": "triangle", "w": "sm", "len": "sm"}); ln.append(te)
    return c

def label(d, anchor, runs, dx=0, dy=0, align=None, gap=0.08, at=None):
    """label at anchor + (dx,dy) cm (or absolute cm 'at') with a leader to the anchor."""
    ax, ay = pt_of(d, anchor)
    tx, ty = at if at else (ax + dx, ay + dy)
    if align is None: align = "l" if dx >= 0 else "r"
    text(tx, ty, runs, align=align)
    sx = tx - gap if align == "l" else tx + gap if align == "r" else tx
    leader(sx, ty, ax, ay)

def letter(x, y, ch):
    text(x, y, f"({ch})", size=LETTER, align="l", w=1.0)

VO = ["V", ("O", "sub"), ("••", "sup")]
BFO = ["La-Sc:BiFeO", ("3", "sub")]

def circle(cx, cy, r, dash=True, w=0.75):
    from pptx.enum.shapes import MSO_SHAPE
    o = s.shapes.add_shape(MSO_SHAPE.OVAL, Cm(cx - r), Cm(cy - r), Cm(2 * r), Cm(2 * r))
    o.fill.background(); o.shadow.inherit = False
    o.line.color.rgb = RGBColor(0, 0, 0); o.line.width = Pt(w)
    if dash: o.line.dash_style = 4          # dash
    return o

def zline(x1, y1, x2, y2):
    c = leader(x1, y1, x2, y2, head=False); c.line.dash_style = 4
    return c

import math
# ---------------- (a): electrode array -> zoomed cross-section  <=>  biological synapse
TOP1, H1 = 0.35, 5.6
a = place("overview", 0.3, TOP1, height=H1)
letter(0.0, TOP1 + 0.1, "a")
label(a, "ito_patch", ["ITO"], at=(4.35, TOP1 + 0.75))
label(a, "film_top", BFO, -2.2, 1.35)
label(a, "glass_edge", ["Glass"], 0.9, 0.3)
label(a, "probed", ["Pt top", "BR", "electrodes"], at=(6.05, TOP1 + 1.3))
# zoom: small dashed circle on the probed electrode -> close-up circle
D = 4.3
zx, zy = pt_of(a, "probed"); zr = 0.22
cx0, cy0 = 7.75 + D / 2, TOP1 + H1 / 2
c = place("closeup", cx0 - D / 2, cy0 - D / 2, height=D)
circle(zx, zy, zr)
dx, dy = cx0 - zx, cy0 - zy; L_ = math.hypot(dx, dy); ang = math.atan2(dy, dx)
beta = math.asin((D / 2 - zr) / L_)          # outer tangents of the two circles
for sgn in (1, -1):
    t = ang + sgn * (math.pi / 2 + beta)
    zline(zx + zr * math.cos(t), zy + zr * math.sin(t), cx0 + D / 2 * math.cos(t), cy0 + D / 2 * math.sin(t))
circle(cx0, cy0, D / 2, dash=False, w=1.0)
label(c, "pt", ["Pt"], 0.45, -0.55)
label(c, "gb", ["Grain boundary"], at=(c["L"] + 0.55, c["T"] + 0.95))
label(c, "vo", VO, at=(c["L"] + D * 0.69, c["T"] + D * 0.80))
label(c, "e", ["e", ("−", "sup")], at=(c["L"] + D * 0.47, c["T"] + D * 0.80))
text(c["L"] + 0.75, c["T"] + D * 0.765, ["ITO"], align="l", w=1)
text(c["L"] + 0.95, c["T"] + D * 0.90, ["Glass"], align="l", w=1.5)
# biological synapse with its labels on the right
ex = cx0 + D / 2
text(ex + 0.38, cy0, ["⇔"], size=16, align="c", w=0.8)
d = place("synapse", ex + 0.75, TOP1, height=H1)
XR = d["L"] + d["w"] * d["s"] + 0.12
label(d, "pre", ["Pre-synaptic", "BR", "neuron"], at=(XR, TOP1 + 0.9), align="l")
label(d, "ves_r", ["Vesicle"], at=(XR, TOP1 + 1.75), align="l")
label(d, "channel", ["Ca", ("2+", "sup"), " channel"], at=(XR, TOP1 + 2.45), align="l")
label(d, "cleft_r", ["Synaptic", "BR", "cleft"], at=(XR, TOP1 + 3.1), align="l")
label(d, (915, 950), ["Receptor"], at=(XR, TOP1 + 3.75), align="l")
label(d, (1000, 1110), ["Post-synaptic", "BR", "neuron"], at=(XR, TOP1 + 4.55), align="l")

# ---------------- (b) cross-section SEM, (c) bipolar I-V (Origin object pasted by paste_iv.ps1)
TOP2 = TOP1 + H1 + 0.4
sem = Image.open(config.ORIGIN_OUT + "/0 SEM/SEM_cross_section_LaSc_P2_labelled.png").crop((0, 120, 1536, 1103))
semf = os.path.join(P, "sem.png"); sem.save(semf, dpi=(600, 600))
H2 = 5.75
s.shapes.add_picture(semf, Cm(0.3), Cm(TOP2), height=Cm(H2))
SEM_W = H2 * sem.width / sem.height
tb = text(0.4, TOP2 + 0.35, ["(b)"], size=LETTER, align="l", w=1.0)
tb.text_frame.paragraphs[0].runs[0].font.color.rgb = RGBColor(255, 255, 255)
letter(0.3 + SEM_W + 0.15, TOP2 + 0.1, "c")
json.dump({"left_cm": 0.3 + SEM_W + 0.35, "top_cm": TOP2, "height_cm": H2, "right_cm": FIG_W - 0.05},
          open(os.path.join(ROOT, "scripts", "iv_slot.json"), "w"))
prs.slide_height = Cm(TOP2 + H2 + 0.15)

out = os.path.join(ROOT, "Figure 1.pptx")
prs.save(out)
print("saved", out)
