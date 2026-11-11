# Fig. S1a-d (and Fig. 2c source graphs): replace the (104)/(110) deconvolution data in the existing Origin projects with
# the converged refit of analysis/xrd/prep_xrd_doublet.py (shared width, K-alpha1 + K-alpha2, unsmoothed data). The old Origin nlfit
# had left the peak positions at their starting values for BiFeO3 and Sc 1 %. Graph styling and frames are kept; only the
# worksheet columns, their comments and the y range change. Paper copies and originals are both updated.
import os as _os, sys as _sys
try:
    _HERE = _os.path.dirname(_os.path.abspath(__file__))
except NameError:            # Origin "run -pyf" may not define __file__
    _HERE = _os.environ["LASC_PKG"] + "/origin_plots"
_sys.path.insert(0, _os.path.normpath(_os.path.join(_HERE, "..")))
_sys.path.insert(0, _HERE)
import config

import sys, os, json
import importlib, oplib as O
importlib.reload(O)
import originpro as op

INFO = json.load(open(O.S + "/prep/csv/XRD_doublet.json"))
PATHS = [config.PAPER_FIG + "/origin/XRD_decon_{}.opju",                       # paper copies (paper_copies.py)
         config.ORIGIN_OUT + "/5 XRD/Deconvolution/XRD_decon_{}.opju"]           # originals (plot4_xrd.py)


def one(tag):
    def f():
        d = O.read_csv(f"XRD_doublet_{tag}")
        I = INFO[tag]
        for k, pat in enumerate(PATHS):
            F = pat.format(tag)
            op.open(F)
            ws = None
            for wb in op.pages("w"):
                for sh in wb:
                    if sh.name == "Deconvolution":
                        ws = sh
            if ws is None:
                raise RuntimeError("no Deconvolution sheet in " + F)
            n = len(d["tth"])
            ws.clear()
            cols = [("tth", "2\\g(q) corrected", "deg", "30.95-33.05 deg, offset-corrected, unsmoothed"),
                    ("I", "Measured intensity", "counts", "fitted data (unsmoothed)"),
                    ("p104", "(104)R peak", "counts", f"pseudo-Voigt, K\\g(a)1+K\\g(a)2, shared FWHM {I['w']:.3f} deg: 2\\g(q) = {I['t104']:.3f} +/- {I['e104']:.3f} deg"),
                    ("p110", "(110)R peak", "counts", f"2\\g(q) = {I['t110']:.3f} +/- {I['e110']:.3f} deg; splitting {I['split']:.3f} +/- {I['esplit']:.3f} deg"),
                    ("fit", "Cumulative fit", "counts", f"R\\+(2) = {I['r2']:.4f}"),
                    ("base", "Baseline", "counts", "fitted constant")]
            for j, (key, lname, unit, com) in enumerate(cols):
                ws.from_list(j, d[key], lname=lname, units=unit, comments=com)
            g = None
            for gp in op.pages("g"):
                if gp.name.startswith("XD"):
                    g = gp
            O.lt(f"win -a {g.name}; layer -s 1;")
            mx = max(d["I"]); mn = min(min(d["I"]), d["base"][0])
            O.lt(f"layer.y.from={mn - 0.08 * mx}; layer.y.to={1.42 * mx};")
            tmp = F + ".tmp.opju"
            op.save(tmp)
            if k == 0:
                g.save_fig(O.S + f"/previews_paper/XRD_decon_{tag}.png", width=900)
            op.new(asksave=False)
            os.remove(F); os.rename(tmp, F)
            O.L(tag, "updated", F, g.name, n, "rows")
    f.__name__ = "decon_v2_" + tag
    return f


O.run_all([one(t) for t in ("BFO", "La", "Sc", "LaSc")], "xrd_decon_v2")
