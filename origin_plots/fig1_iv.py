import os as _os, sys as _sys
try:
    _HERE = _os.path.dirname(_os.path.abspath(__file__))
except NameError:            # Origin "run -pyf" may not define __file__
    _HERE = _os.environ["LASC_PKG"] + "/origin_plots"
_sys.path.insert(0, _os.path.normpath(_os.path.join(_HERE, "..")))
_sys.path.insert(0, _HERE)
import config

import sys
pass
import importlib, oplib as O
importlib.reload(O)
import originpro as op, os

SRC = config.ORIGIN_OUT + "/2 I-V and conduction/IV_bipolar.opju"
DST = config.FIG1 + "/origin/IV_bipolar_Fig1c.opju"

# sweep arrows in axis units (V, uA on log axis): (x1, y1) tail -> (x2, y2) head, label position
ARROWS = [   # short, thin arrows beside each branch: (label, tail, head, label position) in axis units (V, uA log)
    ("1", (10.6, 0.0030), (12.2, 0.0090), (12.6, 0.0040)),   # 0 -> +15 V, lower right branch (HRS)
    ("2", (11.4, 3.0), (8.8, 1.9), (10.3, 4.2)),             # +15 -> 0 V, upper right branch (LRS)
    ("3", (-3.8, 0.0072), (-6.4, 0.0125), (-5.6, 0.0058)),   # 0 -> -12 V, lower left branch
    ("4", (-10.4, 3.6), (-7.6, 2.5), (-9.3, 5.0)),           # -12 -> 0 V, upper left branch
]

def fig1c():
    op.open(SRC, readonly=True)
    g = op.find_graph("IVbip1")
    O.lt(f'win -a {g.name}; layer -s 1;')
    for i in range(1, 12):                                  # drop the slide title (panel letters replace it)
        t = op.lt_str(f'T{i}.text$') if op.lt_float(f'exist(T{i})') else ""
        if "Bipolar" in t:
            O.lt(f'label -r T{i};'); O.L("removed title", f"T{i}")
    for n, (x1, y1), (x2, y2), (tx, ty) in ARROWS:
        nm = f"SW{n}"
        O.lt(f'draw -n {nm} -l {{{x1},{y1},{x2},{y2}}};')
        O.lt(f'{nm}.linewidth=2.5; {nm}.color=color(0,0,0); {nm}.attach=2;'
             f' {nm}.arrowEndShape=2; {nm}.arrowEndLength=9; {nm}.arrowEndWidth=7;')
        O.text(n, tx, ty, fs=24)
    if os.path.exists(DST):
        os.remove(DST)
    op.save(DST)
    g.save_fig(O.S + "/previews/IV_bipolar_Fig1c.png", width=900)
    O.L("saved", DST)

O.run_all([fig1c], "fig1_iv")
