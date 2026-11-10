import os as _os, sys as _sys
try:
    _HERE = _os.path.dirname(_os.path.abspath(__file__))
except NameError:            # Origin "run -pyf" may not define __file__
    _HERE = _os.environ["LASC_PKG"] + "/origin_plots"
_sys.path.insert(0, _os.path.normpath(_os.path.join(_HERE, "..")))
_sys.path.insert(0, _HERE)
import config

import sys, os
pass
import importlib, oplib as O
importlib.reload(O)
import originpro as op, math

FOLD = "3 Synaptic/Pulse schemes"
TNR = "Times New Roman"
MINUS = "\u2212"; EN = "\u2013"; APPROX = "\u2248"; DT = "\\g(D)\\i(t)"

class Sketch:
    """axis-free Origin graph: bold black polylines (data plots, 4 pt), dotted lines, arrows and bold text."""
    def __init__(self, name, lname, xr, yr, shape="left"):
        self.wb, self.ws = O.book("SCH", lname)
        self.name, self.xr, self.yr, self.shape = name, xr, yr, shape
        self.lines = []      # (xs, ys, width_pt, dotted)
        self.ann = []        # deferred LabTalk / text placements
        self.n = 0
    def poly(self, pts, w=4, dotted=False):
        self.lines.append(([p[0] for p in pts], [p[1] for p in pts], w, dotted))
    BAND = 0.44          # "top" sketches: drawing occupies the middle 44 % of the page height (rest is cropped on the slide)
    def text(self, t, x, y, anchor="c", fs=24):
        if self.shape == "top":
            fs = round(fs * 0.8)
        self.ann.append(("t", t, x, y, anchor, fs))
    def arrow(self, x1, y1, x2, y2, both=True, w=1.5):
        """dimension arrow: thin line + open arrowheads drawn as short line pairs (always visible)"""
        self.poly([(x1, y1), (x2, y2)], w=w)
        hx = 0.012 * (self.xr[1] - self.xr[0]); hy = 0.022 * (self.yr[1] - self.yr[0])
        def head(xe, ye, xs, ys):
            if abs(ye - ys) < 1e-9:            # horizontal
                s = 1 if xe > xs else -1
                self.poly([(xe - s * hx, ye + hy), (xe, ye), (xe - s * hx, ye - hy)], w=w)
            else:                               # vertical
                s = 1 if ye > ys else -1
                self.poly([(xe - 0.6 * hx, ye - s * 1.6 * hy), (xe, ye), (xe + 0.6 * hx, ye - s * 1.6 * hy)], w=w)
        head(x2, y2, x1, y1)
        if both: head(x1, y1, x2, y2)
    def build(self):
        spec = []
        for i, (xs, ys, w, dot) in enumerate(self.lines):
            spec += [(xs, 'X', f"x{i + 1}", "", "sketch, not to scale"), (ys, 'Y', f"y{i + 1}", "", "dotted" if dot else "")]
        O.cols(self.ws, spec)
        g = O.graph(self.name, self.name)
        for i in range(len(self.lines)):
            O.plot(g, self.ws, 2 * i + 1, 2 * i, 'l')
        yr = self.yr
        if self.shape == "top":               # page aspect is fixed in Origin: put the drawing in a horizontal band
            mid = 0.5 * (yr[0] + yr[1]); span = (yr[1] - yr[0]) / self.BAND
            yr = (mid - span / 2, mid + span / 2)
        O.style(g, "", "", xr=self.xr, yr=yr)
        O.lt('layer.unit=1; layer.left=1; layer.top=1; layer.width=98; layer.height=98;')
        O.LAYER1.update(left=1, top=1, width=98, height=98, pw=op.lt_float('page.width'), ph=op.lt_float('page.height'))
        O.lt(f'layer.x.from={self.xr[0]}; layer.x.to={self.xr[1]}; layer.y.from={yr[0]}; layer.y.to={yr[1]};')
        self.yr = yr
        O.lt('layer.x.showAxes=0; layer.y.showAxes=0; layer.x.showLabels=0; layer.y.showLabels=0; label -r xb; label -r yl;')
        for ax in ('x', 'y', 'x2', 'y2'):
            O.lt(f'layer.{ax}.thickness=0; layer.{ax}.ticks=0;')
        O.nolegend()
        for i, (xs, ys, w, dot) in enumerate(self.lines):
            O.lt(f'layer.plot={i + 1}; set %C -w {int(w * 500)}; set %C -c color(0,0,0);' + (' set %C -d 2;' if dot else ''))
        for a in self.ann:
            self.n += 1; nm = f"S{self.n}"
            if a[0] == "t":
                _, t, x, y, anchor, fs = a
                O.lt(f'label -s -n {nm} "{O.esc(chr(92) + "b(" + t + ")")}"; {nm}.font=font("{TNR}"); {nm}.fsize={fs}; {nm}.background=0;')
                dx = {"l": f" + {nm}.dx/2", "r": f" - {nm}.dx/2", "c": ""}[anchor]
                O.lt(f'{nm}.x = {x}{dx}; {nm}.y = {y};')
            else:
                _, x1, y1, x2, y2, both, w = a
                O.lt(f'draw -n {nm} -l {{{x1},{y1},{x2},{y2}}}; {nm}.linewidth={w}; {nm}.color=color(0,0,0);'
                     f' {nm}.arrowEndShape=1; {nm}.arrowEndWidth=8; {nm}.arrowEndLength=8;' +
                     (f' {nm}.arrowBeginShape=1; {nm}.arrowBeginWidth=8; {nm}.arrowBeginLength=8;' if both else ''))
        return g

def train(x, lo, hi, n, w=0.55, gap=0.55):
    """n square pulses starting at x on a baseline 'lo' up to 'hi'; returns points and the pulse x-ranges"""
    pts, rng = [], []
    for k in range(n):
        pts += [(x, lo), (x, hi), (x + w, hi), (x + w, lo)]; rng.append((x, x + w)); x += w + gap
    return pts, rng, x

def dots(sk, x, y):
    sk.text("...", x, y, "c", 28)

def levels(sk, x, vw="15 V", vr="1 V", yw=4.0, yr_=1.0, y0=0.0, show0=True):
    sk.text(f"V\\-(W) = {vw}", x, yw, "r", 24)
    sk.text(f"V\\-(R) = {vr}", x, yr_ + 0.45, "r", 24)
    if show0: sk.text("0 V", x, y0 - 0.5, "r", 22)

def save(g, fname, title):
    O.save(g, FOLD, fname, title)

# ---------------------------------------------------------------- I-V sweep (exactly as the reference sketch)
def s_iv():
    sk = Sketch("S_IV", "Bipolar I-V sweep waveform", (-1.6, 15.6), (-19, 21), "left")
    up = 15 / 0.5 * 0.11; dn = 12 / 0.5 * 0.11          # 3.3 s up, 2.64 s down (0.5 V steps of about 0.11 s)
    t0 = 1.0; tp = t0 + up; tz = tp + up; tm = tz + dn; te = tm + dn
    sk.poly([(0, 0), (t0, 0), (tp, 15), (tm, -12), (te, 0), (te + 1.2, 0)], w=4)
    sk.poly([(0, 0), (te + 1.2, 0)], w=1.5, dotted=True)
    cx, cy = t0 + 0.55, 0.55 / up * 15                    # circle on the rising ramp
    sk.poly([(cx + 0.38 * math.cos(a / 30 * 2 * math.pi), cy + 1.5 * math.sin(a / 30 * 2 * math.pi)) for a in range(31)], w=1.5)
    bx0, bx1, by0, by1 = -1.1, 3.4, -16.5, -5.5          # zoom box
    sk.poly([(bx0, by0), (bx1, by0), (bx1, by1), (bx0, by1), (bx0, by0)], w=1.5)
    sk.poly([(cx - 0.3, cy - 1.2), (bx0, by1)], w=1.2); sk.poly([(cx + 0.3, cy - 1.2), (bx1, by1)], w=1.2)
    sk.poly([(-0.8, -14.5), (0.3, -14.5), (0.3, -11.0), (1.4, -11.0), (1.4, -7.5), (2.4, -7.5)], w=2.5)
    sk.arrow(2.0, -11.0, 2.0, -7.5); sk.text("0.5 V", 2.15, -9.25, "l", 18)
    sk.arrow(0.3, -15.6, 1.4, -15.6); sk.text(f"{APPROX} 0.11 s", 0.85, -17.6, "c", 18)
    sk.text("0 V", -0.6, 1.8, "c", 24)
    sk.text("+15 V", tp, 17.3, "c", 26)
    sk.text(f"{MINUS}12 V", tm, -14.5, "c", 26)
    sk.text(f"one sweep {APPROX} 12 s", 12.3, 16.5, "c", 24)
    sk.text("(111 points)", 12.3, 13.4, "c", 20)
    save(sk.build(), "Scheme_IV_sweep", "Bipolar I-V sweep waveform")

# ---------------------------------------------------------------- write / read schemes
def s_epsc():
    sk = Sketch("S_EPSC", "EPSC pulse scheme", (-3.6, 12), (-1.4, 5.6), "left")
    sk.poly([(0, 0), (0.6, 0), (0.6, 1), (3.0, 1), (3.0, 4), (3.8, 4), (3.8, 1), (11.5, 1)])
    sk.poly([(0, 0), (11.5, 0)], w=1.5, dotted=True)
    sk.arrow(3.0, 4.5, 3.8, 4.5); sk.text("0.1 s", 3.4, 5.1, "c", 20)
    sk.arrow(4.2, 1.5, 11.3, 1.5); sk.text("read 100 s", 7.75, 2.1, "c", 22)
    levels(sk, 2.7)
    save(sk.build(), "Scheme_EPSC", "EPSC: single write pulse, read at 1 V")

def s_readv():
    sk = Sketch("S_READV", "EPSC read-voltage scheme", (-4.2, 12), (-1.4, 5.6), "left")
    sk.poly([(0, 0), (0.6, 0), (0.6, 1), (3.0, 1), (3.0, 4), (3.8, 4), (3.8, 1), (11.5, 1)])
    sk.poly([(0, 0), (11.5, 0)], w=1.5, dotted=True)
    sk.arrow(3.0, 4.5, 3.8, 4.5); sk.text("0.1 s", 3.4, 5.1, "c", 20)
    sk.text(f"V\\-(W) = 15 V", 2.7, 4.0, "r", 24)
    sk.text(f"V\\-(R) = 0.25{EN}1 V", 2.7, 1.45, "r", 24)
    sk.text("0 V", 2.7, -0.5, "r", 22)
    sk.arrow(4.2, 1.5, 11.3, 1.5); sk.text("read 100 s", 7.75, 2.1, "c", 22)
    save(sk.build(), "Scheme_read_voltage", "EPSC at read voltages 0.25-1 V")

def s_ppf():
    sk = Sketch("S_PPF", "PPF scheme", (-3.6, 12), (-1.4, 5.6), "top")
    sk.poly([(0, 0), (0.6, 0), (0.6, 1), (3.0, 1), (3.0, 4), (3.6, 4), (3.6, 1), (7.6, 1), (7.6, 4), (8.2, 4), (8.2, 1), (11.5, 1)])
    sk.poly([(0, 0), (11.5, 0)], w=1.5, dotted=True)
    sk.arrow(3.6, 2.6, 7.6, 2.6); sk.text(f"{DT} = 0.05{EN}20 s", 5.6, 3.2, "c", 22)
    sk.arrow(3.0, 4.5, 3.6, 4.5); sk.text("0.1 s", 3.3, 5.1, "c", 20)
    sk.text("A\\-(1)", 4.1, 4.5, "c", 20); sk.text("A\\-(2)", 8.7, 4.5, "c", 20)
    levels(sk, 2.7)
    save(sk.build(), "Scheme_PPF", "Paired-pulse scheme")

def s_sddp():
    sk = Sketch("S_SDDP", "SDDP scheme", (-3.6, 12), (-1.4, 5.6), "top")
    p1, r1, x = train(3.0, 1, 4, 2, w=0.6, gap=0.6)
    p2, r2, x2 = train(x + 1.2, 1, 4, 1, w=0.6, gap=0.6)
    sk.poly([(0, 0), (0.6, 0), (0.6, 1), (3.0, 1)] + p1 + [(x + 1.2, 1)] + p2 + [(x2 + 3.0, 1)])
    sk.poly([(0, 0), (x2 + 3.0, 0)], w=1.5, dotted=True)
    dots(sk, x + 0.6, 1.35)
    sk.arrow(r1[0][0], 4.5, r1[0][1], 4.5); sk.text(f"w = 0.1{EN}0.5 s", sum(r1[0]) / 2, 5.1, "c", 20)
    sk.text("50 pulses", x2 + 0.6, 3.0, "l", 22)
    levels(sk, 2.7)
    save(sk.build(), "Scheme_SDDP", "SDDP: 50 pulses of width w")

def s_train_read(name, fname, title, vw, vr, nlabel, readlabel, shape="left"):
    sk = Sketch(name, title, (-3.6, 13.5), (-1.4, 5.8), shape)
    p1, r1, x = train(3.0, 1, 4, 3, w=0.45, gap=0.45)
    p2, r2, x2 = train(x + 1.1, 1, 4, 1, w=0.45, gap=0.45)
    end = x2 + 5.5
    sk.poly([(0, 0), (0.6, 0), (0.6, 1), (3.0, 1)] + p1 + [(x + 1.1, 1)] + p2 + [(end, 1)])
    sk.poly([(0, 0), (end, 0)], w=1.5, dotted=True)
    dots(sk, x + 0.55, 1.35)
    sk.arrow(r1[0][0], 4.55, r2[0][1], 4.55); sk.text(nlabel, (r1[0][0] + r2[0][1]) / 2, 5.2, "c", 20)
    sk.arrow(r2[0][1] + 0.3, 1.6, end - 0.2, 1.6); sk.text(readlabel, (r2[0][1] + end) / 2, 2.2, "c", 20)
    levels(sk, 2.7, vw=vw, vr=vr)
    save(sk.build(), fname, title)

def s_sndp():
    s_train_read("S_SNDP", "Scheme_SNDP", "SNDP / retention: N pulses then read", "15 V", "1 V",
                 f"N = 20{EN}100 pulses, 0.1 s", "read up to 2000 s")

def s_sndp_top():
    s_train_read("S_SNDPt", "Scheme_SNDP_top", "SNDP: N pulses then read", "15 V", "1 V",
                 f"N = 20{EN}100 pulses, 0.1 s", "read up to 2000 s", shape="top")

def s_la_ret():
    s_train_read("S_LaRET", "Scheme_La_retention", "La 7.5%: N pulses then read", "5 V", "0.7 V",
                 "N = 40, 60 pulses", "read up to 2000 s")

def s_srdp():
    sk = Sketch("S_SRDP", "SRDP scheme", (-3.6, 13.5), (-1.4, 5.8), "left")
    p1, r1, x = train(3.0, 1, 4, 3, w=0.45, gap=0.75)
    p2, r2, x2 = train(x + 1.1, 1, 4, 1, w=0.45, gap=0.75)
    end = x2 + 2.5
    sk.poly([(0, 0), (0.6, 0), (0.6, 1), (3.0, 1)] + p1 + [(x + 1.1, 1)] + p2 + [(end, 1)])
    sk.poly([(0, 0), (end, 0)], w=1.5, dotted=True)
    dots(sk, x + 0.55, 1.35)
    sk.arrow(r1[0][0], 4.55, r2[0][1], 4.55); sk.text(f"30 pulses, f = 0.5{EN}8 Hz", (r1[0][0] + r2[0][1]) / 2, 5.2, "c", 20)
    sk.arrow(r1[0][1], 2.5, r1[1][0], 2.5); sk.text("1/f", (r1[0][1] + r1[1][0]) / 2, 3.1, "c", 18)
    sk.text("0.1 s pulses", end - 0.4, 1.6, "r", 18)
    levels(sk, 2.7)
    save(sk.build(), "Scheme_SRDP", "SRDP: 30 pulses at 0.5-8 Hz")

def s_ltp(name, fname, title, cyc):
    sk = Sketch(name, title, (-5.8, 17.5), (-4.8, 6.0), "top")
    pts = [(0, 0), (0.6, 0), (0.6, 1), (2.8, 1)]
    p1, r1, x = train(2.8, 1, 4, 3, w=0.4, gap=0.4); pts += p1 + [(x + 1.0, 1)]
    p2, r2, x = train(x + 1.0, 1, 4, 1, w=0.4, gap=0.4); pts += p2 + [(x + 0.6, 1)]
    xd = x + 0.6
    p3, r3, x = train(xd, 1, -3, 3, w=0.4, gap=0.4); pts += p3 + [(x + 1.0, 1)]
    p4, r4, x = train(x + 1.0, 1, -3, 1, w=0.4, gap=0.4); pts += p4 + [(x + 2.0, 1)]
    sk.poly(pts)
    sk.poly([(0, 0), (x + 2.0, 0)], w=1.5, dotted=True)
    dots(sk, r1[-1][1] + 0.55, 1.35); dots(sk, r3[-1][1] + 0.55, 1.35)
    sk.arrow(r1[0][0], 4.5, r2[0][1], 4.5); sk.text("50 pulses (potentiation)", (r1[0][0] + r2[0][1]) / 2, 5.2, "c", 20)
    sk.arrow(r3[0][0], -3.5, r4[0][1], -3.5); sk.text("50 pulses (depression)", (r3[0][0] + r4[0][1]) / 2, -4.2, "c", 20)
    sk.text("V\\-(W) = +15 V", 2.5, 4.0, "r", 24); sk.text("V\\-(R) = 1 V", 2.5, 1.85, "r", 24)
    sk.text(f"{MINUS}12 V", 2.5, -3.0, "r", 24); sk.text("0 V", 2.5, -0.5, "r", 22)
    sk.text(cyc, x + 1.0, 3.0, "c", 24)
    save(sk.build(), fname, title)

def s_ltp1():
    s_ltp("S_LTP", "Scheme_LTP_LTD", "LTP/LTD pulse train", "\u00d7 5 cycles")

def s_end():
    s_ltp("S_END", "Scheme_endurance", "Endurance cycling", "\u00d7 2500 cycles")

def s_ml():
    sk = Sketch("S_ML", "Multilevel scheme", (-3.6, 14), (-1.4, 5.8), "left")
    pts = [(0, 0), (0.6, 0), (0.6, 1), (3.0, 1)]
    p1, r1, x = train(3.0, 1, 4, 5, w=0.22, gap=0.22); pts += p1 + [(x + 1.4, 1)]
    xa = x + 1.4
    p2, r2, x = train(xa, 1, 4, 5, w=0.22, gap=0.22); pts += p2 + [(x + 1.8, 1)]
    xb = x + 1.8
    p3, r3, x = train(xb, 1, 4, 5, w=0.22, gap=0.22); pts += p3 + [(x + 1.0, 1)]
    sk.poly(pts); sk.poly([(0, 0), (x + 1.0, 0)], w=1.5, dotted=True)
    dots(sk, xb - 0.8, 1.35)
    sk.arrow(r1[0][0], 4.5, r1[-1][1], 4.5); sk.text("5 pulses", (r1[0][0] + r1[-1][1]) / 2, 5.1, "c", 20)
    sk.text("read", (r1[-1][1] + xa) / 2 + 0.05, 1.6, "c", 16)
    sk.arrow(r1[0][0], -0.9, r3[-1][1], -0.9); sk.text("15 levels", (r1[0][0] + r3[-1][1]) / 2, -0.35, "c", 20)
    levels(sk, 2.7, show0=False)
    save(sk.build(), "Scheme_multilevel", "Multilevel programming: 5 pulses per level")

funcs = [s_iv, s_epsc, s_readv, s_ppf, s_sddp, s_sndp, s_sndp_top, s_la_ret, s_srdp, s_ltp1, s_end, s_ml]
_flt = open(O.S + "/tools/filter.txt").read().split() if os.path.exists(O.S + "/tools/filter.txt") else []
if _flt:
    funcs = [f for f in funcs if any(k in f.__name__ for k in _flt)] or funcs
O.run_all(funcs, "plot3_schemes")
