import os as _os, sys as _sys
try:
    _HERE = _os.path.dirname(_os.path.abspath(__file__))
except NameError:            # Origin "run -pyf" may not define __file__
    _HERE = _os.environ["LASC_PKG"] + "/origin_plots"
_sys.path.insert(0, _os.path.normpath(_os.path.join(_HERE, "..")))
_sys.path.insert(0, _HERE)
import config

import sys, os, json, math
pass
import importlib, oplib as O
importlib.reload(O)
import originpro as op

FOLD = "5 XRD"
INFO = json.load(open(O.CSV + "xrd_info.json"))
Z = INFO["Z"]
NPTS = 7                                   # Savitzky-Golay window (points, 0.05 deg step), order 2
FILMS = [("BFO", "BiFeO\\-(3)", "BiFeO\\-(3)", "0,0,0"),
         ("La", "Bi\\-(0.925)La\\-(0.075)FeO\\-(3)", "La 7.5%", "26,111,223"),
         ("Sc", "BiFe\\-(0.99)Sc\\-(0.01)O\\-(3)", "Sc 1%", "55,173,107"),
         ("LaSc", "Bi\\-(0.925)La\\-(0.075)Fe\\-(0.99)Sc\\-(0.01)O\\-(3)", "La 7.5%-Sc 1%", "230,0,0")]
TT = "\\b(\\i(2\\g(q))  \\(40)degree\\(41))"
YT = "\\b(Intensity \\(40)arb. unit\\(41))"
# BiFeO3 reflections labelled (card K-alpha1 positions; the films sit within 0.1 deg of them after the correction)
LAB = [("(012)", ["012"]), ("(104)/(110)", ["104", "110"]), ("(006)/(202)", ["006", "202"]), ("(024)", ["024"]),
       ("(116)/(122)", ["116", "122"]), ("(214)/(300)", ["018", "214", "300"]), ("(208)/(220)", ["208", "220"])]
ITO = [30.28, 35.23, 60.28]                # In2O3 (222), (400), (622) of the ITO bottom electrode, as measured

def card(h):
    return INFO["card"].get(h)

def load(tag):
    d = O.read_csv(f"xrd_{tag}")
    return d

def film_book(tag, name, short):
    d = load(tag)
    wb, ws = O.book(f"X{tag}", f"XRD {short}")
    spec = [(d["tth_raw"], 'X', "2\\g(q) as measured", "deg", "instrument scale"),
            (d["tth"], 'X', "2\\g(q) corrected", "deg", f"2\\g(q) - ({Z:+.4f}); offset fitted on the pure BiFeO3 scan"),
            (d["I"], 'Y', "Intensity", "counts", "ASC file (background subtracted by the instrument software)")]
    if tag == "Sc":
        spec += [(d["Pt111"], 'Y', "Pt(111) electrode peak (fit)", "counts", "pseudo-Voigt K\\g(a)\\-(1)+K\\g(a)\\-(2) doublet"),
                 (d["I_clean"], 'Y', "Intensity, Pt(111) removed", "counts", "Intensity - Pt(111) fit")]
    else:
        spec += [(d["I_clean"], 'Y', "Intensity (no Pt peak to remove)", "counts", "")]
    spec += [([None] * len(d["tth"]), 'Y', "Smoothed intensity", "counts", f"Savitzky-Golay, {NPTS} points, order 2 (Origin smooth)")]
    O.cols(ws, spec)
    cy = len(spec) - 2
    O.smooth_sg(ws, cy, cy + 1, npts=NPTS, order=2)
    lt_ = O.colvals(ws, cy + 1)
    O.lt(f'wks.col{cy + 2}.type=1;')       # make sure it is a Y column
    return wb, ws, d["tth"], lt_, cy + 1

def peak_near(x, y, x0, half=0.35):
    best = None
    for xi, yi in zip(x, y):
        if abs(xi - x0) <= half and (best is None or yi > best[1]):
            best = (xi, yi)
    return best

def vlabel(nm, t, x, ytop, fs=20, gap=0.03):
    """vertical (rotated) bold label whose lower end sits just above (x, ytop) in axis units"""
    O.lt(f'label -s -n {nm} "{O.esc(chr(92) + "b(" + t + ")")}"; {nm}.font=font("{O.TNR}"); {nm}.fsize={fs}; {nm}.background=0; {nm}.rotate=90;')
    yr = op.lt_float('layer1.y.to') - op.lt_float('layer1.y.from')
    O.lt(f'{nm}.x = {x}; {nm}.y = {ytop} + {gap * yr} + {nm}.dy/2;')

def hide_y_numbers():
    O.lt('layer.y.ticks=0; layer.y.minorTicks=0; layer.y.showLabels=0; layer.y2.showLabels=0; layer.x.showLabels=1;')

# ------------------------------------------------------------------ stacked comparison of the four films
def compare():
    wb, ws = O.book("XCMP", "XRD comparison (normalised, offset)")
    spec = []; data = {}
    for k, (tag, name, short, col) in enumerate(FILMS):
        wbf, wsf, x, s, cs = film_book(tag, name, short)
        mx = max(v for v in s if v == v)
        y = [v / mx + 1.15 * k for v in s]
        data[tag] = (x, y)
        spec += [(x, 'X', "2\\g(q) corrected", "deg", short),
                 (y, 'Y', "Normalised intensity + offset", "", f"{short}: smoothed / max + {1.15 * k:.2f}")]
    O.cols(ws, spec)
    g = O.graph("XCMP", "XRD comparison")
    for k in range(len(FILMS)):
        O.plot(g, ws, 2 * k + 1, 2 * k, 'l')
    top = 1.15 * (len(FILMS) - 1)
    O.style(g, TT, YT, xr=(20, 80, 10), yr=(-0.15, top + 2.4))
    hide_y_numbers()
    for k, f in enumerate(FILMS):
        O.pstyle(k + 1, f[3], 2.5)
    O.nolegend()
    xt, yt = data["LaSc"]
    for i, (t, hs) in enumerate(LAB[:-1]):          # (208)/(220) too weak to label on the stacked plot
        pos = sum(card(h) for h in hs) / len(hs)
        pk = peak_near(xt, yt, pos, 0.5)
        vlabel(f"H{i}", t, pk[0], pk[1], fs=18)
    for i, p in enumerate(ITO):
        pk = peak_near(xt, yt, p, 0.3)
        O.text("*", pk[0], pk[1] + 0.12, fs=24)
    for k, (tag, name, short, col) in enumerate(FILMS):
        nm = O.text(short, 0, 0, fs=20, color=col)
        O.lt(f'{nm}.x = 79 - {nm}.dx/2; {nm}.y = {1.15 * k + 0.38};')
    nm = O.text("* ITO", 0, 0, fs=20)
    O.lt(f'{nm}.x = 79 - {nm}.dx/2; {nm}.y = {top + 2.2};')
    O.save(g, FOLD, "XRD_comparison", "XRD of the four films (corrected, smoothed, normalised and offset)",
           note=f"offset {Z:+.3f} deg from pure BiFeO3; Pt(111) removed from Sc 1%")

# ------------------------------------------------------------------ zoom on (104)/(110)
def zoom():
    wb, ws = O.book("XZM", "XRD (104)/(110) region")
    spec = []
    for k, (tag, name, short, col) in enumerate(FILMS):
        wbf, wsf, x, s, cs = film_book(tag, name, short)
        sel = [(a, b) for a, b in zip(x, s) if 30.8 <= a <= 33.4]
        mx = max(b for a, b in sel)
        spec += [([a for a, b in sel], 'X', "2\\g(q) corrected", "deg", short),
                 ([b / mx + 0.9 * k for a, b in sel], 'Y', "Normalised intensity + offset", "", short)]
    O.cols(ws, spec)
    g = O.graph("XZM", "XRD zoom")
    for k in range(len(FILMS)):
        O.plot(g, ws, 2 * k + 1, 2 * k, 'l')
    O.style(g, TT, YT, xr=(30.8, 33.4, 0.5), yr=(-0.1, 0.9 * 3 + 1.45))
    hide_y_numbers()
    for k, f in enumerate(FILMS):
        O.pstyle(k + 1, f[3], 3)
    O.nolegend()
    c104, c110 = card("104") + INFO["fits"]["BFO"]["corrected_off"], card("110") + INFO["fits"]["BFO"]["corrected_off"]
    for nm, xv in (("D1", c104), ("D2", c110)):
        O.hline(nm, xv, -0.1, xv, 0.9 * 3 + 1.2, w=2, color="gray", dash=2)
    O.text("(104)", c104 - 0.12, 0.9 * 3 + 1.32, fs=20)
    O.text("(110)", c110 + 0.12, 0.9 * 3 + 1.32, fs=20)
    for k, (tag, name, short, col) in enumerate(FILMS):
        nm = O.text(short, 0, 0, fs=20, color=col)
        O.lt(f'{nm}.x = 33.35 - {nm}.dx/2; {nm}.y = {0.9 * k + 0.3};')
    O.save(g, FOLD, "XRD_104_110_zoom", "(104)/(110) region of the four films; dashed lines = pure BiFeO3 peak positions")

# ------------------------------------------------------------------ one full pattern per film (FYP style)
def single(tag, name, short, col):
    def f():
        wb, ws, x, s, cs = film_book(tag, name, short)
        g = O.graph(f"XS{tag}", f"XRD {short}")
        O.plot(g, ws, cs, 1, 'l')
        mx = max(v for v in s if v == v)
        O.style(g, TT, YT, xr=(20, 80, 10), yr=(-0.12 * mx, 1.55 * mx))
        hide_y_numbers()
        O.pstyle(1, "0,0,0", 2.5)
        O.legend("\\l(1) " + "\\b(" + name + ")", fs=22)
        O.at("legend", 0.97, 0.97, anchor="rt")
        for i, (t, hs) in enumerate(LAB):
            pos = sum(card(h) for h in hs) / len(hs)
            pk = peak_near(x, s, pos, 0.5)
            vlabel(f"H{i}", t, pk[0], pk[1], fs=20)
        for i, p in enumerate(ITO):
            pk = peak_near(x, s, p, 0.3)
            O.text("*", pk[0], pk[1] + 0.07 * mx, fs=24)
        nm = O.text("* ITO", 0, 0, fs=20)
        O.lt(f'{nm}.x = 79 - {nm}.dx/2; {nm}.y = {1.22 * mx};')
        O.save(g, FOLD + "/Single patterns", f"XRD_{tag}", f"XRD {short} (corrected, smoothed)")
    f.__name__ = "single_" + tag
    return f

# ------------------------------------------------------------------ (104)/(110) deconvolution (Origin nlfit, 2 pseudo-Voigt peaks)
def pvoigt(x, y0, xc, w, A, mu):
    L = 2 / math.pi * w / (4 * (x - xc) ** 2 + w * w)
    G = math.sqrt(4 * math.log(2)) / (math.sqrt(math.pi) * w) * math.exp(-4 * math.log(2) * (x - xc) ** 2 / (w * w))
    return A * (mu * L + (1 - mu) * G)

# NOTE (11 Nov 2026): this Origin nlfit left the (104)/(110) positions at their starting values for BiFeO3 and Sc 1 %.
# The paper uses the converged refit of analysis/xrd/prep_xrd_doublet.py; origin_plots/xrd_decon_v2.py writes it into
# the XRD_decon_*.opju projects made here (styling kept). Run this script first, then xrd_decon_v2.py.
def decon(tag, name, short, col):
    def f():
        wb, ws, x, s, cs = film_book(tag, name, short)
        lo, hi = 30.95, 33.05
        sel = [(a, b) for a, b in zip(x, s) if lo <= a <= hi]
        xs, ys = [a for a, b in sel], [b for a, b in sel]
        d = wb.add_sheet("Deconvolution")
        O.cols(d, [(xs, 'X', "2\\g(q) corrected", "deg", f"{lo}-{hi} deg"), (ys, 'Y', "Smoothed intensity", "counts", "fitted data")])
        off = INFO["fits"][tag]["corrected_off"]
        x1, x2 = card("104") + off, card("110") + off
        bk = wb.name
        O.lt(f'nlbegin iy:=[{bk}]"Deconvolution"!(1,2) func:=PsdVoigt1 nltree:=tt replica:=1;')
        mx = max(ys)
        O.lt(f'tt.y0=0; tt.xc={x1}; tt.xc__2={x2}; tt.w=0.3; tt.w__2=0.3; tt.A={mx * 0.25}; tt.A__2={mx * 0.25}; tt.mu=0.7; tt.mu__2=0.7; tt.f_mu=1; tt.f_mu__2=1;')   # Lorentz fraction fixed (whole-pattern fit of BiFeO3: 0.69)
        O.lt('nlfit; nlfit;')
        P = {k: op.lt_float(f"tt.{k}") for k in ["y0", "xc", "xc__2", "w", "w__2", "A", "A__2", "mu", "mu__2"]}
        E = {k: op.lt_float(f"tt.e_{k}") for k in ["xc", "xc__2", "w", "w__2"]}
        O.lt('nlend;')
        O.L(tag, "fit", P, E)
        c1 = [pvoigt(v, 0, P["xc"], P["w"], P["A"], P["mu"]) + P["y0"] for v in xs]
        c2 = [pvoigt(v, 0, P["xc__2"], P["w__2"], P["A__2"], P["mu__2"]) + P["y0"] for v in xs]
        cum = [a + b - P["y0"] for a, b in zip(c1, c2)]
        base = [P["y0"]] * len(xs)
        m = sum(ys) / len(ys); r2 = 1 - sum((a - b) ** 2 for a, b in zip(ys, cum)) / sum((a - m) ** 2 for a in ys)
        # the lower-angle peak is (104), the higher-angle one (110)
        lowfirst = P["xc"] <= P["xc__2"]
        p104 = (P["xc"], P["w"], c1) if lowfirst else (P["xc__2"], P["w__2"], c2)
        p110 = (P["xc__2"], P["w__2"], c2) if lowfirst else (P["xc"], P["w"], c1)
        O.cols(d, [(p104[2], 'Y', "(104)R peak", "counts", f"PsdVoigt1 (mu = 0.7 fixed): xc = {p104[0]:.3f} deg, FWHM = {p104[1]:.3f} deg"),
                   (p110[2], 'Y', "(110)R peak", "counts", f"PsdVoigt1 (mu = 0.7 fixed): xc = {p110[0]:.3f} deg, FWHM = {p110[1]:.3f} deg"),
                   (cum, 'Y', "Cumulative fit", "counts", f"R\\+(2) = {r2:.4f}"),
                   (base, 'Y', "Baseline", "counts", "fitted constant y0")], start=2)
        g = O.graph(f"XD{tag}", f"Deconvolution {short}")
        for c in (1, 2, 3, 5, 4):
            O.plot(g, d, c, 0, 'l')
        ymin = min(min(ys), P["y0"]);
        O.style(g, TT, YT, xr=(31, 33, 0.5), yr=(ymin - 0.08 * mx, 1.42 * mx))
        hide_y_numbers()
        O.pstyle(1, "81,81,81", 3); O.pstyle(2, "241,64,64", 4); O.pstyle(3, "26,111,223", 4)
        O.pstyle(4, "177,119,222", 4); O.pstyle(5, "204,153,0", 4)
        O.legend("\\l(2) \\b((104)\\-(R))%(CRLF)\\l(3) \\b((110)\\-(R))", fs=26)
        O.at("legend", 0.04, 0.70, anchor="lt")
        O.page_text("NM", name, 0.03, 0.08, fs=26)
        O.save(g, FOLD + "/Deconvolution", f"XRD_decon_{tag}", f"(104)/(110) deconvolution, {short}",
               note=f"(104) {p104[0]:.3f} deg FWHM {p104[1]:.3f}; (110) {p110[0]:.3f} deg FWHM {p110[1]:.3f}; R2 {r2:.4f}")
        json.dump(dict(tag=tag, p104=p104[:2], p110=p110[:2], r2=r2, A=(P["A"], P["A__2"]), mu=(P["mu"], P["mu__2"]), y0=P["y0"]),
                  open(O.S + f"/xrd/decon_{tag}.json", "w"))
    f.__name__ = "decon_" + tag
    return f

# ------------------------------------------------------------------ Pt(111) removal shown for Sc 1%
def pt_removal():
    d = load("Sc")
    sel = [i for i, v in enumerate(d["tth"]) if 37.5 <= v <= 41.5]
    wb, ws = O.book("XPT", "Sc 1%: Pt(111) removal")
    O.cols(ws, [([d["tth"][i] for i in sel], 'X', "2\\g(q) corrected", "deg", ""),
                ([d["I"][i] for i in sel], 'Y', "As measured", "counts", ""),
                ([d["Pt111"][i] for i in sel], 'Y', "Pt(111) fit", "counts", "pseudo-Voigt doublet"),
                ([d["I_clean"][i] for i in sel], 'Y', "Pt(111) removed", "counts", "")])
    g = O.graph("XPT", "Pt removal")
    for c in (1, 2, 3):
        O.plot(g, ws, c, 0, 'l')
    O.style(g, TT, "\\b(Intensity \\(40)counts\\(41))", xr=(37.5, 41.5, 1), yr=(-50, 400, 100))
    O.pstyle(1, "81,81,81", 2.5); O.pstyle(2, "26,111,223", 3); O.pstyle(3, "230,0,0", 3)
    O.lt('layer.plot=2; set %C -d 1;')
    O.legend("\\l(1) \\b(As measured)%(CRLF)\\l(2) \\b(Pt(111) fit)%(CRLF)\\l(3) \\b(Pt(111) removed)", fs=22)
    O.at("legend", 0.03, 0.97, anchor="lt")
    pt = INFO["Pt111"]
    O.page_text("PT", "BiFe\\-(0.99)Sc\\-(0.01)O\\-(3)", 0.97, 0.06, fs=22, anchor="rc")
    O.save(g, FOLD, "XRD_Sc_Pt_removal", "Sc 1%: Pt(111) electrode peak and its removal",
           note=f"Pt(111) at {pt['center_corrected']:.3f} deg (corrected), FWHM {pt['fwhm']:.3f} deg")

funcs = [compare, zoom] + [single(*f) for f in FILMS] + [decon(*f) for f in FILMS] + [pt_removal]
_flt = open(O.S + "/tools/filter.txt").read().split() if os.path.exists(O.S + "/tools/filter.txt") else []
if _flt:
    funcs = [f for f in funcs if any(k in f.__name__ for k in _flt)] or funcs
O.run_all(funcs, "plot4_xrd")
