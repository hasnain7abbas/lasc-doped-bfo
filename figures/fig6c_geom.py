# Crop and size for Fig. 6c (Origin accuracy-vs-epoch panel) at the print scale of the other figures:
# the 900-px Origin page prints 6.74 cm wide, so 28 pt prints at about 6.4 pt (Figs 2-5: 5.9-6.6 pt).
# Writes fig6c_geom.json next to this script for paste_fig6c.ps1.
# Panel (c) slot in build_figure6_network.py: left 5.85 cm, top 6.8 cm, 5.8 x 4.7 cm.
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.normpath(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..")))
import config

import json, os
from PIL import Image

PRE = config.WORK + "/previews_paper/Accuracy_vs_epoch.png"      # written by origin_plots/acc_epoch.py
PAGE_CM = 6.74
SLOT = dict(left=5.85, top=6.8, w=5.8, h=4.7)
im = Image.open(PRE).convert("L"); W, H = im.size
bb = im.point(lambda v: 255 if v < 245 else 0).getbbox(); m = 6
l, t, r, b = max(bb[0] - m, 0), max(bb[1] - m, 0), min(bb[2] + m, W), min(bb[3] + m, H)
k = PAGE_CM / W                                     # cm per preview pixel
w_cm, h_cm = (r - l) * k, (b - t) * k
g = dict(crop=[l / W, t / H, (W - r) / W, (H - b) / H], width=w_cm,
         left=SLOT["left"] + (SLOT["w"] - w_cm) / 2, top=SLOT["top"] + (SLOT["h"] - h_cm) / 2,
         path=config.PAPER_FIG + "/origin/Accuracy_vs_epoch.opju", graph="ACC1")
json.dump(g, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "fig6c_geom.json"), "w"), indent=1)
print(json.dumps(g), f"height {h_cm:.2f} cm, 28 pt -> {28 * PAGE_CM / 29.5:.1f} pt")
