# XRD preparation: instrument offset from pure BiFeO3, applied to every scan; Pt(111) electrode peak removed from Sc 1%.
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.normpath(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..", "..")))
import config

import numpy as np, pandas as pd, json, os
import shift as S
import pt as P

OUT = config.WORK + "/prep/csv/"
FILES = {"BFO": "pure bfo", "La": "la", "Sc": "sc", "LaSc": "la sc", "Sc2": "sc 2nd"}

xb, yb = S.load("pure bfo")
p, e, (Z, _, wB, etaB, ampsB, _) = S.fit_shift(xb, yb)
info = dict(Z=Z, Zerr=e[0], per_peak={})
for lo, hi, hk in S.REG:
    pp, ee, uu = S.fit_shift(xb, yb, regs=[(lo, hi, hk)])
    info["per_peak"]["/".join(hk)] = (uu[0], ee[0])

fits = {}
for tag, f in FILES.items():
    x, y = S.load(f)
    pp, ee, u = S.fit_shift(x, y)
    fits[tag] = dict(off=u[0], w=u[2], eta=u[3], amps=dict(zip([h for _, _, hk in S.REG for h in hk], u[4])))

# Pt(111) in Sc 1%: BiFeO3 (006)/(202) heights fixed from the same film measured at the second position ("sc 2nd",
# no electrode in the beam), scaled by the (104)+(110) heights; the remaining peak is Pt(111).
x, y = S.load("sc")
f2, f1 = fits["Sc2"], fits["Sc"]
scale = (f1["amps"]["104"] + f1["amps"]["110"]) / (f2["amps"]["104"] + f2["amps"]["110"])
lo, hi = 38.0, 41.0
m = (x >= lo) & (x <= hi); xx, yy = x[m], y[m]
from scipy.optimize import least_squares
def bfo_part(xx):
    out = 0
    for h in ("006", "202"):
        out = out + P.doublet(xx, S.tth(S.dB[h], S.L1) + f1["off"], f2["amps"][h] * scale, f1["w"], f1["eta"], S.dB[h])
    return out
tP = S.tth(P.dPt["111"], S.L1)
def res(q):
    return yy - (q[0] + q[1] * (xx - xx.mean()) + bfo_part(xx) + P.doublet(xx, q[2], q[3], q[4], q[5], P.dPt["111"]))
r = least_squares(res, [0, 0, 39.4, 150, 0.3, 0.5], bounds=([-np.inf, -np.inf, tP - 0.8, 0, 0.08, 0], [np.inf, np.inf, tP + 0.3, np.inf, 1.0, 1]))
q = r.x
pt_comp = P.doublet(x, q[2], q[3], q[4], q[5], P.dPt["111"])
info["Pt111"] = dict(center_raw=q[2], height=q[3], fwhm=q[4], eta=q[5], center_corrected=q[2] - Z, card=tP,
                     bfo_scale=scale, window=[lo, hi])
print("Pt(111) in Sc 1%%: centre %.3f (raw) / %.3f (corrected), height %.0f, FWHM %.3f" % (q[2], q[2] - Z, q[3], q[4]))

for tag, f in FILES.items():
    x, y = S.load(f)
    d = pd.DataFrame({"tth_raw": x, "tth": x - Z, "I": y})
    d["I_clean"] = y - pt_comp if tag == "Sc" else y
    if tag == "Sc": d["Pt111"] = pt_comp
    d.to_csv(OUT + f"xrd_{tag}.csv", index=False)

info["fits"] = {k: dict(off=v["off"], corrected_off=v["off"] - Z, fwhm=v["w"]) for k, v in fits.items()}
# card positions (K-alpha1) for labels
info["card"] = {h: S.tth(S.dB[h], S.L1) for h in S.dB}
json.dump(info, open(OUT + "xrd_info.json", "w"), indent=1, default=float)
print(json.dumps({k: info[k] for k in ("Z", "Zerr", "per_peak")}, indent=1, default=float))
for k, v in info["fits"].items(): print(k, {a: round(b, 3) for a, b in v.items()})
