# Layout for the paper figures (Fig. 2-7 main, S1-S4 supplementary), 17.5 cm double-column width, 3 panels per row.
# Every Origin panel uses the same scale (same printed font size everywhere); white page margins are cropped.
# Output: spec.json for build_figures.ps1
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.normpath(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..")))
import config

import json, os, glob
from PIL import Image

ROOT = config.PAPER_FIG
T = config.WORK
PRE = os.path.join(T, "previews_paper")
FIG_W, NCOL, MX, GX = 17.5, 3, 0.1, 0.15          # cm: width, columns, side margin, column gap
COL_W = (FIG_W - 2 * MX - (NCOL - 1) * GX) / NCOL
BAND, GY = 0.30, 0.15                              # letter band above each row, gap between rows

S = lambda name: ("scheme", name)
FIGS = {
    # main text
    # restructure of 10 Nov: film selection in one figure, mechanism/PUND detail in the SI, tau(N) and G+/G- panels dropped,
    # SNDP and retention (same five runs) shown once
    "Figure 2": [["XRD_comparison", "XRD_104_110_zoom"],
                 ["PE_compare_25V", "UNI_compare_J_E"]],
    "Figure 3": [["EPSC", "EPSC_read_voltage", "PPF_trace"],
                 ["PPF_index", "SRDP_index", "SDDP_pulse_number"],
                 ["SDDP_dW_vs_width", "SDDP_decay"]],
    "Figure 4": [["Retention", "SNDP_weight_change", "SNDP_dW_vs_pulse_number"]],
    "Figure 5": [[S("Scheme_LTP_LTD"), "LTP_LTD_5cycles", "LTP_LTD_powerlaw_fit"],
                 ["DGG_potentiation", "DGG_depression", "Multilevel_states"],
                 ["Endurance"]],
    # supplementary
    "Figure S1": [["XRD_decon_BFO", "XRD_decon_La", "XRD_decon_Sc"], ["XRD_decon_LaSc", "XRD_Sc_Pt_removal"]],
    "Figure S2": [["PE_BFO", "PE_La7.5", "PE_Sc1"], ["PE_LaSc"]],
    "Figure S3": [["PUND_compare_25V", "PUND_compare_LC_25V"],
                  ["PUND_La7.5_25V", "PUND_Sc1_25V", "PUND_LaSc_25V"], ["PUND_LaSc_26V", "PUND_LaSc_27V"]],
    "Figure S4": [["COND_LaSc_pos", "COND_LaSc_neg"], ["COND_BFO_pos", "COND_BFO_neg"],
                  ["COND_La7.5_pos", "COND_La7.5_neg"], ["COND_Sc1_pos", "COND_Sc1_neg"]],
}

REG = {}
for f in glob.glob(os.path.join(T, "tools", "*_registry.json")):
    for r in json.load(open(f)):
        REG[os.path.splitext(os.path.basename(r["path"]))[0]] = r["graph"]

def bbox(name):
    im = Image.open(os.path.join(PRE, name + ".png")).convert("L")
    bb = im.point(lambda v: 255 if v < 245 else 0).getbbox()
    W, H = im.size
    m = 6                                            # px margin kept around the content
    l, t, r, b = max(bb[0] - m, 0), max(bb[1] - m, 0), min(bb[2] + m, W), min(bb[3] + m, H)
    return dict(W=W, H=H, l=l / W, t=t / H, r=(W - r) / W, b=(H - b) / H, cw=r - l, ch=b - t)

names = [n for f in FIGS.values() for row in f for n in row if isinstance(n, str)]
BB = {n: bbox(n) for n in names}

spec = []
AVAIL = FIG_W - 2 * MX
for fig, rows in FIGS.items():
    fn = [n for row in rows for n in row if isinstance(n, str)]
    med = sorted(BB[n]["cw"] for n in fn)[len(fn) // 2]          # width given to a scheme, in preview px
    cw = lambda n: BB[n]["cw"] if isinstance(n, str) else med
    # one scale per figure: the largest that lets every row (3 slots, min gap GX) fit the width
    K = min((AVAIL - (NCOL - 1) * GX) / (sum(cw(n) for n in row) + (NCOL - len(row)) * med) for row in rows)
    pt = 28 * 900 * K / 29.5
    print(f"{fig}: Origin page printed {900 * K:.2f} cm -> 28 pt prints at {pt:.1f} pt")
    items, y, k = [], 0.1, 0
    for row in rows:
        h_row = max((BB[n]["ch"] * K for n in row if isinstance(n, str)), default=4.0)
        ws = [cw(n) * K for n in row]
        gap = (AVAIL - sum(ws) - (NCOL - len(row)) * med * K) / (NCOL - 1)
        x = MX + (AVAIL - sum(ws) - gap * (len(row) - 1)) / 2      # short rows are centred
        for c, n in enumerate(row):
            w = ws[c]
            letter = "(" + "abcdefghijklmnop"[k] + ")"; k += 1
            top = y + BAND
            if isinstance(n, str):
                b = BB[n]
                ptop = top + (h_row - b["ch"] * K) / 2
                items.append(dict(kind="origin", name=n, graph=REG[n],
                                  path=os.path.join(ROOT, "origin", n + ".opju").replace("\\", "/"),
                                  crop=[b["l"], b["t"], b["r"], b["b"]], width=w, left=x, top=ptop))
            else:
                ptop = top
                items.append(dict(kind="scheme", name=n[1], left=x - 0.05, top=top + 0.1,
                                  width=w * 0.82, height=h_row - 0.2, font=pt / 14.0))   # room for text that sticks out right
            items.append(dict(kind="letter", text=letter, left=x - 0.1, top=y + 0.02))       # same height across the row
            x += w + gap
        y += BAND + h_row + GY
    spec.append(dict(name=fig, width=FIG_W, height=round(y + 0.05, 2), items=items, font_pt=round(pt, 1),
                     pptx=os.path.join(ROOT, fig + ".pptx"), png=os.path.join(ROOT, "previews", fig + ".png")))
os.makedirs(os.path.join(ROOT, "previews"), exist_ok=True)
json.dump(spec, open(os.path.join(ROOT, "scripts", "spec.json"), "w"), indent=1)
for f in spec:
    print(f["name"], f["height"], "cm tall,", sum(i["kind"] != "letter" for i in f["items"]), "panels")
