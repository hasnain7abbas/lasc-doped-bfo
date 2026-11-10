# Paper version of the unidirectional J-E comparison: the same smoothed data as UNI_compare_logJ_E (plot2_iv.uni_compare),
# but J on a log axis (house rule: log-scaled axis, no "log" in the axis title) and no slide title.
# Saves "2 I-V and conduction/UNI_compare_J_E.opju"; the original UNI_compare_logJ_E.opju is not touched.
import os as _os, sys as _sys
try:
    _HERE = _os.path.dirname(_os.path.abspath(__file__))
except NameError:            # Origin "run -pyf" may not define __file__
    _HERE = _os.environ["LASC_PKG"] + "/origin_plots"
_sys.path.insert(0, _os.path.normpath(_os.path.join(_HERE, "..")))
_sys.path.insert(0, _HERE)
import config

import sys, math
pass
import importlib, oplib as O
importlib.reload(O)
import originpro as op

FOLD = "2 I-V and conduction"
M2 = O.manifest2()
NAME = {"BFO": "BiFeO\\-(3)", "La7.5": "La 7.5%", "Sc1": "Sc 1%", "LaSc": "La 7.5%-Sc 1%"}
PLAIN = {"BFO": "BiFeO3", "La7.5": "La 7.5%", "Sc1": "Sc 1%", "LaSc": "La 7.5%-Sc 1%"}
COL = {"BFO": "0,0,0", "La7.5": "230,0,0", "Sc1": "0,170,0", "LaSc": "0,0,230"}
TAGS = ["BFO", "La7.5", "Sc1", "LaSc"]

def uni_log():
    wb, ws = O.book("UNIcmpJ", "Unidirectional J-E, best cycle of each film (log J axis)")
    spec = []; meta = {}
    for t in TAGS:
        d = O.read_csv(f"v2_UNI_{t}"); mt = M2[f"v2_UNI_{t}"]
        E = d["E"]; lj = d["logJ"]; br = d["branch"]
        for b, bn in [(-1, "neg"), (1, "pos")]:
            idx = [i for i in range(len(E)) if br[i] == b and lj[i] is not None]
            if b == -1: idx = idx[::-1]
            ee = [E[i] for i in idx]; ll = [lj[i] for i in idx]
            spec += [(ee, 'X', "E", "kV/cm", f"{PLAIN[t]}, cycle {mt['cycle']}, {bn} branch, d = {mt['d_um']} \\g(m)m"),
                     (ll, 'Y', "log J (raw)", "log(A/cm\\+(2))", "J = |I|/A, A = 3.14e-4 cm\\+(2)"),
                     ([None] * len(ee), 'Y', "log J smoothed", "log(A/cm\\+(2))", "Savitzky-Golay 21 pts, 2nd order (Origin)")]
        meta[t] = mt
    O.cols(ws, spec)
    for k in range(8):
        O.smooth_sg(ws, 3 * k + 1, 3 * k + 2, npts=21, order=2)
    s2 = wb.add_sheet("Plotted (every 3rd)")
    sp2 = []
    for k in range(8):
        x = ws.to_list(3 * k); y = ws.to_list(3 * k + 2)
        yj = [10 ** v if (v is not None and v == v) else None for v in y[::3]]
        sp2 += [(x[::3], 'X', "E", "kV/cm", ws.get_label(3 * k, 'C')), (yj, 'Y', "J", "A/cm\\+(2)", "10^(smoothed log J)")]
    O.cols(s2, sp2)
    g = O.graph("UNIcmpJ", "J-E comparison, log J axis")
    for k in range(8):
        O.plot(g, s2, 2 * k + 1, 2 * k, 's')
    allx = [abs(v) for k in range(8) for v in s2.to_list(2 * k) if v is not None and v == v]
    ally = [math.log10(v) for k in range(8) for v in s2.to_list(2 * k + 1) if v is not None and v == v and v > 0]
    xl = math.ceil(max(allx) / 100) * 100 + 100
    y0 = math.floor(min(ally)); y1 = math.ceil(max(ally)) + (1 if math.ceil(max(ally)) - max(ally) < 0.3 else 0)
    O.style(g, "\\b(\\i(E) \\(40)kV/cm\\(41))", "\\b(\\i(J) \\(40)A/cm\\+(2)\\(41))", ylog=True,
            xr=(-xl, xl, 100), yr=(10 ** y0, 10 ** y1))
    for k in range(8):
        O.pstyle(k + 1, COL[TAGS[k // 2]], None, sym=1, ssize=8, hollow=True)
    O.nolegend()
    O.hline("z0", 0, 10 ** y0, 0, 10 ** y1, w=2.5)
    for j, t in enumerate(TAGS):
        x = s2.to_list(2 * (2 * j + 1)); y = s2.to_list(2 * (2 * j + 1) + 1)
        pts = [(a, b) for a, b in zip(x, y) if a is not None and b is not None and a == a and b == b]
        xe, ye = pts[-1]
        nm = O.text(NAME[t], 0, 0, fs=20, color=COL[t])
        O.lt(f'{nm}.x = {xe} + {nm}.dx/2 + 0.03*(layer.x.to-layer.x.from); {nm}.y = {ye};')
    O.save(g, FOLD, "UNI_compare_J_E", "Unidirectional J-E of the four films, log J axis (best cycle, smoothed)",
           note="; ".join(f"{PLAIN[t]}: cycle {meta[t]['cycle']}, d = {meta[t]['d_um']} um" for t in TAGS))

O.run_all([uni_log], "uni_log")
