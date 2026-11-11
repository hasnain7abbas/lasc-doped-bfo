# Crop and size for the Origin panels of Fig. 6 (c: update model vs measured, d: accuracy vs epoch) at the print scale
# of the other figures: the 900-px Origin page prints 6.74 cm wide, so 28 pt prints at about 6.4 pt (Figs 2-5: 5.9-6.6 pt).
# Writes fig6_geom.json next to this script for paste_fig6.ps1. Slots match build_figure6_network.py (P1, P2, PTOP).
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.normpath(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..")))
import config

import json, os
from PIL import Image

PRE = config.WORK + "/previews_paper"              # written by origin_plots/lut_check.py and acc_epoch.py
ORG = config.PAPER_FIG + "/origin/"
PAGE_CM = 6.74
TOP = 6.35 + 0.42                                   # letter row + gap
PANELS = [("LUT_check", "LUTchk1", 2.6), ("Accuracy_vs_epoch", "ACC1", 9.36)]
out = []
for name, graph, left in PANELS:
    im = Image.open(os.path.join(PRE, name + ".png")).convert("L"); W, H = im.size
    bb = im.point(lambda v: 255 if v < 245 else 0).getbbox(); m = 6
    l, t, r, b = max(bb[0] - m, 0), max(bb[1] - m, 0), min(bb[2] + m, W), min(bb[3] + m, H)
    k = PAGE_CM / W
    out.append(dict(name=name, graph=graph, path=ORG + name + ".opju", crop=[l / W, t / H, (W - r) / W, (H - b) / H],
                    width=(r - l) * k, height=(b - t) * k, left=left, top=TOP))
json.dump(out, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "fig6_geom.json"), "w"), indent=1)
for o in out:
    print(f'{o["name"]:20s} {o["width"]:.2f} x {o["height"]:.2f} cm at ({o["left"]:.2f}, {o["top"]:.2f})')
print(f"28 pt -> {28 * PAGE_CM / 29.5:.1f} pt")
