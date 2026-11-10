import os as _os, sys as _sys
try:
    _HERE = _os.path.dirname(_os.path.abspath(__file__))
except NameError:            # Origin "run -pyf" may not define __file__
    _HERE = _os.environ["LASC_PKG"] + "/origin_plots"
_sys.path.insert(0, _os.path.normpath(_os.path.join(_HERE, "..")))
_sys.path.insert(0, _HERE)
import config

import sys, os, csv
pass
import importlib, oplib as O
importlib.reload(O)
import originpro as op, math

OC = O.S + "/other_csv/"
GU = "\\g(m)S"
MINUS = "\u2212"; ARROW = "\u2192"

def rd(tag):
    rows = list(csv.reader(open(OC + tag + ".csv", encoding="utf8")))
    head, body = rows[0], rows[1:]
    out = {}
    for j, h in enumerate(head):
        c = []
        for r in body:
            v = r[j] if j < len(r) else ""
            c.append(float(v) if v not in ("", "nan") else None)
        while c and c[-1] is None: c.pop()
        out[h] = c
    return out

def legend_entries(entries, fs=20, frame=0, sep="%(CRLF)"):
    O.lt('legend -r;')
    O.lt('legend.text$ = "' + sep.join(f"\\l({i + 1}) \\b({e})" for i, e in enumerate(entries)) + '";')
    O.lt(f'legend.font=font("Times New Roman"); legend.fsize={fs}; legend.background={frame};')

def bipolar(tag, sample, vmax, xl):
    def f():
        d = rd(tag)
        k = 0.6 / 0.5        # files used d = 0.6 um (5 V -> 83.3 kV/cm); recalculated with d = 0.5 um
        wb, ws = O.book("BIP", f"Bipolar J-E, {sample}")
        spec = []
        for c in range(1, 6):
            spec += [([v * k for v in d[f"x_L1_{c}"]], 'X', "Electric field", "kV/cm", f"Cycle {c}; E = V/d, d = 0.5 \\g(m)m"),
                     (d[f"y_L1_{c}"], 'Y', "Current density", "A/cm\\+(2)", f"Cycle {c}"),
                     (d[f"x_L1_{c}"], 'Y', "Field as in the original graph", "kV/cm", "d = 0.6 \\g(m)m")]
        O.cols(ws, spec)
        g = O.graph("BIP", f"Bipolar {sample}")
        for c in range(5):
            O.plot(g, ws, 3 * c + 1, 3 * c, 'l')
        ymin = min(v for c in range(1, 6) for v in d[f"y_L1_{c}"] if v and v > 0)
        ymax = max(v for c in range(1, 6) for v in d[f"y_L1_{c}"] if v and v > 0)
        y0 = 10 ** math.floor(math.log10(ymin)); y1 = 10 ** math.ceil(math.log10(ymax))     # axis spans the data decades
        O.style(g, "\\b(Electric Field \\(40)kV/cm\\(41))", "\\b(Current Density \\(40)A/cm\\+(2)\\(41))", ylog=True, xr=(-1.12 * xl, 1.12 * xl, xl / 2), yr=(y0, y1))   # a little room beyond the sweep ends
        for c in range(5):
            O.pstyle(c + 1, O.pal(c), 3)
        legend_entries([f"Cycle {c}" for c in range(1, 6)], fs=20)          # one column, like the other graphs
        O.at("legend", 0.03, 0.03, anchor="lb")
        O.page_text("HD", f"0 {ARROW} +{vmax} V {ARROW} {MINUS}{vmax} V {ARROW} 0", 0.5, 0.06, fs=22, anchor="cc")
        O.L(tag, "y range", y0, y1)
        O.save(g, "2 I-V and conduction/Bipolar loops", f"BIP_{tag.split('_')[1]}", f"Bipolar loops, {sample}",
               note="E recalculated with d = 0.5 um (the original graph used 0.6 um); 5 cycles")
    f.__name__ = "bip_" + tag
    return f

def la_ppf():
    d = rd("La_PPF")
    x = [v for v in d["x_L1_1"] if v is not None][:6]; y = d["y_L1_1"][:6]   # rows shown in the original graph (row 7 was outside its plot range)
    wb, ws = O.book("LPPF", "La 7.5%: PPF index")
    O.cols(ws, [(x, 'X', "Pulse interval", "ms", "La 7.5%"), (y, 'Y', "PPF index", "%", "from the original graph")])
    fr = O.fitlr(ws, 0, 1, 1, len(x))
    xs = [0, 2100]
    s2 = wb.add_sheet("Linear fit")
    O.cols(s2, [(xs, 'X', "Pulse interval", "ms", ""), ([fr["a"] + fr["b"] * v for v in xs], 'Y', "Linear fit", "%",
               f"PPF = {fr['a']:.2f} + ({fr['b']:.5f}) dt; R\\+(2) = {fr['r2']:.3f}")])
    g = O.graph("LPPF", "La PPF")
    O.plot(g, ws, 1, 0, 's'); O.plot(g, s2, 1, 0, 'l')
    O.style(g, "\\b(Interval \\(40)ms\\(41))", "\\b(PPF Index \\(40)%\\(41))", xr=(-100, 2200, 500), yr=(60, 180, 20))
    O.pstyle(1, "81,81,81", None, sym=2, ssize=12); O.pstyle(2, "230,0,0", 3); O.lt('layer.plot=2; set %C -d 1;')
    legend_entries(["Raw data", "Fitting"], fs=24); O.at("legend", 0.96, 0.95, anchor="rt")
    O.page_text("PF", f"\\i(R)\\+(2) = {fr['r2']:.3f}", 0.05, 0.92, fs=20)
    O.save(g, "4 Synaptic La 7.5%", "La_PPF_index", "La 7.5%: PPF index vs pulse interval with linear fit",
           note=f"slope {fr['b']:.4f} %/ms, R2 {fr['r2']:.3f}")

def la_ltp():
    d = rd("La_LTP")
    wb, ws = O.book("LLTP", "La 7.5%: LTP/LTD")
    O.cols(ws, [(d["x1"], 'X', "Pulse number", "", "potentiation"), (d["y1"], 'Y', "Conductance", GU, "Potentiation"),
                (d["x2"], 'X', "Pulse number", "", "depression"), (d["y2"], 'Y', "Conductance", GU, "Depression")])
    g = O.graph("LLTP", "La LTP")
    O.plot(g, ws, 1, 0, 's'); O.plot(g, ws, 3, 2, 's')
    O.style(g, "\\b(Pulse Number)", "\\b(Conductance \\(40)\\g(m)S\\(41))", xr=(-30, 1030, 200), yr=(0, 120, 20), wide=True)
    O.pstyle(1, "0,0,0", None, sym=2, ssize=7); O.pstyle(2, "230,0,0", None, sym=2, ssize=7)
    legend_entries(["Potentiation", "Depression"], fs=20); O.at("legend", 0.02, 0.97)
    O.save(g, "4 Synaptic La 7.5%", "La_LTP_LTD", "La 7.5%: LTP/LTD over ten cycles")

def la_ret():
    d = rd("La_RET")
    d = {k: v[:10] for k, v in d.items()}      # rows 1-10 are the ones the original graph plotted (rows 11-12 were outside its range)
    wb, ws = O.book("LRET", "La 7.5%: retention")
    O.cols(ws, [(d["x1"], 'X', "Time", "s", "N = 40"), (d["y1"], 'Y', "Conductance", GU, "N = 40"),
                (d["x2"], 'X', "Time", "s", "N = 60"), (d["y2"], 'Y', "Conductance", GU, "N = 60")])
    g = O.graph("LRET", "La retention")
    O.plot(g, ws, 1, 0, 'y'); O.plot(g, ws, 3, 2, 'y')
    O.style(g, "\\b(Time \\(40)s\\(41))", "\\b(Conductance \\(40)\\g(m)S\\(41))", xlog=True, xr=(0.5, 5000), yr=(0, 0.3, 0.05))
    O.pstyle(1, "81,81,81", 3, sym=1, ssize=12); O.pstyle(2, "230,0,0", 3, sym=2, ssize=12)
    legend_entries(["N=40", "N=60"], fs=20); O.at("legend", 0.72, 0.55)
    O.title_above("Retention")
    O.pulse_inset(g, wb, fx=0.50, fy=0.03, fw=0.47, fh=0.30, vw="5V", vr="0.7V")
    O.save(g, "4 Synaptic La 7.5%", "La_retention", "La 7.5%: retention after 40 and 60 pulses")

funcs = [bipolar("bip_La", "La 7.5%", 5, 100), bipolar("bip_Sc", "Sc 1%", 10, 200), la_ppf, la_ltp, la_ret]
_flt = open(O.S + "/tools/filter.txt").read().split() if os.path.exists(O.S + "/tools/filter.txt") else []
if _flt:
    funcs = [f for f in funcs if any(k in f.__name__ for k in _flt)] or funcs
O.run_all(funcs, "plot3_other")
