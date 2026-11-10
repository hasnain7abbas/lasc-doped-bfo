# Look for Pt electrode reflections (fcc, a = 3.9231 A) in the Sc and La-Sc scans.
# Window model: BiFeO3 reflections (positions from the card + the sample's own fitted offset) + one free extra peak near Pt.
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.normpath(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..", "..")))
import config

import numpy as np, json, sys
from scipy.optimize import least_squares
import shift as S

aPt = 3.9231
PT = {"111": (1, 1, 1), "200": (2, 0, 0), "220": (2, 2, 0)}
dPt = {k: aPt / np.sqrt(sum(i * i for i in v)) for k, v in PT.items()}
WIN = {"111": (38.3, 40.8, ["006", "202"]), "200": (45.0, 47.2, ["024"]), "220": (66.0, 68.6, ["208", "220"])}
S.dB["208"] = S.d_hex(2, 0, 8); S.dB["220"] = S.d_hex(2, 2, 0)

def doublet(x, t1, amp, w, eta, d):
    t2 = S.tth(d, S.L2) - S.tth(d, S.L1) + t1
    return amp * (S.pv(x, t1, w, eta) + 0.5 * S.pv(x, t2, w, eta))

def window(x, y, off, w0, eta0, hk_pt, extra=True):
    lo, hi, hks = WIN[hk_pt]; m = (x >= lo) & (x <= hi); xx, yy = x[m], y[m]
    tP = S.tth(dPt[hk_pt], S.L1)
    def model(p, xx=xx):
        mod = p[0] + p[1] * (xx - xx.mean())
        for i, h in enumerate(hks):
            mod = mod + doublet(xx, S.tth(S.dB[h], S.L1) + off, p[2 + i], p[-3] if extra else w0, eta0, S.dB[h])
        if extra:
            mod = mod + doublet(xx, p[-2], p[-1], p[-3], eta0, dPt[hk_pt])
        return mod
    nh = len(hks)
    p0 = [0, 0] + [50] * nh + ([w0, tP - 0.3, 50] if extra else [])
    lb = [-np.inf, -np.inf] + [0] * nh + ([0.1, tP - 0.7, 0] if extra else [])
    ub = [np.inf, np.inf] + [np.inf] * nh + ([1.0, tP + 0.3, np.inf] if extra else [])
    r = least_squares(lambda p: yy - model(p), p0, bounds=(lb, ub))
    return r, model, xx, yy

if __name__ == "__main__":
    Z = json.load(open("shift.json"))["Z"]
    out = {}
    for f in ["pure bfo", "la", "sc", "sc 2nd", "la sc"]:
        x, y = S.load(f)
        p, e, u = S.fit_shift(x, y); off, w0, eta0 = u[0], u[2], u[3]
        for hk in WIN:
            r1, m1, xx, yy = window(x, y, off, w0, eta0, hk, True)
            r0, m0, _, _ = window(x, y, off, w0, eta0, hk, False)
            chi1, chi0 = (r1.fun ** 2).sum(), (r0.fun ** 2).sum()
            print(f"{f:9s} Pt({hk}) card {S.tth(dPt[hk], S.L1):.2f}: extra peak at {r1.x[-2]:.2f} (raw), amp {r1.x[-1]:6.1f}, "
                  f"fwhm {r1.x[-3]:.2f}; chi2 {chi0:8.0f} -> {chi1:8.0f}")
            out[f"{f}|{hk}"] = dict(center=r1.x[-2], amp=r1.x[-1], w=r1.x[-3], eta=eta0, chi0=chi0, chi1=chi1, off=off)
    json.dump(out, open("pt.json", "w"), indent=1)
