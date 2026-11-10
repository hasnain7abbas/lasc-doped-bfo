import os as _os, sys as _sys
try:
    _HERE = _os.path.dirname(_os.path.abspath(__file__))
except NameError:            # Origin "run -pyf" may not define __file__
    _HERE = _os.environ["LASC_PKG"] + "/origin_plots/extract_pe"
_sys.path.insert(0, _os.path.normpath(_os.path.join(_HERE, "..", "..")))
_sys.path.insert(0, _HERE)
import config

import originpro as op, traceback, csv
S = config.WORK
log = open(S + "/tools/t_bfo2.log", "w", encoding="utf8")
try:
    op.open(config.RAW + "/p2 bfo pure.opju", readonly=True)
    sh = op.find_sheet('w', '[Book2]Selected_C2_C3_Loops')
    cols = [sh.to_list(i) for i in range(sh.cols)]
    names = [sh.get_label(i,'L') + ("_E" if i%2==0 else "_P") for i in range(sh.cols)]
    m = max(len(c) for c in cols)
    with open(S + "/pe_csv/BFO_P2.csv", "w", newline="") as fh:
        w = csv.writer(fh); w.writerow(names)
        for k in range(m): w.writerow([c[k] if k < len(c) else "" for c in cols])
    op.lt_exec('win -a Graph1; string __a$ = "x " + $(layer1.x.from) + " " + $(layer1.x.to) + " y " + $(layer1.y.from)+" "+$(layer1.y.to);')
    log.write(op.get_lt_str('__a$') + "\n")
except Exception:
    log.write(traceback.format_exc())
log.close()
