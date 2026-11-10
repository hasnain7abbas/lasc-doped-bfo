"""Run the whole data-preparation chain (system Python) in the right order.

  python analysis/run_prep.py

Reads the raw data from config.RAW / config.XRD_RAW and writes every table used by the figures to
config.WORK/prep/csv (plus manifest files with the provenance of each table). The P-E step needs
work/pe_csv, which is extracted once from the Origin objects in "ferro plots.pptx" with the scripts in
origin_plots/extract_pe (OriginPro required); see README.
"""
import os, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
STEPS = [
    ("prep_all.py", HERE),          # synaptic workbook, PUND, I-V, retention, endurance ... -> csv + manifest.json
    ("prep_pe.py", HERE),           # P-E loops (needs work/pe_csv)
    ("prep_v2.py", HERE),           # second round: smoothed J-E, PUND metrics, EPSC, SDDP, P-E comparison
    ("prep_v3.py", HERE),           # SNDP and retention blocks
    ("prep_v4.py", HERE),           # conduction branches (log J - log E)
    ("prep_xrd.py", os.path.join(HERE, "xrd")),   # 2-theta offset, (104)/(110) fits, lattice parameters
    ("fix_pt.py", os.path.join(HERE, "xrd")),     # Pt(111) removal from the Sc 1 % scan
    ("prep_srdp_rep.py", HERE),     # SRDP second run (Fig. 4e)
    ("prep_stats.py", HERE),        # dG-G conditional CDF maps, endurance statistics
    ("prep_ltpfit_cs.py", HERE),    # power-law (CrossSim form) fit of the cycle-averaged LTP/LTD
]

for script, cwd in STEPS:
    t0 = time.time()
    r = subprocess.run([sys.executable, os.path.join(cwd, script)], cwd=cwd, capture_output=True, text=True)
    status = "ok" if r.returncode == 0 else f"FAILED ({r.returncode})"
    print(f"{script:22s} {status:12s} {time.time() - t0:5.1f} s")
    if r.returncode:
        print(r.stdout[-2000:], r.stderr[-3000:])
        sys.exit(1)
print("all steps finished")
