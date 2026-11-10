# Fig. 5c re-plotted with the CrossSim power-law model (fit by prep/prep_ltpfit_cs.py, scipy curve_fit):
#   P: G = G0 + (G1-G0)[1-(1-n/49)^aP],  D: G = G1 + (G0-G1)(1-n/49)^aD
# so the alpha in the figure is the alpha used in the network simulation. Overwrites LTP_LTD_powerlaw_fit.opju
# (old Allometric1 version backed up in scratchpad/backup_old_ltpfit).
import os as _os, sys as _sys
try:
    _HERE = _os.path.dirname(_os.path.abspath(__file__))
except NameError:            # Origin "run -pyf" may not define __file__
    _HERE = _os.environ["LASC_PKG"] + "/origin_plots"
_sys.path.insert(0, _os.path.normpath(_os.path.join(_HERE, "..")))
_sys.path.insert(0, _HERE)
import config

import sys, json
pass
import importlib, oplib as O
importlib.reload(O)
import originpro as op

FOLD = "3 Synaptic"
GU = "\\g(m)S"
GT = "\\b(Conductance \\(40)\\g(m)S\\(41))"
FI = json.load(open(O.S + "/prep/csv/LTPLTD_fit_cs.json"))

def legend_entries(entries, fs=20, idx=None):
    idx = idx or list(range(1, len(entries) + 1))
    O.lt('legend -r;')
    O.lt('legend.text$ = "' + "%(CRLF)".join(f"\\l({i}) \\b({e})" for i, e in zip(idx, entries)) + '";')
    O.lt(f'legend.font=font("Times New Roman"); legend.fsize={fs}; legend.background=0;')

def ltp_fit_cs():
    d = O.read_csv("LTPLTD_avg"); f = O.read_csv("LTPLTD_fit_cs")
    k = d["k"]; Gm = d["Gmean"]; Gs = d["Gstd"]
    P, D = FI["P"], FI["D"]
    wb, ws = O.book("LTPfit", "Cycle-averaged LTP/LTD with power-law fits (CrossSim model)")
    O.cols(ws, [(k, 'X', "Pulse number", "", ""), (Gm, 'Y', "G mean", GU, "mean of 5 cycles"), (Gs, 'E', "G s.d.", GU, ""),
                (d["Gp"], 'Y', "Potentiation", GU, "mean of 5 cycles"), (d["Gp_err"], 'E', "s.d.", GU, ""),
                (d["Gd"], 'Y', "Depression", GU, "mean of 5 cycles"), (d["Gd_err"], 'E', "s.d.", GU, ""),
                (f["k"], 'X', "Pulse number (fit)", "", "n = k - 1 (P), k - 51 (D); N = 49"),
                (f["fit"][:50] + [None] * 50, 'Y', "Power-law fit P", GU,
                 f"G = G0 + (G1 - G0)[1 - (1 - n/N)^aP], aP = {P['alpha']:.3f} +/- {P['alpha_se']:.3f}, R2 = {P['r2']:.4f}"),
                ([None] * 50 + f["fit"][50:], 'Y', "Power-law fit D", GU,
                 f"G = G1 + (G0 - G1)(1 - n/N)^aD, aD = {D['alpha']:.3f} +/- {D['alpha_se']:.3f}, R2 = {D['r2']:.4f}")])
    O.lt(f'win -a {wb.name}; page.longname$ = "Cycle-averaged LTP/LTD, power-law fit in the CrossSim lookup-table form (scipy curve_fit, free end points)";')
    g = O.graph("LTPfit", "LTP LTD fit")
    O.plot(g, ws, 3, 0, 's', cyerr=4); O.plot(g, ws, 5, 0, 's', cyerr=6)
    O.plot(g, ws, 8, 7, 'l'); O.plot(g, ws, 9, 7, 'l')
    O.style(g, "\\b(Pulse Number)", GT, xr=(0, 100, 20), yr=(0.15, 0.5, 0.05))
    O.pstyle(1, "0,0,0", None, sym=2, ssize=9); O.lt('layer.plot=2; set %C -c color(0,0,0);')
    O.pstyle(3, "230,0,0", None, sym=2, ssize=9); O.lt('layer.plot=4; set %C -c color(230,0,0);')
    O.pstyle(5, "0,0,230", 3); O.pstyle(6, "0,0,230", 3)
    legend_entries(["Potentiation", "Depression", "Power-law fit"], fs=20, idx=[1, 3, 5])
    O.at("legend", 0.97, 0.84, anchor="rt")
    O.page_text("AP", f"\\g(a)\\-(P) = {P['alpha']:.3f}", 0.06, 0.07, fs=24)
    O.page_text("AD", f"\\g(a)\\-(D) = {D['alpha']:.3f}", 0.60, 0.07, fs=24)
    O.save(g, FOLD + "/LTP-LTD", "LTP_LTD_powerlaw_fit", "Cycle-averaged LTP/LTD (mean +/- s.d.) with power-law fits (CrossSim model)",
           note=f"alphaP = {P['alpha']:.4f} (R2 {P['r2']:.4f}), alphaD = {D['alpha']:.4f} (R2 {D['r2']:.4f}); same model and values as device_params.json")

O.run_all([ltp_fit_cs], "ltp_fit_cs")
