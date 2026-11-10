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

FOLD = "2 I-V and conduction/Conduction"
M2 = O.manifest2()
PLAIN = {"BFO": "BiFeO3", "La7.5": "La 7.5%", "Sc1": "Sc 1%", "LaSc": "La 7.5%-Sc 1%"}

def two_seg(x, y, nmin=5):
    best = None
    def sse(a, b):
        xs, ys = x[a:b + 1], y[a:b + 1]; m = len(xs); mx = sum(xs) / m; my = sum(ys) / m
        sxx = sum((u - mx) ** 2 for u in xs); sxy = sum((u - mx) * (v - my) for u, v in zip(xs, ys))
        bb = sxy / sxx; return sum((v - (my + bb * (u - mx))) ** 2 for u, v in zip(xs, ys))
    for i in range(nmin - 1, len(x) - nmin):
        s = sse(0, i) + sse(i + 1, len(x) - 1)
        if best is None or s < best[0]: best = (s, i)
    return best[1]

def nice_top(v):
    k = 10 ** math.floor(math.log10(v))
    for m in (1, 2, 3, 5, 10):
        if m * k >= v: return m * k

def cond(tag, br):
    def f():
        key = f"v4_COND_{tag}_{br}"
        d = O.read_csv(key); mt = M2[key]; n = len(d["logE"])
        lab = "(a) Positive branch" if br == "pos" else "(b) Negative branch"
        wb, ws = O.book("COND", f"Conduction {PLAIN[tag]} {br}")
        O.cols(ws, [(d["V"], 'X', "Voltage", "V", f"cycle {mt['cycle']} (lowest noise), {'positive' if br == 'pos' else 'negative'} bias, |V| >= 1.5 V"),
                    (d["absI"], 'Y', "|I|", "A", ""),
                    (d["E"], 'Y', "E", "kV/cm", f"E = |V|/d, d = {mt['d_um']} \\g(m)m"),
                    (d["J"], 'Y', "J", "A/cm\\+(2)", "J = |I|/A, A = 3.14e-4 cm\\+(2)"),
                    (d["logE"], 'X', "log E", "", ""), (d["logJ"], 'Y', "log J (raw)", "", ""),
                    ([None] * n, 'Y', "log J smoothed", "", "Savitzky-Golay 15 pts, 2nd order (Origin smooth)")])
        O.smooth_sg(ws, 5, 6, 15)
        x = ws.to_list(4); y = ws.to_list(6)
        ok = [i for i in range(n) if x[i] == x[i] and y[i] == y[i]]
        xs = [x[i] for i in ok]; ys = [y[i] for i in ok]
        tx0, ty0, last = [], [], -9
        for u, v in zip(xs, ys):
            if u - last >= 0.02: tx0.append(u); ty0.append(v); last = u
        # two linear regions; if they come out (nearly) parallel, the first points (low-voltage charging hump)
        # are dropped step by step until a real crossover appears (dropped points stay on the graph, unfitted)
        def lsq(xx, yy):
            m = len(xx); mx = sum(xx) / m; my = sum(yy) / m
            sxx = sum((u - mx) ** 2 for u in xx); b = sum((u - mx) * (v - my) for u, v in zip(xx, yy)) / sxx
            return b, sum((v - (my + b * (u - mx))) ** 2 for u, v in zip(xx, yy))
        for drop in range(0, int(0.4 * len(tx0)) + 1):
            tx, ty = tx0[drop:], ty0[drop:]
            kt = two_seg(tx, ty, nmin=5)
            bA, _ = lsq(tx[:kt + 1], ty[:kt + 1]); bB, _ = lsq(tx[kt + 1:], ty[kt + 1:])
            if bB - bA < 0.3:       # best-SSE split not a real crossover: best split among those with dn >= 0.3
                cands = []
                for k in range(4, len(tx) - 5):
                    b_1, s_1 = lsq(tx[:k + 1], ty[:k + 1]); b_2, s_2 = lsq(tx[k + 1:], ty[k + 1:])
                    if b_2 - b_1 >= 0.3: cands.append((s_1 + s_2, k))
                if cands: kt = min(cands)[1]
            xb = 0.5 * (tx[kt] + tx[kt + 1]); start = tx[0]
            okf = [i for i in ok if x[i] >= start - 1e-9]
            kb = max(j for j, i in enumerate(okf) if x[i] <= xb)
            r = [(okf[0] + 1, okf[kb] + 1), (okf[kb + 1] + 1, okf[-1] + 1)]
            f1, f2 = O.fitlr(ws, 4, 6, *r[0]), O.fitlr(ws, 4, 6, *r[1])
            a1, b1, a2, b2 = f1["a"], f1["b"], f2["a"], f2["b"]
            xc = (a1 - a2) / (b2 - b1) if abs(b2 - b1) > 1e-6 else 99
            if abs(b2 - b1) >= 0.3 and start < xc < max(xs):
                break
        Ec = 10 ** xc
        lo, hi = start, max(xs)
        O.L(tag, br, "fit starts at E =", round(10 ** start, 1), "kV/cm (dropped", drop, "log-spaced points)")
        L1 = [lo - 0.06, xc + 0.22]; L2 = [xc - 0.22, hi + 0.06]
        s2 = wb.add_sheet("Fits")
        O.cols(s2, [([10 ** v for v in L1], 'X', "E", "kV/cm", "region 1"), ([10 ** (a1 + b1 * v) for v in L1], 'Y', "fit 1", "A/cm\\+(2)",
                     f"log J = {a1:.3f} + {b1:.3f} log E; n = {b1:.2f} +/- {f1['berr']:.2f}; R\\+(2) = {f1['r2']:.4f}"),
                    ([10 ** v for v in L2], 'X', "E", "kV/cm", "region 2"), ([10 ** (a2 + b2 * v) for v in L2], 'Y', "fit 2", "A/cm\\+(2)",
                     f"log J = {a2:.3f} + {b2:.3f} log E; n = {b2:.2f} +/- {f2['berr']:.2f}; R\\+(2) = {f2['r2']:.4f}"),
                    ([Ec], 'Y', "Crossover field", "kV/cm", "intersection of the two fits")])
        s3 = wb.add_sheet("Plotted points")
        px, py, last = [], [], -9
        for u, v in zip(xs, ys):
            if u - last >= 0.03: px.append(10 ** u); py.append(10 ** v); last = u
        O.cols(s3, [(px, 'X', "E", "kV/cm", "smoothed, thinned to 0.03 decade"), (py, 'Y', "J", "A/cm\\+(2)", "")])
        g = O.graph("COND", f"J-E {PLAIN[tag]} {br}")
        O.plot(g, s3, 1, 0, 's'); O.plot(g, s2, 1, 0, 'l'); O.plot(g, s2, 3, 2, 'l')
        x0 = 10; x1 = nice_top(10 ** (hi + 0.2))
        y0 = 10 ** math.floor(min(ys) - 0.35); y1 = 10 ** math.ceil(max(ys) + 0.35)
        O.style(g, "\\b(\\i(E) \\(40)kV/cm\\(41))", "\\b(\\i(J) \\(40)A/cm\\+(2)\\(41))", xlog=True, ylog=True, xr=(x0, x1), yr=(y0, y1))
        O.pstyle(1, "0,0,0", None, sym=1, ssize=8)
        O.pstyle(2, "230,0,0", 3); O.pstyle(3, "230,0,0", 3)
        O.nolegend()
        P = lambda lx, ly: (10 ** lx, 10 ** ly)
        yc = a2 + b2 * xc
        X, Y1 = P(xc, yc - 0.75); _, Y2 = P(xc, yc + 0.55)
        O.lt(f'draw -n xc -l {{{X},{Y1},{X},{Y2}}}; xc.linewidth=2; xc.lineType=2; xc.color=color(0,0,0);')
        def put(nm, t, lx, ly, color, anchor="c", fs=22):
            O.lt(f'label -s -n {nm} "{O.esc(chr(92) + "b(" + t + ")")}"; {nm}.font=font("Times New Roman"); {nm}.fsize={fs}; {nm}.background=0; {nm}.color=color({color});')
            O.lt(f'{nm}.x = {10 ** lx}; {nm}.y = {10 ** ly};')
            if anchor == "l":
                O.lt(f'{nm}.left = {nm}.left + {nm}.width/2;')
            elif anchor == "r":
                O.lt(f'{nm}.left = {nm}.left - {nm}.width/2;')
        put("n1", f"n = {b1:.2f}", lo + 0.18, a1 + b1 * (lo + 0.18) - 0.42, "230,0,230")
        put("n2", f"n = {b2:.2f}", xc - 0.04, yc + 0.6, "139,0,0", anchor="r")
        put("ec", f"{Ec:.0f} kV/cm", xc + 0.05, yc - 0.55, "0,0,230", anchor="l")
        nm = O.text(lab, 0, 0, fs=22); O.at(nm, 0.04, 0.96, anchor="lt")
        O.L(tag, br, "cycle", mt["cycle"], "n1 %.2f n2 %.2f Ec %.0f" % (b1, b2, Ec), "R2 %.4f %.4f" % (f1["r2"], f2["r2"]))
        O.save(g, FOLD, f"COND_{tag}_{br}", f"J-E {PLAIN[tag]}, {'positive' if br == 'pos' else 'negative'} branch",
               note=f"n1 = {b1:.2f}, n2 = {b2:.2f}, crossover {Ec:.0f} kV/cm (cycle {mt['cycle']}, d = {mt['d_um']} um)")
    f.__name__ = f"cond_{tag}_{br}"
    return f

funcs = [cond(t, b) for t in ["BFO", "La7.5", "Sc1", "LaSc"] for b in ["pos", "neg"]]
_flt = open(O.S + "/tools/filter.txt").read().split() if os.path.exists(O.S + "/tools/filter.txt") else []
if _flt:
    funcs = [f for f in funcs if any(k in f.__name__ for k in _flt)] or funcs
O.run_all(funcs, "plot3_cond")
