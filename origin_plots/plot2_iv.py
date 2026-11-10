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

FOLD = "2 I-V and conduction"
M2 = O.manifest2()
NAME = {"BFO": "BiFeO\\-(3)", "La7.5": "La 7.5%", "Sc1": "Sc 1%", "LaSc": "La 7.5%-Sc 1%"}
PLAIN = {"BFO": "BiFeO3", "La7.5": "La 7.5%", "Sc1": "Sc 1%", "LaSc": "La 7.5%-Sc 1%"}
COL = {"BFO": "0,0,0", "La7.5": "26,111,223", "Sc1": "55,173,107", "LaSc": "230,0,0"}   # same order as the XRD plots (Fig. 2)
TAGS = ["BFO", "La7.5", "Sc1", "LaSc"]

def finite(c):
    return [v for v in c if v is not None and not (isinstance(v, float) and math.isnan(v))]

def smooth_cols(ws, cy, cout, npts):
    O.smooth_sg(ws, cy, cout, npts=npts, order=2)

# ---------------------------------------------------------------- bipolar I-V (Sheet5), smoothed branch by branch
def bipolar():
    d = O.read_csv("IV_bipolar_Sheet5")
    wb, ws = O.book("IVbip", "Bipolar I-V, La 7.5%-Sc 1% (Sheet5)")
    spec = []
    for c in range(1, 6):
        spec += [(d[f"V{c}"], 'X', "Voltage", "V", f"Cycle {c}"), (d[f"I{c}"], 'Y', "Current", "A", f"Cycle {c} (raw)")]
    O.cols(ws, spec)
    s2 = wb.add_sheet("Smoothed branches")
    spec = []; branches = []
    for c in range(1, 6):
        V = finite(d[f"V{c}"]); I = [abs(x) for x in finite(d[f"I{c}"])][:len(V)]
        # turning points: 0 -> +max -> 0 -> -max -> 0
        imax = V.index(max(V)); imin = V.index(min(V))
        i0 = next(i for i in range(imax, len(V)) if V[i] <= 0)
        segs = [(0, imax), (imax, i0), (i0, imin), (imin, len(V) - 1)]
        for b, (a, z) in enumerate(segs):
            vv = V[a:z + 1]; ii = I[a:z + 1]
            li = [math.log10(x) if x > 0 else None for x in ii]
            spec += [(vv, 'X', "Voltage", "V", f"Cycle {c}, branch {b + 1}"),
                     (li, 'Y', "log|I| (raw)", "log A", f"Cycle {c}, branch {b + 1}"),
                     ([None] * len(vv), 'Y', "log|I| smoothed", "log A", "Savitzky-Golay 9 pts, 2nd order (Origin)"),
                     ([None] * len(vv), 'Y', "|I| smoothed", "\\g(m)A", "10^(smoothed log|I|) x 10^6")]
            branches.append((c, b))
    O.cols(s2, spec)
    bk = wb.name
    for k in range(len(branches)):
        base = 4 * k
        smooth_cols(s2, base + 1, base + 2, 9)
        O.lt(f'win -a {bk}; page.active$ = "Smoothed branches"; col({base + 4}) = 10^col({base + 3}) * 1e6;')
    g = O.graph("IVbip", "Bipolar I-V")
    for k in range(len(branches)):
        O.plot(g, s2, 4 * k + 3, 4 * k, 'l')
    O.style(g, "\\b(Voltage \\(40)V\\(41))", "\\b(Current \\(40)\\g(m)A\\(41))", ylog=True, xr=(-15, 18, 5), yr=(1e-4, 10))
    for k, (c, b) in enumerate(branches):
        O.pstyle(k + 1, O.pal(c - 1), 3)
    O.lt('legend -r; legend.text$ = "' + "%(CRLF)".join(f"\\l({4 * (c - 1) + 1}) \\b(Cycle {c})" for c in range(1, 6)) + '";'
         ' legend.font=font("Times New Roman"); legend.fsize=20; legend.background=0;')
    O.at("legend", 0.03, 0.04, anchor="lb")
    O.title_above("Bipolar Voltage Sweep")
    O.save(g, FOLD, "IV_bipolar", "Bipolar I-V sweeps, La 7.5%-Sc 1% (5 cycles, smoothed)",
           note="Sheet5; each branch smoothed separately (Savitzky-Golay, 9 points) in Origin")

# ---------------------------------------------------------------- unidirectional comparison (reference: open circles, labels at the curve ends)
def uni_compare():
    wb, ws = O.book("UNIcmp", "Unidirectional J-E, best cycle of each film")
    spec = []; meta = {}
    for t in TAGS:
        d = O.read_csv(f"v2_UNI_{t}"); mt = M2[f"v2_UNI_{t}"]
        E = d["E"]; lj = d["logJ"]; br = d["branch"]
        for b, bn in [(-1, "neg"), (1, "pos")]:
            idx = [i for i in range(len(E)) if br[i] == b and lj[i] is not None]
            if b == -1: idx = idx[::-1]          # |E| increasing away from 0 on each side
            ee = [E[i] for i in idx]; ll = [lj[i] for i in idx]
            spec += [(ee, 'X', "E", "kV/cm", f"{PLAIN[t]}, cycle {mt['cycle']}, {bn} branch, d = {mt['d_um']} \\g(m)m"),
                     (ll, 'Y', "log J (raw)", "log(A/cm\\+(2))", f"J = |I|/A, A = 3.14e-4 cm\\+(2)"),
                     ([None] * len(ee), 'Y', "log J smoothed", "log(A/cm\\+(2))", "Savitzky-Golay 21 pts, 2nd order (Origin)")]
        meta[t] = mt
    O.cols(ws, spec)
    for k in range(8):
        smooth_cols(ws, 3 * k + 1, 3 * k + 2, 21)
    # thinned copy for open-circle symbols (every 3rd point)
    s2 = wb.add_sheet("Plotted (every 3rd)")
    sp2 = []
    for k in range(8):
        x = ws.to_list(3 * k); y = ws.to_list(3 * k + 2)
        sp2 += [(x[::3], 'X', "E", "kV/cm", ws.get_label(3 * k, 'C')), (y[::3], 'Y', "log J smoothed", "log(A/cm\\+(2))", "")]
    O.cols(s2, sp2)
    g = O.graph("UNIcmp", "J-E comparison")
    for k in range(8):
        O.plot(g, s2, 2 * k + 1, 2 * k, 's')
    allx = [abs(v) for k in range(8) for v in s2.to_list(2 * k) if v == v and v is not None]
    ally = [v for k in range(8) for v in s2.to_list(2 * k + 1) if v == v and v is not None]
    xl = math.ceil(max(allx) / 100) * 100 + 100          # room inside the frame for the end labels
    y0 = math.floor(min(ally)); y1 = math.ceil(max(ally)) + 0.5
    O.style(g, "\\b(\\i(E) \\(40)kV/cm\\(41))", "\\b(log \\i(J) \\(40)A/cm\\+(2)\\(41))", xr=(-xl, xl, 100), yr=(y0, y1, 1))
    for k in range(8):
        t = TAGS[k // 2]
        O.pstyle(k + 1, COL[t], None, sym=1, ssize=8, hollow=True)
    O.nolegend()
    O.hline("z0", 0, y0, 0, y1, w=2.5)
    for j, t in enumerate(TAGS):
        x = s2.to_list(2 * (2 * j + 1)); y = s2.to_list(2 * (2 * j + 1) + 1)
        pts = [(a, b) for a, b in zip(x, y) if a == a and b == b and a is not None and b is not None]
        xe, ye = pts[-1]
        nm = O.text(NAME[t], 0, 0, fs=20, color=COL[t])
        O.lt(f'{nm}.x = {xe} + {nm}.dx/2 + 0.03*(layer.x.to-layer.x.from); {nm}.y = {ye};')
    O.title_above("Unidirectional sweep (-V to +V), best cycle of each film", fs=22)
    O.save(g, FOLD, "UNI_compare_logJ_E", "Unidirectional log J-E of the four films (best cycle, smoothed)",
           note="; ".join(f"{PLAIN[t]}: cycle {meta[t]['cycle']}, d = {meta[t]['d_um']} um" for t in TAGS))

# ---------------------------------------------------------------- conduction: log J - log E with two linear regions
def two_seg(x, y, nmin=8):
    best = None
    def sse(a, b):
        xs, ys = x[a:b + 1], y[a:b + 1]; m = len(xs); mx = sum(xs) / m; my = sum(ys) / m
        sxx = sum((u - mx) ** 2 for u in xs); sxy = sum((u - mx) * (v - my) for u, v in zip(xs, ys))
        bb = sxy / sxx; return sum((v - (my + bb * (u - mx))) ** 2 for u, v in zip(xs, ys))
    for i in range(nmin - 1, len(x) - nmin):
        s = sse(0, i) + sse(i + 1, len(x) - 1)
        if best is None or s < best[0]: best = (s, i)
    return best[1]

SYM = {"BFO": (2, False, "0,0,0"), "La7.5": (1, False, "220,30,30"), "Sc1": (1, True, "128,0,160"), "LaSc": (3, False, "90,90,90")}
LETTER = {"BFO": "(a)", "La7.5": "(b)", "Sc1": "(c)", "LaSc": "(d)"}

def conduction(t):
    def f():
        d = O.read_csv(f"v2_COND_{t}"); mt = M2[f"v2_COND_{t}"]
        n = len(d["logE"])
        wb, ws = O.book("COND", f"Conduction {PLAIN[t]}")
        O.cols(ws, [(d["V"], 'X', "Voltage", "V", f"cycle {mt['cycle']}, {mt['branch']}"),
                    (d["absI"], 'Y', "|I|", "A", ""),
                    (d["E"], 'Y', "E", "kV/cm", f"E = |V|/d, d = {mt['d_um']} \\g(m)m"),
                    (d["J"], 'Y', "J", "A/cm\\+(2)", "J = |I|/A, A = 3.14e-4 cm\\+(2)"),
                    (d["logE"], 'X', "log E", "log(kV/cm)", ""),
                    (d["logJ"], 'Y', "log J (raw)", "log(A/cm\\+(2))", ""),
                    ([None] * n, 'Y', "log J smoothed", "log(A/cm\\+(2))", "Savitzky-Golay 15 pts, 2nd order (Origin)")])
        smooth_cols(ws, 5, 6, 15)
        x = ws.to_list(4); y = ws.to_list(6)
        ok = [i for i in range(n) if x[i] == x[i] and y[i] == y[i]]
        xs = [x[i] for i in ok]; ys = [y[i] for i in ok]
        # breakpoint found on points spaced evenly in log E (so the dense high-field end does not dominate)
        tx, ty, last = [], [], -9
        for u, v in zip(xs, ys):
            if u - last >= 0.02: tx.append(u); ty.append(v); last = u
        kt = two_seg(tx, ty, nmin=5)
        xbreak = 0.5 * (tx[kt] + tx[kt + 1])
        kb = max(i for i in range(len(xs)) if xs[i] <= xbreak)
        r = [(ok[0] + 1, ok[kb] + 1), (ok[kb + 1] + 1, ok[-1] + 1)]
        fits = [O.fitlr(ws, 4, 6, a, b) for a, b in r]
        a1, b1 = fits[0]["a"], fits[0]["b"]; a2, b2 = fits[1]["a"], fits[1]["b"]
        xc = (a1 - a2) / (b2 - b1) if b2 != b1 else xs[kb]
        Ec = 10 ** xc
        lo, hi = min(xs), max(xs)
        l1 = [lo - 0.05, min(xc + 0.2, hi)]; l2 = [max(xc - 0.25, lo), hi + 0.05]
        s2 = wb.add_sheet("Fits")
        O.cols(s2, [(l1, 'X', "log E", "", "region 1"), ([a1 + b1 * v for v in l1], 'Y', "fit 1", "",
                     f"log J = {a1:.3f} + {b1:.3f} log E; n = {b1:.2f} +/- {fits[0]['berr']:.2f}; R\\+(2) = {fits[0]['r2']:.4f}; rows {r[0][0]}-{r[0][1]}"),
                    (l2, 'X', "log E", "", "region 2"), ([a2 + b2 * v for v in l2], 'Y', "fit 2", "",
                     f"log J = {a2:.3f} + {b2:.3f} log E; n = {b2:.2f} +/- {fits[1]['berr']:.2f}; R\\+(2) = {fits[1]['r2']:.4f}; rows {r[1][0]}-{r[1][1]}"),
                    ([Ec], 'Y', "Crossover field", "kV/cm", "intersection of the two fits")])
        # thinned symbols: one point per 0.04 decade of E
        s3 = wb.add_sheet("Plotted points")
        px, py, last = [], [], -9
        for u, v in zip(xs, ys):
            if u - last >= 0.04: px.append(u); py.append(v); last = u
        O.cols(s3, [(px, 'X', "log E", "log(kV/cm)", "smoothed data, thinned to 0.04 decade"), (py, 'Y', "log J smoothed", "log(A/cm\\+(2))", "")])
        g = O.graph("COND", f"log J-log E {PLAIN[t]}")
        O.plot(g, s3, 1, 0, 's'); O.plot(g, s2, 1, 0, 'l'); O.plot(g, s2, 3, 2, 'l')
        x0 = math.floor((lo - 0.1) * 5) / 5; x1 = math.ceil((hi + 0.1) * 5) / 5
        yv = py + [a1 + b1 * v for v in l1] + [a2 + b2 * v for v in l2]
        y0 = math.floor(min(yv) * 2) / 2 - 0.25; y1 = math.ceil(max(yv) * 2) / 2 + 0.25
        O.style(g, "\\b(log \\i(E) \\(40)kV/cm\\(41))", "\\b(log \\i(J) \\(40)A/cm\\+(2)\\(41))", xr=(x0, x1, 0.2), yr=(y0, y1, 0.5))
        O.lt('layer.x.label.numFormat=1; layer.x.label.decPlaces=1; layer.y.label.numFormat=1; layer.y.label.decPlaces=1;')
        sym, hollow, c = SYM[t]
        O.pstyle(1, c, None, sym=sym, ssize=10, hollow=hollow)
        O.pstyle(2, "190,0,190", 3); O.pstyle(3, "165,72,42", 3)
        O.nolegend()
        # crossover marker
        O.lt(f'draw -n xc -l {{{xc},{y0 + 0.08 * (y1 - y0)},{xc},{a2 + b2 * xc + 0.35}}}; xc.linewidth=2; xc.lineType=2; xc.color=color(0,0,220);')
        nm = O.text(f"{Ec:.0f} kV/cm", 0, 0, fs=22, color="0,0,220")
        O.lt(f'{nm}.x = {xc + 0.12} + {nm}.dx/2; {nm}.y = {a2 + b2 * xc - 0.35};')
        O.lt(f'draw -n xa -l {{{xc + 0.11},{a2 + b2 * xc - 0.3},{xc + 0.01},{a2 + b2 * xc - 0.05}}}; xa.linewidth=2; xa.color=color(0,0,220); xa.arrowEndShape=1;')
        nm = O.text(f"n = {b1:.2f}", 0, 0, fs=24, color="190,0,190")
        O.lt(f'{nm}.x = {lo + 0.25 * (xc - lo)} + {nm}.dx/2; {nm}.y = {a1 + b1 * (lo + 0.25 * (xc - lo)) - 0.45};')
        nm = O.text(f"n = {b2:.2f}", 0, 0, fs=24, color="165,72,42")
        # below-right of the high-field line; if that region is short (label would hit the crossover), above-left instead
        if hi - xc >= 0.4:
            O.lt(f'{nm}.x = {hi - 0.08}; {nm}.y = {a2 + b2 * (hi - 0.08) - 0.5};')
        else:
            O.lt(f'{nm}.x = {hi - 0.2}; {nm}.y = {a2 + b2 * (hi - 0.2) + 0.45};')
        nm = O.text(f"{LETTER[t]} {NAME[t]}", 0, 0, fs=24); O.at(nm, 0.04, 0.96, anchor="lt")
        O.L(t, "cycle", mt["cycle"], "n1 %.2f n2 %.2f Ec %.1f kV/cm" % (b1, b2, Ec), "R2", fits[0]["r2"], fits[1]["r2"])
        O.save(g, FOLD + "/Conduction", f"COND_{t}", f"log J-log E, {PLAIN[t]} (negative bias, cycle {mt['cycle']})",
               note=f"n1 = {b1:.2f}, n2 = {b2:.2f}, crossover {Ec:.0f} kV/cm, d = {mt['d_um']} um")
    f.__name__ = "cond_" + t
    return f

funcs = [bipolar, uni_compare] + [conduction(t) for t in TAGS]
_flt = open(O.S + "/tools/filter.txt").read().split() if os.path.exists(O.S + "/tools/filter.txt") else []
if _flt:
    funcs = [f for f in funcs if any(k in f.__name__ for k in _flt)] or funcs
O.run_all(funcs, "plot2_iv")
