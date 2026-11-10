# Shared Origin helpers (runs inside Origin's embedded Python 3.11; no numpy there)
import os as _os, sys as _sys
try:
    _HERE = _os.path.dirname(_os.path.abspath(__file__))
except NameError:            # Origin "run -pyf" may not define __file__
    _HERE = _os.environ["LASC_PKG"] + "/origin_plots"
_sys.path.insert(0, _os.path.normpath(_os.path.join(_HERE, "..")))
_sys.path.insert(0, _HERE)
import config

import originpro as op, os, json, csv, math, traceback

S = config.WORK
CSV = S + "/prep/csv/"
OUTROOT = config.ORIGIN_OUT
def manifest2():
    return json.load(open(S + "/prep/manifest_v2.json"))
TNR = "Times New Roman"
LOGF = None
TRACE = os.path.exists(S + "/tools/trace.on")
REG = []          # registry of saved graphs -> used for the PowerPoint step

# Origin default line palette, as used in the user's ferro / FYP graphs
PAL = ["81,81,81", "241,64,64", "26,111,223", "55,173,107", "177,119,222", "204,153,0", "0,203,204",
       "125,78,78", "142,142,0", "251,101,1", "102,153,204", "111,184,2"]
def pal(i):
    return PAL[i % len(PAL)]

def L(*a):
    if LOGF:
        LOGF.write(" ".join(str(x) for x in a) + "\n"); LOGF.flush()

def esc(s):
    """Origin rich text -> LabTalk string literal (LabTalk eats single backslashes like \\b)."""
    return s.replace('"', "'")

import re as _re
_NAMED = {"black": (0, 0, 0), "red": (241, 64, 64), "blue": (26, 111, 223), "green": (55, 173, 107), "gray": (128, 128, 128)}
def _ocol(r, g, b):
    return 0x1000000 + (int(b) << 16) + (int(g) << 8) + int(r)
def _colsub(cmd):
    cmd = _re.sub(r'color\((\d+)\s*,\s*(\d+)\s*,\s*(\d+)\)', lambda m: str(_ocol(*m.groups())), cmd)
    return _re.sub(r'color\((black|red|blue|green|gray)\)', lambda m: str(_ocol(*_NAMED[m.group(1)])), cmd)

def lt(cmd):
    cmd = _colsub(cmd)
    if TRACE: L("  lt:", cmd[:200])
    ok = op.lt_exec(cmd)
    if not ok:
        L("LT-FAIL:", cmd[:400])
    return ok

def read_csv(name):
    with open(CSV + name + ".csv", newline="", encoding="utf8") as fh:
        r = list(csv.reader(fh))
    head, body = r[0], r[1:]
    out = {}
    for j, h in enumerate(head):
        c = []
        for row in body:
            v = row[j] if j < len(row) else ""
            if v == "" or v.lower() == "nan":
                c.append(None)
            else:
                try:
                    c.append(float(v))
                except ValueError:
                    c.append(v)
        while c and c[-1] is None:
            c.pop()
        out[h] = c
    return out

def manifest():
    return json.load(open(S + "/prep/manifest.json"))

def fresh():
    op.new(asksave=False)

def book(name, lname, sheet="Data"):
    wb = op.new_book('w', lname=lname)
    wb.name = name
    ws = wb[0]
    ws.name = sheet
    return wb, ws

def cols(ws, spec, start=0):
    """spec: list of (data, desig, lname, units, comment)."""
    ws.cols = max(ws.cols, start + len(spec))
    for k, (data, desig, ln, un, cm) in enumerate(spec):
        d = [float('nan') if v is None else v for v in data]
        ws.from_list(start + k, d, lname=ln, units=un, comments=cm, axis=desig)
    return ws

def set_formula(ws, col, formula):
    """Store a column formula (shown in the column's F(x) row) and recalculate."""
    lt(f'win -a {ws.get_book().name}; page.active$ = "{ws.name}"; col({col + 1})[F]$ = "{formula}"; '
       f'wks.col{col + 1}.formula$ = "{formula}"; wks.col{col + 1}.exec();')

def graph(name, lname):
    g = op.new_graph(template="line", lname=lname)
    g.name = name
    lt(f'win -a {g.name}; layer -s 1;')
    return g

def plot(g, ws, cy, cx, kind='l', layer=0, cyerr=-1):
    return g[layer].add_plot(ws, coly=cy, colx=cx, type=kind, colyerr=cyerr)

def frame4(layer_idx=1, right_axis=False):
    """4 pt lines on all four sides (bottom/left AND top/right), outward ticks, bold TNR labels."""
    lt(f'layer -s {layer_idx};')
    for ax in ('x', 'y', 'x2', 'y2'):
        lt(f'layer.{ax}.thickness=4; layer.{ax}.tickThickness=2.5; layer.{ax}.tickLength=8; layer.{ax}.ticks=10;')
    # top (and right, unless it is a real axis) frame lines stay clean: no tick marks, as in the FYP graphs
    lt('layer.x2.ticks=0;')
    if not right_axis:
        lt('layer.y2.ticks=0;')
    lt('layer.x.showAxes=3; layer.y.showAxes=3; layer.x.showLabels=1; layer.y.showLabels=1;')

def style(g, xt, yt, xlog=False, ylog=False, xr=None, yr=None, tick=28, ttl=28, minor=1, wide=False, right_axis=False):
    """Paper style copied from the user's own Origin graphs: 4 pt frame on all sides, Times New Roman bold."""
    lt(f'win -a {g.name}; layer -s 1;')
    if wide:
        LAYER1.update(left=11.5, top=11.6, width=82.5, height=71.79, pw=9432, ph=4923)
    else:
        LAYER1.update(left=17.89, top=11.6, width=62.5 if right_axis else 68.19, height=71.79, pw=6432, ph=4923)
    L1 = LAYER1
    lt(f'page.width={L1["pw"]}; page.height={L1["ph"]};')
    lt(f'layer.unit=1; layer.left={L1["left"]}; layer.top={L1["top"]}; layer.width={L1["width"]}; layer.height={L1["height"]};')
    if xlog: lt('layer.x.type=2;')
    if ylog: lt('layer.y.type=2;')
    if xr:
        lt(f'layer.x.from={xr[0]}; layer.x.to={xr[1]};' + (f' layer.x.inc={xr[2]};' if len(xr) > 2 and xr[2] else ''))
    if yr:
        lt(f'layer.y.from={yr[0]}; layer.y.to={yr[1]};' + (f' layer.y.inc={yr[2]};' if len(yr) > 2 and yr[2] else ''))
    for ax in ('x', 'y'):
        lt(f' layer.{ax}.minorTicks={minor if (ax == "x" and not xlog) or (ax == "y" and not ylog) else 8};'
           f' layer.{ax}.label.font=font("{TNR}"); layer.{ax}.label.pt={tick}; layer.{ax}.label.bold=1;')
    frame4(1, right_axis)
    lt(f'xb.text$ = "{esc(xt)}"; xb.font=font("{TNR}"); xb.fsize={ttl};')
    lt(f'yl.text$ = "{esc(yt)}"; yl.font=font("{TNR}"); yl.fsize={ttl};')

def title_above(t, fs=26):
    """Bold title just above the top-left corner of the frame (FYP style: 'SNDP', 'Retention', ...)."""
    _lab[0] += 1
    nm = f"T{_lab[0]}"
    lt(f'label -s -n {nm} "{esc(chr(92) + "b(" + t + ")")}"; {nm}.font=font("{TNR}"); {nm}.fsize={fs}; {nm}.background=0;')
    lt(f'{nm}.left = layer1.left*page.width/100; {nm}.top = layer1.top*page.height/100 - {nm}.height - 60;')
    return nm

def inset_layer(g, fx, fy, fw, fh, xr, yr):
    """Add an axis-free layer occupying the fraction box (fx, fy = left, top; fw, fh) of layer 1's frame.
    Returns its 1-based index. Coordinates inside are the given linear ranges."""
    n0 = len(list(g))
    lt(f'win -a {g.name}; layadd type:=0;')
    n = len(list(g))
    k = n if n > n0 else n0 + 1
    lt(f'layer -s {k}; layer.unit=1;'
       f' layer.left = layer1.left + {fx}*layer1.width; layer.top = layer1.top + {fy}*layer1.height;'
       f' layer.width = {fw}*layer1.width; layer.height = {fh}*layer1.height;')
    lt(f'layer.x.from={xr[0]}; layer.x.to={xr[1]}; layer.y.from={yr[0]}; layer.y.to={yr[1]};')
    lt('layer.x.showAxes=0; layer.y.showAxes=0; layer.x.showLabels=0; layer.y.showLabels=0; layer.x.ticks=0; layer.y.ticks=0;')
    lt('label -r xb; label -r yl; label -r legend;')
    return k

def inset_text(k, nm, t, x, y, fs=18, color=None, anchor="lc"):
    """text in inset layer k at its axis coordinates; anchor 'lc' = left edge, vertically centred"""
    lt(f'layer -s {k}; label -s -n {nm} "{esc(chr(92) + "b(" + t + ")")}"; {nm}.font=font("{TNR}"); {nm}.fsize={fs}; {nm}.background=0;')
    if color: lt(f'{nm}.color=color({color});')
    if anchor == "lc":
        lt(f'{nm}.x = {x} + {nm}.dx/2; {nm}.y = {y};')
    elif anchor == "rc":
        lt(f'{nm}.x = {x} - {nm}.dx/2; {nm}.y = {y};')
    else:
        lt(f'{nm}.x = {x}; {nm}.y = {y};')

PULSE_W = 2000          # pulse-sketch line width (set -w units; 2000 = 4 pt, same as the frame)
LAYER1 = dict(left=17.89, top=11.6, width=68.19, height=71.79, pw=6432, ph=4923)

def page_xy(fx, fy):
    """fraction of layer-1 frame (from left, from TOP) -> page coordinates"""
    L1 = LAYER1
    return (L1["left"] / 100 * L1["pw"] + fx * L1["width"] / 100 * L1["pw"],
            L1["top"] / 100 * L1["ph"] + fy * L1["height"] / 100 * L1["ph"])

def page_text(nm, t, fx, fy, fs=18, color="0,0,0", anchor="lc", bold=True):
    """text on layer 1 placed by layer-1 frame fraction (fy from the top); anchor lc/rc/cc"""
    px, py = page_xy(fx, fy)
    s = f"\\b({t})" if bold else t
    lt(f'layer -s 1; label -s -n {nm} "{esc(s)}"; {nm}.font=font("{TNR}"); {nm}.fsize={fs}; {nm}.background=0; {nm}.color=color({color});')
    if anchor == "lc":
        lt(f'{nm}.left = {px}; {nm}.top = {py} - {nm}.height/2;')
    elif anchor == "rc":
        lt(f'{nm}.left = {px} - {nm}.width; {nm}.top = {py} - {nm}.height/2;')
    else:
        lt(f'{nm}.left = {px} - {nm}.width/2; {nm}.top = {py} - {nm}.height/2;')

def fraction(g, prefix, num, den, suffix, fx=0.03, fy=0.03, fw=0.62, fh=0.20, fs=20, tag="FR"):
    """Formula typeset as a fraction:  prefix = (num / den) suffix, inside a box of layer 1
    (fx, fy = left, top as fractions of the frame; fy measured from the top)."""
    k = inset_layer(g, fx, fy, fw, fh, (0, 10), (0, 10))
    lt(f'layer -s {k}; draw -n {tag}bar -l {{3.55,5,7.25,5}}; {tag}bar.linewidth=2; {tag}bar.color=color(0,0,0);')
    def frac(xv, yv):
        return fx + xv / 10 * fw, fy + (10 - yv) / 10 * fh
    a, b = frac(3.4, 5); page_text(f"{tag}p", prefix, a, b, fs=fs, anchor="rc")
    a, b = frac(5.4, 7.6); page_text(f"{tag}n", num, a, b, fs=fs, anchor="cc")
    a, b = frac(5.4, 2.4); page_text(f"{tag}d", den, a, b, fs=fs, anchor="cc")
    a, b = frac(7.4, 5); page_text(f"{tag}s", suffix, a, b, fs=fs, anchor="lc")
    lt('layer -s 1;')
    return k

def frac_to_axis(fx, fy_top):
    """layer-1 frame fraction (x from left, y from TOP) -> layer-1 axis coordinates (handles log axes)"""
    x0, x1 = op.lt_float('layer1.x.from'), op.lt_float('layer1.x.to')
    y0, y1 = op.lt_float('layer1.y.from'), op.lt_float('layer1.y.to')
    xl, yl = op.lt_float('layer1.x.type') == 2, op.lt_float('layer1.y.type') == 2
    fy = 1 - fy_top
    X = 10 ** (math.log10(x0) + fx * (math.log10(x1) - math.log10(x0))) if xl else x0 + fx * (x1 - x0)
    Y = 10 ** (math.log10(y0) + fy * (math.log10(y1) - math.log10(y0))) if yl else y0 + fy * (y1 - y0)
    return X, Y

def seg(name, fa, fb, w=3.0, dotted=False, arrow_begin=False, color="0,0,0"):
    """straight line object on layer 1 between two frame-fraction points (fx, fy_from_top)"""
    (xa, ya), (xb_, yb) = frac_to_axis(*fa), frac_to_axis(*fb)
    lt(f'layer -s 1; draw -n {name} -l {{{xa},{ya},{xb_},{yb}}}; {name}.linewidth={w}; {name}.color=color({color});')
    if dotted: lt(f'{name}.lineType=7;')                     # dotted style used in the FYP graphs
    if arrow_begin: lt(f'{name}.arrowBeginShape=2; {name}.arrowBeginLength=10; {name}.arrowBeginWidth=5;')   # 2 = arrowhead

def pulse_inset(g, wb, fx=0.50, fy=0.04, fw=0.47, fh=0.30, vw="15V", vr="1V", tag="PS", fs=18):
    """FYP-style write/read pulse sketch drawn with bold line objects on layer 1 (they keep their width):
    labels on the left with dotted arrow leaders, a square pulse and the 0 V line on the right.
    fx, fy, fw, fh: box inside layer 1 as fractions of its frame (fy from the top)."""
    ws = wb.add_sheet("Pulse scheme")
    cols(ws, [(["V_W", "V_R", "0 V"], 'X', "Level", "", "pulse sketch drawn on the graph (not to scale)"), ([vw, vr, "0V"], 'Y', "Value", "", "")])
    U0, U1, V0, V1 = 0.0, 10.0, -0.5, 3.6
    def F(u, v):
        return (fx + (u - U0) / (U1 - U0) * fw, fy + (V1 - v) / (V1 - V0) * fh)
    shape = [(5.2, 1.0), (6.3, 1.0), (6.3, 3.0), (8.0, 3.0), (8.0, 1.0), (9.8, 1.0)]
    for i in range(len(shape) - 1):
        seg(f"{tag}s{i}", F(*shape[i]), F(*shape[i + 1]), w=4.0)          # 4 pt, same as the frame
    seg(f"{tag}z", F(5.2, 0.0), F(9.8, 0.0), w=4.0)
    for nm, (ua, ub, v) in {f"{tag}l1": (3.35, 6.2, 3.0), f"{tag}l2": (3.35, 5.1, 1.0), f"{tag}l3": (3.35, 5.1, 0.0)}.items():
        seg(nm, F(ua, v), F(ub, v), w=2.0, dotted=True, arrow_begin=True)   # dotted leader, arrowhead at the label
    for nm, txt, v in [(f"{tag}a", f"V\\-(W) = {vw}", 3.0), (f"{tag}b", f"V\\-(R) = {vr}", 1.0), (f"{tag}c", "0V", 0.0)]:
        a, b = F(3.2, v)
        page_text(nm, txt, a, b, fs=fs, anchor="rc")
    lt('layer -s 1;')
    return 1

def pstyle(i, color=None, lw=4, sym=None, ssize=9, kind=None, hollow=False):
    """i: 1-based plot index in layer 1."""
    lt(f'layer.plot={i};')
    if lw is not None: lt(f'set %C -w {int(lw * 500)};')
    if color is not None:
        lt(f'set %C -c color({color}); set %C -cl color({color});')
    if sym is not None:
        lt(f'set %C -k {sym}; set %C -z {ssize};')
        if color is not None:
            lt(f'set %C -cse color({color});' + ('' if hollow else f' set %C -csf color({color});'))
        if hollow: lt('set %C -kf 1;')

def legend(text=None, fs=20, x=None, y=None, frame=0):
    lt('legend -r;')
    if text is not None:
        lt(f'legend.text$ = "{esc(text)}";')
    lt(f'legend.font=font("{TNR}"); legend.fsize={fs}; legend.background={frame};')
    if x is not None:
        lt(f'legend.x={x}; legend.y={y};')

def nolegend():
    lt('label -r legend;')

_lab = [0]
def text(t, x, y, fs=24, color=None, bold=True):
    """Text object centred at axis coordinates (x, y)."""
    _lab[0] += 1
    nm = f"T{_lab[0]}"
    s = f"\\b({t})" if bold else t
    lt(f'label -s -n {nm} "{esc(s)}";')
    lt(f'{nm}.font=font("{TNR}"); {nm}.fsize={fs}; {nm}.background=0; {nm}.x={x}; {nm}.y={y};')
    if color: lt(f'{nm}.color=color({color});')
    return nm

def text_lt(t, x, y, fs=24, color=None, bold=True):
    """Text object with its LEFT-TOP corner at axis coordinates (x, y)."""
    nm = text(t, x, y, fs, color, bold)
    lt(f'{nm}.x = {x} + {nm}.dx/2; {nm}.y = {y} - {nm}.dy/2;')
    return nm

def at(nm, fx, fy, xlog=False, ylog=False, anchor="lt"):
    """Place object nm so its anchor corner ('lt', 'rb', ...) sits at axis fraction (fx, fy) from left/bottom.
    Works on linear and log10 axes (on a log axis the anchor offset is applied in decades)."""
    # page coordinates are scale independent, so this works for linear and log axes alike
    lt('double __PL = layer.left*page.width/100; double __PT = layer.top*page.height/100;'
       ' double __PW = layer.width*page.width/100; double __PH = layer.height*page.height/100;')
    xl = f'__PL + {fx}*__PW' + (f' - {nm}.width' if "r" in anchor else '')
    yt = f'__PT + (1-{fy})*__PH' + (f' - {nm}.height' if "b" in anchor else '')
    lt(f'{nm}.left = {xl}; {nm}.top = {yt};')

def hline(name, x1, y1, x2, y2, w=2.5, color="black", dash=0):
    lt(f'draw -n {name} -l {{{x1},{y1},{x2},{y2}}};')
    lt(f'{name}.linewidth={w}; {name}.color=color({color}); {name}.attach=2;')
    if dash: lt(f'{name}.lineType={dash};')

def fitlr(ws, cx, cy, r1, r2):
    """Linear fit y = a + b x on rows r1..r2 (1-based, inclusive) using Origin's fitlr."""
    bk = ws.get_book().name
    lt(f'range __rx = [{bk}]"{ws.name}"!col({cx + 1})[{r1}:{r2}]; range __ry = [{bk}]"{ws.name}"!col({cy + 1})[{r1}:{r2}];')
    lt('fitlr iy:=(__rx, __ry) a:=__fa b:=__fb aerr:=__fae berr:=__fbe r:=__fr N:=__fn;')
    return dict(a=op.lt_float('__fa'), b=op.lt_float('__fb'), aerr=op.lt_float('__fae'), berr=op.lt_float('__fbe'),
                r2=op.lt_float('__fr') ** 2, n=op.lt_float('__fn'))

def smooth_sg(ws, cy, cout, npts=7, order=2):
    """Savitzky-Golay smoothing done by Origin's smooth X-Function."""
    bk = ws.get_book().name
    lt(f'smooth iy:=[{bk}]"{ws.name}"!col({cy + 1}) method:=1 npts:={npts} polyorder:={order} boundary:=1 oy:=[{bk}]"{ws.name}"!col({cout + 1});')

def colvals(ws, c):
    return [v for v in ws.to_list(c)]

def save(g, folder, fname, title, note=""):
    path = f"{OUTROOT}/{folder}/{fname}.opju"
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if os.path.exists(path):
        os.remove(path)
    lt(f'win -a {g.name};')
    op.save(path)
    g.save_fig(S + f"/previews/{fname}.png", width=900)
    REG.append(dict(path=path, graph=g.name, title=title, folder=folder, note=note))
    L("saved", path)

def run_all(funcs, logname):
    global LOGF
    os.makedirs(S + "/previews", exist_ok=True)
    LOGF = open(S + f"/tools/{logname}.log", "w", encoding="utf8")
    for f in funcs:
        L("START", f.__name__)
        try:
            fresh()
            _lab[0] = 0
            f()
        except Exception:
            L("ERROR in", f.__name__, traceback.format_exc())
    reg_path = S + f"/tools/{logname}_registry.json"
    old = json.load(open(reg_path)) if os.path.exists(reg_path) else []
    new_paths = {r["path"] for r in REG}
    if len(funcs) < 60 and old:   # partial (filtered) run: keep the other entries, replace re-made ones in place
        merged = [next((r for r in REG if r["path"] == o["path"]), o) for o in old]
        merged += [r for r in REG if r["path"] not in {o["path"] for o in old}]
    else:
        merged = REG
    seen = set(); final = []
    for r in merged:
        if r["path"] not in seen:
            seen.add(r["path"]); final.append(r)
    json.dump(final, open(reg_path, "w"), indent=1)
    L("DONE", len(REG), "graphs")
    LOGF.close()
