"""
Runs the full 40-epoch CrossSim MNIST study and plots it when done. Resumable: run again after a
crash/reboot and every arm continues from its last finished epoch.

  python run_all.py

Paper arms (in parallel):  ideal, device_nonlin, device_wn
Supplementary arm:         device_full (adds assumed read noise 0.03), starts when 'ideal' finishes
Progress: results/<arm>/log.txt ; overall: results/run_all.log
"""
import os, subprocess, sys, time, json
HERE = os.path.dirname(os.path.abspath(__file__))
PY = sys.executable
LOG = os.path.join(HERE, "results", "run_all.log")
os.makedirs(os.path.dirname(LOG), exist_ok=True)
EPOCHS = 40

def log(s):
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(time.strftime("%Y-%m-%d %H:%M:%S  ") + s + "\n")

def done(arm):
    p = os.path.join(HERE, "results", arm, "accuracy.json")
    return os.path.exists(p) and len(json.load(open(p))["accuracy"]) >= EPOCHS

def start(arm):
    out = open(os.path.join(HERE, "results", f"{arm}.stdout.txt"), "a", encoding="utf-8")
    env = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONWARNINGS="ignore")
    log(f"start {arm}")
    return subprocess.Popen([PY, os.path.join(HERE, "train_mnist_crosssim.py"), "--arm", arm,
                             "--epochs", str(EPOCHS)], cwd=HERE, stdout=out, stderr=subprocess.STDOUT, env=env)

log(f"run_all launched (pid {os.getpid()})")
# Ask Windows not to idle-sleep while this process runs (released automatically when it exits;
# no power settings are changed). A closed lid or manual Sleep still sleeps the laptop.
try:
    import ctypes
    ctypes.windll.kernel32.SetThreadExecutionState(0x80000000 | 0x00000001)  # ES_CONTINUOUS | ES_SYSTEM_REQUIRED
    log("idle-sleep blocked for the duration of the run")
except Exception as e:
    log(f"could not block idle sleep: {e}")
queue = ["device_full"]
running = {a: start(a) for a in ["device_nonlin", "device_wn", "ideal"] if not done(a)}
if "ideal" not in running and not done("device_full"):
    running["device_full"] = start(queue.pop(0))
retries = {}
while running:
    time.sleep(30)
    for arm, p in list(running.items()):
        rc = p.poll()
        if rc is None:
            continue
        del running[arm]
        if done(arm):
            log(f"finished {arm}")
            if queue:
                nxt = queue.pop(0)
                if not done(nxt):
                    running[nxt] = start(nxt)
        else:
            retries[arm] = retries.get(arm, 0) + 1
            log(f"{arm} exited with code {rc} before finishing (retry {retries[arm]})")
            if retries[arm] <= 3:
                running[arm] = start(arm)   # resumes from its checkpoint
log("all arms finished, plotting")
subprocess.call([PY, os.path.join(HERE, "plot_results.py")], cwd=HERE)
log("run_all done")
