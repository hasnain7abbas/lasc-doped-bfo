# Second-round data preparation (system Python). Reads only data from "strict final la sc"
# (and the P-E data already extracted from that folder's pptx / opju).
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.normpath(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..")))
import config

import sys, os, json, re
import numpy as np, pandas as pd
from scipy.signal import savgol_filter

S = config.WORK
ROOT = config.RAW
C = S + "/prep/csv/"
MAN = json.load(open(S + "/prep/manifest.json"))
OUT = {}
AREA = 3.14e-4                                   # cm2, electrode area from the PUND headers
D_UM = {"BFO": 0.5, "La7.5": 0.5, "Sc1": 0.5, "LaSc": 0.580}   # film thickness (um); La-Sc from the P2 cross-section SEM (top surface to film/ITO interface, 215 px x 2.695 nm/px)
NAME = {"BFO": "BiFeO\\-(3)", "La7.5": "La 7.5%", "Sc1": "Sc 1%", "LaSc": "La 7.5%-Sc 1%"}

def save(name, df, meta=None):
    df.to_csv(C + name + ".csv", index=False); OUT[name] = meta or {}

# ---------------------------------------------------------------- P-E (point 2; Sc uses P3 as instructed)
pe_src = {"BFO": "PE_BFO_P2", "La7.5": "PE_La7.5_P2", "Sc1": "PE_Sc1_P3", "LaSc": "PE_LaSc_P2b"}
pe_man = {m["csv"][:-4]: m for m in json.load(open(S + "/prep/pe_manifest.json"))}
for tag, src in pe_src.items():
    d = pd.read_csv(C + src + ".csv"); volts = pe_man[src]["volts"]
    cols = {}; fac = []
    for v in volts:
        e = d[f"E_{v}V"]; p = d[f"P_{v}V"]
        emax = np.nanmax(np.abs(e.values))
        d_rec_cm = v / (emax * 1e3)                       # thickness the tester used for this loop
        k = d_rec_cm / (D_UM[tag] * 1e-4)
        cols[f"Erec_{v}V"] = e; cols[f"E_{v}V"] = e * k; cols[f"P_{v}V"] = p; fac.append(round(d_rec_cm * 1e4, 3))
    save(f"v2_PE_{tag}", pd.DataFrame(cols), dict(volts=volts, d_rec_um=fac, d_um=D_UM[tag], src=src))
# comparison at 25 V
cmp = {}
for tag in ["BFO", "La7.5", "Sc1", "LaSc"]:
    d = pd.read_csv(C + f"v2_PE_{tag}.csv")
    cmp[f"E_{tag}"] = d["E_25V"]; cmp[f"P_{tag}"] = d["P_25V"]
save("v2_PE_compare25", pd.DataFrame(cmp))

# ---------------------------------------------------------------- PUND (point 2 only)
pund = [("La7.5", "La7.5_25V", "pund la point 2/25"), ("Sc1", "Sc1_25V", "pund sc point 2/1ms 25v"),
        ("LaSc", "LaSc_25V", "pund la sc point 2/1ms 25v"), ("LaSc", "LaSc_26V", "pund la sc point 2/1ms 26v"),
        ("LaSc", "LaSc_27V", "pund la sc point 2/1ms 27v")]
summ = []
for tag, key, rel in pund:
    L = open(f"{ROOT}/{rel}").read().splitlines()
    h = [l for l in L if "area (cm2)" in l][0]
    hv = {k.strip(): float(v) for k, v in re.findall(r"([a-z ]+\([a-z0-9]+\)):\s*([-0-9.eE]+)", h)}
    k0 = [i for i, l in enumerate(L) if l.startswith("time (s)")][0]
    a = np.array([[float(x) for x in l.split("\t")[:3]] for l in L[k0 + 1:] if l.strip()])
    t = a[:, 0]; Erec = a[:, 1] * 1e-5; P = a[:, 2] * 100.0
    E = Erec * hv["thickness (um)"] / D_UM[tag]
    on = np.abs(Erec) > 0.5 * np.abs(Erec).max()
    edges = np.flatnonzero(np.diff(on.astype(int))); segs = []; s0 = 0 if on[0] else None
    for e in edges:
        if on[e + 1]: s0 = e + 1
        else: segs.append((s0, e)); s0 = None
    if s0 is not None: segs.append((s0, len(t) - 1))
    nm = ["Pre", "P", "U", "N", "D"]; sg = dict(zip(nm, segs))
    pP_relax = P[sg["U"][0] - 1]                # P just before the U pulse (relaxed after P)
    pU_end = P[sg["U"][1]]                      # P at the end of the U pulse
    pU_relax = P[sg["N"][0] - 1]                # P just before the N pulse (relaxed after U)
    Pr = pP_relax - pU_relax
    PC = pU_end - pU_relax
    i0, i1 = sg["U"]; j0 = i0 + int(0.25 * (i1 - i0))
    sl, ic = np.polyfit(t[j0:i1 + 1] * 1e3, P[j0:i1 + 1], 1)      # uC cm-2 ms-1 = mA cm-2
    fit = np.full(len(t), np.nan); fit[j0:i1 + 1] = sl * t[j0:i1 + 1] * 1e3 + ic
    step = 6
    sub = np.zeros(len(t), bool); sub[::step] = True
    for (q0, q1) in segs:                       # keep pulse edges in the thinned columns
        sub[max(q0 - 2, 0):q0 + 3] = True; sub[max(q1 - 2, 0):min(q1 + 3, len(t))] = True
    df = pd.DataFrame({"t": t, "Erec": Erec, "E": E, "P": P, "Pfit": fit})
    df2 = pd.DataFrame({"ts": t[sub], "Es": E[sub], "Ps": P[sub]})
    df = pd.concat([df, df2], axis=1)
    meta = dict(tag=tag, sample=NAME[tag], file=rel, header=hv, d_um=D_UM[tag], Pr=float(Pr), PC=float(PC), LC=float(sl),
                tUend=float(t[i1]), tNstart=float(t[sg["N"][0]]), pU_end=float(pU_end), pU_relax=float(pU_relax),
                V=hv["voltage (v)"])
    save(f"v2_PUND_{key}", df, meta)
    summ.append(dict(key=key, sample=NAME[tag], V=hv["voltage (v)"], Pr=Pr, PC=PC, LC=sl))
save("v2_PUND_summary", pd.DataFrame(summ))

# ---------------------------------------------------------------- unidirectional: best cycle per sample
def uni(tag):
    d = pd.read_csv(C + f"UNI_{tag}.csv"); cyc = [int(c[1:]) for c in d.columns if c.startswith("V")]
    best = None
    for c in cyc:
        V = d[f"V{c}"].dropna().values; I = d[f"I{c}"].dropna().values[:len(V)]
        m = V < -0.2; v = np.abs(V[m]); i = np.abs(I[m]); o = np.argsort(v)
        li = np.log10(i[o]); rms = np.sqrt(np.mean((li - savgol_filter(li, 11, 2)) ** 2))
        if best is None or rms < best[0]: best = (rms, c)
    return best[1], d
UNI = {}
for tag in ["BFO", "La7.5", "Sc1", "LaSc"]:
    c, d = uni(tag)
    V = d[f"V{c}"].dropna().values; I = d[f"I{c}"].dropna().values[:len(V)]
    E = V / (D_UM[tag] * 1e-4) / 1e3; J = np.abs(I) / AREA
    UNI[tag] = c
    # full sweep (for the comparison plot), split into branches so smoothing does not cross V = 0
    neg = V < 0; pos = V > 0
    save(f"v2_UNI_{tag}", pd.DataFrame({"V": V, "I": I, "E": E, "J": J,
                                         "logJ": np.log10(np.where(J > 0, J, np.nan)),
                                         "branch": np.where(neg, -1, np.where(pos, 1, 0))}),
         dict(cycle=c, d_um=D_UM[tag]))
    # conduction: negative-bias branch, |E| increasing, |V| >= 0.3 V
    m = V <= -1.5; v = np.abs(V[m]); i = np.abs(I[m]); o = np.argsort(v)
    v, i = v[o], i[o]
    Ec = v / (D_UM[tag] * 1e-4) / 1e3; Jc = i / AREA
    save(f"v2_COND_{tag}", pd.DataFrame({"V": -v, "absV": v, "absI": i, "E": Ec, "J": Jc,
                                          "logE": np.log10(Ec), "logJ": np.log10(Jc)}),
         dict(cycle=c, d_um=D_UM[tag], branch="negative bias, |V| >= 1.5 V"))

# ---------------------------------------------------------------- SDDP decay: keep only the relaxation after the train
d = pd.read_csv(C + "SDDP_decay.csv"); out = {}
for pw in [0.1, 0.2, 0.3, 0.4, 0.5]:
    t = d[f"t_{pw}"].dropna().values; G = d[f"G_{pw}"].dropna().values[:len(t)]
    k = int(np.argmax(G)); out[f"t_{pw}"] = pd.Series(t[k:] - t[k]); out[f"G_{pw}"] = pd.Series(G[k:])
save("v2_SDDP_decay", pd.DataFrame(out))

# ---------------------------------------------------------------- SNDP normalised weight (Luo Fig. 2I / Yang Fig. 4j style)
d = pd.read_csv(C + "SNDP_traces.csv"); Ns = MAN["SNDP_traces"]["N"]; out = {}
for N in Ns:
    t = d[f"t_{N}"].dropna().values; G = d[f"G_{N}"].dropna().values[:len(t)]
    m = t <= 100.5; t, G = t[m], G[m]
    W = G / G[0] * 100
    out[f"t_{N}"] = pd.Series(t); out[f"W_{N}"] = pd.Series(W)
    keep = (t <= 3.0) | (np.arange(len(t)) % 8 == 0)          # dense at the start, every 8th point later
    ts = t[keep]; Ws = W[keep]
    out[f"ts_{N}"] = pd.Series(ts); out[f"Ws_{N}"] = pd.Series(Ws)
save("v2_SNDP_norm", pd.DataFrame(out), dict(N=Ns))

# ---------------------------------------------------------------- EPSC at V_R = 1 V (current in uA) and PPF trace (current in uA)
d = pd.read_csv(C + "READV.csv")
t = d["t_1.0"].dropna().values; I = d["I_1.0"].dropna().values[:len(t)] / 1e3
k = int(np.argmax(I)); base = I[:k - 1]; post = I[k + 1:]
save("v2_EPSC", pd.DataFrame({"t": t, "I": I}), dict(t_pulse=float(t[k]), I_base=float(np.mean(base[-15:])),
                                                     I_after=float(np.mean(I[k + 5:k + 15])), I_end=float(np.mean(I[-15:]))))

json.dump(OUT, open(S + "/prep/manifest_v2.json", "w"), indent=1, default=float)
print(pd.DataFrame(summ).round(2).to_string()); print("UNI best cycles", UNI)
print({k: v for k, v in OUT["v2_EPSC"].items()})
for tag in D_UM: print(tag, OUT[f"v2_PE_{tag}"]["d_rec_um"][:4])
