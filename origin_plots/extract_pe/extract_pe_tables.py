import os as _os, sys as _sys
try:
    _HERE = _os.path.dirname(_os.path.abspath(__file__))
except NameError:            # Origin "run -pyf" may not define __file__
    _HERE = _os.environ["LASC_PKG"] + "/origin_plots/extract_pe"
_sys.path.insert(0, _os.path.normpath(_os.path.join(_HERE, "..", "..")))
_sys.path.insert(0, _HERE)
import config

import originpro as op, os, glob, traceback
S = config.WORK
log = open(S + "/tools/t_extract_pe2.log", "w", encoding="utf8")
def L(*a): log.write(" ".join(str(x) for x in a) + "\n"); log.flush()
out = S + "/pe_csv"; os.makedirs(out, exist_ok=True)
for f in sorted(glob.glob(S + "/pe_opj/*.opju")):
  try:
    op.new(asksave=False)
    op.open(f.replace("\\", "/"))
    tag = os.path.basename(f)[:-5]
    gp = list(op.pages('g'))[0]
    gname = gp.name
    op.lt_exec(f'win -a {gname};')
    # text labels on graph
    op.lt_exec('string __s$ = ""; doc -e G {}; ')  # noop
    op.lt_exec('''string __txt$=""; int __n = 0;
      doc -e LG { __txt$ = __txt$ + "|" + %B; };
    ''')
    L("##", tag, gname)
    op.lt_exec(f'layer -s 1; string __leg$ = legend.text$; string __lab$=""; ')
    L(" legend:", op.get_lt_str('__leg$').replace("\n", " / ").replace("\r",""))
    # list graphic objects
    op.lt_exec('string __objs$=""; doc -e G { __objs$ = __objs$ + "|" + %B + "=" + %B.text$; };')
    L(" objs:", op.get_lt_str('__objs$').replace("\n"," ").replace("\r",""))
    op.lt_exec('string __ax$ = "x:" + $(layer1.x.from) + "," + $(layer1.x.to) + " y:" + $(layer1.y.from) + "," + $(layer1.y.to) + " xt:" + xb.text$ + " yt:" + yl.text$;')
    L(" axes:", op.get_lt_str('__ax$'))
    n = len(gp[0].plot_list())
    cols = []
    import csv
    data = []
    names = []
    for i in range(1, n + 1):
        op.lt_exec(f'win -a {gname}; layer -s 1; range __rr = 1!{i}; dataset __dx = xof(__rr); dataset __dy = __rr; string __pn$ = __rr.name$; ')
        dx = op.get_lt_str('__dx') if False else None
        # pull via LabTalk to python
        nx = int(op.lt_float('__dx.GetSize()'))
        xs = [op.lt_float(f'__dx[{k}]') for k in range(1, nx + 1)]
        ys = [op.lt_float(f'__dy[{k}]') for k in range(1, nx + 1)]
        data.append((xs, ys)); names.append(op.get_lt_str('__pn$'))
    L(" plots:", n, "dataset names:", names, "sizes:", [len(d[0]) for d in data])
    m = max(len(d[0]) for d in data)
    with open(f"{out}/{tag}.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(sum([[f"E{i+1}", f"P{i+1}"] for i in range(n)], []))
        for k in range(m):
            row = []
            for xs, ys in data:
                row += [xs[k], ys[k]] if k < len(xs) else ["", ""]
            w.writerow(row)
  except Exception:
    L(tag if 'tag' in dir() else f, traceback.format_exc())
log.close()
