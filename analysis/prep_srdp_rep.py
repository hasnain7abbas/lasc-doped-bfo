# SRDP, second (repeated) run: "srdp repeated" sheet of la sc synaptic.xlsx -> SRDP_rep_all.csv (all rows) and
# SRDP_rep.csv (1-8 Hz). The 0.5 Hz row is left out of the paper figure because its pre-stimulus conductance
# (0.0117 uS) is ten times lower than in every other run, which inflates its SRDP index to ~1048 %.
# SRDP index = (Gpost - Gpre) / Gpre x 100 %.
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.normpath(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..")))
import config
import os
import openpyxl, pandas as pd

wb = openpyxl.load_workbook(os.path.join(config.RAW, "la sc synaptic.xlsx"), read_only=True, data_only=True)
rows = [r[:7] for r in wb["srdp repeated"].iter_rows(values_only=True)
        if isinstance(r[0], (int, float)) and all(isinstance(v, (int, float)) for v in r[:7])]
d = pd.DataFrame(rows, columns=["f", "N", "on", "trainT", "gap", "Gpre", "Gpost"])
d["SRDP"] = (d.Gpost - d.Gpre) / d.Gpre * 100
out = os.path.join(config.WORK, "prep", "csv")
d.to_csv(os.path.join(out, "SRDP_rep_all.csv"), index=False)
d[d.f >= 1].to_csv(os.path.join(out, "SRDP_rep.csv"), index=False)
print(d.to_string(index=False))
