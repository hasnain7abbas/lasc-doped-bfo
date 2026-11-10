# Switching statistics from existing data only (la sc synaptic.xlsx via LTPLTD_raw.csv and ENDURANCE.csv):
#  1) dG-G maps: dG = G(n+1) - G(n) for consecutive potentiation (or depression) pulses of the 5 LTP/LTD cycles.
#     Conditional CDF of dG at each G, Gaussian kernel in G (sigma 0.012 uS) and in dG (h 1.2 nS).
#  2) Cumulative probability of G+ and G- over 2500 endurance cycles, with cycle-to-cycle CV.
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.normpath(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..")))
import config

import json, os, numpy as np, pandas as pd
from math import erf, sqrt
C = os.path.join(config.WORK, "prep", "csv")
d = pd.read_csv(os.path.join(C, "LTPLTD_raw.csv"))
G = d.G.values
ph = np.where(d.Gp.notna(), "P", "D")
info = {}
Phi = np.vectorize(lambda z: 0.5 * (1 + erf(z / sqrt(2))))
for P, name in (("P", "potentiation"), ("D", "depression")):
    g0, dg = [], []
    for i in range(len(G) - 1):
        if ph[i] == P and ph[i + 1] == P:
            g0.append(G[i]); dg.append((G[i + 1] - G[i]) * 1e3)          # nS
    g0, dg = np.array(g0), np.array(dg)
    pd.DataFrame({"G_uS": g0, "dG_nS": dg}).to_csv(os.path.join(C, f"DGG_points_{P}.csv"), index=False)
    gx = np.round(np.linspace(0.19, 0.42, 47), 4) if P == "P" else np.round(np.linspace(0.18, 0.46, 57), 4)
    dy = np.round(np.arange(-15, 25.01, 0.25), 2) if P == "P" else np.round(np.arange(-25, 15.01, 0.25), 2)
    rows = []
    for gc in gx:
        w = np.exp(-0.5 * ((g0 - gc) / 0.012) ** 2); w /= w.sum()
        for y in dy:
            rows.append((gc, y, float((w * Phi((y - dg) / 1.2)).sum())))
    pd.DataFrame(rows, columns=["G_uS", "dG_nS", "CDF"]).to_csv(os.path.join(C, f"DGG_map_{P}.csv"), index=False)
    info[name] = dict(n=int(len(dg)), mean_nS=round(float(dg.mean()), 2), sd_nS=round(float(dg.std(ddof=1)), 2),
                      wrong_sign_pct=round(100 * float(((dg < 0) if P == "P" else (dg > 0)).mean()), 1),
                      G_range=[round(float(g0.min()), 3), round(float(g0.max()), 3)])
e = pd.read_csv(os.path.join(C, "ENDURANCE.csv"))
out = {}
for c, nm in (("Gp", "G+"), ("Gm", "G-")):
    v = np.sort(e[c].values); n = len(v)
    out[f"{c}_uS"] = v; out[f"{c}_prob"] = 100 * (np.arange(1, n + 1) - 0.5) / n
    info[nm] = dict(n=n, mean_uS=round(float(v.mean()), 4), sd_uS=round(float(v.std(ddof=1)), 4),
                    CV_pct=round(100 * float(v.std(ddof=1) / v.mean()), 1))
r = e["ratio"].values
info["G+/G-"] = dict(mean=round(float(r.mean()), 2), CV_pct=round(100 * float(r.std(ddof=1) / r.mean()), 1))
pd.DataFrame(out).to_csv(os.path.join(C, "END_cumprob.csv"), index=False)
json.dump(info, open(os.path.join(C, "stats_info.json"), "w"), indent=1)
print(json.dumps(info, indent=1))
