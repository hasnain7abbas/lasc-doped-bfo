# conduction: both branches of each film, best (lowest-noise) cycle per branch, |V| >= 1.5 V
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.normpath(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..")))
import config

import sys, json, numpy as np, pandas as pd
from scipy.signal import savgol_filter
S = config.WORK; C = S + "/prep/csv/"
AREA = 3.14e-4; D_UM = {"BFO": 0.5, "La7.5": 0.5, "Sc1": 0.5, "LaSc": 0.580}
man = json.load(open(S + "/prep/manifest_v2.json"))
for tag in D_UM:
    d = pd.read_csv(C + f"UNI_{tag}.csv"); cyc = [int(c[1:]) for c in d.columns if c.startswith("V")]
    for br, sgn in [("pos", 1), ("neg", -1)]:
        best = None
        for c in cyc:
            V = d[f"V{c}"].dropna().values; I = d[f"I{c}"].dropna().values[:len(V)]
            m = sgn * V >= 1.5; v = np.abs(V[m]); i = np.abs(I[m]); o = np.argsort(v); v, i = v[o], i[o]
            if len(v) < 20 or np.any(i <= 0): continue
            li = np.log10(i); rms = np.sqrt(np.mean((li - savgol_filter(li, 11, 2)) ** 2))
            if best is None or rms < best[0]: best = (rms, c, v, i)
        rms, c, v, i = best
        E = v / (D_UM[tag] * 1e-4) / 1e3; J = i / AREA
        pd.DataFrame({"V": sgn * v, "absI": i, "E": E, "J": J, "logE": np.log10(E), "logJ": np.log10(J)}).to_csv(C + f"v4_COND_{tag}_{br}.csv", index=False)
        man[f"v4_COND_{tag}_{br}"] = dict(cycle=c, d_um=D_UM[tag], rms=float(rms))
        print(tag, br, "cycle", c, "n", len(v), "rms %.3f" % rms)
json.dump(man, open(S + "/prep/manifest_v2.json", "w"), indent=1, default=float)
