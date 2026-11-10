# SNDP from the N = 20, 40, 60, 80, 100 runs (stored in the "retention" sheet of la sc synaptic.xlsx).
# Logged points (t = 0, 1, 2, 5, ... 2000 s) exist for all five runs; continuous logs (0.12-1 s steps) for N = 20-80.
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.normpath(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..")))
import config

import sys, re, json
import numpy as np, pandas as pd, openpyxl

S = config.WORK; C = S + "/prep/csv/"
ROOT = config.RAW
wb = openpyxl.load_workbook(f"{ROOT}/la sc synaptic.xlsx", read_only=True, data_only=True)
rows = list(wb["retention"].iter_rows(values_only=True))
blocks = []; cur = None
for x in rows:
    s = x[0]
    if isinstance(s, str) and s.startswith("BEGIN_RETENTION"):
        if cur: blocks.append(cur)
        cur = dict(N=int(s.split()[1]), data=[], reset=None)
    elif isinstance(s, str) and s.startswith("Initial (post-reset)") and cur:
        cur["reset"] = float(re.search(r"=\s*([0-9.eE-]+)", s).group(1)); blocks.append(cur); cur = None
    elif cur is not None and isinstance(x[0], (int, float)) and isinstance(x[1], (int, float)):
        cur["data"].append((float(x[0]), float(x[1])))
if cur: blocks.append(cur)
logged = {b["N"]: np.array(b["data"]) for b in blocks if len(b["data"]) < 40}
cont = {b["N"]: np.array(b["data"]) for b in blocks if len(b["data"]) >= 40}
reset = {}
for b in blocks:
    if b["reset"] is not None: reset[b["N"]] = b["reset"]
Ns = [20, 40, 60, 80, 100]
OUT = {}
# N = 100: the continuous record at the start of the "sndp final" sheet (time from peak, 0.12 s steps)
sn = pd.read_csv(C + "SNDP_traces.csv")
t100 = sn["t_100"].dropna().values; g100 = sn["G_100"].dropna().values[:len(t100)]
cont[100] = np.column_stack([t100, g100])
reset[100] = float(pd.read_csv(C + "SNDP_summary.csv").set_index("N").loc[100, "G0"])     # 0.10138 uS

# traces: continuous t >= 0 for 20-80, logged points for 100
d = {}
for N in Ns:
    if N in cont:
        a = cont[N]; a = a[a[:, 0] >= 0]; src = "continuous log" if N != 100 else "continuous log (sndp final sheet)"
    else:
        a = logged[N]; src = "logged points (no continuous log recorded)"
    d[f"t_{N}"] = pd.Series(a[:, 0]); d[f"G_{N}"] = pd.Series(a[:, 1]); OUT[str(N)] = src
pd.DataFrame(d).to_csv(C + "v3_SNDP_traces.csv", index=False)

# normalised weight W = G/G(peak) x 100 over 0-100 s; thinned copy for symbols
d = {}
for N in Ns:
    a = cont[N] if N in cont else logged[N]
    a = a[(a[:, 0] >= 0) & (a[:, 0] <= 100.5)]
    t, G = a[:, 0], a[:, 1]; W = G / G[0] * 100
    d[f"t_{N}"] = pd.Series(t); d[f"W_{N}"] = pd.Series(W)
    keep = np.zeros(len(t), bool); last = -9.0          # same time spacing for every N: all points to 2 s, then >= 1 s apart
    for i, tt in enumerate(t):
        if tt <= 2.0 or tt - last >= 1.0:
            keep[i] = True; last = tt
    d[f"ts_{N}"] = pd.Series(t[keep]); d[f"Ws_{N}"] = pd.Series(W[keep])
pd.DataFrame(d).to_csv(C + "v3_SNDP_norm.csv", index=False)

# summary for dW vs N, from the continuous record of each run
summ = []
for N in Ns:
    a = cont[N]; a = a[a[:, 0] >= 0]
    g = lambda t: float(a[np.argmin(np.abs(a[:, 0] - t)), 1])
    G0 = reset[N]; Gp = float(a[:, 1].max())
    summ.append(dict(N=N, G0=G0, Gpeak=Gp, G100=g(100), dW_peak=(Gp - G0) / G0 * 100, dW_100=(g(100) - G0) / G0 * 100))
pd.DataFrame(summ).to_csv(C + "v3_SNDP_summary.csv", index=False)

# retention: logged points for all five runs (same measurement, consistent sampling)
d = {}
for N in Ns:
    a = logged[N]; d[f"t_{N}"] = pd.Series(a[:, 0]); d[f"G_{N}"] = pd.Series(a[:, 1])
pd.DataFrame(d).to_csv(C + "v3_RETENTION.csv", index=False)

m = json.load(open(S + "/prep/manifest_v2.json"))
m["v3_SNDP"] = dict(N=Ns, source=OUT, reset=reset)
json.dump(m, open(S + "/prep/manifest_v2.json", "w"), indent=1, default=float)
print(pd.DataFrame(summ).round(4).to_string()); print(OUT)
