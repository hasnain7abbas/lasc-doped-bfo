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

FOLD = "3 Synaptic"
MAN = O.manifest(); M2 = O.manifest2()
GU = "\\g(m)S"
GT = "\\b(Conductance \\(40)\\g(m)S\\(41))"
at = O.at
INFERNO = ["40,11,84", "101,21,110", "159,42,99", "212,72,66", "245,125,21", "250,193,39"]
BAR = ["253,199,151", "151,213,151", "190,174,212", "255,255,153", "145,180,230"]   # FYP pastel bars

def finite(c):
    return [v for v in c if v is not None and not (isinstance(v, float) and math.isnan(v))]

def legend_entries(entries, fs=20, frame=0, idx=None):
    idx = idx or list(range(1, len(entries) + 1))
    O.lt('legend -r;')
    O.lt('legend.text$ = "' + "%(CRLF)".join(f"\\l({i}) \\b({e})" for i, e in zip(idx, entries)) + '";')
    O.lt(f'legend.font=font("Times New Roman"); legend.fsize={fs}; legend.background={frame};')

def nice(v, n=5):
    raw = v / n; k = 10 ** math.floor(math.log10(raw))
    for m in (1, 2, 2.5, 5, 10):
        if m * k >= raw: return math.ceil(v * 1.02 / (m * k)) * m * k, m * k

def r2(y, f):
    m = sum(y) / len(y)
    return 1 - sum((a - b) ** 2 for a, b in zip(y, f)) / sum((a - m) ** 2 for a in y)

def axes_inset(g, fx, fy, fw, fh, xr, yr, xt, yt, fs=16):
    """zoom inset with its own (thin) axes, FYP 'Baseline Shift' style"""
    lt = O.lt
    lt(f'win -a {g.name}; layadd type:=0;')
    k = len(list(g))
    lt(f'layer -s {k}; layer.unit=1; layer.left = layer1.left + {fx}*layer1.width; layer.top = layer1.top + {fy}*layer1.height;'
       f' layer.width = {fw}*layer1.width; layer.height = {fh}*layer1.height;')
    lt(f'layer.x.from={xr[0]}; layer.x.to={xr[1]}; layer.y.from={yr[0]}; layer.y.to={yr[1]};' +
       (f' layer.x.inc={xr[2]};' if len(xr) > 2 else '') + (f' layer.y.inc={yr[2]};' if len(yr) > 2 else ''))
    for ax in ('x', 'y', 'x2', 'y2'):
        lt(f'layer.{ax}.thickness=2; layer.{ax}.ticks=10; layer.{ax}.tickLength=4;')
    lt('layer.x.showAxes=3; layer.y.showAxes=3; layer.x.showLabels=1; layer.y.showLabels=1;')
    for ax in ('x', 'y'):
        lt(f'layer.{ax}.label.font=font("Times New Roman"); layer.{ax}.label.pt={fs}; layer.{ax}.label.bold=1;')
    lt(f'label -xb "{O.esc(xt)}"; xb.font=font("Times New Roman"); xb.fsize={fs}; label -yl "{O.esc(yt)}"; yl.font=font("Times New Roman"); yl.fsize={fs};')
    lt('label -r legend;')
    return k

# ---------------------------------------------------------------- pulse schemes (FYP style, no axes)
def scheme_sweep():
    d = O.read_csv("IV_bipolar_Sheet5")
    V = finite(d["V1"])
    xs, ys = [], []
    for i, v in enumerate(V):
        xs += [i, i + 1]; ys += [v, v]
    wb, ws = O.book("SWP", "I-V sweep waveform (Sheet5)")
    O.cols(ws, [(xs, 'X', "Point", "", "staircase drawn from the measured voltage list"), (ys, 'Y', "Voltage", "V", "0 -> +15 -> 0 -> -12 -> 0 V, 0.5 V steps"),
                ([-6, len(V) + 6], 'X', "x0", "", ""), ([0, 0], 'Y', "0 V line", "V", "")])
    g = O.graph("SWP", "I-V sweep scheme")
    O.plot(g, ws, 1, 0, 'l'); O.plot(g, ws, 3, 2, 'l')
    O.style(g, "", "", xr=(-12, len(V) + 14), yr=(-17, 20))
    O.lt('layer.x.showAxes=0; layer.y.showAxes=0; layer.x.showLabels=0; layer.y.showLabels=0; label -r xb; label -r yl;')
    O.lt('layer.x2.thickness=0; layer.y2.thickness=0;')
    O.pstyle(1, "0,0,0", 3); O.pstyle(2, "0,0,0", 1.5); O.lt('layer.plot=2; set %C -d 2;')
    O.nolegend()
    ipk = V.index(max(V)); imn = V.index(min(V))
    nm = O.text("+15 V", 0, 0, fs=26); O.lt(f'{nm}.x = {ipk}; {nm}.y = 17.5;')
    nm = O.text("-12 V", 0, 0, fs=26); O.lt(f'{nm}.x = {imn}; {nm}.y = -14.5;')
    nm = O.text("0 V", 0, 0, fs=24); O.lt(f'{nm}.x = -8; {nm}.y = 1.8;')
    nm = O.text(f"one cycle = {len(V)} points", 0, 0, fs=22); O.lt(f'{nm}.x = {0.78 * len(V)}; {nm}.y = 16.5;')
    nm = O.text("5 cycles", 0, 0, fs=22); O.lt(f'{nm}.x = {0.78 * len(V)}; {nm}.y = 12.5;')
    # zoom of the first steps
    ws2 = wb.add_sheet("Zoom")
    zx, zy = [], []
    for i in range(5):
        zx += [i, i + 1]; zy += [0.5 * i, 0.5 * i]
    O.cols(ws2, [(zx, 'X', "Point", "", "first five steps"), (zy, 'Y', "Voltage", "V", "")])
    k = O.inset_layer(g, 0.06, 0.62, 0.26, 0.30, (-0.6, 5.6), (-0.4, 2.6))
    g[k - 1].add_plot(ws2, coly=1, colx=0, type='l')
    O.lt(f'layer -s {k}; layer.plot=1; set %C -w 1500; set %C -c color(0,0,0);')
    O.lt(f'layer -s {k}; layer.x.showAxes=3; layer.y.showAxes=3; layer.x.thickness=1.5; layer.y.thickness=1.5; layer.x2.thickness=1.5; layer.y2.thickness=1.5;')
    O.lt(f'layer -s {k}; draw -n zs -l {{3.3,1.0,3.3,1.5}}; zs.linewidth=1.5; zs.arrowBeginShape=1; zs.arrowEndShape=1;')
    O.page_text("ZS", "0.5 V step", 0.33, 0.70, fs=18, anchor="lc")
    O.save(g, FOLD + "/Pulse schemes", "Scheme_IV_sweep", "Voltage waveform of the bipolar I-V sweep")

def scheme_pulse():
    wb, ws = O.book("PLS", "Write / read pulse scheme")
    t = [0, 4, 4, 6, 6, 10]; v = [1, 1, 15, 15, 1, 1]
    O.cols(ws, [(t, 'X', "Time (sketch)", "", "not to scale"), (v, 'Y', "Voltage", "V", "V_W = 15 V, 100 ms; V_R = 1 V")])
    spec = []
    levels = [(1.0, "1 V", "230,0,0"), (0.75, "0.75 V", "0,170,0"), (0.5, "0.5 V", "0,0,230"), (0.25, "0.25 V", "0,170,200")]
    for lv, _, _ in levels:
        spec += [([0.6, 3.6], 'X', "x", "", ""), ([lv * 6, lv * 6], 'Y', f"V_R = {lv} V (left)", "", "drawn x6 for visibility"),
                 ([6.4, 9.4], 'X', "x", "", ""), ([lv * 6, lv * 6], 'Y', f"V_R = {lv} V (right)", "", "")]
    O.cols(ws, spec, start=2)
    g = O.graph("PLS", "Pulse scheme")
    O.plot(g, ws, 1, 0, 'l')
    for j in range(len(levels) * 2):
        O.plot(g, ws, 3 + 2 * j, 2 + 2 * j, 'l')
    O.style(g, "", "", xr=(-2.5, 15.5), yr=(-1.5, 18))
    O.lt('layer.x.showAxes=0; layer.y.showAxes=0; layer.x.showLabels=0; layer.y.showLabels=0; label -r xb; label -r yl; layer.x2.thickness=0; layer.y2.thickness=0;')
    O.nolegend()
    O.pstyle(1, "0,0,0", 4)
    for j, (lv, lab, c) in enumerate(levels):
        for s in (0, 1):
            O.lt(f'layer.plot={2 + 2 * j + s}; set %C -w 1500; set %C -c color({c}); set %C -d 2;')
        nm = O.text(lab, 0, 0, fs=20, color=c); O.lt(f'{nm}.x = 9.6 + {nm}.dx/2; {nm}.y = {lv * 6};')
    O.lt('draw -n ar -l {-0.8,0,-0.8,15}; ar.linewidth=2.5; ar.arrowBeginShape=1; ar.arrowEndShape=1;')
    nm = O.text("V\\-(W) = 15 V", 0, 0, fs=26); O.lt(f'{nm}.x = -0.9 - {nm}.dx/2; {nm}.y = 8;')
    nm = O.text("100 ms", 0, 0, fs=22); O.lt(f'{nm}.x = 5; {nm}.y = 16.2;')
    nm = O.text("Write voltage = V\\-(W)", 0, 0, fs=24); O.lt(f'{nm}.x = 12.2; {nm}.y = 16.0;')
    nm = O.text("Read voltage = V\\-(R)", 0, 0, fs=24); O.lt(f'{nm}.x = 12.2; {nm}.y = 13.3;')
    O.lt('draw -n bl -l {0,0,10,0}; bl.linewidth=1.5; bl.lineType=2;')
    nm = O.text("0 V", 0, 0, fs=20); O.lt(f'{nm}.x = 10.4 + {nm}.dx/2; {nm}.y = 0;')
    O.save(g, FOLD + "/Pulse schemes", "Scheme_write_read", "Write / read pulse scheme (V_W = 15 V, V_R = 0.25-1 V)")

def scheme_ltp():
    wb, ws = O.book("LTPS", "LTP/LTD pulse train")
    t, v = [0], [1]
    x = 0.6
    for i in range(6):
        t += [x, x, x + 0.35, x + 0.35]; v += [1, 15, 15, 1]; x += 0.8
    t += [x + 0.6]; v += [1]; x += 1.6
    for i in range(6):
        t += [x, x, x + 0.35, x + 0.35]; v += [1, -12, -12, 1]; x += 0.8
    t += [x + 0.6]; v += [1]
    O.cols(ws, [(t, 'X', "Time (sketch)", "", "6 of 50 pulses shown per branch"), (v, 'Y', "Voltage", "V", "+15 V x50, -12 V x50, 100 ms, read at 1 V")])
    g = O.graph("LTPS", "LTP LTD scheme")
    O.plot(g, ws, 1, 0, 'l')
    O.style(g, "", "", xr=(-1.5, x + 1.5), yr=(-17, 20))
    O.lt('layer.x.showAxes=0; layer.y.showAxes=0; layer.x.showLabels=0; layer.y.showLabels=0; label -r xb; label -r yl; layer.x2.thickness=0; layer.y2.thickness=0;')
    O.nolegend(); O.pstyle(1, "0,0,0", 3)
    O.lt(f'draw -n zl -l {{-1,0,{x + 1},0}}; zl.linewidth=1.5; zl.lineType=2;')
    nm = O.text("+15 V \\'d7 50 (potentiation)", 0, 0, fs=22); O.lt(f'{nm}.text$ = "\\b(+15 V, 50 pulses \\(40)potentiation\\(41))"; {nm}.x = 2.6; {nm}.y = 17.5;')
    nm = O.text("-12 V, 50 pulses (depression)", 0, 0, fs=22); O.lt(f'{nm}.text$ = "\\b(-12 V, 50 pulses \\(40)depression\\(41))"; {nm}.x = {x - 3.0}; {nm}.y = -14.8;')
    nm = O.text("V\\-(R) = 1 V between pulses", 0, 0, fs=20); O.lt(f'{nm}.x = 2.8; {nm}.y = -5;')
    nm = O.text("0 V", 0, 0, fs=20); O.lt(f'{nm}.x = -1.0 - {nm}.dx/2 + 0.2; {nm}.y = -1.6;')
    O.save(g, FOLD + "/Pulse schemes", "Scheme_LTP_LTD", "LTP/LTD pulse train (5 cycles of 50 + 50 pulses)")

# ---------------------------------------------------------------- EPSC (FYP image style with a baseline-shift inset)
def epsc():
    d = O.read_csv("v2_EPSC"); mt = M2["v2_EPSC"]
    wb, ws = O.book("EPSC", "EPSC, V_W = 15 V, V_R = 1 V")
    O.cols(ws, [(d["t"], 'X', "Time", "s", "read at 1 V; one 15 V, 100 ms pulse"), (d["I"], 'Y', "Current", "\\g(m)A", "")])
    s2 = wb.add_sheet("Levels")
    O.cols(s2, [([mt["t_pulse"] - 3, mt["t_pulse"] + 4.5], 'X', "t", "s", ""), ([mt["I_base"]] * 2, 'Y', "Baseline before pulse", "\\g(m)A", "mean of 15 reads before the pulse"),
                ([mt["I_after"]] * 2, 'Y', "Level after pulse", "\\g(m)A", "mean of reads 5-15 after the pulse"),
                (["\\g(D)I"], 'Y', "Shift", "", f"{mt['I_after'] - mt['I_base']:.3f} \\g(m)A")])
    g = O.graph("EPSC", "EPSC")
    O.plot(g, ws, 1, 0, 'y')
    Imax = max(finite(d["I"]))
    yl, ys = nice(Imax * 1.12, 5)
    O.style(g, "\\b(Time \\(40)s\\(41))", "\\b(Current \\(40)\\g(m)A\\(41))", xr=(0, 110, 20), yr=(-0.2 * ys, yl, ys))
    O.pstyle(1, "26,111,223", 1.5, sym=2, ssize=5)
    O.nolegend()
    O.page_text("E1", "EPSC", 0.80, 0.07, fs=30, anchor="cc")
    O.page_text("E2", "V\\-(W) = 15 V, V\\-(R) = 1 V", 0.80, 0.17, fs=22, anchor="cc")
    lo = min(mt["I_base"], mt["I_after"]); hi = max(mt["I_base"], mt["I_after"])
    k = axes_inset(g, 0.42, 0.30, 0.50, 0.42, (mt["t_pulse"] - 3, mt["t_pulse"] + 4.5), (lo - 0.4 * (hi - lo), hi + 0.6 * (hi - lo)),
                   "\\b(Time \\(40)s\\(41))", "\\b(I \\(40)\\g(m)A\\(41))", fs=30)
    g[k - 1].add_plot(ws, coly=1, colx=0, type='l'); g[k - 1].add_plot(s2, coly=1, colx=0, type='l'); g[k - 1].add_plot(s2, coly=2, colx=0, type='l')
    O.lt(f'layer -s {k}; layer.plot=1; set %C -w 1000; set %C -c color(0,0,0);'
         ' layer.plot=2; set %C -w 1000; set %C -c color(230,0,0); set %C -d 3; layer.plot=3; set %C -w 1000; set %C -c color(230,0,0); set %C -d 3;')
    O.lt(f'layer -s {k}; label -s -n IS "\\b(Baseline Shift)"; IS.font=font("Times New Roman"); IS.fsize=20; IS.background=0;'
         f' IS.x = layer.x.to - 0.05*(layer.x.to-layer.x.from) - IS.dx/2; IS.y = layer.y.to - 0.07*(layer.y.to-layer.y.from) - IS.dy/2;')
    O.lt(f'layer -s {k}; label -s -n ID "\\b(\\g(D)I = {mt["I_after"] - mt["I_base"]:.3f} \\g(m)A)"; ID.font=font("Times New Roman"); ID.fsize=20; ID.background=0;'
         f' ID.x = layer.x.to - 0.05*(layer.x.to-layer.x.from) - ID.dx/2; ID.y = {0.5 * (lo + hi)};')
    O.lt('layer -s 1;')
    # zoom connectors (dotted red), FYP style
    O.lt(f'layer -s 1; draw -n c1 -l {{{mt["t_pulse"]},{hi},{110 * 0.42},{yl * 0.70}}}; c1.lineType=2; c1.color=color(230,0,0); c1.linewidth=1.5;')
    O.save(g, FOLD, "EPSC", "EPSC after a single 15 V pulse (read at 1 V) with baseline-shift inset",
           note=f"baseline {mt['I_base']:.3f} uA, after pulse {mt['I_after']:.3f} uA")

def epsc_readv():
    d = O.read_csv("READV"); vrs = MAN["READV"]["vr"]
    wb, ws = O.book("EPSCv", "EPSC at different read voltages")
    spec = []
    for v in vrs:
        spec += [(d[f"t_{v}"], 'X', "Time", "s", f"V\\-(R) = {v} V"), (d[f"I_{v}"], 'Y', "Current", "nA", f"V\\-(R) = {v} V")]
    O.cols(ws, spec)
    g = O.graph("EPSCv", "EPSC vs read voltage")
    for k in range(len(vrs)):
        O.plot(g, ws, 2 * k + 1, 2 * k, 'l')
    O.style(g, "\\b(Time \\(40)s\\(41))", "\\b(Current \\(40)nA\\(41))", ylog=True, xr=(0, 110, 20), yr=(1, 1e4))
    for k in range(len(vrs)):
        O.pstyle(k + 1, O.pal(k), 3)
    legend_entries([f"V\\-(R) = {v} V" for v in vrs], fs=20)
    at("legend", 0.55, 0.95)
    O.page_text("EV", "V\\-(W) = 15 V, 100 ms", 0.04, 0.07, fs=22)
    O.save(g, FOLD, "EPSC_read_voltage", "EPSC read at 0.25-1 V")

# ---------------------------------------------------------------- PPF
def ppf_trace():
    d = O.read_csv("PPF_traces")
    wb, ws = O.book("PPFtr", "PPF trace, dt = 50 ms")
    O.cols(ws, [(d["t_0.05"], 'X', "Time", "s", "\\g(D)t = 50 ms"), (d["G_0.05"], 'Y', "Current", "\\g(m)A", "read at 1 V (= conductance in \\g(m)S)")])
    g = O.graph("PPFtr", "PPF trace")
    O.plot(g, ws, 1, 0, 'y')
    Imax = max(finite(d["G_0.05"])); yl, ys = nice(Imax * 1.15, 5)
    O.style(g, "\\b(Time \\(40)s\\(41))", "\\b(Current \\(40)\\g(m)A\\(41))", xr=(-0.5, 10, 2), yr=(-0.1 * yl, yl, ys))
    O.pstyle(1, "0,0,0", 1, sym=2, ssize=5); O.lt('layer.plot=1; set %C -cse color(26,111,223); set %C -csf color(26,111,223);')
    O.nolegend()
    O.page_text("P1", "PPF", 0.95, 0.07, fs=30, anchor="rc")
    O.page_text("P2", "V\\-(W) = 15 V, \\g(D)t = 50 ms", 0.95, 0.17, fs=22, anchor="rc")
    O.save(g, FOLD + "/PPF", "PPF_trace", "Paired-pulse response, dt = 50 ms")

def ppf_index():
    d = O.read_csv("PPF_index")
    wb, ws = O.book("PPF", "PPF index vs interval")
    O.cols(ws, [(d["dt_ms"], 'X', "Pulse interval", "ms", ""), (d["A1_uA"], 'Y', "A\\-(1)", "\\g(m)A", ""),
                (d["A2_uA"], 'Y', "A\\-(2)", "\\g(m)A", ""), (d["PPF"], 'Y', "PPF index", "%", "(A\\-(2) - A\\-(1))/A\\-(1) x 100")])
    nfit = sum(1 for v in d["dt_ms"] if v <= 2000)
    fr = O.fitlr(ws, 0, 3, 1, nfit)
    xs = [0, 2100]
    s2 = wb.add_sheet("Linear fit")
    O.cols(s2, [(xs, 'X', "Pulse interval", "ms", ""), ([fr["a"] + fr["b"] * x for x in xs], 'Y', "Linear fit", "%",
               f"PPF = {fr['a']:.3f} + ({fr['b']:.5f}) dt; fitted on dt = 50-2000 ms; R\\+(2) = {fr['r2']:.3f}. Longer intervals (5-20 s) are in the Data sheet.")])
    g = O.graph("PPF", "PPF index")
    O.plot(g, ws, 3, 0, 's'); O.plot(g, s2, 1, 0, 'l')
    O.style(g, "\\b(Interval \\(40)ms\\(41))", "\\b(PPF Index \\(40)%\\(41))", xr=(-100, 2200, 500), yr=(5, 10.5, 1))
    O.pstyle(1, "81,81,81", None, sym=2, ssize=12); O.pstyle(2, "230,0,0", 3); O.lt('layer.plot=2; set %C -d 1;')
    legend_entries(["Raw data", "Fitting"], fs=24)
    at("legend", 0.96, 0.95, anchor="rt")
    O.page_text("PF", f"\\i(R)\\+(2) = {fr['r2']:.3f}", 0.05, 0.92, fs=20)
    O.save(g, FOLD + "/PPF", "PPF_index", "PPF index vs pulse interval with linear fit (50-2000 ms)",
           note=f"slope {fr['b']:.5f} %/ms, intercept {fr['a']:.2f} %, R2 {fr['r2']:.3f}")

# ---------------------------------------------------------------- SDDP
PWS = [0.1, 0.2, 0.3, 0.4, 0.5]

def sddp_bars():
    d = O.read_csv("SDDP_pulses")
    wb, ws = O.book("SDDP", "SDDP: conductance vs pulse number")
    spec = [(d["n_0.1"], 'X', "Pulse number", "", "")]
    for pw in PWS:
        spec.append((d[f"G_{pw}"], 'Y', "Conductance", GU, f"P\\-(W) = {int(pw * 1000)} ms"))
    O.cols(ws, spec)
    s2 = wb.add_sheet("Every5th")
    idx = [0] + list(range(4, 50, 5))
    spec = [([d["n_0.1"][i] for i in idx], 'X', "Pulse number", "", "pulses 1, 5, 10, ..., 50")]
    for pw in PWS:
        spec.append(([d[f"G_{pw}"][i] for i in idx], 'Y', "Conductance", GU, f"P\\-(W) = {int(pw * 1000)} ms"))
    O.cols(s2, spec)
    g = O.graph("SDDP", "SDDP bars")
    for k in range(5):
        O.plot(g, s2, k + 1, 0, 'c')
    g[0].group()
    O.style(g, "\\b(Pulse Number)", GT, xr=(-2, 53, 10), yr=(0, 0.2, 0.05))
    for k in range(5):
        O.lt(f'layer.plot={k + 1}; set %C -c color(0,0,0); layer1.plot{k + 1}.color = color({BAR[k]}); set %C -w 500;')
    legend_entries([f"{int(pw * 1000)}ms" for pw in PWS], fs=18, frame=1)
    at("legend", 0.03, 0.97)
    O.page_text("SD", "V\\-(W) = 15 V, V\\-(R) = 1 V", 0.30, 0.07, fs=20)
    O.save(g, FOLD + "/SDDP", "SDDP_pulse_number", "SDDP: conductance vs pulse number for 100-500 ms widths")

def sddp_dw():
    d = O.read_csv("SDDP_summary")
    wb, ws = O.book("SDDPdw", "SDDP weight change vs pulse width")
    O.cols(ws, [(d["pw_ms"], 'X', "Pulse width", "ms", ""), (d["G1"], 'Y', "G\\-(1)", GU, "after pulse 1"),
                (d["G50"], 'Y', "G\\-(50)", GU, "after pulse 50"), (d["dW"], 'Y', "\\g(D)W", "%", "(G\\-(50) - G\\-(1))/G\\-(1) x 100")])
    g = O.graph("SDDPdw", "SDDP dW")
    O.plot(g, ws, 3, 0, 'y')
    O.style(g, "\\b(Pulse Width \\(40)ms\\(41))", "\\b(\\g(D)\\i(W) \\(40)%\\(41))", xr=(50, 550, 100), yr=(0, 250, 50))
    O.pstyle(1, "26,111,223", 3, sym=2, ssize=14); O.nolegend()
    O.fraction(g, "\\g(D)\\i(W) =", "\\i(G)\\-(50) − \\i(G)\\-(1)", "\\i(G)\\-(1)", "× 100%", fx=0.02, fy=0.03, fw=0.55, fh=0.20, tag="FDW")
    O.save(g, FOLD + "/SDDP", "SDDP_dW_vs_width", "SDDP weight change vs pulse width")

def sddp_decay():
    d = O.read_csv("v2_SDDP_decay")
    wb, ws = O.book("SDDPd", "SDDP decay (after the 50-pulse train)")
    spec = []
    for pw in PWS:
        spec += [(d[f"t_{pw}"], 'X', "Time after the train", "s", f"P\\-(W) = {int(pw * 1000)} ms; t = 0 at the conductance peak"),
                 (d[f"G_{pw}"], 'Y', "Conductance", GU, f"P\\-(W) = {int(pw * 1000)} ms")]
    O.cols(ws, spec)
    g = O.graph("SDDPd", "SDDP decay")
    for k in range(5):
        O.plot(g, ws, 2 * k + 1, 2 * k, 'l')
    gm = max(max(finite(d[f"G_{pw}"])) for pw in PWS)
    tm = max(max(finite(d[f"t_{pw}"])) for pw in PWS)
    yl, ys = nice(gm * 1.45, 4)
    O.style(g, "\\b(Time \\(40)s\\(41))", GT, xr=(0, math.ceil(tm / 50) * 50, 50), yr=(0, yl, ys))
    for k in range(5):
        O.pstyle(k + 1, O.pal(k), 4)
    legend_entries([f"P\\-(W)={int(pw * 1000)}ms" for pw in PWS], fs=18)
    at("legend", 0.66, 0.62)
    O.title_above("SDDP Decay")
    O.pulse_inset(g, wb, fx=0.50, fy=0.03, fw=0.47, fh=0.30)
    O.save(g, FOLD + "/SDDP", "SDDP_decay", "SDDP: relaxation after 50 pulses of 100-500 ms")

# ---------------------------------------------------------------- SNDP
NS3 = [20, 40, 60, 80, 100]
SRC3 = lambda N: M2["v3_SNDP"]["source"][str(N)]

def sndp_traces():
    d = O.read_csv("v3_SNDP_traces")
    wb, ws = O.book("SNDP", "SNDP relaxation after N = 20-100 pulses")
    spec = []
    for N in NS3:
        spec += [(d[f"t_{N}"], 'X', "Time from peak", "s", f"N = {N}; {SRC3(N)}"), (d[f"G_{N}"], 'Y', "Conductance", GU, f"N = {N}")]
    O.cols(ws, spec)
    g = O.graph("SNDP", "SNDP traces")
    for k, N in enumerate(NS3):
        O.plot(g, ws, 2 * k + 1, 2 * k, 'l' if SRC3(N).startswith("continuous") else 'y')
    O.style(g, "\\b(Time \\(40)s\\(41))", GT, xr=(0, 200, 50), yr=(0, 0.8, 0.2))
    for k, N in enumerate(NS3):
        if SRC3(N).startswith("continuous"):
            O.pstyle(k + 1, O.pal(k), 4)
        else:
            O.pstyle(k + 1, O.pal(k), 3, sym=2, ssize=12)
    legend_entries([f"N={N}" for N in NS3], fs=20)
    at("legend", 0.72, 0.62)
    O.title_above("SNDP")
    O.pulse_inset(g, wb, fx=0.50, fy=0.03, fw=0.47, fh=0.30)
    O.save(g, FOLD + "/SNDP", "SNDP_traces", "SNDP: conductance relaxation after N = 20-100 pulses",
           note="N = 20-80 continuous logs; N = 100 logged points only (no continuous log in the file)")

def sndp_weight():
    d = O.read_csv("v3_SNDP_norm")
    wb, ws = O.book("SNDPw", "SNDP: normalised weight change, N = 20-100")
    spec = []
    for N in NS3:
        spec += [(d[f"t_{N}"], 'X', "Time", "s", f"N = {N}; {SRC3(N)}"),
                 (d[f"W_{N}"], 'Y', "Weight change", "%", f"N = {N}; W = G(t)/G(peak) x 100")]
    O.cols(ws, spec)
    bk = wb.name; fits = []
    for k, N in enumerate(NS3):
        W = finite(d[f"W_{N}"]); y0g = W[-1]
        O.lt(f'win -a {bk}; page.active$ = "Data"; nlbegin iy:=(col({2 * k + 1}), col({2 * k + 2})) func:=ExpDec1 nltree:=__ee;'
             f' __ee.y0 = {y0g}; __ee.A1 = {100 - y0g}; __ee.t1 = 15; nlfit; nlend;')
        p = dict(y0=op.lt_float('__ee.y0'), A=op.lt_float('__ee.A1'), tau=op.lt_float('__ee.t1'), tau_e=op.lt_float('__ee.e_t1'))
        tt = finite(d[f"t_{N}"]); ff = [p["y0"] + p["A"] * math.exp(-x / p["tau"]) for x in tt]
        p["r2"] = r2(W[:len(ff)], ff); fits.append(p)
    s2 = wb.add_sheet("Plotted + fits")
    spec = []
    tf = [k * 0.5 for k in range(201)]
    for k, N in enumerate(NS3):
        p = fits[k]
        spec += [(d[f"ts_{N}"], 'X', "Time", "s", f"N = {N} (plotted points)"), (d[f"Ws_{N}"], 'Y', "Weight change", "%", f"N = {N}"),
                 (tf, 'X', "Time (fit)", "s", ""), ([p["y0"] + p["A"] * math.exp(-x / p["tau"]) for x in tf], 'Y', "Fit", "%",
                  f"W = W\\-(0) + A exp(-t/\\g(t)); W\\-(0) = {p['y0']:.1f}, A = {p['A']:.1f}, \\g(t) = {p['tau']:.2f} s, R\\+(2) = {p['r2']:.3f}")]
    O.cols(s2, spec)
    s3 = wb.add_sheet("Tau")
    O.cols(s3, [(NS3, 'X', "Pulse number N", "", ""), ([p["tau"] for p in fits], 'Y', "\\g(t)", "s", "ExpDec1 fit, 0-100 s"),
                ([p["tau_e"] for p in fits], 'E', "\\g(t) error", "s", ""), ([p["y0"] for p in fits], 'Y', "W\\-(0) (long-term level)", "%", ""),
                ([p["r2"] for p in fits], 'Y', "R\\+(2)", "", "")])
    g = O.graph("SNDPw", "SNDP weight change")
    for k in range(len(NS3)):
        O.plot(g, s2, 4 * k + 1, 4 * k, 's')          # data as dots only (fits are kept in the workbook)
    O.style(g, "\\b(Time \\(40)s\\(41))", "\\b(Weight Change \\(40)%\\(41))", xr=(-3, 100, 20), yr=(0, 110, 20))
    for k, N in enumerate(NS3):
        O.pstyle(k + 1, INFERNO[k], None, sym=2, ssize=8, hollow=True)
    legend_entries([f"N={N}" for N in NS3], fs=20)
    at("legend", 0.20, 0.90, anchor="lt")
    O.pulse_inset(g, wb, fx=0.40, fy=0.03, fw=0.57, fh=0.27)
    O.save(g, FOLD + "/SNDP", "SNDP_weight_change", "SNDP: normalised weight change after N = 20-100 pulses",
           note="; ".join(f"N={N}: tau={p['tau']:.1f} s" for N, p in zip(NS3, fits)) + " (exponential fits in the workbook)")
    O.fresh()
    wb, ws = O.book("TAU", "SNDP relaxation time vs pulse number")
    O.cols(ws, [(NS3, 'X', "Pulse number N", "", ""), ([p["tau"] for p in fits], 'Y', "\\g(t)", "s", "ExpDec1 fit of the weight change, 0-100 s"),
                ([p["tau_e"] for p in fits], 'E', "\\g(t) error", "s", "")])
    g = O.graph("TAU", "tau vs N")
    O.plot(g, ws, 1, 0, 's', cyerr=2)
    tmax = max(p["tau"] + p["tau_e"] for p in fits); yl, ys = nice(tmax * 1.25, 5)
    O.style(g, "\\b(Pulse Number)", "\\b(\\g(t) \\(40)s\\(41))", xr=(0, 110, 20), yr=(0, yl, ys))
    O.pstyle(1, "0,0,0", None, sym=2, ssize=14)
    O.nolegend()
    O.page_text("TF", "\\i(W) = \\i(W)\\-(0) + \\i(A)\u00b7\\i(e)\\+(\u2212\\i(t)/\\g(t))", 0.04, 0.08, fs=24)
    O.save(g, FOLD + "/SNDP", "SNDP_tau_vs_N", "SNDP: relaxation time constant vs pulse number (N = 20-100)")

def sndp_dw():
    d = O.read_csv("v3_SNDP_summary")
    wb, ws = O.book("SNDPdw", "SNDP weight change vs pulse number")
    O.cols(ws, [(d["N"], 'X', "Pulse number N", "", ""), (d["G0"], 'Y', "G\\-(0)", GU, "conductance after reset (file)"),
                (d["Gpeak"], 'Y', "G\\-(peak)", GU, "maximum of the continuous record"), (d["G100"], 'Y', "G\\-(100 s)", GU, "100 s after the peak"),
                (d["dW_peak"], 'Y', "\\g(D)W (peak)", "%", "(G\\-(peak) - G\\-(0))/G\\-(0) x 100"),
                (d["dW_100"], 'Y', "\\g(D)W (100 s)", "%", "(G\\-(100 s) - G\\-(0))/G\\-(0) x 100")])
    g = O.graph("SNDPdw", "SNDP dW")
    O.plot(g, ws, 4, 0, 'y'); O.plot(g, ws, 5, 0, 'y')          # line + symbol, as in the earlier version
    O.style(g, "\\b(Pulse Number)", "\\b(\\g(D)\\i(W) \\(40)%\\(41))", xr=(0, 110, 20), yr=(0, 600, 100))
    O.pstyle(1, "0,0,0", 3, sym=2, ssize=14); O.pstyle(2, "230,0,0", 3, sym=1, ssize=14)
    legend_entries(["\\g(D)\\i(W) at peak", "\\g(D)\\i(W) after 100 s"], fs=22)
    at("legend", 0.96, 0.70, anchor="rt")
    O.fraction(g, "\\g(D)\\i(W) =", "\\i(G) − \\i(G)\\-(0)", "\\i(G)\\-(0)", "× 100%", fx=0.02, fy=0.03, fw=0.50, fh=0.20, tag="FSW")
    O.save(g, FOLD + "/SNDP", "SNDP_dW_vs_pulse_number", "SNDP: weight change vs pulse number (N = 20-100)")

# ---------------------------------------------------------------- SRDP, retention, LTP/LTD, multilevel, endurance
def srdp():
    d = O.read_csv("SRDP_rep")           # "srdp repeated" sheet, 1-8 Hz (0.5 Hz row left out: its Gpre is 10x the others)
    wb, ws = O.book("SRDP", "SRDP (repeated): 30 pulses at 1-8 Hz")
    O.cols(ws, [(d["f"], 'X', "Pulse frequency", "Hz", "30 pulses, 15 V, 100 ms"), (d["gap"], 'Y', "Inter-pulse gap", "s", ""),
                (d["Gpre"], 'Y', "G\\-(pre)", GU, ""), (d["Gpost"], 'Y', "G\\-(post)", GU, ""),
                (d["SRDP"], 'Y', "SRDP index", "%", "(G\\-(post) - G\\-(pre))/G\\-(pre) x 100")])
    a = O.read_csv("SRDP_rep_all")
    s0 = wb.add_sheet("All rows (incl. 0.5 Hz)")
    O.cols(s0, [(a["f"], 'X', "Pulse frequency", "Hz", "srdp repeated sheet, as recorded"), (a["Gpre"], 'Y', "G\\-(pre)", GU, ""),
                (a["Gpost"], 'Y', "G\\-(post)", GU, ""),
                (a["SRDP"], 'Y', "SRDP index", "%", "0.5 Hz not plotted: Gpre = 0.01174 uS is ten times lower than the other rows")])
    s2 = wb.add_sheet("Plot")
    O.cols(s2, [(list(range(1, len(d["f"]) + 1)), 'X', "Bar position", "", "tick labels = frequency"),
                (d["SRDP"], 'Y', "SRDP index", "%", "")])
    g = O.graph("SRDP", "SRDP index")
    O.plot(g, s2, 1, 0, 'c')
    yl, ys = nice(max(d["SRDP"]) * 1.35, 5)
    O.style(g, "\\b(Frequency \\(40)Hz\\(41))", "\\b(SRDP Index \\(40)%\\(41))", xr=(0.4, len(d["f"]) + 0.6, 1), yr=(0, yl, ys))
    O.lt('layer.plot=1; set %C -c color(0,0,0); layer1.plot1.color = color(240,0,0); set %C -w 500;')
    O.lt('layer.x.minorTicks=0;')
    O.nolegend()
    # explicit tick labels (frequency) placed under each bar
    O.lt('layer.x.showLabels=0;')
    for i, f in enumerate(d["f"]):
        nm = O.text(("%g" % f), 0, 0, fs=28)
        O.lt(f'{nm}.x = {i + 1}; {nm}.top = (layer1.top + layer1.height)*page.height/100 + 60;')
    O.lt('xb.top = (layer1.top + layer1.height)*page.height/100 + 420;')
    O.fraction(g, "SRDP\\-(index) =", "\\i(G)\\-(post) − \\i(G)\\-(pre)", "\\i(G)\\-(pre)", "× 100%", fx=0.02, fy=0.03, fw=0.66, fh=0.20, tag="FSR")
    O.save(g, FOLD, "SRDP_index", "SRDP index vs pulse frequency (30 pulses)")

def retention():
    d = O.read_csv("v3_RETENTION"); Ns = [20, 40, 60, 80, 100]
    wb, ws = O.book("RET", "Retention after N pulses (logged points)")
    spec = []
    for N in Ns:
        spec += [(d[f"t_{N}"], 'X', "Time", "s", f"N = {N}"), (d[f"G_{N}"], 'Y', "Conductance", GU, f"N = {N}, logged points")]
    O.cols(ws, spec)
    g = O.graph("RET", "Retention")
    for k in range(len(Ns)):
        O.plot(g, ws, 2 * k + 1, 2 * k, 'y')
    O.style(g, "\\b(Time \\(40)s\\(41))", GT, xlog=True, xr=(0.5, 5000), yr=(0, 0.7, 0.1))
    for k in range(len(Ns)):
        O.pstyle(k + 1, O.pal(k), 3, sym=[2, 1, 3, 4, 5][k], ssize=12)
    legend_entries([f"N={N}" for N in Ns], fs=20)
    at("legend", 0.72, 0.62)
    O.title_above("Retention")
    O.pulse_inset(g, wb, fx=0.50, fy=0.03, fw=0.47, fh=0.30)
    O.save(g, FOLD, "Retention", "Retention of states written with 20-100 pulses")

def ltp_raw():
    d = O.read_csv("LTPLTD_raw")
    wb, ws = O.book("LTP", "LTP/LTD, 5 cycles")
    O.cols(ws, [(d["n"], 'X', "Pulse number", "", ""), (d["G"], 'Y', "Conductance", GU, "read at 1 V"),
                (d["Gp"], 'Y', "Potentiation", GU, "+15 V, 100 ms"), (d["Gd"], 'Y', "Depression", GU, "-12 V, 100 ms")])
    g = O.graph("LTP", "LTP LTD cycles")
    O.plot(g, ws, 2, 0, 's'); O.plot(g, ws, 3, 0, 's')
    O.style(g, "\\b(Pulse Number)", GT, xr=(-10, 510, 100), yr=(0.1, 0.5, 0.1), wide=True)
    O.pstyle(1, "0,0,0", None, sym=2, ssize=8); O.pstyle(2, "230,0,0", None, sym=2, ssize=8)
    legend_entries(["Potentiation", "Depression"], fs=20)
    at("legend", 0.02, 0.97)
    O.save(g, FOLD + "/LTP-LTD", "LTP_LTD_5cycles", "LTP/LTD over five cycles")

def ltp_fit():
    d = O.read_csv("LTPLTD_avg")
    k = d["k"]; Gm = d["Gmean"]; Gs = d["Gstd"]
    wb, ws = O.book("LTPfit", "Cycle-averaged LTP/LTD with power-law fits")
    nP = list(range(1, 51)); nD = list(range(51, 101)); GP = Gm[:50]; GD = Gm[50:]
    O.cols(ws, [(k, 'X', "Pulse number", "", ""), (Gm, 'Y', "G mean", GU, "mean of 5 cycles"), (Gs, 'E', "G s.d.", GU, ""),
                (d["Gp"], 'Y', "Potentiation", GU, "mean"), (d["Gp_err"], 'E', "s.d.", GU, ""),
                (d["Gd"], 'Y', "Depression", GU, "mean"), (d["Gd_err"], 'E', "s.d.", GU, ""),
                ([n - 1 for n in nP], 'X', "n - 1 (P)", "", ""), ([g - GP[0] for g in GP], 'Y', "G - G\\-(1) (P)", GU, ""),
                ([m - 51 for m in nD], 'X', "m - 1 (D)", "", ""), ([GD[0] - g for g in GD], 'Y', "G\\-(51) - G (D)", GU, "")])
    res = {}; bk = wb.name
    for tag, cx, cy in [("P", 7, 8), ("D", 9, 10)]:
        O.lt(f'win -a {bk}; nlbegin iy:=(col({cx + 1})[2:50], col({cy + 1})[2:50]) func:=Allometric1 nltree:=__aa; __aa.a = 0.01; __aa.b = 0.8; nlfit; nlend;')
        res[tag] = dict(a=op.lt_float('__aa.a'), b=op.lt_float('__aa.b'))
        yy = [GP[i] - GP[0] for i in range(1, 50)] if tag == "P" else [GD[0] - GD[i] for i in range(1, 50)]
        res[tag]["r2"] = r2(yy, [res[tag]["a"] * x ** res[tag]["b"] for x in range(1, 50)])
    fitP = [GP[0] + res["P"]["a"] * (n - 1) ** res["P"]["b"] for n in nP]
    fitD = [GD[0] - res["D"]["a"] * (m - 51) ** res["D"]["b"] for m in nD]
    aP, aD = 1 / res["P"]["b"], 1 / res["D"]["b"]
    O.cols(ws, [(nP + nD, 'X', "Pulse number (fit)", "", ""),
                (fitP + [None] * 50, 'Y', "Power-law fit P", GU, f"G = G\\-(1) + a(n-1)\\+(1/\\g(a)), \\g(a)\\-(P) = {aP:.3f}, R\\+(2) = {res['P']['r2']:.4f}"),
                ([None] * 50 + fitD, 'Y', "Power-law fit D", GU, f"G = G\\-(51) - a(m-1)\\+(1/\\g(a)), \\g(a)\\-(D) = {aD:.3f}, R\\+(2) = {res['D']['r2']:.4f}")], start=11)
    g = O.graph("LTPfit", "LTP LTD fit")
    O.plot(g, ws, 3, 0, 's', cyerr=4); O.plot(g, ws, 5, 0, 's', cyerr=6)
    O.plot(g, ws, 12, 11, 'l'); O.plot(g, ws, 13, 11, 'l')
    O.style(g, "\\b(Pulse Number)", GT, xr=(0, 100, 20), yr=(0.15, 0.5, 0.05))
    O.pstyle(1, "0,0,0", None, sym=2, ssize=9); O.lt('layer.plot=2; set %C -c color(0,0,0);')
    O.pstyle(3, "230,0,0", None, sym=2, ssize=9); O.lt('layer.plot=4; set %C -c color(230,0,0);')
    O.pstyle(5, "0,0,230", 3); O.pstyle(6, "0,0,230", 3)
    legend_entries(["Potentiation", "Depression", "Power-law fit"], fs=20, idx=[1, 3, 5])
    at("legend", 0.97, 0.84, anchor="rt")
    O.page_text("AP", f"\\g(a)\\-(P) = {aP:.3f}", 0.06, 0.07, fs=24)
    O.page_text("AD", f"\\g(a)\\-(D) = {aD:.3f}", 0.60, 0.07, fs=24)
    O.save(g, FOLD + "/LTP-LTD", "LTP_LTD_powerlaw_fit", "Cycle-averaged LTP/LTD (mean +/- s.d.) with power-law fits",
           note=f"alphaP = {aP:.3f} (R2 {res['P']['r2']:.4f}), alphaD = {aD:.3f} (R2 {res['D']['r2']:.4f})")

def multilevel():
    d = O.read_csv("MULTILEVEL")
    wb, ws = O.book("ML", "Multilevel states")
    O.cols(ws, [(d["level"], 'X', "Conductance level", "", "15 V, 100 ms, 5 pulses per level"), (d["pulses"], 'Y', "Total pulses", "", ""),
                (d["I"], 'Y', "Read current", "A", "at 1 V"), (d["G"], 'Y', "Conductance", GU, "G = I/1 V")])
    g = O.graph("ML", "Multilevel")
    O.plot(g, ws, 3, 0, 'y')
    O.style(g, "\\b(Conductance Level)", GT, xr=(0, 16, 3), yr=(0.1, 0.45, 0.05))
    O.pstyle(1, "0,0,0", 3, sym=2, ssize=12); O.nolegend()
    O.title_above("Multilevel Conductance States")
    O.page_text("MLt", "5 pulses/level, V\\-(W) = 15 V, V\\-(R) = 1 V", 0.04, 0.07, fs=20)
    O.save(g, FOLD, "Multilevel_states", "Fifteen conductance levels")

def endurance():
    d = O.read_csv("ENDURANCE")
    wb, ws = O.book("END", "Endurance")
    O.cols(ws, [(d["cycle"], 'X', "Cycle", "", ""), (d["Gp"], 'Y', "G\\-(+) (potentiated)", GU, ""),
                (d["Gm"], 'Y', "G\\-(-) (depressed)", GU, ""), (d["ratio"], 'Y', "G\\-(+)/G\\-(-)", "", "dynamic range")])
    g = O.graph("END", "Endurance")
    O.plot(g, ws, 1, 0, 'y'); O.plot(g, ws, 2, 0, 'y')
    O.style(g, "\\b(Cycle)", GT, ylog=True, xr=(-100, 2600, 500), yr=(0.01, 1))
    O.pstyle(1, "0,0,0", 1, sym=2, ssize=5); O.pstyle(2, "230,0,0", 1, sym=1, ssize=5)
    legend_entries(["G\\-(+) (Potentiation)", "G\\-(-) (Depression)"], fs=20)
    at("legend", 0.40, 0.05, anchor="lb")
    O.title_above("Endurance")
    O.save(g, FOLD + "/Endurance", "Endurance", "Endurance over 2500 LTP/LTD cycles")
    O.fresh()
    wb, ws = O.book("DR", "Dynamic range vs cycle")
    O.cols(ws, [(d["cycle"], 'X', "Cycle", "", ""), (d["ratio"], 'Y', "G\\-(+)/G\\-(-)", "", "dynamic range")])
    g = O.graph("DR", "Dynamic range")
    O.plot(g, ws, 1, 0, 'y')
    O.style(g, "\\b(Cycle Number)", "\\b(Dynamic Range \\(40)\\i(G)\\-(+)/\\i(G)\\-(-)\\(41))", xr=(-100, 2600, 500), yr=(0, 8, 2))
    O.pstyle(1, "230,0,0", 1, sym=2, ssize=5); O.nolegend()
    r = finite(d["ratio"]); mean = sum(r) / len(r); sd = (sum((x - mean) ** 2 for x in r) / (len(r) - 1)) ** 0.5
    O.title_above("Dynamic Range vs Cycling")
    O.save(g, FOLD + "/Endurance", "Dynamic_range", "Dynamic range G+/G- over 2500 cycles")

funcs = [epsc, epsc_readv, ppf_trace, ppf_index, sddp_bars, sddp_dw, sddp_decay,
         sndp_traces, sndp_weight, sndp_dw, srdp, retention, ltp_raw, ltp_fit, multilevel, endurance]
_flt = open(O.S + "/tools/filter.txt").read().split() if os.path.exists(O.S + "/tools/filter.txt") else []
if _flt:
    funcs = [f for f in funcs if any(k in f.__name__ for k in _flt)] or funcs
O.run_all(funcs, "plot2_syn")
