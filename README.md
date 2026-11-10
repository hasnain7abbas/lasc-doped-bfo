# La 7.5 %–Sc 1 % co-doped BiFeO₃ memristive synapse — measurement, analysis and simulation code

Code accompanying the paper *"Reduced-leakage (La, Sc) co-doped BiFeO₃ memristive synapse with statistically
characterized analog weight updates"* ([[authors, journal, DOI]]). It covers every step from the instrument to the
figures:

```
measurement_scripts/   Keithley 2602 TSP/Lua protocols (I–V, EPSC, PPF, SDDP, LTP/LTD, retention, ...)
analysis/              raw data -> tidy CSV tables (system Python): synaptic metrics, PUND, conduction,
                       XRD offset/peak fits/lattice parameters, ΔG–G statistics, power-law fit
origin_plots/          OriginPro 2024 scripts that draw and save every graph (.opju) from those tables
crosssim/              device-parameter extraction and hardware-aware MNIST training in CrossSim 2.0
figures/               assembly of the paper figures (PowerPoint, editable Origin objects) and Fig. 6
config.py              the only place where folders are defined
```

## 1. Set-up

Python ≥ 3.10 with `pip install -r requirements.txt`. Origin steps need **OriginPro 2024** (its embedded Python);
figure assembly needs **Microsoft PowerPoint** (COM, Windows). The CrossSim step needs CrossSim 2.0 (see 4).

Point the code at the raw data (folder names as delivered with the data set):

```bash
set LASC_RAW=D:\data\strict final la sc      # la sc synaptic.xlsx, PUND folders, unidirectional IV, *.opju, *.pptx
set LASC_XRD=D:\data\xrds                    # pure bfo.ASC, la.ASC, sc.ASC, la sc.ASC
```

All outputs go to `work/` unless `LASC_WORK` is set (see `config.py`). Nothing is written into the raw-data folder.

## 2. Data preparation (system Python)

```bash
python analysis/run_prep.py
```

Runs, in order: `prep_all` (synaptic workbook, PUND, I–V, endurance), `prep_pe` (P–E loops), `prep_v2`
(J–E smoothing, PUND metrics ΔPr/PC/LC, EPSC, SDDP), `prep_v3` (SNDP, retention), `prep_v4` (log J–log E
two-region fits), `xrd/prep_xrd` + `xrd/fix_pt` (instrument offset −0.044°, pseudo-Voigt (104)/(110) fits,
lattice parameters, Pt(111) removal), `prep_stats` (ΔG–G conditional CDF maps, n = 245 updates per polarity;
endurance CV) and `prep_ltpfit_cs` (power-law fit in the CrossSim form, α_P = 1.191, α_D = 2.117).
Each table is listed with its source sheet and settings in `work/prep/manifest*.json`.

The P–E loops are stored as Origin objects inside `ferro plots.pptx`; `origin_plots/extract_pe/` extracts them
once into `work/pe_csv` (OriginPro required) before `prep_pe` runs.

## 3. Graphs (OriginPro 2024)

```powershell
powershell -File origin_plots/run_origin.ps1 -py origin_plots/plot2_syn.py
```

`run_origin.ps1` starts Origin through COM and runs a script with `run -pyf`. Scripts: `plot2_ferro`, `plot2_iv`,
`plot2_syn`, `plot3_cond`, `plot3_other`, `plot3_schemes`, `plot4_xrd`, `plot5_stats` (ΔG–G maps), `uni_log`,
`ltp_fit_cs` (Fig. 5c), `fig1_iv` (Fig. 1c); `paper_copies` makes the title-free copies used in the paper; `fig2_colours` gives Fig. 2c, d the film colours of Fig. 2a, b;
`acc_epoch` draws Fig. 6c from `crosssim/accuracy_vs_epoch.csv`.
Style: Times New Roman bold, 28 pt, 4 pt frame. `oplib.py` holds the shared helpers.

## 4. Device parameters and network training (CrossSim 2.0)

```bash
cd crosssim
git clone --branch v2.0 https://github.com/sandialabs/cross-sim.git crosssim/cross-sim-2.0
cd crosssim/cross-sim-2.0 && git apply ../../crosssim_v2.0_patch.diff && cd ../..
python extract_params.py      # -> device_params.json (G_min/G_max, α_P/α_D, σ_w) from the 5 LTP/LTD cycles
python run_all.py             # ideal / nonlinearity / nonlinearity + write noise (+ read noise), 40 epochs, resumable
python plot_results.py        # -> accuracy_vs_epoch.csv
```

`crosssim_v2.0_patch.diff` vectorizes the lookup-table update and skips zero-input rows (≈10× faster; identical
weights without noise) and clamps the lookup-table index. MNIST is downloaded by torchvision on first use
(`crosssim/data`). `crosssim/README.md` lists the corrections relative to the earlier notebook.
The results of the paper's run are included: `crosssim/accuracy_vs_epoch.csv` (test accuracy per epoch for the four
cases) and `crosssim/results_summary.txt` (final, last-five-epoch mean and best accuracy).

## 5. Figures

```bash
python figures/make_spec.py                                   # layout of Figs 2–5 and S1–S4 (17.5 cm wide)
powershell -File figures/build_figures.ps1 -only "Figure 5"   # Origin Copy Page -> editable objects in PowerPoint
python figures/build_figure6_network.py --hidden 200          # Fig. 6(a, b) network and crossbar schematic
python figures/fig6c_geom.py                                  # crop/size of the Origin accuracy panel
powershell -File figures/paste_fig6c.ps1                      # Fig. 6(c) pasted from Origin, preview exported
python figures/figure1/build_figure1.py                       # Fig. 1 from the Blender renders
```

## Reproducibility notes

* Film thickness: 580 nm (SEM) for La-Sc; 0.5 µm assumed for the other films (`prep_v2.py`, `D_UM`).
* Electrode area 3.14 × 10⁻⁴ cm² (200 µm Pt dots).
* SRDP 0.5 Hz (second run) is excluded: its pre-stimulus conductance is 10× lower than all others (see paper).
* The first ΔG after each polarity reversal is excluded from the update statistics (reversal transient).

## Licence and citation

Code: MIT licence ([LICENSE](LICENSE)). Please cite the paper ([CITATION.cff](CITATION.cff)). CrossSim is © Sandia
National Laboratories and is not redistributed here; MNIST is from LeCun et al.
