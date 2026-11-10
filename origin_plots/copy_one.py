import os as _os, sys as _sys
try:
    _HERE = _os.path.dirname(_os.path.abspath(__file__))
except NameError:            # Origin "run -pyf" may not define __file__
    _HERE = _os.environ["LASC_PKG"] + "/origin_plots"
_sys.path.insert(0, _os.path.normpath(_os.path.join(_HERE, "..")))
_sys.path.insert(0, _HERE)
import config

import originpro as op, json, traceback
S = config.WORK
jp = op.get_lt_str('jobpath$')
with open(jp.replace(".json", ".log"), "w", encoding="utf8") as log:
    try:
        with open(jp, encoding="utf-8-sig") as fh:
            job = json.load(fh)
        op.new(asksave=False)
        op.open(job["path"], readonly=True)
        g = op.find_graph(job["graph"])
        op.lt_exec(f'win -a {g.name};')
        g.copy_page('OLE')
        log.write("OK\n")
    except Exception:
        log.write(traceback.format_exc())
