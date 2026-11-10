import os as _os, sys as _sys
_sys.path.insert(0, _os.path.normpath(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..")))
import config

"""
Device parameter extraction for the La-Sc BFO synapse (sheet '15 -12', 5 cycles x 50 P + 50 D).
Method follows Parameter_Extraction_v3_Fixed.ipynb (power-law, curve_fit with free endpoints),
with one addition: write noise is also computed from the cycle-to-cycle residual of each step
(step minus the mean step at the same pulse index), which removes the deterministic nonlinearity
that the v3 formula std(all steps)/dG counts as noise. Both values are reported; the residual
value is what CrossSim receives because the LUT already carries the mean nonlinear step.
Writes device_params.json and extraction_report.txt + figures next to this script.
"""
import json, os
import numpy as np
import openpyxl
from scipy.optimize import curve_fit
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
XLSX = os.path.join(config.RAW, "la sc synaptic.xlsx")
SHEET = "15 -12"
N_CYCLES, PPP = 5, 50

wb = openpyxl.load_workbook(XLSX, read_only=True, data_only=True)
rows = [r for r in wb[SHEET].iter_rows(values_only=True) if isinstance(r[0], (int, float)) and r[2] is not None]
data = np.array([float(r[2]) for r in rows])          # conductance column, uS
assert len(data) == N_CYCLES * 2 * PPP, len(data)

stride = 2 * PPP
pot = np.array([data[c*stride: c*stride+PPP] for c in range(N_CYCLES)])
dep = np.array([data[c*stride+PPP: c*stride+2*PPP] for c in range(N_CYCLES)])
pot_avg, dep_avg = pot.mean(0), dep.mean(0)

out = []
def say(s=""):
    print(s); out.append(s)

say(f"source  {os.path.normpath(XLSX)}  sheet '{SHEET}'")
say(f"points  {len(data)}  ({N_CYCLES} cycles x {PPP} P + {PPP} D), G range {data.min():.4f}-{data.max():.4f} uS")

# Step 3: Gmin / Gmax from end-of-phase values
pot_ends, dep_ends = pot[:, -1], dep[:, -1]
G_max, G_min = pot_ends.mean(), dep_ends.mean()
dr = G_max - G_min
say(f"\nG_min = {G_min:.4f} +/- {dep_ends.std(ddof=1):.4f} uS   G_max = {G_max:.4f} +/- {pot_ends.std(ddof=1):.4f} uS")
say(f"dG = {dr:.4f} uS, on/off = {G_max/G_min:.3f}")

# Step 4: power-law alpha
N = PPP - 1
n_arr = np.arange(PPP, dtype=float)
def pot_model(n, Gmin, Gmax, a):
    t = np.clip(1 - n/N, 1e-12, 1); return Gmin + (Gmax-Gmin)*(1 - t**a)
def dep_model(n, Gmax, Gmin, a):
    t = np.clip(1 - n/N, 1e-12, 1); return Gmin + (Gmax-Gmin)*t**a
def fit(y, dep_phase):
    f = dep_model if dep_phase else pot_model
    p, _ = curve_fit(f, n_arr, y, p0=[y[0], y[-1], 2.0], bounds=([0, 0, 0.01], [np.inf, np.inf, 200]), maxfev=50000)
    yf = f(n_arr, *p); r2 = 1 - np.sum((y-yf)**2)/np.sum((y-y.mean())**2)
    return p, r2, yf
pP, r2P, fitP = fit(pot_avg, False)
pD, r2D, fitD = fit(dep_avg, True)
aP_c = np.array([fit(pot[c], False)[0][2] for c in range(N_CYCLES)])
aD_c = np.array([fit(dep[c], True)[0][2] for c in range(N_CYCLES)])
say(f"\nalpha_P (avg curve) = {pP[2]:.4f}  R2 = {r2P:.4f}   endpoints {pP[0]:.4f} -> {pP[1]:.4f}")
say(f"alpha_D (avg curve) = {pD[2]:.4f}  R2 = {r2D:.4f}   endpoints {pD[0]:.4f} -> {pD[1]:.4f}")
say(f"alpha_P per cycle   = {aP_c.round(3).tolist()}  mean {aP_c.mean():.4f} +/- {aP_c.std(ddof=1):.4f}")
say(f"alpha_D per cycle   = {aD_c.round(3).tolist()}  mean {aD_c.mean():.4f} +/- {aD_c.std(ddof=1):.4f}")

# Step 5: CCV and write noise
sP, sD = np.diff(pot, axis=1), np.diff(dep, axis=1)          # (cycles, 49)
ccv_p = np.std(np.abs(sP), ddof=1)/np.mean(np.abs(sP))*100
ccv_d = np.std(np.abs(sD), ddof=1)/np.mean(np.abs(sD))*100
sw_P_v3 = np.std(sP.ravel(), ddof=1)/dr
sw_D_v3 = np.std(sD.ravel(), ddof=1)/dr
# residual noise: deviation of each cycle's step from the mean step at that pulse index
resP = (sP - sP.mean(0)).ravel(); resD = (sD - sD.mean(0)).ravel()
corr = np.sqrt(N_CYCLES/(N_CYCLES-1))                        # unbiased for the 5-sample mean removal
sw_P = np.sqrt(np.mean(resP**2))*corr/dr
sw_D = np.sqrt(np.mean(resD**2))*corr/dr
say(f"\nCCV_P = {ccv_p:.1f} %   CCV_D = {ccv_d:.1f} %")
say(f"sigma_w (v3 formula, std of all steps / dG):   P {sw_P_v3:.4f}   D {sw_D_v3:.4f}")
say(f"sigma_w (cycle-to-cycle residual / dG, used):  P {sw_P:.4f}   D {sw_D:.4f}")

# Step 6: levels / bits
def levels(c):
    s = np.abs(np.diff(c)); eff = s.mean() + 2*s.std(ddof=1)
    return int(max(2, min(256, round((c.max()-c.min())/eff))))
nlP, nlD = levels(pot_avg), levels(dep_avg)
wbits = int(np.floor(np.log2(min(nlP, nlD))))
say(f"\nN_levels P {nlP}, D {nlD}, weight bits {wbits}")

# Step 7/8
asym = abs(aP_c.mean()-aD_c.mean())/max(aP_c.mean(), aD_c.mean())
def sui(c):
    G, d = c[:-1], np.diff(c); cv = np.cov(G, d, ddof=0); s = cv[0, 1]/cv[0, 0]
    return max(0, min(1, 1-abs(s)))
say(f"asymmetry {asym:.4f}, SUI P {sui(pot_avg):.4f}, D {sui(dep_avg):.4f}")

params = dict(
    device_id="La7.5-Sc1 BFO, sheet '15 -12'",
    G_min=float(G_min*1e-6), G_max=float(G_max*1e-6), N_pulses=PPP,
    alpha_P=float(pP[2]), alpha_D=float(pD[2]),
    alpha_P_per_cycle=float(aP_c.mean()), alpha_D_per_cycle=float(aD_c.mean()),
    r2_P=float(r2P), r2_D=float(r2D),
    sigma_w_P=float(sw_P), sigma_w_D=float(sw_D),
    sigma_w_P_v3=float(sw_P_v3), sigma_w_D_v3=float(sw_D_v3),
    ccv_P=float(ccv_p), ccv_D=float(ccv_d),
    read_noise_sigma=0.03, n_levels=[nlP, nlD], weight_bits=wbits, asymmetry=float(asym),
    pot_avg_uS=pot_avg.tolist(), dep_avg_uS=dep_avg.tolist(),
)
json.dump(params, open(os.path.join(HERE, "device_params.json"), "w"), indent=1)
open(os.path.join(HERE, "extraction_report.txt"), "w", encoding="utf-8").write("\n".join(out) + "\n")

fig, ax = plt.subplots(1, 3, figsize=(15, 4))
for c in range(N_CYCLES):
    ax[0].plot(np.arange(c*stride, c*stride+PPP), pot[c], "r.", ms=3)
    ax[0].plot(np.arange(c*stride+PPP, (c+1)*stride), dep[c], "b.", ms=3)
ax[0].set_title("raw P/D, 5 cycles"); ax[0].set_xlabel("pulse"); ax[0].set_ylabel("G (uS)")
ax[1].plot(n_arr, pot_avg, "ro", ms=3, label="P avg"); ax[1].plot(n_arr, fitP, "k-", label=f"a_P={pP[2]:.3f}, R2={r2P:.3f}")
ax[1].plot(n_arr, dep_avg, "bs", ms=3, label="D avg"); ax[1].plot(n_arr, fitD, "k--", label=f"a_D={pD[2]:.3f}, R2={r2D:.3f}")
ax[1].legend(fontsize=8); ax[1].set_xlabel("pulse in phase"); ax[1].set_title("power-law fits")
ax[2].scatter(pot_avg[:-1], np.diff(pot_avg), c="r", s=10, label="P"); ax[2].scatter(dep_avg[:-1], np.diff(dep_avg), c="b", s=10, label="D")
ax[2].axhline(0, c="gray", ls="--"); ax[2].set_xlabel("G (uS)"); ax[2].set_ylabel("dG per pulse (uS)"); ax[2].legend()
plt.tight_layout(); plt.savefig(os.path.join(HERE, "extraction_fits.png"), dpi=150)
print("\nwrote device_params.json, extraction_report.txt, extraction_fits.png")
