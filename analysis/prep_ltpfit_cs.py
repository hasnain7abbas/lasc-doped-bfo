# Power-law fit of the cycle-averaged LTP/LTD in the CrossSim lookup-table form (same model as
# parameter extraction and mnist/crosssim_run/extract_params.py), so Fig. 5c reports the alpha used in the simulation.
#   P: G(n) = G0 + (G1 - G0) * [1 - (1 - n/N)^aP]      D: G(n) = G1 + (G0 - G1) * (1 - n/N)^aD,  n = 0..N, N = 49
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.normpath(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..")))
import config

import os, json, numpy as np, pandas as pd
from scipy.optimize import curve_fit
C = os.path.join(config.WORK, "prep", "csv")
d = pd.read_csv(os.path.join(C, "LTPLTD_avg.csv")); Gm = d.Gmean.values
P, D = Gm[:50], Gm[50:]; N = 49; n = np.arange(50.0)
pot = lambda n, a0, a1, a: a0 + (a1 - a0) * (1 - np.clip(1 - n / N, 1e-12, 1) ** a)
dep = lambda n, b1, b0, a: b0 + (b1 - b0) * np.clip(1 - n / N, 1e-12, 1) ** a
out = {}
for tag, f, y in (("P", pot, P), ("D", dep, D)):
    p, cov = curve_fit(f, n, y, p0=[y[0], y[-1], 2.0], bounds=([0, 0, 0.01], [np.inf, np.inf, 200]), maxfev=50000)
    yf = f(n, *p); r2 = 1 - np.sum((y - yf) ** 2) / np.sum((y - y.mean()) ** 2)
    out[tag] = dict(alpha=float(p[2]), alpha_se=float(np.sqrt(cov[2, 2])), start=float(p[0]), end=float(p[1]), r2=float(r2), fit=yf.tolist())
pd.DataFrame({"k": np.arange(1, 101), "fit": out["P"]["fit"] + out["D"]["fit"]}).to_csv(os.path.join(C, "LTPLTD_fit_cs.csv"), index=False)
info = {k: {kk: vv for kk, vv in v.items() if kk != "fit"} for k, v in out.items()}
json.dump(info, open(os.path.join(C, "LTPLTD_fit_cs.json"), "w"), indent=1); print(json.dumps(info, indent=1))
