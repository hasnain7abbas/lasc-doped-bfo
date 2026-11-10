# Pt(111) removal for Sc 1%: window 37.8-41.2 deg = linear background + BiFeO3 (006)+(202) (card height ratio 9.7:31.3,
# the film's own fitted offset and FWHM, free common height) + one free Pt(111) pseudo-Voigt doublet (eta 0.5). Pt part subtracted.
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.normpath(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..", "..")))
import config

import numpy as np, pandas as pd, json
import shift as S, pt as P
from scipy.optimize import least_squares
OUT = config.WORK + "/prep/csv/"
info = json.load(open(OUT + "xrd_info.json")); Z = info["Z"]
off = info["fits"]["Sc"]["off"]; w = info["fits"]["Sc"]["fwhm"]
x, y = S.load("sc"); m = (x > 37.8) & (x < 41.2); xx, yy = x[m], y[m]
d6, d2, dp = S.dB["006"], S.dB["202"], P.dPt["111"]
def model(q, xx):
    b = q[0] + q[1] * (xx - 39.5)
    bfo = q[2] * (P.doublet(xx, S.tth(d6, S.L1) + off, 9.7 / 31.3, w, 0.7, d6) + P.doublet(xx, S.tth(d2, S.L1) + off, 1, w, 0.7, d2))
    return b, bfo, P.doublet(xx, q[3], q[4], q[5], 0.5, dp)
r = least_squares(lambda q: yy - sum(model(q, xx)), [0, 0, 60, 39.35, 200, 0.2], bounds=([-50, -50, 0, 39.1, 0, 0.08], [50, 50, 500, 39.7, 1000, 0.45]))
q = r.x; ptc = model(q, x)[2]
d = pd.read_csv(OUT + "xrd_Sc.csv"); d["Pt111"] = ptc; d["I_clean"] = d["I"] - ptc; d.to_csv(OUT + "xrd_Sc.csv", index=False)
info["Pt111"] = dict(center_raw=q[3], center_corrected=q[3] - Z, height=q[4], fwhm=q[5], eta=0.5, card=S.tth(dp, S.L1),
                     bfo202_height=q[2], window=[37.8, 41.2], method="BFO (006)+(202) card ratio, film offset/FWHM, free height + free Pt(111)")
json.dump(info, open(OUT + "xrd_info.json", "w"), indent=1, default=float)
print(np.round(q, 3), "corrected centre", round(q[3] - Z, 3))
