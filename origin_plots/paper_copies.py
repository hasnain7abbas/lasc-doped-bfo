# Paper copies of the finished graphs: drop the slide title above the frame and any "(a) " prefix inside the graph.
# Originals are opened read-only; copies go to Paper figures\origin, previews to previews_paper.
import os as _os, sys as _sys
try:
    _HERE = _os.path.dirname(_os.path.abspath(__file__))
except NameError:            # Origin "run -pyf" may not define __file__
    _HERE = _os.environ["LASC_PKG"] + "/origin_plots"
_sys.path.insert(0, _os.path.normpath(_os.path.join(_HERE, "..")))
_sys.path.insert(0, _HERE)
import config

import sys, os, re, json, glob
pass
import importlib, oplib as O
importlib.reload(O)
import originpro as op

OUT = config.PAPER_FIG + "/origin"
PRE = O.S + "/previews_paper"
WANT = json.load(open(O.S + "/tools/paper_list.json"))
if os.path.exists(O.S + "/tools/paper_only.json"): WANT = json.load(open(O.S + "/tools/paper_only.json"))          # [name, ...]
REGS = {}
for f in glob.glob(O.S + "/tools/*_registry.json"):
    for r in json.load(open(f)):
        REGS[os.path.splitext(os.path.basename(r["path"]))[0]] = r

def one(name):
    r = REGS[name]
    op.open(r["path"], readonly=True)
    g = op.find_graph(r["graph"])
    O.lt(f'win -a {g.name}; layer -s 1;')
    O.lt('__LTP = layer1.top*page.height/100;')
    lt_top = op.lt_float('__LTP')
    O.L(name, "frame top", lt_top)
    gl = g[0]
    for i in range(1, 80):
        nm = f"T{i}"
        lb = gl.label(nm)
        if lb is None:
            continue
        txt = lb.text
        top = op.lt_float(f'{nm}.top'); h = op.lt_float(f'{nm}.height')
        O.L(name, nm, top, h, repr(txt[:40]))
        if top + h <= lt_top + 5:                          # sits above the frame -> slide title
            gl.remove_label(lb); O.L(name, "removed title", repr(txt))
        else:
            new = re.sub(r'\((?:a|b|c|d)\) ', '', txt)
            if new != txt:
                lb.text = new; O.L(name, "stripped letter", repr(txt), "->", repr(new))
    dst = f"{OUT}/{name}.opju"
    if os.path.exists(dst):
        os.remove(dst)
    op.save(dst)
    g.save_fig(f"{PRE}/{name}.png", width=900)
    O.L("saved", dst)

def make(name):
    def f():
        one(name)
    f.__name__ = name
    return f

O.run_all([make(n) for n in WANT], "paper_copies")
