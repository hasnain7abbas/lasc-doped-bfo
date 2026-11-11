# Fig. 6c data: the update model used by CrossSim (mean step of Eq. 1 with the crosssim/device_params.json values,
# +/- sigma_w) against the measured single-pulse updates (245 per polarity, Fig. 5d, e; DGG_points_P/D.csv from
# prep_stats.py) averaged in 0.03-uS conductance bins (bins with >= 10 updates).
#   P: G = Gmin + dGw[1 - (1 - n/N)^aP]  ->  step(G) = G(n+1) - G(n) at n(G)
#   D: G = Gmin + dGw(1 - n/N)^aD        ->  step(G) = G(n+1) - G(n) (negative)
# Output: <WORK>/prep/csv/LUT_check.csv and LUT_check.json (bin statistics and agreement with the model)
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.normpath(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..")))
import config

import json
import numpy as np, pandas as pd

C = config.WORK + "/prep/csv/"
p = json.load(open(config.PKG + "/crosssim/device_params.json"))
Gmin, Gmax = p["G_min"] * 1e6, p["G_max"] * 1e6          # uS
dGw = Gmax - Gmin
N = p["N_pulses"] - 1                                     # 49 steps per branch
aP, aD = p["alpha_P"], p["alpha_D"]
sP, sD = p["sigma_w_P"] * dGw * 1e3, p["sigma_w_D"] * dGw * 1e3   # nS

G = np.linspace(Gmin, Gmax, 200)
x = (G - Gmin) / dGw
nP = 1 - (1 - np.clip(x, 0, 1)) ** (1 / aP)
stepP = (Gmin + dGw * (1 - np.clip(1 - nP - 1 / N, 0, 1) ** aP) - G) * 1e3
nD = 1 - np.clip(x, 0, 1) ** (1 / aD)
stepD = (Gmin + dGw * np.clip(1 - nD - 1 / N, 0, 1) ** aD - G) * 1e3
stepP[G >= Gmax - 1e-9] = np.nan; stepD[G <= Gmin + 1e-9] = np.nan

out = {"G_model_uS": G, "P_mean_nS": stepP, "P_lo_nS": stepP - sP, "P_hi_nS": stepP + sP,
       "D_mean_nS": stepD, "D_lo_nS": stepD - sD, "D_hi_nS": stepD + sD}
info = dict(Gmin=Gmin, Gmax=Gmax, aP=aP, aD=aD, sigma_P_nS=sP, sigma_D_nS=sD, bins={})
edges = np.arange(0.16, 0.50, 0.03)
for t, step in (("P", stepP), ("D", stepD)):
    mean_fn = lambda g, step=step: np.interp(g, G, step)
    d = pd.read_csv(C + f"DGG_points_{t}.csv")
    rows = []
    for lo, hi in zip(edges[:-1], edges[1:]):
        m = (d.G_uS >= lo) & (d.G_uS < hi)
        if m.sum() >= 10:
            v = d.dG_nS[m]
            rows.append((d.G_uS[m].mean(), v.mean(), v.std(ddof=1), v.std(ddof=1) / np.sqrt(m.sum()), int(m.sum())))
    r = np.array(rows)
    out[f"{t}_bin_G_uS"] = r[:, 0]; out[f"{t}_bin_mean_nS"] = r[:, 1]; out[f"{t}_bin_sd_nS"] = r[:, 2]
    out[f"{t}_bin_sem_nS"] = r[:, 3]; out[f"{t}_bin_n"] = r[:, 4]
    inside = (r[:, 0] >= Gmin) & (r[:, 0] <= Gmax)
    resid = r[inside, 1] - mean_fn(r[inside, 0])
    info["bins"][t] = dict(G=r[:, 0].round(4).tolist(), mean=r[:, 1].round(2).tolist(), sd=r[:, 2].round(2).tolist(),
                           n=r[:, 4].astype(int).tolist(), model_at_bins=np.round(mean_fn(r[:, 0]), 2).tolist(),
                           rms_resid_in_window_nS=float(np.sqrt(np.mean(resid ** 2))),
                           within_sem=int(np.sum(np.abs(resid) <= r[inside, 3])),
                           within_2sem=int(np.sum(np.abs(resid) <= 2 * r[inside, 3])), n_bins_in_window=int(inside.sum()))
pd.DataFrame({k: pd.Series(v) for k, v in out.items()}).to_csv(C + "LUT_check.csv", index=False)
json.dump(info, open(C + "LUT_check.json", "w"), indent=1)
print({t: (b["rms_resid_in_window_nS"], b["within_sem"], b["within_2sem"], b["n_bins_in_window"]) for t, b in info["bins"].items()})
