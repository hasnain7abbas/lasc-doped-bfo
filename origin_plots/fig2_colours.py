# Paper copies of Fig. 2c (P-E 25 V) and 2d (J-E): recolour the four films to the XRD order of Fig. 2a, b
# (BiFeO3 black, La 7.5% blue, Sc 1% green, La 7.5%-Sc 1% red). Plots are in film order BFO, La7.5, Sc1, LaSc
# (one plot per film in P-E, two branches per film in J-E); the J-E end labels are recoloured by their text.
import os as _os, sys as _sys
try:
    _HERE = _os.path.dirname(_os.path.abspath(__file__))
except NameError:            # Origin "run -pyf" may not define __file__
    _HERE = _os.environ["LASC_PKG"] + "/origin_plots"
_sys.path.insert(0, _os.path.normpath(_os.path.join(_HERE, "..")))
_sys.path.insert(0, _HERE)
import config

import sys, os
import importlib, oplib as O
importlib.reload(O)
import originpro as op

D = config.PAPER_FIG + "/origin/"
COL = ["0,0,0", "26,111,223", "55,173,107", "230,0,0"]            # BFO, La7.5, Sc1, LaSc (= plot4_xrd FILMS)
KEYS = [("Sc 1%", 3), ("La 7.5%-Sc 1%", 3), ("La 7.5%", 1), ("BiFeO", 0)]   # longest match first is handled below


def film_of(text):
    t = text.replace("\\b(", "").replace(")", "")
    if "Sc" in t and "La" in t: return 3
    if "Sc" in t: return 2
    if "La" in t: return 1
    if "BiFeO" in t: return 0
    return None


def first_graph():
    for p in op.pages("g"):
        return p
    return None


def save_over(F, g, png):
    tmp = F + ".tmp.opju"
    op.save(tmp)
    op.new(asksave=False)
    os.remove(F); os.rename(tmp, F)
    op.open(F, readonly=True)
    op.find_graph(g).save_fig(O.S + "/previews_paper/" + png, width=900)


def pe():
    F = D + "PE_compare_25V.opju"
    op.open(F)
    g = first_graph(); O.L("PE graph", g.name)
    O.lt(f"win -a {g.name}; layer -s 1;")
    n = len(g[0].plot_list()); O.L("plots", n)
    for i in range(1, n + 1):
        c = COL[i - 1]
        O.lt(f"layer.plot={i}; set %C -c color({c}); set %C -cl color({c});")
    O.lt("legend -r;") if False else None                          # custom legend uses \l(n): colours follow the plots
    save_over(F, g.name, "PE_compare_25V.png"); O.L("saved", F)


def je():
    F = D + "UNI_compare_J_E.opju"
    op.open(F)
    g = first_graph(); O.L("JE graph", g.name)
    O.lt(f"win -a {g.name}; layer -s 1;")
    n = len(g[0].plot_list()); O.L("plots", n)
    for i in range(1, n + 1):
        c = COL[(i - 1) // 2]
        O.lt(f"layer.plot={i}; set %C -c color({c}); set %C -cl color({c}); set %C -cse color({c});")
    # end labels: graphic objects whose text names a film
    names = []
    O.lt('string _nm$=""; doc -e G { _nm$ = _nm$ + "%B "; };')
    for nm in op.get_lt_str("_nm$").split():
        try:
            txt = op.get_lt_str(f"{nm}.text$")
        except Exception:
            continue
        k = film_of(txt)
        if k is not None and nm.lower() != "legend":
            O.lt(f"{nm}.color=color({COL[k]});"); names.append((nm, txt, k))
    O.L("labels recoloured", names)
    save_over(F, g.name, "UNI_compare_J_E.png"); O.L("saved", F)


O.run_all([pe, je], "fig2_colours")
