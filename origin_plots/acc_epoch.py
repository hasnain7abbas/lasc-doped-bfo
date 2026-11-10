# Fig. 6c: MNIST test accuracy versus epoch from the CrossSim run (crosssim_run/accuracy_vs_epoch.csv).
# Main panel: ideal weights, measured nonlinearity only, nonlinearity + write noise. The assumed-read-noise arm
# (device_full) is kept in the workbook but not plotted (reported in Table S2).
# Built on a copy of the Fig. 5c paper graph (LTP_LTD_powerlaw_fit.opju) so the layer, 4-pt frame and fonts are those of
# the other panels: a graph created from scratch here rendered without the top/right frame lines on Copy Page.
import os as _os, sys as _sys
try:
    _HERE = _os.path.dirname(_os.path.abspath(__file__))
except NameError:            # Origin "run -pyf" may not define __file__
    _HERE = _os.environ["LASC_PKG"] + "/origin_plots"
_sys.path.insert(0, _os.path.normpath(_os.path.join(_HERE, "..")))
_sys.path.insert(0, _HERE)
import config

import sys, os, csv, shutil
import importlib, oplib as O
importlib.reload(O)
import originpro as op

SRC = config.PKG + "/crosssim/accuracy_vs_epoch.csv"            # written by crosssim/plot_results.py
BASE = config.PAPER_FIG + "/origin/LTP_LTD_powerlaw_fit.opju"   # paper copy made by paper_copies.py
PAPER = config.PAPER_FIG + "/origin/Accuracy_vs_epoch.opju"
ORIG = config.ORIGIN_OUT + "/4 Network/Accuracy_vs_epoch.opju"


def legend_entries(entries, fs=20):
    O.lt('legend -r;')
    O.lt('legend.text$ = "' + "%(CRLF)".join(f"\\l({i}) \\b({e})" for i, e in enumerate(entries, 1)) + '";')
    O.lt(f'legend.font=font("Times New Roman"); legend.fsize={fs}; legend.background=0;')


def acc_epoch():
    rows = list(csv.DictReader(open(SRC, encoding="utf8")))
    col = lambda k: [float(r[k]) for r in rows]
    tmp = PAPER + ".base.opju"
    shutil.copyfile(BASE, tmp)
    op.open(tmp)
    g = op.find_graph("LTPfit1")
    O.lt(f"win -a {g.name}; layer -s 1;")
    n = len(g[0].plot_list())
    for _ in range(n):
        O.lt("layer.plot=1; layer -e %C;")
    O.lt("AP.show=0; AD.show=0;")                      # hide the alpha labels (deleting them dropped the top/right frame)
    wb, ws = O.book("ACC", "MNIST accuracy vs epoch (CrossSim)")
    O.cols(ws, [(col("epoch"), 'X', "Epoch", "", ""),
                (col("ideal"), 'Y', "Ideal", "%", "floating-point weights"),
                (col("device_nonlin"), 'Y', "Nonlinearity", "%", "measured alpha_P, alpha_D, no update noise"),
                (col("device_wn"), 'Y', "Nonlinearity + write noise", "%", "measured alpha and sigma_w"),
                (col("device_full"), 'Y', "+ read noise (assumed 0.03)", "%", "not plotted; Table S2")])
    O.lt(f'win -a {wb.name}; page.longname$ = "CrossSim 2.0, 784-200-10 sigmoid MLP, MNIST 60k/10k, 40 epochs";')
    O.lt(f"win -a {g.name}; layer -s 1; page.longname$ = \"Accuracy vs epoch\";")
    for c in (1, 2, 3):
        O.plot(g, ws, c, 0, 'y')
    O.lt(f"win -a {g.name}; win -r %H ACC1;")
    g = op.find_graph("ACC1"); O.L("renamed to", repr(g.name) if g else None)
    O.style(g, "\\b(Epoch)", "\\b(Test Accuracy \\(40)%\\(41))", xr=(0, 40, 10), yr=(80, 100, 4))
    O.pstyle(1, "0,0,0", 3, sym=2, ssize=7)
    O.pstyle(2, "26,111,223", 3, sym=1, ssize=7)
    O.pstyle(3, "230,0,0", 3, sym=3, ssize=7)
    legend_entries(["Ideal", "Nonlinearity", "Nonlinearity + write noise"], fs=20)
    O.at("legend", 0.97, 0.03, anchor="rb")
    O.lt("win -c LTPfit;")                              # drop the copied LTP workbook
    O.lt(f"win -a {g.name};")
    for path in (PAPER, ORIG):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        if os.path.exists(path):
            os.remove(path)
        op.save(path)
    g.save_fig(O.S + "/previews_paper/Accuracy_vs_epoch.png", width=900)
    op.new(asksave=False)
    os.remove(tmp)
    O.L("saved", PAPER, ORIG, g.name)


O.run_all([acc_epoch], "acc_epoch")
