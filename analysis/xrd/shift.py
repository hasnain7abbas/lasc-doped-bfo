# Instrument 2-theta offset from the pure BiFeO3 scan.
# Each reflection = pseudo-Voigt at the Cu K-alpha1 position + 0.5 x the same at K-alpha2 (xrdml: 1.540598 / 1.544426 A).
# Reference d-spacings: BiFeO3 R3c, COD 2102909 (Palewicz et al., Acta Cryst. B 63, 537 (2007)), a = 5.57882, c = 13.86932 A.
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.normpath(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..", "..")))
import config

import numpy as np, sys, json
from scipy.optimize import least_squares

D = config.XRD_RAW + "/"
L1, L2 = 1.540598, 1.544426
a, c = 5.57882, 13.86932
def d_hex(h, k, l): return 1 / np.sqrt(4 / 3 * (h * h + h * k + k * k) / a ** 2 + l * l / c ** 2)
def tth(d, lam): return 2 * np.degrees(np.arcsin(lam / (2 * d)))
BFO = {"012": (0, 1, 2), "104": (1, 0, 4), "110": (1, 1, 0), "006": (0, 0, 6), "202": (2, 0, 2), "024": (0, 2, 4),
       "116": (1, 1, 6), "122": (1, 2, 2), "018": (0, 1, 8), "214": (2, 1, 4), "300": (3, 0, 0)}
dB = {k: d_hex(*v) for k, v in BFO.items()}
REG = [(21.2, 23.6, ["012"]), (30.9, 33.0, ["104", "110"]), (38.4, 40.4, ["006", "202"]), (44.9, 46.8, ["024"]),
       (50.4, 52.6, ["116", "122"]), (55.6, 58.2, ["018", "214", "300"])]

def pv(x, x0, w, eta):
    g = np.exp(-4 * np.log(2) * (x - x0) ** 2 / w ** 2); l = 1 / (1 + 4 * (x - x0) ** 2 / w ** 2)
    return eta * l + (1 - eta) * g

def load(f):
    a_ = np.loadtxt(D + f + ".ASC"); return a_[:, 0], a_[:, 1]

def fit_shift(x, y, regs=REG, model="const"):
    sel = [((x >= lo) & (x <= hi), hk) for lo, hi, hk in regs]
    nh = sum(len(h) for _, h in sel)
    def unpack(p):
        Z, S, w, eta = p[0], p[1], p[2], p[3]; amps = p[4:4 + nh]; bg = p[4 + nh:]
        return Z, S, w, eta, amps, bg
    def resid(p):
        Z, S, w, eta, amps, bg = unpack(p); r = []; k = 0
        for j, (m, hk) in enumerate(sel):
            xx = x[m]; mod = bg[2 * j] + bg[2 * j + 1] * (xx - xx.mean())
            for h in hk:
                for lam, wt in ((L1, 1.0), (L2, 0.5)):
                    t0 = tth(dB[h], lam)
                    off = Z + (S * np.cos(np.radians(t0 / 2)) if model == "disp" else 0)
                    mod = mod + amps[k] * wt * pv(xx, t0 + off, w, eta)
                k += 1
            r.append(y[m] - mod)
        return np.concatenate(r)
    p0 = [-0.05, 0, 0.3, 0.6] + [100] * nh + [0, 0] * len(sel)
    lb = [-1.5, -2, 0.05, 0] + [0] * nh + [-np.inf] * 2 * len(sel)
    ub = [1.5, 2, 1.0, 1] + [np.inf] * nh + [np.inf] * 2 * len(sel)
    if model == "const": lb[1], ub[1] = -1e-9, 1e-9; p0[1] = 0
    r = least_squares(resid, p0, bounds=(lb, ub))
    J = r.jac; dof = max(1, len(r.fun) - len(p0)); s2 = (r.fun ** 2).sum() / dof
    try: cov = np.linalg.pinv(J.T @ J) * s2; err = np.sqrt(np.diag(cov))
    except Exception: err = np.full(len(p0), np.nan)
    return r.x, err, unpack(r.x)

if __name__ == "__main__":
    x, y = load("pure bfo")
    p, e, (Z, S, w, eta, amps, bg) = fit_shift(x, y)
    print(f"constant offset Z = {Z:+.4f} +/- {e[0]:.4f} deg, FWHM {w:.3f}, eta {eta:.2f}")
    p2, e2, u2 = fit_shift(x, y, model="disp")
    print(f"zero + displacement: Z = {u2[0]:+.4f} +/- {e2[0]:.3f}, S = {u2[1]:+.4f} +/- {e2[1]:.3f}")
    # single-peak check: each region alone
    for lo, hi, hk in REG:
        pp, ee, uu = fit_shift(x, y, regs=[(lo, hi, hk)])
        print(f"  {'/'.join(hk):12s} offset {uu[0]:+.3f} +/- {ee[0]:.3f}")
    json.dump(dict(Z=Z, Zerr=e[0], fwhm=w, eta=eta), open(sys.argv[1], "w"))
