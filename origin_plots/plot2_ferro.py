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

FOLD = "1 Ferroelectric"
UC = "\\g(m)C/cm\\+(2)"
PT = "\\b(Polarization \\(40)\\g(m)C/cm\\+(2)\\(41))"
ET = "\\b(Electric Field \\(40)kV/cm\\(41))"
M2 = O.manifest2()
NAME = {"BFO": "BiFeO\\-(3)", "La7.5": "La 7.5%", "Sc1": "Sc 1%", "LaSc": "La 7.5%-Sc 1%"}
PLAIN = {"BFO": "BiFeO3", "La7.5": "La 7.5%", "Sc1": "Sc 1%", "LaSc": "La 7.5%-Sc 1%"}
SAMPLE_COL = {"BFO": "0,0,0", "La7.5": "26,111,223", "Sc1": "55,173,107", "LaSc": "230,0,0"}   # same order as the XRD plots (Fig. 2)

def nice(v, n=4):
    raw = v / n; k = 10 ** math.floor(math.log10(raw))
    for m in (1, 2, 2.5, 5, 10):
        if m * k >= raw:
            step = m * k; break
    return math.ceil(v * 1.03 / step) * step, step

def legend_list(entries, fs=17, frame=1):
    O.lt('legend -r;')
    O.lt('legend.text$ = "' + "%(CRLF)".join(f"\\l({i + 1}) \\b({e})" for i, e in enumerate(entries)) + '";')
    O.lt(f'legend.font=font("Times New Roman"); legend.fsize={fs}; legend.background={frame};')

def box_label(t, fx=0.03, fy=0.04, fs=24, frame=1):
    O._lab[0] += 1
    nm = f"T{O._lab[0]}"
    O.lt(f'label -s -n {nm} "{O.esc(chr(92) + "b(" + t + ")")}"; {nm}.font=font("Times New Roman"); {nm}.fsize={fs}; {nm}.background={frame};')
    O.at(nm, fx, 1 - fy, anchor="lt")
    return nm

# ------------------------------------------------------------------ P-E loops (point 2)
def make_pe(tag):
    def f():
        d = O.read_csv(f"v2_PE_{tag}"); mt = M2[f"v2_PE_{tag}"]; volts = mt["volts"]
        wb, ws = O.book("PE", f"P-E loops {PLAIN[tag]}")
        spec = []
        for i, v in enumerate(volts):
            spec += [(d[f"E_{v}V"], 'X', "Electric field", "kV/cm", f"{v} V; E = V/d, d = {mt['d_um']} \\g(m)m"),
                     (d[f"P_{v}V"], 'Y', "Polarization", UC, f"{v} V"),
                     (d[f"Erec_{v}V"], 'Y', "Field as recorded", "kV/cm", f"{v} V; tester thickness {mt['d_rec_um'][i]} \\g(m)m")]
        O.cols(ws, spec)
        O.lt(f'win -a {wb.name};' + "".join(f' wks.col{3 * i + 3}.type = 4;' for i in range(len(volts))))   # recorded field = 2nd X
        g = O.graph("PEgraph", f"P-E {PLAIN[tag]}")
        n = len(volts)
        pick = sorted(set(round(j * (n - 1) / 4) for j in range(5)))      # five loops, evenly spread, highest included
        for i in pick:
            O.plot(g, ws, 3 * i + 1, 3 * i, 'l')
        emax = max(abs(x) for i in pick for x in d[f"E_{volts[i]}V"] if x is not None)
        pmax = max(abs(x) for i in pick for x in d[f"P_{volts[i]}V"] if x is not None)
        xl, xs = nice(emax, 2 if emax > 700 else 4); yl, ys = nice(pmax)
        O.style(g, ET, PT, xr=(-xl, xl, xs), yr=(-yl, yl, ys))
        for j, i in enumerate(pick):
            O.pstyle(j + 1, ["0,0,0", "230,0,0", "0,0,230", "0,160,0", "160,0,200"][j], 4)
        O.hline("zx", -xl, 0, xl, 0, w=3); O.hline("zy", 0, -yl, 0, yl, w=3)
        legend_list([f"{volts[i]} V" for i in pick], fs=20, frame=0)
        O.at("legend", 0.97, 0.04, anchor="rb")
        O.L(tag, "loops plotted", [volts[i] for i in pick])
        box_label(NAME[tag], fs=24)
        O.save(g, FOLD + "/P-E loops", f"PE_{tag}", f"P-E loops, {PLAIN[tag]}",
               note=f"E = V/d with d = {mt['d_um']} um (recorded field kept as a second X column)")
    f.__name__ = "pe_" + tag
    return f

def pe_compare():
    d = O.read_csv("v2_PE_compare25")
    tags = ["BFO", "La7.5", "Sc1", "LaSc"]
    wb, ws = O.book("PEcmp", "P-E comparison at 25 V")
    spec = []
    for t in tags:
        spec += [(d[f"E_{t}"], 'X', "Electric field", "kV/cm", f"{PLAIN[t]}, 25 V, d = {M2['v2_PE_' + t]['d_um']} \\g(m)m"),
                 (d[f"P_{t}"], 'Y', "Polarization", UC, f"{PLAIN[t]}, 25 V")]
    O.cols(ws, spec)
    g = O.graph("PEcmp", "P-E 25 V comparison")
    for k in range(4):
        O.plot(g, ws, 2 * k + 1, 2 * k, 'l')
    emax = max(abs(x) for t in tags for x in d[f"E_{t}"] if x is not None)
    pmax = max(abs(x) for t in tags for x in d[f"P_{t}"] if x is not None)
    xl, xs = nice(emax); yl, ys = nice(pmax)
    O.style(g, ET, PT, xr=(-xl, xl, xs), yr=(-yl, yl, ys))
    for k, t in enumerate(tags):
        O.pstyle(k + 1, SAMPLE_COL[t], 4)
    O.hline("zx", -xl, 0, xl, 0, w=3); O.hline("zy", 0, -yl, 0, yl, w=3)
    legend_list([NAME[t] for t in tags], fs=20, frame=0)
    O.at("legend", 0.97, 0.04, anchor="rb")
    nm = O.text("25 V", 0, 0, fs=24); O.at(nm, 0.04, 0.96, anchor="lt")
    O.save(g, FOLD + "/P-E loops", "PE_compare_25V", "P-E loops of the four compositions at 25 V")

# ------------------------------------------------------------------ PUND (reference style: E left, P right)
PUND = ["La7.5_25V", "Sc1_25V", "LaSc_25V", "LaSc_26V", "LaSc_27V"]

def make_pund(key):
    def f():
        d = O.read_csv(f"v2_PUND_{key}"); mt = M2[f"v2_PUND_{key}"]; tag = mt["tag"]
        wb, ws = O.book("PUND", f"PUND {PLAIN[tag]} {mt['V']:.0f} V")
        O.cols(ws, [(d["t"], 'X', "Time", "s", "as recorded"),
                    (d["E"], 'Y', "Electric field", "kV/cm", f"E = V/d, d = {mt['d_um']} \\g(m)m"),
                    (d["Erec"], 'Y', "Field as recorded", "kV/cm", f"tester thickness {mt['header']['thickness (um)']} \\g(m)m"),
                    (d["P"], 'Y', "Polarization", UC, "charge density x 100"),
                    (d["Pfit"], 'Y', "Linear fit on U pulse", UC, f"slope = LC = {mt['LC']:.1f} mA/cm\\+(2)"),
                    (d["ts"], 'X', "Time (thinned)", "s", "every 6th point + pulse edges, for symbols"),
                    (d["Es"], 'Y', "E (thinned)", "kV/cm", ""), (d["Ps"], 'Y', "P (thinned)", UC, "")])
        s3 = wb.add_sheet("Results")
        O.cols(s3, [(["P\\-(r)", "PC", "LC"], 'X', "Quantity", "", ""),
                    ([mt["Pr"], mt["PC"], mt["LC"]], 'Y', "Value", "", ""),
                    ([UC, UC, "mA/cm\\+(2)"], 'Y', "Unit", "", ""),
                    (["P(relaxed after P) - P(relaxed after U)", "P(end of U pulse) - P(relaxed after U)",
                      "slope dP/dt on the U pulse (last 75 %)"], 'Y', "Definition", "", "")])
        g = O.graph("PUND", f"PUND {PLAIN[tag]}")
        O.plot(g, ws, 6, 5, 'y')                        # E (left axis)
        Emax = max(abs(v) for v in d["E"] if v is not None)
        Pmax = max(abs(v) for v in d["P"] if v is not None)
        el, es = nice(Emax * 1.1, 4); pl, ps = nice(Pmax * 1.1, 3)
        tmax = max(v for v in d["t"] if v is not None)
        O.style(g, "\\b(Time \\(40)s\\(41))", "\\b(\\i(E) \\(40)kV/cm\\(41))", xr=(-0.0002, round(tmax + 0.0002, 4), 0.001),
                yr=(-el, el, es), right_axis=True, tick=26)
        O.lt('layer.x.label.numFormat=1; layer.x.label.decPlaces=3;')
        O.pstyle(1, "81,81,81", 1.5, sym=2, ssize=5)
        O.nolegend()
        # right Y layer for polarization
        O.lt(f'win -a {g.name}; layadd type:=2;')
        g[1].add_plot(ws, coly=7, colx=5, type='s')     # P thinned (red symbols)
        g[1].add_plot(ws, coly=4, colx=0, type='l')     # U-pulse fit (blue)
        O.lt(f'layer -s 2; layer.unit=1; layer.left={O.LAYER1["left"]}; layer.top={O.LAYER1["top"]}; layer.width={O.LAYER1["width"]}; layer.height={O.LAYER1["height"]};')
        O.lt(f'layer.y.from={-pl}; layer.y.to={pl}; layer.y.inc={ps}; layer.x.from=-0.0002; layer.x.to={round(tmax + 0.0002, 4)};')
        O.lt('layer.y2.label.font=font("Times New Roman"); layer.y2.label.pt=26; layer.y2.label.bold=1; layer.y2.label.color=color(230,0,0);')
        O.lt('layer.y.label.font=font("Times New Roman"); layer.y.label.pt=26; layer.y.label.bold=1; layer.y.label.color=color(230,0,0);')
        O.lt('layer -s 2; layer.y.showAxes=2; layer.y.showLabels=2; layer.x.showAxes=0; layer.x.showLabels=0;'
             ' layer.y2.thickness=4; layer.y2.tickThickness=2.5; layer.y2.tickLength=8; layer.y2.ticks=10; layer.y.ticks=10;')
        O.lt('layer.plot=1; set %C -k 2; set %C -z 6; set %C -c color(230,0,0); set %C -cse color(230,0,0); set %C -csf color(230,0,0);')
        O.lt('layer.plot=2; set %C -w 2500; set %C -c color(0,0,230);')
        O.lt(f'layer -s 2; yr.text$ = "{O.esc(chr(92) + "b(Polarization " + chr(92) + "(40)" + UC + chr(92) + "(41))")}"; yr.font=font("Times New Roman"); yr.fsize=28; yr.color=color(230,0,0);')
        O.lt('label -r legend;')
        # PC bracket on the P layer
        t1 = mt["tUend"]; dx = 0.00042
        O.lt(f'layer -s 2; draw -n pc1 -l {{{t1},{mt["pU_end"]},{t1 + dx},{mt["pU_end"]}}}; pc1.linewidth=2; pc1.color=color(0,0,0);')
        O.lt(f'draw -n pc2 -l {{{t1},{mt["pU_relax"]},{t1 + dx},{mt["pU_relax"]}}}; pc2.linewidth=2; pc2.color=color(0,0,0);')
        O.lt(f'draw -n pc3 -l {{{t1 + 0.8 * dx},{mt["pU_end"]},{t1 + 0.8 * dx},{mt["pU_relax"]}}}; pc3.linewidth=2.5; pc3.color=color(0,176,80);'
             ' pc3.arrowBeginShape=1; pc3.arrowEndShape=1;')
        # label sits above the upper bracket line, centred on the arrow, so it touches neither line nor data
        O.lt(f'label -s -n pct "\\b(PC)"; pct.font=font("Times New Roman"); pct.fsize=20; pct.color=color(0,176,80); pct.background=0;'
             f' pct.x = {t1 + 0.8 * dx}; pct.y = {mt["pU_end"]} + pct.dy/2 + 0.02*(layer.y.to-layer.y.from);')
        O.lt('layer -s 1;')
        # numbers (top right) and sample label (top left)
        O.page_text("R1", f"P\\-(r) = {mt['Pr']:.1f} \\(40){UC}\\(41)", 0.97, 0.06, fs=18, anchor="rc")
        O.page_text("R2", f"PC = {mt['PC']:.1f} \\(40){UC}\\(41)", 0.97, 0.13, fs=18, color="0,176,80", anchor="rc")
        O.page_text("R3", f"LC = {mt['LC']:.1f} \\(40)mA/cm\\+(2)\\(41)", 0.97, 0.20, fs=18, color="0,0,230", anchor="rc")
        O.page_text("R4", f"{NAME[tag]}, {mt['V']:.0f} V", 0.03, 0.06, fs=22, anchor="lc")
        O.save(g, FOLD + "/PUND", f"PUND_{key}", f"PUND {PLAIN[tag]}, {mt['V']:.0f} V",
               note=f"Pr = {mt['Pr']:.1f} uC/cm2, PC = {mt['PC']:.1f} uC/cm2, LC = {mt['LC']:.1f} mA/cm2")
    f.__name__ = "pund_" + key
    return f

def pund_compare():
    d = O.read_csv("v2_PUND_summary")
    keys = ["La7.5_25V", "Sc1_25V", "LaSc_25V"]
    idx = [d["key"].index(k) for k in keys]
    labs = [PLAIN[k.split("_")[0]] for k in keys]
    wb, ws = O.book("PUNDcmp", "PUND comparison at 25 V")
    O.cols(ws, [(labs, 'X', "Sample", "", "point 2, 25 V"),
                ([d["Pr"][i] for i in idx], 'Y', "P\\-(r)", UC, "P(relaxed after P) - P(relaxed after U)"),
                ([d["PC"][i] for i in idx], 'Y', "PC", UC, "P(end of U) - P(relaxed after U)"),
                ([d["LC"][i] for i in idx], 'Y', "LC", "mA/cm\\+(2)", "slope on U pulse")])
    g = O.graph("PUNDcmp", "PUND comparison")
    O.plot(g, ws, 1, 0, 'c'); O.plot(g, ws, 2, 0, 'c')
    g[0].group()
    yl, ys = nice(max(max(d["Pr"][i], d["PC"][i]) for i in idx) * 1.3, 4)
    O.style(g, "\\b(Composition)", "\\b(Polarization \\(40)\\g(m)C/cm\\+(2)\\(41))", xr=(0.4, 3.6, 1), yr=(0, yl, ys), tick=24)
    for i, c in [(1, "0,0,0"), (2, "0,176,80")]:
        O.lt(f'layer.plot={i}; set %C -c color(0,0,0); layer1.plot{i}.color = color({c}); set %C -w 1000;')
    O.lt('layer.x.ticks=0; layer.x.minorTicks=0;')
    O.lt('legend -r; legend.text$ = "\\l(1) \\b(\\i(P)\\-(r))%(CRLF)\\l(2) \\b(PC)"; legend.font=font("Times New Roman"); legend.fsize=22; legend.background=0;')
    O.at("legend", 0.97, 0.97, anchor="rt")
    O.save(g, FOLD + "/PUND", "PUND_compare_25V", "PUND Pr and PC at 25 V (point 2)")
    O.fresh()
    wb, ws = O.book("PUNDlc", "PUND leakage at 25 V")
    O.cols(ws, [(labs, 'X', "Sample", "", "point 2, 25 V"), ([d["LC"][i] for i in idx], 'Y', "LC", "mA/cm\\+(2)", "slope on U pulse")])
    g = O.graph("PUNDlc", "PUND leakage")
    O.plot(g, ws, 1, 0, 'c')
    yl, ys = nice(max(d["LC"][i] for i in idx) * 1.15, 4)
    O.style(g, "\\b(Composition)", "\\b(LC \\(40)mA/cm\\+(2)\\(41))", xr=(0.4, 3.6, 1), yr=(0, yl, ys), tick=24)
    O.lt('layer.plot=1; set %C -c color(0,0,0); layer1.plot1.color = color(0,0,230); set %C -w 1000; layer.x.ticks=0; layer.x.minorTicks=0;')
    O.nolegend()
    O.save(g, FOLD + "/PUND", "PUND_compare_LC_25V", "PUND leakage current density at 25 V (point 2)")

funcs = [make_pe(t) for t in ["BFO", "La7.5", "Sc1", "LaSc"]] + [pe_compare] + [make_pund(k) for k in PUND] + [pund_compare]
_flt = open(O.S + "/tools/filter.txt").read().split() if os.path.exists(O.S + "/tools/filter.txt") else []
if _flt:
    funcs = [f for f in funcs if any(k in f.__name__ for k in _flt)] or funcs
O.run_all(funcs, "plot2_ferro")
