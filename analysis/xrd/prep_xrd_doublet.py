# (104)/(110) doublet fit used in the paper (Table 1, Table S1, Fig. S1a-d).
# Model: two pseudo-Voigt peaks (Origin PsdVoigt1 form, Lorentzian fraction 0.7) with ONE shared width, each with its
# Cu K-alpha2 companion (half intensity, at the K-alpha2 angle), constant background, 30.95-33.05 deg, offset-corrected
# unsmoothed scans (xrd_<tag>.csv from prep_xrd.py / fix_pt.py). 1-sigma errors from the fit covariance; the uncertainties
# quoted in the paper (+/- 0.02 deg, etc.) also include the spread over Lorentzian fraction 0.5-0.9, fit window and
# background model.
# This replaces the Origin nlfit of origin_plots/plot4_xrd.py, which had left the peak positions at their starting values
# for BiFeO3 and Sc 1 %.
# Output: <WORK>/prep/csv/XRD_doublet_<tag>.csv (curves for Fig. S1a-d) and XRD_doublet.json
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.normpath(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..", "..")))
import config

import json
import numpy as np, pandas as pd
from scipy.optimize import least_squares

C = config.WORK + "/prep/csv/"
L1, L2, LAM = 1.540598, 1.544426, 1.5406
a0, c0 = 5.57882, 13.86932                       # BiFeO3, COD 2102909 (hexagonal setting)


def d_hex(h, k, l, a=a0, c=c0): return 1 / np.sqrt(4 / 3 * (h * h + h * k + k * k) / a ** 2 + l * l / c ** 2)
def tth(d, lam=L1): return 2 * np.degrees(np.arcsin(lam / (2 * d)))
def dsp(t, lam=LAM): return lam / (2 * np.sin(np.radians(t / 2)))


def latt(t104, t110):
    d104, d110 = dsp(t104), dsp(t110)
    a = 2 * d110
    c = 4 * (1 / d104 ** 2 - 4 / (3 * a ** 2)) ** -0.5
    return a, c, c / a, np.sqrt(3) / 2 * a * a * c


def pv_area(x, xc, w, A, mu):                    # Origin PsdVoigt1 (area-normalized)
    L = 2 / np.pi * w / (4 * (x - xc) ** 2 + w * w)
    G = np.sqrt(4 * np.log(2)) / (np.sqrt(np.pi) * w) * np.exp(-4 * np.log(2) * (x - xc) ** 2 / w ** 2)
    return A * (mu * L + (1 - mu) * G)


DK = tth(d_hex(1, 0, 4), L2) - tth(d_hex(1, 0, 4), L1)      # K-alpha2 offset near 32 deg (~0.081 deg)


def fit_doublet(x, y, lo=30.95, hi=33.05, mu=0.7):
    m = (x >= lo) & (x <= hi); xx, yy = x[m], y[m]
    def model(p, xx=xx):
        y0, x1, x2, A1, A2, w = p
        out = y0
        for xc, A in ((x1, A1), (x2, A2)):
            out = out + pv_area(xx, xc, w, A, mu) + 0.5 * pv_area(xx, xc + DK, w, A, mu)
        return out
    mx = yy.max()
    p0 = [0, 31.74, 32.06, mx * .25, mx * .25, 0.3]
    lb = [-np.inf, 31.3, 31.75, 0, 0, 0.05]; ub = [np.inf, 32.05, 32.5, np.inf, np.inf, 1.0]
    r = least_squares(lambda p: yy - model(p), p0, bounds=(lb, ub))
    cov = np.linalg.pinv(r.jac.T @ r.jac) * (r.fun ** 2).sum() / (len(yy) - len(p0))
    return r.x, cov, xx, yy


def derived(p, cov, nmc=4000, rng=np.random.default_rng(1)):
    x1, x2 = p[1], p[2]
    sub = cov[1:3, 1:3]
    s = rng.multivariate_normal([x1, x2], sub, nmc)
    Ls = np.array([latt(a, b) for a, b in s])
    a, c, ca, V = latt(x1, x2)
    return dict(t104=x1, t110=x2, e104=np.sqrt(sub[0, 0]), e110=np.sqrt(sub[1, 1]), split=x2 - x1,
                esplit=np.sqrt(sub[0, 0] + sub[1, 1] - 2 * sub[0, 1]), a=a, c=c, ca=ca, V=V,
                ea=Ls[:, 0].std(), ec=Ls[:, 1].std(), eca=Ls[:, 2].std(), eV=Ls[:, 3].std())


info = {}
for tag in ["BFO", "La", "Sc", "LaSc"]:
    d0 = pd.read_csv(C + f"xrd_{tag}.csv")
    p, cov, xx, yy = fit_doublet(d0["tth"].values, d0["I_clean"].values)
    y0, x1, x2, A1, A2, w = p
    comp = lambda xc, A: pv_area(xx, xc, w, A, 0.7) + 0.5 * pv_area(xx, xc + DK, w, A, 0.7)
    c104, c110 = comp(x1, A1), comp(x2, A2)
    fit = y0 + c104 + c110
    pd.DataFrame({"tth": xx, "I": yy, "p104": c104 + y0, "p110": c110 + y0, "fit": fit, "base": np.full_like(xx, y0),
                  "resid": yy - fit}).to_csv(C + f"XRD_doublet_{tag}.csv", index=False)
    r2 = 1 - ((yy - fit) ** 2).sum() / ((yy - yy.mean()) ** 2).sum()
    d = derived(p, cov)
    info[tag] = dict(**{k: float(v) for k, v in d.items()}, w=float(w), r2=float(r2))
    print(f"{tag:5s} 104 {x1:.3f} 110 {x2:.3f} split {x2 - x1:.3f}+-{d['esplit']:.3f} c/a {d['ca']:.4f} V {d['V']:.1f} "
          f"w {w:.3f} R2 {r2:.4f}")
json.dump(info, open(C + "XRD_doublet.json", "w"), indent=1)
