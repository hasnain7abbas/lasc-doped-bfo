# CrossSim MNIST training — La-Sc BFO synapse

Started 9 Nov 2026, 22:45, on this laptop (i5-4210U, 2 cores, no GPU).

## What runs

| Arm | Meaning | Role |
|---|---|---|
| `ideal` | float64 weights, same network and update rule | paper |
| `device_nonlin` | CrossSim crossbar, measured P/D nonlinearity, no noise | paper |
| `device_wn` | nonlinearity + measured write noise (no read noise) | paper |
| `device_full` | + read noise σ = 0.03 (assumed, not measured) | supplementary; starts after `ideal` ends |

Network: 784-200-10, sigmoid hidden and output, squared-error loss, no bias, batch 1 (per-sample
outer-product update), lr 0.1, 40 epochs, full MNIST (60 000 train / 10 000 test). Every arm starts
from the same weights and sees the same sample order.

## Device parameters (`device_params.json`, from `extract_params.py`)

Data: `strict final la sc\la sc synaptic.xlsx`, sheet `15 -12`, 5 cycles × (50 P + 50 D).
Method: `Parameter_Extraction_v3_Fixed.ipynb` (power law, curve_fit, free endpoints).

| Parameter | Value |
|---|---|
| G_min / G_max | 0.2112 / 0.4280 µS (on/off 2.03) |
| α_P / α_D (avg curve) | 1.1909 (R² 0.9986) / 2.1165 (R² 0.9980) |
| σ_w P / D (cycle-to-cycle residual / ΔG) | 0.0253 / 0.0227 |
| σ_w P / D (v3 formula, for reference) | 0.0247 / 0.0274 |
| levels P / D, bits | 26 / 19, 4 bits |

The write noise sent to CrossSim is the residual of each step around the mean step at that pulse,
so the nonlinearity (already in the lookup table) is not counted twice. See `extraction_report.txt`
and `extraction_fits.png`.

## Corrections compared with `CrossSim_MNIST_FINAL_WORKING.ipynb`

1. **IndexError 101, root cause.** The notebook wrote the noise table on a CDF grid 0.005–0.995, but
   CrossSim indexes rows as round(u/step) from 0. The table now uses a 0–1 grid with quantiles at
   the bin centres, and CrossSim clamps indices as a safety net.
2. **Read noise was never applied.** CrossSim's default read-noise model is `"none"`, so
   `READ_NOISE = 0.03` did nothing. It is now applied (`alpha` model), and only in `device_full`.
3. **Ideal baseline was a different model** (PyTorch, softmax cross-entropy, momentum, batch 100).
   The ideal arm now uses the identical network, loss and per-sample update.
4. Initial weights were 0.01·randn; they are now uniform ±1/√fan_in, the same for all arms.
5. Each arm writes its own lookup tables, so parallel runs don't overwrite each other's files.

## Speed patch to CrossSim (≈10× faster)

`crosssim\cross-sim-2.0\...\cores\numeric_core.py` and `...\parameters\numeric_params.py`
(originals kept as `*.orig`):

- Rows whose input is zero (≈80 % of MNIST pixels) get a target update of exactly 0, so they now
  skip the lookup-table model.
- The single-lookup-table update is vectorised with `np.where` and flat indexing, using the same
  formula: `scale·mean_dG(w) + error(CDF, w)·sqrt(scale)`.
- Checked against the original: with noise off the weights are bit-identical after 300 updates;
  with noise on they agree within the original's seed-to-seed spread.
- Time per training sample: 65 ms → 5 ms (nonlinearity only), 9 ms (write noise), 18 ms (read noise).

## Files and progress

- `results\run_all.log` — overall progress; `results\<arm>\log.txt` — per-epoch accuracy.
- `results\<arm>\accuracy.json`, `checkpoint.pkl` — written after every epoch.
- When everything finishes: `accuracy_vs_epoch.csv` (Origin-ready), `results_summary.txt`
  (final / mean of last 5 / best), `accuracy_vs_epoch_preview.png`.

## If the laptop restarted or the run stopped

Run this again from this folder. Every arm resumes after its last finished epoch:

```
python run_all.py
```

The launcher keeps Windows from idle-sleeping while it runs. A closed lid or a manual Sleep still
pauses it; running `run_all.py` again afterwards continues from the checkpoints.
