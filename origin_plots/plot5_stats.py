# Switching statistics, La 7.5%-Sc 1% (data prepared by prep\prep_stats.py from la sc synaptic.xlsx, no new measurements):
#   DGG_potentiation / DGG_depression : conditional CDF of dG = G(n+1) - G(n) vs G, 5 LTP/LTD cycles (245 pulses each)
#   END_cumprob                       : cumulative probability of G+ and G- over 2500 endurance cycles (CV in the graph)
import os as _os, sys as _sys
try:
    _HERE = _os.path.dirname(_os.path.abspath(__file__))
except NameError:            # Origin "run -pyf" may not define __file__
    _HERE = _os.environ["LASC_PKG"] + "/origin_plots"
_sys.path.insert(0, _os.path.normpath(_os.path.join(_HERE, "..")))
_sys.path.insert(0, _HERE)
import config

import sys, os, json
pass
import importlib, oplib as O
importlib.reload(O)
import originpro as op

FOLD = "3 Synaptic/Statistics"
INFO = json.load(open(O.S + "/prep/csv/stats_info.json"))
GX = "\\b(Conductance (\\g(m)S))"
PAL = config.PAPER_FIG + "/scripts/RdYlBu_CDF.pal"     # RdYlBu: CDF 0 red, 0.5 pale yellow, 1 blue
LEVELS = {"minors": 3, "levels": [0, 0.2, 0.4, 0.6, 0.8, 1.0]}       # 20 colour bands, isolines at the quintiles
# the 20 band colours Origin takes from the stretched 256-entry palette (index k*255/19), read from the .pal file
_pal = open(PAL, "rb").read()[24:]
BAND_RGB = [tuple(_pal[4 * round(k * 255 / 19): 4 * round(k * 255 / 19) + 3]) for k in range(20)]

def dgg(P, name, title, yr):
    d = O.read_csv(f"DGG_map_{P}")
    pts = O.read_csv(f"DGG_points_{P}")
    wb, ws = O.book(f"DGG{P}", f"dG-G switching statistics, {name}")
    O.cols(ws, [(d["G_uS"], 'X', "Conductance G", "\\g(m)S", "kernel centre, sigma = 0.012 uS"),
                (d["dG_nS"], 'Y', "\\g(D)G", "nS", "dG = G(n+1) - G(n), kernel h = 1.2 nS"),
                (d["CDF"], 'Z', "Cumulative probability", "", "CDF")])
    O.lt(f'win -a {wb.name}; page.longname$ = "dG-G conditional CDF, {INFO[name]["n"]} consecutive {name} pulses of 5 LTP/LTD cycles";')
    s2 = wb.add_sheet("Pulse data")
    O.cols(s2, [(pts["G_uS"], 'X', "G(n)", "\\g(m)S", "conductance before the pulse"),
                (pts["dG_nS"], 'Y', "\\g(D)G", "nS", "G(n+1) - G(n)")])
    s3 = wb.add_sheet("Colour bar")
    O.cols(s3, [([0, 1], 'X', "bar x", "", "colour bar: 20 bands, filled to the next line")] +
                [([k / 20, k / 20], 'Y', f"CDF {k / 20:.2f}", "", "") for k in range(21)])
    g = op.new_graph(template="TriContour", lname=title)
    g.name = f"DGG{P}"
    p = g[0].add_plot(ws, colz=2, colx=0, coly=1)
    p.zlevels = LEVELS
    p.colormap = PAL
    O.lt(f'win -a {g.name}; layer -s 1; layer.plot=1; set %C -w 0;')
    sp = g[0].label("Spectrum1")
    if sp is not None:
        g[0].remove_label(sp)                      # replaced by the Origin-drawn colour bar in layer 2 (TNR bold)
    O.style(g, GX, "\\b(\\g(D)G (nS))", xr=((0.19 if P == "P" else 0.18), 0.42 if P == "P" else 0.46, 0.05),
            yr=yr, right_axis=True)
    # colour bar: narrow layer with a z = y contour strip, same levels and palette, right-hand axis 0-1
    O.lt(f'win -a {g.name}; layadd type:=0;')
    O.lt('layer -s 2; layer.unit=1; layer.left = layer1.left + layer1.width + 3.5; layer.top = layer1.top;'
         ' layer.width = 4.5; layer.height = layer1.height;')
    for k in range(21):
        pb = g[1].add_plot(s3, coly=k + 1, colx=0, type='l')
        r, gg, b = BAND_RGB[min(k, 19)]
        pb.set_fill_area(f"color({r},{gg},{b})", 9, f"color({r},{gg},{b})")    # band k: from line k to line k+1
        pb.set_cmd('-w 0')
    O.lt('layer -s 2; layer.plot=21; set %C -pf 0;')                      # top line closes the last band
    O.lt('layer.x.from=0; layer.x.to=1; layer.y.from=0; layer.y.to=1; layer.y.inc=0.2; layer.y.minorTicks=0;')
    for ax in ('x', 'y', 'x2', 'y2'):
        O.lt(f'layer.{ax}.thickness=2.5; layer.{ax}.ticks=0;')
    O.lt('layer.x.showAxes=3; layer.y.showAxes=3; layer.x.showLabels=0; layer.y.showLabels=2; layer.y2.ticks=10;'
         ' layer.y2.tickLength=6; layer.y2.tickThickness=2;')
    for ax in ('y', 'y2'):
        O.lt(f'layer.{ax}.label.font=font("{O.TNR}"); layer.{ax}.label.pt=24; layer.{ax}.label.bold=1;')
    for nm in ("xb", "yl", "legend", "Spectrum1"):
        lb = g[1].label(nm)
        if lb is not None:
            g[1].remove_label(lb)
    O.lt(f'layer -s 2; label -s -n CBT "\\b(CDF)"; CBT.font=font("{O.TNR}"); CBT.fsize=26; CBT.background=0; CBT.rotate=90;'
         ' CBT.left = layer.left*page.width/100 + layer.width*page.width/100 + 380;'
         ' CBT.top = layer.top*page.height/100 + layer.height*page.height/100/2 - CBT.height/2;')
    O.lt('layer -s 1;')
    O.lt('draw -n Z0 -l {0.1,0,0.5,0}; Z0.lineType=2; Z0.linewidth=2; Z0.color=color(0,0,0);')
    O.lt(f'Z0.x1={0.19 if P == "P" else 0.18}; Z0.x2={0.42 if P == "P" else 0.46}; Z0.y1=0; Z0.y2=0;')
    O.page_text(f"TT{P}", name.capitalize(), 0.03, 0.07, fs=24, anchor="lc")
    st = INFO[name]
    O.page_text(f"TN{P}", f"n = {st['n']} updates (5 × 49)", 0.03, 0.16, fs=20, anchor="lc")
    O.save(g, FOLD, f"DGG_{name}", f"dG-G switching statistics during {name} (conditional CDF)",
           note=f"mean {st['mean_nS']} nS, s.d. {st['sd_nS']} nS, opposite-sign updates {st['wrong_sign_pct']} %")

def dgg_p():
    dgg("P", "potentiation", "dG-G map, potentiation", (-15, 25, 5))

def dgg_d():
    dgg("D", "depression", "dG-G map, depression", (-25, 15, 5))

def end_cdf():
    d = O.read_csv("END_cumprob")
    wb, ws = O.book("ENDcdf", "Cumulative probability of G+ and G- (2500 cycles)")
    O.cols(ws, [(d["Gp_uS"], 'X', "G\\-(+)", "\\g(m)S", "sorted, 2500 cycles"),
                (d["Gp_prob"], 'Y', "Cumulative probability", "%", "(i - 0.5)/N x 100"),
                (d["Gm_uS"], 'X', "G\\-(-)", "\\g(m)S", "sorted, 2500 cycles"),
                (d["Gm_prob"], 'Y', "Cumulative probability", "%", "(i - 0.5)/N x 100")])
    g = O.graph("ENDcdf", "Cumulative probability of G+ and G-")
    O.plot(g, ws, 1, 0, 's'); O.plot(g, ws, 3, 2, 's')
    O.style(g, GX, "\\b(Cumulative Probability (%))", xlog=True, xr=(0.05, 1), yr=(-5, 105, 20))
    O.pstyle(1, "0,0,0", None, sym=2, ssize=6); O.pstyle(2, "230,0,0", None, sym=1, ssize=6)
    O.lt('legend -r; legend.text$ = "\\l(1) \\b(G\\-(+) (Potentiation))%(CRLF)\\l(2) \\b(G\\-(-) (Depression))";'
         f' legend.font=font("{O.TNR}"); legend.fsize=20; legend.background=0;')
    O.at("legend", 0.30, 0.30, xlog=True, anchor="lb")
    a, b = INFO["G+"], INFO["G-"]
    O.page_text("CVp", f"CV = {a['CV_pct']}%", 0.76, 0.12, fs=22, anchor="lc")
    O.page_text("CVm", f"CV = {b['CV_pct']}%", 0.27, 0.12, fs=22, anchor="lc", color="230,0,0")
    O.save(g, FOLD, "Endurance_cumulative_probability", "Cumulative probability of G+ and G- over 2500 cycles",
           note=f"G+ {a['mean_uS']} +/- {a['sd_uS']} uS (CV {a['CV_pct']}%), G- {b['mean_uS']} +/- {b['sd_uS']} uS (CV {b['CV_pct']}%)")

O.run_all([dgg_p, dgg_d], "plot5_stats")
