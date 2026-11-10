# Prepares clean, column-labelled tables for every graph (system Python).
# Only reads files inside "strict final la sc" (plus P-E data already extracted from that folder's pptx/opju).
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.normpath(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..")))
import config

import sys, os, json, re
import numpy as np, pandas as pd, openpyxl

S = config.WORK
ROOT = config.RAW
OUT = S + "/prep/csv"; os.makedirs(OUT, exist_ok=True)
MAN = {}
AREA_CM2 = 3.14e-4          # electrode area from PUND file headers (200 um dot)
D_CM = 0.5e-4               # film thickness used for E = V/d (0.5 um, as used for the La-Sc P-E loops)

def save(name, df, meta=None):
    df.to_csv(f"{OUT}/{name}.csv", index=False)
    MAN[name] = meta or {}

wb = openpyxl.load_workbook(f"{ROOT}/la sc synaptic.xlsx", read_only=True, data_only=True)
def rows(sheet): return list(wb[sheet].iter_rows(values_only=True))
def num_rows(rs, ncol):
    return [r[:ncol] for r in rs if all(isinstance(r[k], (int, float)) for k in range(ncol))]
def hdr_float(text, key):
    m = re.search(key + r"\s*=\s*([-+0-9.eE]+)", text); return float(m.group(1)) if m else None

# ---------------------------------------------------------------- PUND
pund_files = [("BFO", "BiFeO\\-(3)", "pund bfo point 2/1ms 25v"),
              ("La7.5", "La 7.5%", "pund la point 2/25"),
              ("Sc1_P1a", "Sc 1% (P1a)", "pund sc point 1a/1ms 25v"),
              ("Sc1_P2", "Sc 1% (P2)", "pund sc point 2/1ms 25v"),
              ("LaSc_25V", "La 7.5%-Sc 1%", "pund la sc point 2/1ms 25v"),
              ("LaSc_26V", "La 7.5%-Sc 1%", "pund la sc point 2/1ms 26v"),
              ("LaSc_27V", "La 7.5%-Sc 1%", "pund la sc point 2/1ms 27v")]
pund_summary = []
for tag, samp, rel in pund_files:
    L = open(f"{ROOT}/{rel}").read().splitlines()
    h = [l for l in L if "area (cm2)" in l][0]
    hv = dict(re.findall(r"([a-z ]+\([a-z0-9]+\)):\s*([-0-9.eE]+)", h))
    hv = {k.strip(): float(v) for k, v in hv.items()}
    k0 = [i for i, l in enumerate(L) if l.startswith("time (s)")][0]
    ki = [i for i, l in enumerate(L) if l.startswith("P*")][0]
    hnames = L[ki].split("\t"); hvals = [float(x) for x in L[ki + 1].split("\t") if x.strip()]
    kd = [i for i, l in enumerate(L) if l.startswith("Delta P")][0]
    dvals = [float(x) for x in L[kd + 1].split("\t") if x.strip()]
    a = np.array([[float(x) for x in l.split("\t")[:3]] for l in L[k0 + 1:] if l.strip()])
    t = a[:, 0] * 1e3; E = a[:, 1] * 1e-5; P = a[:, 2] * 100.0     # ms, kV/cm, uC/cm2
    on = np.abs(E) > 0.5 * np.abs(E).max()
    edges = np.flatnonzero(np.diff(on.astype(int)))
    segs = []; s = 0 if on[0] else None
    for e in edges:
        if on[e + 1]: s = e + 1
        else: segs.append((s, e)); s = None
    if s is not None: segs.append((s, len(t) - 1))
    assert len(segs) == 5, (tag, len(segs))
    names = ["Pre-set", "P", "U", "N", "D"]
    res = {}
    for nm, (i0, i1) in zip(names, segs):
        base = P[i0 - 1] if i0 > 0 else P[0]
        res[nm] = dict(i0=int(i0), i1=int(i1), t0=float(t[i0]), t1=float(t[i1]), dP=float(P[i1] - base), Pend=float(P[i1]),
                       Eamp=float(np.median(E[i0:i1 + 1])))
    # remanent part: value after field removed (just before next pulse) minus value before pulse
    for j, nm in enumerate(names[:-1]):
        nxt = segs[j + 1][0]; res[nm]["Prem_after"] = float(P[nxt - 1])
    Psw_pos = res["P"]["dP"] - res["U"]["dP"]
    Psw_neg = abs(res["N"]["dP"]) - abs(res["D"]["dP"])
    # leakage: linear slope of P(t) over the last 60 % of the U pulse (non-switching) -> uC cm^-2 ms^-1 = mA cm^-2
    i0, i1 = res["U"]["i0"], res["U"]["i1"]; j0 = i0 + int(0.4 * (i1 - i0))
    sl, ic = np.polyfit(t[j0:i1 + 1], P[j0:i1 + 1], 1)
    df = pd.DataFrame({"t": t, "E": E, "P": P})
    fit = np.full(len(t), np.nan); fit[j0:i1 + 1] = sl * t[j0:i1 + 1] + ic
    df["Pfit"] = fit
    meta = dict(sample=samp, file=rel, header=hv, header_P=dict(zip(hnames, hvals)),
                header_dP=dict(zip(["Delta P", "Delta Pr", "-Delta P", "-Delta Pr"], dvals)),
                segs=res, Psw_pos=Psw_pos, Psw_neg=Psw_neg, J_leak=float(sl), leak_window=[float(t[j0]), float(t[i1])],
                Vamp=hv.get("voltage (v)"))
    save(f"PUND_{tag}", df, meta)
    pund_summary.append(dict(tag=tag, sample=samp, V=hv.get("voltage (v)"), Psw_pos=Psw_pos, Psw_neg=Psw_neg, J_leak=sl,
                             dP_P=res["P"]["dP"], dP_U=res["U"]["dP"], dP_N=res["N"]["dP"], dP_D=res["D"]["dP"],
                             d_um=hv.get("thickness (um)"), delay_ms=hv.get("pulse delay (ms)")))
save("PUND_summary", pd.DataFrame(pund_summary))

# ---------------------------------------------------------------- Bipolar I-V (Sheet5, 5 cycles)
r = [x for x in rows("Sheet5") if isinstance(x[0], (int, float)) and isinstance(x[1], (int, float))]
cyc = {}
for c, v, i in r: cyc.setdefault(int(c), []).append((v, i))
m = max(len(v) for v in cyc.values()); d = {}
for c in sorted(cyc):
    v = [p[0] for p in cyc[c]]; i = [p[1] for p in cyc[c]]
    d[f"V{c}"] = pd.Series(v); d[f"I{c}"] = pd.Series(i); d[f"absI{c}"] = pd.Series(np.abs(i) * 1e6)
save("IV_bipolar_Sheet5", pd.DataFrame(d), dict(cycles=sorted(cyc), source="la sc synaptic.xlsx / Sheet5"))
# SCLC branches of the last cycle: positive 0 -> +Vmax, negative 0 -> -Vmax
c = max(cyc); v = np.array([p[0] for p in cyc[c]]); i = np.array([p[1] for p in cyc[c]])
ipk = int(np.argmax(v)); ineg = int(np.argmin(v))
pos = (v[:ipk + 1], i[:ipk + 1])
k0 = int(np.flatnonzero((np.arange(len(v)) > ipk) & (np.abs(v) < 1e-6))[0]) if np.any((np.arange(len(v)) > ipk) & (np.abs(v) < 1e-6)) else ipk
neg = (v[k0:ineg + 1], i[k0:ineg + 1])
for nm, (vv, ii) in [("pos", pos), ("neg", neg)]:
    keep = np.abs(vv) > 1e-6
    vv, ii = vv[keep], ii[keep]
    df = pd.DataFrame({"V": vv, "I": ii, "absV": np.abs(vv), "absI": np.abs(ii),
                       "E": np.abs(vv) / D_CM / 1e3, "J": np.abs(ii) / AREA_CM2 * 1e3})
    save(f"SCLC_{nm}", df, dict(cycle=c, d_cm=D_CM, area_cm2=AREA_CM2,
                                 branch="0 to +Vmax (positive up-sweep)" if nm == "pos" else "0 to -Vmax (negative sweep)"))

# ---------------------------------------------------------------- Unidirectional I-V comparison
def uni_xlsx(path):
    ws = openpyxl.load_workbook(path, read_only=True, data_only=True).worksheets[0]
    rr = [x for x in ws.iter_rows(values_only=True) if isinstance(x[0], (int, float)) and isinstance(x[1], (int, float))]
    cc = {}
    for c, v, i in rr: cc.setdefault(int(c), []).append((v, i))
    return {c: (np.array([p[0] for p in q]), np.array([p[1] for p in q])) for c, q in cc.items()}
uni = {"BFO": uni_xlsx(f"{ROOT}/unidirectional IV/BFO unidirectional.xlsx"),
       "La7.5": uni_xlsx(f"{ROOT}/unidirectional IV/La 7.5 all.xlsx"),
       "Sc1": uni_xlsx(f"{ROOT}/unidirectional IV/Sc 1 uni.xlsx")}
L = open(f"{ROOT}/unidirectional IV/La-Sc p2 -10.txt").read().splitlines()
a = np.array([[float(x) for x in l.split("\t")] for l in L[3:] if l.strip()])
uni["LaSc"] = {k + 1: (a[:, 2 * k], a[:, 2 * k + 1]) for k in range(a.shape[1] // 2)}
for tag, cc in uni.items():
    d = {}
    for c in sorted(cc):
        d[f"V{c}"] = pd.Series(cc[c][0]); d[f"I{c}"] = pd.Series(cc[c][1]); d[f"absI{c}"] = pd.Series(np.abs(cc[c][1]))
    save(f"UNI_{tag}", pd.DataFrame(d), dict(cycles=sorted(cc)))

# ---------------------------------------------------------------- Synaptic (La-Sc)
def block_table(sheet, ncol=3):
    rs = rows(sheet)
    hdr = " ".join(str(x[0]) for x in rs if isinstance(x[0], str))
    return hdr, np.array(num_rows(rs, ncol), dtype=float)

# EPSC / read-voltage dependence
rv = {}
for sh, vr in [("0.25v (2)", 0.25), ("0.5v (2)", 0.5), ("0.75v (2)", 0.75), ("1v (2)", 1.0)]:
    _, a = block_table(sh, 2); rv[vr] = a
d = {}
for vr, a in rv.items():
    d[f"t_{vr}"] = pd.Series(a[:, 0]); d[f"I_{vr}"] = pd.Series(a[:, 1] * 1e9)
save("READV", pd.DataFrame(d), dict(vr=list(rv)))

# PPF
ppf = []; tr = {}
for sh in ["0.05", "0.1", "0.2", "0.3", "0.5sss", "1ss", "2s", "5s", "10s", "20s"]:
    hdr, a = block_table(sh)
    dt = hdr_float(hdr, "deltaT"); A1 = hdr_float(hdr, "A1"); A2 = hdr_float(hdr, "A2"); idx = hdr_float(hdr, "PPF_index")
    ppf.append(dict(dt_s=dt, dt_ms=dt * 1e3, A1_uA=A1 * 1e6, A2_uA=A2 * 1e6, PPF=idx, PPF_check=(A2 - A1) / A1 * 100))
    tr[dt] = a
save("PPF_index", pd.DataFrame(ppf).sort_values("dt_s"))
d = {}
for dt in sorted(tr):
    d[f"t_{dt}"] = pd.Series(tr[dt][:, 0]); d[f"G_{dt}"] = pd.Series(tr[dt][:, 2])
save("PPF_traces", pd.DataFrame(d), dict(dts=sorted(tr)))

# SDDP (potentiation vs pulse number, pulse width 0.1-0.5 s) and SDDP decay
sddp_p = {0.1: "Sheet29", 0.2: "Sheet25", 0.3: "Sheet26", 0.4: "Sheet27", 0.5: "Sheet28"}
sddp_d = {0.1: "Sheet31", 0.2: "Sheet33", 0.3: "Sheet34", 0.4: "Sheet35", 0.5: "Sheet36"}
d = {}; sum_ = []
for pw, sh in sddp_p.items():
    hdr, a = block_table(sh)
    d[f"n_{pw}"] = pd.Series(a[:, 0]); d[f"G_{pw}"] = pd.Series(a[:, 2])
    G0 = hdr_float(hdr, "G")  # reset baseline G (uS)
    sum_.append(dict(pw_ms=pw * 1e3, G0=G0, G1=a[0, 2], G50=a[-1, 2], dW=(a[-1, 2] - a[0, 2]) / a[0, 2] * 100))
save("SDDP_pulses", pd.DataFrame(d)); save("SDDP_summary", pd.DataFrame(sum_))
d = {}
for pw, sh in sddp_d.items():
    _, a = block_table(sh)
    d[f"t_{pw}"] = pd.Series(a[:, 0]); d[f"G_{pw}"] = pd.Series(a[:, 2])
save("SDDP_decay", pd.DataFrame(d))

# SNDP
rs = rows("sndp final"); tests = []; cur = None
for x in rs:
    if isinstance(x[0], str) and x[0].startswith("# RESET done"):
        base = hdr_float(x[0], "G")
    if isinstance(x[0], str) and x[0].startswith("BEGIN_TEST"):
        cur = dict(N=int(x[1]), G0=base, data=[])
    elif isinstance(x[0], str) and x[0].startswith("END_TEST"):
        tests.append(cur); cur = None
    elif cur is not None and isinstance(x[0], (int, float)) and isinstance(x[2], (int, float)):
        cur["data"].append((x[0], x[1], x[2]))
tests.sort(key=lambda q: q["N"])
d = {}; sn = []
for q in tests:
    a = np.array(q["data"]); t = a[:, 0]
    if q["N"] == 100:   # this run logs time from the start of the train; shift so t = 0 at the peak like the others
        t = t - t[np.argmax(a[:, 2])]
    keep = t >= 0
    d[f"t_{q['N']}"] = pd.Series(t[keep]); d[f"G_{q['N']}"] = pd.Series(a[keep, 2]); d[f"I_{q['N']}"] = pd.Series(a[keep, 1] * 1e6)
    Gp = a[:, 2].max(); Gend = a[-1, 2]
    sn.append(dict(N=q["N"], G0=q["G0"], Gpeak=Gp, Gend=Gend, t_end=float(t[-1]), dW_peak=(Gp - q["G0"]) / q["G0"] * 100,
                   dW_end=(Gend - q["G0"]) / q["G0"] * 100))
save("SNDP_traces", pd.DataFrame(d), dict(N=[q["N"] for q in tests]))
save("SNDP_summary", pd.DataFrame(sn))
# EPSC from the single-pulse (N = 1) SNDP record
q = [q for q in tests if q["N"] == 1][0]; a = np.array(q["data"])
save("EPSC_single", pd.DataFrame({"t": a[:, 0], "I": a[:, 1] * 1e6, "G": a[:, 2]}), dict(G0=q["G0"]))

# SRDP
rs = rows("srdp"); a = np.array(num_rows(rs, 7), dtype=float)
save("SRDP", pd.DataFrame({"f": a[:, 0], "N": a[:, 1], "gap": a[:, 4], "Gpre": a[:, 5], "Gpost": a[:, 6],
                           "SRDP": (a[:, 6] - a[:, 5]) / a[:, 5] * 100}))

# Retention: logged points for N = 100, 80, 60, 40; N = 20 only exists as a continuous log, sampled at the same times
rs = rows("retention"); blocks = []; cur = None
for x in rs:
    if isinstance(x[0], str) and x[0].startswith("BEGIN_RETENTION"):
        cur = dict(N=int(x[0].split()[1]), data=[])
    elif isinstance(x[0], str) and x[0].startswith("END_RETENTION"):
        blocks.append(cur); cur = None
    elif cur is not None and isinstance(x[0], (int, float)) and isinstance(x[1], (int, float)):
        cur["data"].append((x[0], x[1]))
ret = {}
for b in blocks:
    a = np.array(b["data"])
    if b["N"] not in ret and len(a) < 40: ret[b["N"]] = ("logged", a)
times = ret[100][1][:, 0]
for b in blocks:
    a = np.array(b["data"])
    if b["N"] == 20 and len(a) > 40 and 20 not in ret:
        idx = [int(np.argmin(np.abs(a[:, 0] - tt))) for tt in times]
        ret[20] = ("sampled from continuous log", a[idx])
d = {}
for N in sorted(ret, reverse=True):
    d[f"t_{N}"] = pd.Series(ret[N][1][:, 0]); d[f"G_{N}"] = pd.Series(ret[N][1][:, 1])
save("RETENTION", pd.DataFrame(d), {str(N): ret[N][0] for N in ret})

# LTP / LTD, 5 cycles x (50 P + 50 D)
rs = rows("15 -12"); a = np.array(num_rows(rs, 3), dtype=float)
n = a[:, 0]; G = a[:, 2]
ph = np.where(((n - 1) % 100) < 50, "P", "D")
save("LTPLTD_raw", pd.DataFrame({"n": n, "G": G, "Gp": np.where(ph == "P", G, np.nan), "Gd": np.where(ph == "D", G, np.nan)}))
Gc = G.reshape(5, 100); mean = Gc.mean(0); std = Gc.std(0, ddof=1)
save("LTPLTD_avg", pd.DataFrame({"k": np.arange(1, 101), "Gmean": mean, "Gstd": std,
                                 "Gp": np.r_[mean[:50], [np.nan] * 50], "Gp_err": np.r_[std[:50], [np.nan] * 50],
                                 "Gd": np.r_[[np.nan] * 50, mean[50:]], "Gd_err": np.r_[[np.nan] * 50, std[50:]]}))

# Multilevel (15 levels x 5 pulses), read at 1 V -> G = I / 1 V
rs = rows("Sheet58"); a = np.array(num_rows(rs, 3), dtype=float)
save("MULTILEVEL", pd.DataFrame({"level": a[:, 0], "pulses": a[:, 1], "I": a[:, 2], "G": a[:, 2] / 1.0 * 1e6}))

# Endurance
rs = rows("endurance best"); a = np.array(num_rows(rs, 4), dtype=float)
save("ENDURANCE", pd.DataFrame({"cycle": a[:, 0], "Gp": a[:, 1], "Gm": a[:, 2], "ratio": a[:, 1] / a[:, 2], "window": a[:, 3]}))

json.dump(MAN, open(S + "/prep/manifest.json", "w"), indent=1, default=float)
for k, v in MAN.items():
    print(k, {kk: vv for kk, vv in v.items() if kk not in ("segs", "header", "header_P", "header_dP")} if v else "")
print(pd.DataFrame(pund_summary).round(2).to_string())
print(pd.DataFrame(ppf).round(2).to_string())
print(pd.DataFrame(sn).round(3).to_string())
print(pd.DataFrame(sum_).round(3).to_string())
