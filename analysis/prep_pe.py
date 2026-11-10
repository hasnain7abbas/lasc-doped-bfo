import os as _os, sys as _sys
_sys.path.insert(0, _os.path.normpath(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..")))
import config

import pandas as pd, numpy as np, json, sys, os
S = config.WORK; out = S + "/prep/csv"; os.makedirs(out, exist_ok=True)
# (source csv, sample, point label, voltages)
odd = lambda a, b: list(range(a, b + 1, 2))
specs = [
 ("slide2_oleObject1",  "Sc 1%",            "P1", odd(9, 41)),
 ("slide3_oleObject2",  "Sc 1%",            "P3", odd(9, 31) + [32] + odd(33, 41)),
 ("slide5_oleObject3",  "La 7.5%-Sc 1%",    "P1", [5] + odd(9, 29)),
 ("slide6_oleObject4",  "La 7.5%-Sc 1%",    "P2a", odd(9, 29)),
 ("slide7_oleObject5",  "La 7.5%-Sc 1%",    "P2b", odd(9, 31) + [32]),
 ("slide8_oleObject6",  "La 7.5%-Sc 1%",    "P2c", odd(9, 31) + [33]),
 ("slide9_oleObject7",  "La 7.5%-Sc 1%",    "P3a", odd(9, 27)),
 ("slide10_oleObject8", "La 7.5%-Sc 1%",    "P3b", odd(9, 31)),
 ("slide11_oleObject9", "La 7.5%-Sc 1%",    "P4a", odd(9, 27) + [28] + odd(31, 35)),
 ("slide12_oleObject10","La 7.5%-Sc 1%",    "P4b", odd(9, 27) + odd(31, 37)),
 ("slide13_oleObject11","La 7.5%-Sc 1%",    "P4c", odd(9, 37)),
 ("slide14_oleObject12","La 7.5%-Sc 1%",    "P5", odd(9, 23) + [27, 29]),
 ("slide16_oleObject13","La 7.5%",          "P1", odd(9, 49)),
 ("slide17_oleObject14","La 7.5%",          "P2", odd(9, 33)),
 ("slide18_oleObject15","La 7.5%",          "P3", odd(9, 29)),
 ("slide19_oleObject16","La 7.5%",          "P4", odd(9, 29)),
 ("slide20_oleObject17","La 7.5%",          "P5", odd(9, 37)),
]
man = []
for src, samp, pt, volts in specs:
    d = pd.read_csv(f"{S}/pe_csv/{src}.csv")
    n = len(volts)
    cols = {}
    for i, v in enumerate(volts):
        x = d.iloc[1:, 2*i].reset_index(drop=True); y = d.iloc[1:, 2*i+1].reset_index(drop=True)
        bad = (x.abs() < 1e-3) & (y.isin([100.0, 200.0]))   # Radiant export header marker (E = 0, P = 100/200)
        x, y = x[~bad].reset_index(drop=True), y[~bad].reset_index(drop=True)
        assert x.notna().sum() > 100, (src, i)
        cols[f"E_{v}V"] = x; cols[f"P_{v}V"] = y
    # sanity: any extra non-empty plots beyond n?
    extra = [k for k in range(n, d.shape[1]//2) if d.iloc[1:, 2*k+1].notna().sum() > 0]
    tag = {"Sc 1%": "Sc1", "La 7.5%-Sc 1%": "LaSc", "La 7.5%": "La7.5"}[samp]
    fn = f"PE_{tag}_{pt}.csv"; pd.DataFrame(cols).to_csv(f"{out}/{fn}", index=False)
    man.append(dict(csv=fn, sample=samp, point=pt, volts=volts, extra_nonempty=extra,
                    emax=float(np.nanmax(np.abs(d.iloc[1:, 0::2].values)))))
d = pd.read_csv(f"{S}/pe_csv/BFO_P2.csv"); volts = odd(5, 25); cols = {}
for i, v in enumerate(volts):
    cols[f"E_{v}V"] = d.iloc[:, 2*i]; cols[f"P_{v}V"] = d.iloc[:, 2*i+1]
pd.DataFrame(cols).to_csv(f"{out}/PE_BFO_P2.csv", index=False)
man.insert(0, dict(csv="PE_BFO_P2.csv", sample="BiFeO3", point="P2", volts=volts, extra_nonempty=[], emax=float(d.iloc[:,0::2].abs().max().max())))
json.dump(man, open(f"{S}/prep/pe_manifest.json", "w"), indent=1)
for m in man: print(m["csv"], len(m["volts"]), "extra", m["extra_nonempty"], "Emax %.0f" % m["emax"])
