"""Folder locations for every script in this package.

Set the environment variables below (or edit the defaults) once; nothing else in the code is machine-specific.

  LASC_RAW         raw measurement folder ("strict final la sc": la sc synaptic.xlsx, PUND folders, unidirectional IV, ...)
  LASC_XRD         raw XRD scans (*.ASC)
  LASC_WORK        scratch/output folder for intermediate CSVs, previews and logs  (default: ./work)
  LASC_ORIGIN_OUT  where the Origin projects (.opju) are saved                     (default: ./work/origin_figures)
  LASC_PAPER_FIG   where the assembled paper figures (.pptx) are written           (default: ./work/paper_figures)
  LASC_FIG1        Figure 1 folder (Blender renders, panels)                       (default: ./work/figure1)
"""
import os

PKG = os.path.dirname(os.path.abspath(__file__)).replace("\\", "/")
_env = lambda name, default: os.environ.get(name, default).replace("\\", "/")

PROJECT = _env("LASC_PROJECT", PKG + "/data")
RAW = _env("LASC_RAW", PROJECT + "/strict final la sc")
XRD_RAW = _env("LASC_XRD", PROJECT + "/xrds")
WORK = _env("LASC_WORK", PKG + "/work")
ORIGIN_OUT = _env("LASC_ORIGIN_OUT", WORK + "/origin_figures")
PAPER_FIG = _env("LASC_PAPER_FIG", WORK + "/paper_figures")
FIG1 = _env("LASC_FIG1", WORK + "/figure1")

for _d in (WORK, WORK + "/prep/csv"):
    os.makedirs(_d, exist_ok=True)
