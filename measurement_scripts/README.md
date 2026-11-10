# Measurement scripts (Keithley 2602 SMU, Test Script Processor / Lua 5.0)

All electrical tests were run on a Keithley 2602 in a two-probe configuration (bias on the Pt top electrode, ITO
grounded) with scripts loaded through Test Script Builder. The files here are the author's protocol scripts, copied
unchanged. **Parameter values inside the files are those of the last device they were used on** (several different
films were measured with the same functions); the values used for the La 7.5 %-Sc 1 % device are listed below and are
also printed by the scripts at the top of every raw data block (`# PARAMS: ...`, `# RESET: ...`), so each data file
documents its own settings.

## La-Sc device: common settings

| Setting | Value |
|---|---|
| Write (potentiation) | +15 V, 100 ms |
| Write (depression) | −12 V, 100 ms |
| Read | 1 V (EPSC also at 0.25, 0.5, 0.75 V) |
| Reset before each test | 5 × (−12 V, 0.1 s), then 90 s rest, baseline read at 1 V |
| Read delay after a write | 0.05 s |

## Test → script map

| Test (paper figure) | File | Function | Header printed in the data | Status |
|---|---|---|---|---|
| Bipolar I–V (Fig. 1c) | `protocols_retention_endurance.lua` (single channel) or `protocols_LTP_LTD_SNDP.lua` (dual channel) | top-level sweep block (loop limits edited to 0 → +15 → 0 → −12 → 0 V, 0.5 V steps) | `Sweep Complete.` | matches; which of the two files was used is not recorded in the data |
| EPSC, read voltage (Fig. 4a, b) | `protocols_core_IV_EPSC_PPF_SDDP_SRDP.lua` | `run_EPSC` | `Status: Measuring Baseline...` | matches |
| PPF (Fig. 4c, d) | `protocols_core_IV_EPSC_PPF_SDDP_SRDP.lua` | `run_PPF` | `# TEST: PPF ...`, `# RESULT: A1=... A2=... PPF_index=...` | matches |
| SDDP train (Fig. 4f, g) | `protocols_core_IV_EPSC_PPF_SDDP_SRDP.lua` | `run_SDDP` | `# TEST: SDDP (potentiation vs pulse number)` | matches |
| SDDP relaxation (Fig. 4h) | `protocols_core_IV_EPSC_PPF_SDDP_SRDP.lua` | `run_SDDP_Decay` | `# TEST: SDDP-Decay` (1500 reads, 0.1 s) | matches |
| LTP/LTD, 5 cycles (Fig. 6b, c) | `protocols_LTP_LTD_SNDP.lua` | `run_LTP_LTD` | `Status: LTP/LTD for 5 cycles` | matches (50 + 50 pulses; 100 ms write + 50 ms read gap) |
| Retention (Fig. 5e) | `protocols_retention_endurance.lua` | `run_Retention` | `BEGIN_RETENTION N ... END_RETENTION` | matches |
| SRDP (Fig. 4e) | — | — | `# TEST: SRDP, fixed pulse count` / `ON-time constant at 3 s` | **version used not in this folder** (`run_SRDP` here is an earlier variant) |
| SNDP (Fig. 5a–d) | — | — | `SNDP TEST` … `BEGIN_TEST` | **version used not in this folder** (`run_SNDP` in `protocols_LTP_LTD_SNDP.lua` is related) |
| Multilevel states (Fig. 6f) | — | — | `Multi-Level Burst Programming` | **not in this folder** |
| Endurance, 2500 cycles (Fig. 6g, h) | — | — | `Pre-run reset: 5 pulses at -12V` / `Endurance: +15V x50 / -12V x50, read 1V` | **version used not in this folder**; `run_Endurance1500` here applies 5 + 5 pulses per cycle. The x50 in the printed header is a label, see the paper (5 + 5 pulses per cycle) |
| STDP | `protocols_STDP_SRDP_retention_v2.lua` | `run_STDP_Curve` | — | not used in the paper |

[[Author: add the SRDP, SNDP, multilevel and endurance scripts that produced the La-Sc data before publishing, and
correct the endurance header string.]]

## How to run

Open the file in Keithley Test Script Builder, set the parameters at the top of the function to the values above, load
the script, then call the function from the TSP prompt, e.g. `run_PPF(15, 1, 0.1, 0.05, 5)`. Copy the printed output
into the raw-data workbook; the analysis scripts read the numeric blocks below each header.
