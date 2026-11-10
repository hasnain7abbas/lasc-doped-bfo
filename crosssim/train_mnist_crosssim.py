"""
Hardware-aware MNIST training on CrossSim V2.0 with the La-Sc device lookup tables.

  python train_mnist_crosssim.py --arm ideal|device_nonlin|device_full [--epochs 40]
                                 [--n-train 60000] [--n-test 10000] [--hidden 200]

Arms (same network, same initial weights, same sample order):
  ideal          float64 weights, plain SGD outer-product update (no device model)
  device_nonlin  CrossSim BALANCED crossbar, measured P/D response, no write/read noise
  device_wn      CrossSim BALANCED crossbar, measured P/D response + measured write noise (no read noise)
  device_full    CrossSim BALANCED crossbar, measured P/D response + write noise + read noise (read noise 0.03 is assumed, not measured)

Network 784-H-10, sigmoid hidden and output, squared-error delta, no bias, per-sample
updates (batch size 1, as an analog outer-product update). Every epoch is checkpointed in
results/<arm>/; rerunning the same command resumes after the last finished epoch.
"""
import argparse, json, os, sys, time, pickle
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", message=".*pkg_resources.*")
import numpy as np
from scipy.stats import norm

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "crosssim", "cross-sim-2.0"))

ap = argparse.ArgumentParser()
ap.add_argument("--arm", required=True, choices=["ideal", "device_nonlin", "device_wn", "device_full"])
ap.add_argument("--epochs", type=int, default=40)
ap.add_argument("--n-train", type=int, default=60000)
ap.add_argument("--n-test", type=int, default=10000)
ap.add_argument("--hidden", type=int, default=200)
ap.add_argument("--lr", type=float, default=0.1)
ap.add_argument("--seed", type=int, default=0)
ap.add_argument("--tag", default="")
ap.add_argument("--profile-samples", type=int, default=0, help="time N training samples and exit")
args = ap.parse_args()

dev = json.load(open(os.path.join(HERE, "device_params.json")))
G_min, G_max, N_pulses = dev["G_min"], dev["G_max"], int(dev["N_pulses"])
alpha_P, alpha_D = dev["alpha_P"], dev["alpha_D"]
sigma_w_P, sigma_w_D = dev["sigma_w_P"], dev["sigma_w_D"]
READ_NOISE = dev.get("read_noise_sigma", 0.03)
G_range = G_max - G_min

OUT = os.path.join(HERE, "results", args.arm + (("_" + args.tag) if args.tag else ""))
os.makedirs(OUT, exist_ok=True)
LOG = open(os.path.join(OUT, "log.txt"), "a", buffering=1, encoding="utf-8")
def log(s):
    s = time.strftime("%Y-%m-%d %H:%M:%S  ") + s
    print(s, flush=True); LOG.write(s + "\n")

# ---------------------------------------------------------------- lookup tables
LUT_N_BINS, LUT_N_CDF = 100, 101
def build_luts():
    tp = np.clip(1.0 - np.arange(N_pulses, dtype=float) / (N_pulses - 1), 0.0, 1.0)
    G_pot = G_min + G_range * (1.0 - tp ** alpha_P)
    G_dep = G_min + G_range * tp ** alpha_D
    G_bins = np.linspace(G_min, G_max, LUT_N_BINS)
    dG_P = np.interp(G_bins, G_pot[:-1], np.diff(G_pot))
    dG_D = np.interp(G_bins, G_dep[:-1][::-1], np.diff(G_dep)[::-1])
    # CrossSim indexes row k of the table with a uniform random number u via k = round(u / step),
    # so the CDF row vector must run 0..1 on a uniform grid (the old 0.005..0.995 grid produced
    # index 101 -> IndexError, and shifted the noise distribution). Row k holds the normal quantile
    # at the centre of the u-interval it covers (end rows cover half intervals).
    cdf_vec = np.linspace(0.0, 1.0, LUT_N_CDF)
    step = cdf_vec[1]
    q = cdf_vec.copy(); q[0] = step / 4; q[-1] = 1 - step / 4
    z = norm.ppf(q)
    z -= np.sum(z[:-1] * step) / 1.0 * 0   # (kept explicit: no re-centring, CrossSim subtracts its own mean)
    paths = {}
    for name, dG, sig in (("potentiation", dG_P, sigma_w_P), ("depression", dG_D, sigma_w_D)):
        M = dG[None, :] + z[:, None] * sig * G_range
        p = os.path.join(OUT, f"{name}_lut.csv")
        with open(p, "w") as f:
            f.write(f"{name} LUT, La-Sc power-law alpha_P={alpha_P:.4f} alpha_D={alpha_D:.4f}\n")
            f.write(",".join(f"{g*1e6:.8f}" for g in G_bins) + "\n")
            f.write(",".join(f"{c:.6f}" for c in cdf_vec) + "\n")
            for row in M:
                f.write(",".join(f"{v*1e6:.10f}" for v in row) + "\n")
        paths[name] = p
    return paths

# ---------------------------------------------------------------- cores
class IdealCore:
    def __init__(self, W): self.W = W.astype(np.float64).copy()
    def vmm(self, x): return x @ self.W
    def mvm(self, d): return self.W @ d
    def update(self, x, d, lr): self.W += lr * np.outer(x, d)
    def get(self): return self.W.copy()
    def put(self, W): self.W = W.copy()

class AnalogCore:
    def __init__(self, W, params):
        from cross_sim import MakeCore
        self.core = MakeCore(params=params)
        self.core.set_matrix(W.astype(np.float64))
    def vmm(self, x): return np.asarray(self.core.run_xbar_vmm(x), dtype=np.float64)
    def mvm(self, d): return np.asarray(self.core.run_xbar_mvm(d), dtype=np.float64)
    def update(self, x, d, lr): self.core.update_matrix(x, d, learning_rate=lr)
    def _bal(self):
        # locate the BalancedCore holding the two NumericCores (G+ and G- arrays)
        o, seen = self.core, 0
        while not hasattr(o, "core_pos"):
            o = getattr(o, "core"); seen += 1
            if seen > 5: raise RuntimeError("BalancedCore not found")
        return o
    def get(self):
        b = self._bal(); return {"pos": b.core_pos.matrix.copy(), "neg": b.core_neg.matrix.copy()}
    def put(self, m):
        b = self._bal(); b.core_pos.matrix = m["pos"].copy(); b.core_neg.matrix = m["neg"].copy()

def make_params(noise, read=False):
    from cross_sim import Parameters
    luts = build_luts()
    p = Parameters()
    p.numeric_params.useGPU = False
    p.algorithm_params.crossbar_type = "BALANCED"
    p.algorithm_params.sim_type = "NUMERIC"
    p.numeric_params.update_model = "DG_LOOKUP"
    p.numeric_params.dG_lookup.file_increasing = luts["potentiation"]
    p.numeric_params.dG_lookup.file_decreasing = luts["depression"]
    p.numeric_params.dG_lookup.Gmin_relative = 0.0
    p.numeric_params.dG_lookup.Gmax_relative = 1.0
    p.numeric_params.dG_lookup.disable_nonlinearity = False
    p.numeric_params.dG_lookup.disable_writenoise = not noise
    p.numeric_params.read_noise.sigma = READ_NOISE if read else 0.0
    # CrossSim ignores read_noise.sigma unless a read-noise model is selected (default "none"):
    # the old notebook's READ_NOISE = 0.03 was never applied. "alpha" = state-independent Gaussian.
    p.weight_error_params.noise_model = "alpha" if read else "none"
    for grp in (p.algorithm_params.weights, p.algorithm_params.row_update, p.algorithm_params.col_update):
        grp.maximum, grp.minimum = 1.0, -1.0
    return p

# ---------------------------------------------------------------- data
def load_mnist():
    cache = os.path.join(HERE, "data", "mnist.npz")
    if not os.path.exists(cache):
        from torchvision import datasets
        tr = datasets.MNIST(os.path.join(HERE, "data"), train=True, download=True)
        te = datasets.MNIST(os.path.join(HERE, "data"), train=False, download=True)
        np.savez_compressed(cache, xtr=tr.data.numpy(), ytr=tr.targets.numpy(),
                            xte=te.data.numpy(), yte=te.targets.numpy())
    d = np.load(cache)
    Xtr = d["xtr"].reshape(-1, 784).astype(np.float64) / 255.0
    Xte = d["xte"].reshape(-1, 784).astype(np.float64) / 255.0
    return Xtr[:args.n_train], d["ytr"][:args.n_train], Xte[:args.n_test], d["yte"][:args.n_test]

def sigmoid(z): return 1.0 / (1.0 + np.exp(-np.clip(z, -500, 500)))

# ---------------------------------------------------------------- main
Xtr, ytr, Xte, yte = load_mnist()
Ytr = np.eye(10)[ytr]
H = args.hidden

rng0 = np.random.default_rng(args.seed)
# Uniform +-1/sqrt(fan_in) start, identical for every arm, inside the [-1, 1] crossbar weight range
W1_0 = rng0.uniform(-1, 1, (784, H)) / np.sqrt(784)
W2_0 = rng0.uniform(-1, 1, (H, 10)) / np.sqrt(H)

state_path = os.path.join(OUT, "checkpoint.pkl")
res_path = os.path.join(OUT, "accuracy.json")

if args.arm == "ideal":
    c1, c2 = IdealCore(W1_0), IdealCore(W2_0)
else:
    NOISE = args.arm in ("device_wn", "device_full"); READ = args.arm == "device_full"
    params = make_params(noise=NOISE, read=READ)
    c1, c2 = AnalogCore(W1_0, params), AnalogCore(W2_0, params.copy() if hasattr(params, "copy") else make_params(noise=NOISE, read=READ))

def snapshot():
    return {"W1": c1.get(), "W2": c2.get()}

def restore(s):
    c1.put(s["W1"]); c2.put(s["W2"])

acc_hist, start_ep = [], 1
order_rng = np.random.default_rng(args.seed + 1)
if os.path.exists(state_path) and not args.profile_samples:
    with open(state_path, "rb") as f:
        st = pickle.load(f)
    restore(st["cores"]); acc_hist = st["acc"]; start_ep = len(acc_hist) + 1
    order_rng.bit_generator.state = st["order_rng"]; np.random.set_state(st["np_rng"])
    log(f"resumed {args.arm} after epoch {len(acc_hist)}")
else:
    np.random.seed(args.seed + 2)   # CrossSim draws its write/read noise from np.random

def evaluate():
    correct = 0
    for j in range(len(Xte)):
        a1 = sigmoid(c1.vmm(Xte[j]))
        correct += int(np.argmax(c2.vmm(a1)) == yte[j])
    return 100.0 * correct / len(Xte)

def train_sample(x, t, lr):
    z1 = c1.vmm(x); a1 = sigmoid(z1)
    z2 = c2.vmm(a1); a2 = sigmoid(z2)
    d2 = (a2 - t) * a2 * (1 - a2)
    d1 = c2.mvm(d2) * a1 * (1 - a1)
    c2.update(a1, -d2, args.lr)
    c1.update(x, -d1, args.lr)

if args.profile_samples:
    t0 = time.time()
    for i in range(args.profile_samples):
        train_sample(Xtr[i], Ytr[i], args.lr)
    dt = (time.time() - t0) / args.profile_samples
    t0 = time.time()
    for j in range(min(1000, len(Xte))):
        c2.vmm(sigmoid(c1.vmm(Xte[j])))
    de = (time.time() - t0) / min(1000, len(Xte))
    ep = dt * len(Xtr) + de * len(Xte)
    log(f"PROFILE {args.arm}: {dt*1e3:.2f} ms/train sample, {de*1e3:.2f} ms/test sample -> "
        f"{ep/60:.1f} min/epoch, {ep*args.epochs/3600:.1f} h for {args.epochs} epochs")
    sys.exit(0)

log(f"arm {args.arm} | 784-{H}-10 sigmoid, MSE, lr {args.lr}, batch 1 | train {len(Xtr)} test {len(Xte)} | "
    f"device G {G_min*1e6:.4f}-{G_max*1e6:.4f} uS, aP {alpha_P:.4f}, aD {alpha_D:.4f}, "
    f"sw P {sigma_w_P:.4f} D {sigma_w_D:.4f}, read {READ_NOISE if args.arm=='device_full' else 0}, write noise {'on' if args.arm in ('device_wn','device_full') else 'off'}")
if start_ep == 1:
    a0 = evaluate(); log(f"epoch  0  test {a0:6.2f} %  (untrained)")
for ep in range(start_ep, args.epochs + 1):
    t0 = time.time()
    order = order_rng.permutation(len(Xtr))
    for k, i in enumerate(order):
        train_sample(Xtr[i], Ytr[i], args.lr)
        if (k + 1) % 10000 == 0:
            log(f"  epoch {ep}: {k+1}/{len(Xtr)} samples, {(time.time()-t0)/60:.1f} min")
    acc = evaluate(); acc_hist.append(acc)
    with open(state_path + ".tmp", "wb") as f:
        pickle.dump({"cores": snapshot(), "acc": acc_hist, "order_rng": order_rng.bit_generator.state,
                     "np_rng": np.random.get_state()}, f)
    os.replace(state_path + ".tmp", state_path)
    json.dump({"arm": args.arm, "accuracy": acc_hist, "hidden": H, "lr": args.lr,
               "n_train": len(Xtr), "n_test": len(Xte), "device": {k: v for k, v in dev.items()
               if not isinstance(v, list)}}, open(res_path, "w"), indent=1)
    log(f"epoch {ep:2d}  test {acc:6.2f} %   ({(time.time()-t0)/60:.1f} min)")
log("done")
