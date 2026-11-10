# Paper copy of EPSC: make the baseline-shift inset readable at print size (bigger tick labels, fewer ticks).
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
import originpro as op
F = config.PAPER_FIG + "/origin/EPSC.opju"
def epsc_fix():
    op.open(F)
    g = op.find_graph("EPSC1")
    O.L("layers", len(list(g)))
    tnr = O.TNR
    O.lt(f'win -a {g.name}; layer -s 2; layer2.y.inc=0.05; layer2.y.minorTicks=0; layer2.x.inc=2; layer2.x.minorTicks=0;'
         f' layer2.x.label.font=font("{tnr}"); layer2.x.label.pt=55; layer2.x.label.bold=1;'
         f' layer2.y.label.font=font("{tnr}"); layer2.y.label.pt=55; layer2.y.label.bold=1;'
         f' xb.fsize=55; yl.fsize=55; xb.font=font("{tnr}"); yl.font=font("{tnr}");')
    ylb = g[1].label('yl')
    if ylb is not None:
        g[1].remove_label(ylb); O.L('removed inset y title')   # same unit (uA) as the main axis
    O.L("pt now", op.lt_float('layer2.x.label.pt'), op.lt_float('layer2.y.label.pt'), op.lt_float('layer1.x.label.pt'))
    O.lt('layer -s 1;')
    tmp = F + ".tmp.opju"
    op.save(tmp)
    op.new(asksave=False)
    os.remove(F); os.rename(tmp, F)
    op.open(F, readonly=True)
    op.find_graph("EPSC1").save_fig(O.S + "/previews_paper/EPSC.png", width=900)
    O.L("saved", F)
O.run_all([epsc_fix], "epsc_paper_fix")
