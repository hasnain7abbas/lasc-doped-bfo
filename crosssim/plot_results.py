"""Collects results/<arm>/accuracy.json into accuracy_vs_epoch.csv (Origin-ready) and a preview PNG."""
import os, json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
ARMS = [("ideal", "Ideal (software)"),
        ("device_nonlin", "Device, nonlinearity only"),
        ("device_wn", "Device, nonlinearity + write noise"),
        ("device_full", "Device, + write + read noise (0.03, assumed)")]
data = {}
for arm, lab in ARMS:
    p = os.path.join(HERE, "results", arm, "accuracy.json")
    if os.path.exists(p):
        data[arm] = json.load(open(p))["accuracy"]
n = max((len(v) for v in data.values()), default=0)
with open(os.path.join(HERE, "accuracy_vs_epoch.csv"), "w") as f:
    f.write("epoch," + ",".join(a for a, _ in ARMS if a in data) + "\n")
    for e in range(n):
        f.write(str(e + 1) + "," + ",".join(f"{data[a][e]:.2f}" if e < len(data[a]) else ""
                                              for a, _ in ARMS if a in data) + "\n")
plt.rcParams.update({"font.family": "Times New Roman", "font.weight": "bold", "font.size": 14,
                     "axes.linewidth": 2, "axes.labelweight": "bold"})
fig, ax = plt.subplots(figsize=(7, 5.5))
mk = {"ideal": "s", "device_nonlin": "o", "device_wn": "^", "device_full": "v"}
col = {"ideal": "k", "device_nonlin": "r", "device_wn": "b", "device_full": "g"}
for arm, lab in ARMS:
    if arm in data:
        a = data[arm]
        ax.plot(np.arange(1, len(a) + 1), a, marker=mk[arm], color=col[arm], ms=5, lw=1.8,
                label=f"{lab} ({a[-1]:.2f} %)")
ax.set_xlabel("Training epoch"); ax.set_ylabel("Accuracy (%)")
ax.set_ylim(0, 100); ax.set_xlim(0, max(n, 1) + 1)
ax.tick_params(direction="in", width=2)
ax.legend(frameon=False, fontsize=11, loc="lower right")
plt.tight_layout(); plt.savefig(os.path.join(HERE, "accuracy_vs_epoch_preview.png"), dpi=200)
lines = ["CrossSim MNIST, 784-200-10 sigmoid, MSE, lr 0.1, batch 1, 60k train / 10k test",
         f"{'arm':<48}{'final':>9}{'mean last 5':>13}{'best':>9}{'epochs':>8}"]
for arm, lab in ARMS:
    if arm in data:
        a = data[arm]
        lines.append(f"{lab:<48}{a[-1]:8.2f}%{np.mean(a[-5:]):12.2f}%{max(a):8.2f}%{len(a):8d}")
if "ideal" in data and "device_wn" in data:
    lines.append(f"\nloss vs ideal (mean last 5): nonlinearity {np.mean(data['ideal'][-5:])-np.mean(data.get('device_nonlin', [np.nan])[-5:]):.2f} pts, "
                 f"nonlinearity + write noise {np.mean(data['ideal'][-5:])-np.mean(data['device_wn'][-5:]):.2f} pts")
open(os.path.join(HERE, "results_summary.txt"), "w", encoding="utf-8").write("\n".join(lines) + "\n")
print("\n".join(lines))
