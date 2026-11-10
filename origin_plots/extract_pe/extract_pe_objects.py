import os as _os, sys as _sys
try:
    _HERE = _os.path.dirname(_os.path.abspath(__file__))
except NameError:            # Origin "run -pyf" may not define __file__
    _HERE = _os.environ["LASC_PKG"] + "/origin_plots/extract_pe"
_sys.path.insert(0, _os.path.normpath(_os.path.join(_HERE, "..", "..")))
_sys.path.insert(0, _HERE)
import config

import originpro as op, os, glob, traceback
S = config.WORK
log = open(S + "/tools/t_extract_pe.log", "w", encoding="utf8")
def L(*a): log.write(" ".join(str(x) for x in a) + "\n"); log.flush()
try:
    import sys; L("py", sys.version)
    out = S + "/pe_csv"; os.makedirs(out, exist_ok=True)
    for f in sorted(glob.glob(S + "/pe_opj/*.opju")):
        op.open(f.replace("\\", "/"))
        tag = os.path.basename(f)[:-5]
        L("##", tag)
        for gp in op.pages('g'):
            L(" graph", gp.name, gp.lname)
            for ly in gp:
                for pl in ly.plot_list():
                    L("   plot", pl.lt_range(), )
        for wb in op.pages('w'):
            for sh in wb:
                L(" sheet", wb.name, wb.lname, sh.name, "cols", sh.cols, "rows", sh.rows)
                L("   lnames", [sh.get_label(i, 'L') for i in range(sh.cols)])
                L("   units", [sh.get_label(i, 'U') for i in range(sh.cols)])
                L("   comments", [sh.get_label(i, 'C') for i in range(sh.cols)])
                df = sh.to_df()
                df.to_csv(f"{out}/{tag}__{wb.name}_{sh.name}.csv", index=False)
except Exception:
    L(traceback.format_exc())
log.close()
