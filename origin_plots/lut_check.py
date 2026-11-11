# Fig. 6c: the update model used in CrossSim (mean step of Eq. 1, +/- sigma_w) against the measured single-pulse updates
# (245 per polarity) averaged in 0.03-uS conductance bins (mean +/- s.d.). Data: analysis/prep_lut_check.py -> LUT_check.csv.
# Built on a copy of the Fig. 5c paper graph so layer, 4-pt frame and fonts match the other panels (labels hidden, not
# deleted: deleting them dropped the top/right frame lines).
import os as _os, sys as _sys
try:
    _HERE = _os.path.dirname(_os.path.abspath(__file__))
except NameError:            # Origin "run -pyf" may not define __file__
    _HERE = _os.environ["LASC_PKG"] + "/origin_plots"
_sys.path.insert(0, _os.path.normpath(_os.path.join(_HERE, "..")))
_sys.path.insert(0, _HERE)
import config

import sys, os, shutil
import importlib, oplib as O
importlib.reload(O)
import originpro as op

BASE = config.PAPER_FIG + "/origin/LTP_LTD_powerlaw_fit.opju"   # paper copy made by paper_copies.py
PAPER = config.PAPER_FIG + "/origin/LUT_check.opju"
ORIG = config.ORIGIN_OUT + "/4 Network/LUT_check.opju"
GU = "\\g(m)S"


def legend_entries(entries, idx, fs=18):
    O.lt('legend -r;')
    O.lt('legend.text$ = "' + "%(CRLF)".join(f"\\l({i}) \\b({e})" for i, e in zip(idx, entries)) + '";')
    O.lt(f'legend.font=font("Times New Roman"); legend.fsize={fs}; legend.background=0;')


def lut_check():
    d = O.read_csv("LUT_check")
    num = lambda k: [v for v in d[k] if v is not None and v == v]
    tmp = PAPER + ".base.opju"
    shutil.copyfile(BASE, tmp)
    op.open(tmp)
    g = op.find_graph("LTPfit1")
    O.lt(f"win -a {g.name}; layer -s 1;")
    for _ in range(len(g[0].plot_list())):
        O.lt("layer.plot=1; layer -e %C;")
    O.lt("AP.show=0; AD.show=0;")
    wb, ws = O.book("LUT", "Update model vs measured updates")
    O.cols(ws, [(d["G_model_uS"], 'X', "G (model)", GU, "Gmin..Gmax of the lookup table"),
                (d["P_mean_nS"], 'Y', "Model P mean", "nS", "step of Eq. (1), alpha_P"),
                (d["P_lo_nS"], 'Y', "Model P - sigma_w", "nS", ""), (d["P_hi_nS"], 'Y', "Model P + sigma_w", "nS", ""),
                (d["D_mean_nS"], 'Y', "Model D mean", "nS", "step of Eq. (1), alpha_D"),
                (d["D_lo_nS"], 'Y', "Model D - sigma_w", "nS", ""), (d["D_hi_nS"], 'Y', "Model D + sigma_w", "nS", ""),
                (num("P_bin_G_uS"), 'X', "G (P bins)", GU, "0.03-uS bins, n >= 10"),
                (num("P_bin_mean_nS"), 'Y', "Measured P mean", "nS", "245 updates"), (num("P_bin_sd_nS"), 'E', "s.d.", "nS", ""),
                (num("D_bin_G_uS"), 'X', "G (D bins)", GU, "0.03-uS bins, n >= 10"),
                (num("D_bin_mean_nS"), 'Y', "Measured D mean", "nS", "245 updates"), (num("D_bin_sd_nS"), 'E', "s.d.", "nS", "")])
    O.lt(f'win -a {wb.name}; page.longname$ = "CrossSim update model (Eq. 1 + sigma_w) vs measured single-pulse updates";')
    O.lt(f"win -a {g.name}; layer -s 1;")
    O.plot(g, ws, 8, 7, 's', cyerr=9)       # 1 measured P
    O.plot(g, ws, 11, 10, 's', cyerr=12)    # 2 measured D
    O.plot(g, ws, 1, 0, 'l')                # 3 model P
    O.plot(g, ws, 2, 0, 'l'); O.plot(g, ws, 3, 0, 'l')   # 4, 5
    O.plot(g, ws, 4, 0, 'l')                # 6 model D
    O.plot(g, ws, 5, 0, 'l'); O.plot(g, ws, 6, 0, 'l')   # 7, 8
    O.lt(f"win -a {g.name}; win -r %H LUTchk1;")
    g = op.find_graph("LUTchk1")
    O.style(g, "\\b(Conductance \\(40)\\g(m)S\\(41))", "\\b(\\g(D)\\i(G) per pulse \\(40)nS\\(41))",
            xr=(0.15, 0.45, 0.05), yr=(-25, 15, 5))
    # plot order in the layer: 1 P points, 2 P error bars, 3 D points, 4 D error bars, 5-7 model P (mean, -, +), 8-10 model D
    n = len(g[0].plot_list()); O.L("plots in layer", n)
    O.pstyle(1, "0,0,0", None, sym=2, ssize=9)
    O.lt("layer.plot=2; set %C -c color(0,0,0); set %C -w 1000;")
    O.pstyle(3, "230,0,0", None, sym=1, ssize=9)
    O.lt("layer.plot=4; set %C -c color(230,0,0); set %C -w 1000;")
    for i in (5, 8):
        O.pstyle(i, "26,111,223", 3)
    for i in (6, 7, 9, 10):
        O.pstyle(i, "26,111,223", 2); O.lt(f"layer.plot={i}; set %C -d 1;")      # dashed
    O.hline("z0", 0.15, 0, 0.45, 0, w=1.5, color="gray", dash=2)
    legend_entries(["Measured, potentiation", "Measured, depression"], [1, 3], fs=18)
    O.at("legend", 0.03, 0.03, anchor="lb")
    O.lt(r'label -s -n LG2 "\l(5) \b(Model, Eq. 1)%(CRLF)\l(6) \b(Model \(177) \g(s)\-(w))";')
    O.lt('LG2.font=font("Times New Roman"); LG2.fsize=18; LG2.background=0;')
    O.at("LG2", 0.97, 0.03, anchor="rb")
    O.lt("win -c LTPfit;")
    O.lt(f"win -a {g.name};")
    for path in (PAPER, ORIG):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        if os.path.exists(path):
            os.remove(path)
        op.save(path)
    g.save_fig(O.S + "/previews_paper/LUT_check.png", width=900)
    op.new(asksave=False)
    os.remove(tmp)
    O.L("saved", PAPER, ORIG, g.name)


O.run_all([lut_check], "lut_check")
