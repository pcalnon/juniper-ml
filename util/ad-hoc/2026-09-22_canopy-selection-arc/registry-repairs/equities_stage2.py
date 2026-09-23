"""Item 11 stage 2: fit CascadeCorrelationNetwork on the stage-1 NPZs (JuniperCascor1).

The SAME bounded trainability probe as juniper-ml util/ad-hoc/2026-09-10_rank2_cascor_fit.py
(CONFIG, BOUNDED_EPOCHS, MAX_ROWS, seeded subsample, 2 threads, CPU) so the numbers are
comparable with the 2026-09-10/11 measurement recorded in canopy's model_registry.py. Only the
artifact directory differs. Scratch only.

The ``__main__`` guard is load-bearing: cascor's candidate pool uses a non-fork start method,
so its children re-import ``__main__``; without the guard every child re-runs the fit loop and
candidate training fails with "start a new process before ... bootstrapping phase".
"""

import os
import sys
import time
from pathlib import Path

os.environ.setdefault("OMP_NUM_THREADS", "2")
os.environ.setdefault("MKL_NUM_THREADS", "2")
os.environ.setdefault("CUDA_VISIBLE_DEVICES", "")

import numpy as np  # noqa: E402
import torch  # noqa: E402

CASCOR_SRC = Path("/home/pcalnon/Development/python/Juniper/juniper-cascor/src")
if str(CASCOR_SRC) not in sys.path:
    sys.path.insert(0, str(CASCOR_SRC))

from cascade_correlation.cascade_correlation import CascadeCorrelationNetwork  # noqa: E402

BOUNDED_EPOCHS = 60
CONFIG = {"max_iterations": 8, "output_epochs": BOUNDED_EPOCHS, "candidate_epochs": 40, "candidate_pool_size": 4, "generate_plots": False, "random_seed": 0}
MAX_ROWS = 4000


def main(art_dir: Path) -> int:
    for npz_path in sorted(art_dir.glob("*.npz")):
        arrays = np.load(npz_path)
        x_train = np.asarray(arrays["X_train"], dtype=np.float32)
        y_train = np.asarray(arrays["y_train"], dtype=np.float32)
        shape_before = x_train.shape
        if len(x_train) > MAX_ROWS:
            idx = np.random.default_rng(0).choice(len(x_train), MAX_ROWS, replace=False)
            x_train, y_train = x_train[idx], y_train[idx]
        x_val = arrays["X_val"].astype(np.float32)[:MAX_ROWS]
        y_val = arrays["y_val"].astype(np.float32)[:MAX_ROWS]
        net = CascadeCorrelationNetwork(input_size=int(x_train.shape[1]), output_size=int(y_train.shape[1]), **CONFIG)
        t0 = time.monotonic()
        history = net.fit(torch.from_numpy(x_train), torch.from_numpy(y_train), x_val=torch.from_numpy(x_val), y_val=torch.from_numpy(y_val), max_epochs=BOUNDED_EPOCHS, max_iterations=CONFIG["max_iterations"])
        fit_s = time.monotonic() - t0
        loss = history.get("train_loss") if isinstance(history, dict) else None
        with torch.no_grad():
            pred = net.forward(torch.from_numpy(x_train))
        top1 = float((pred.argmax(dim=1) == torch.from_numpy(y_train).argmax(dim=1)).float().mean().item())
        units = getattr(net, "hidden_units", None)
        first = f"{float(loss[0]):.6g}" if loss else "n/a"
        last = f"{float(loss[-1]):.6g}" if loss else "n/a"
        print(f"RESULT {npz_path.stem}: X_train{tuple(shape_before)} fit={fit_s:.1f}s hidden_units={len(units) if isinstance(units, list) else None} train_loss {first} -> {last} (n={len(loss) if loss else 0}) train_top1={top1:.4f}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main(Path(sys.argv[1])))
