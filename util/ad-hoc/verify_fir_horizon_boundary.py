"""Ad-hoc refuter check: pin the ARM A (FIR) shift-register recall cliff to K-1.

Self-contained (no import of the sibling PoC). Builds the exact newest-first tap
register [a(t), a(t-1), ..., a(t-K+1)] with an identity activation so taps[:,j]
== x(t-j) exactly, then tests EVERY integer lag straddling K-1 to confirm:
  - lag <= K-1: a tap column exists -> |corr| == 1.000
  - lag >= K:   no tap column        -> |corr| collapses to chance
This is the "targeted boundary check" referenced (but not committed) by the
findings under E2. Verifies the "hard cliff at exactly K-1" headline.

Author: Claude (refuter verification, for Paul Calnon)
Created: 2026-06-09
Status: ad-hoc - one-shot verification of the FIR horizon boundary claim.
"""

from __future__ import annotations

import numpy as np

SEED = 20260609
K = 35


def fir_taps_vectorized(a: np.ndarray, k: int) -> np.ndarray:
    a_pad = np.concatenate([np.zeros(k - 1, dtype=a.dtype), a])
    win = np.lib.stride_tricks.sliding_window_view(a_pad, k)
    return win[:, ::-1].copy()


def pearson_abs(out: np.ndarray, err: np.ndarray) -> float:
    o = out - out.mean()
    e = err - err.mean()
    denom = np.linalg.norm(o) * np.linalg.norm(e) + 1e-8
    return float(abs(float(o @ e) / denom))


def main() -> int:
    rng = np.random.default_rng(SEED)
    t = 1500
    x = rng.standard_normal(t)
    taps = fir_taps_vectorized(x, K)  # identity activation: taps[:,j] == x(t-j)
    print(f"K={K}: register holds taps j=0..{K - 1}; x(t-{K}) is unrepresentable")
    for lag in [29, 30, 31, 32, 33, 34, 35, 36]:
        tgt = np.zeros(t)
        tgt[lag:] = x[: t - lag]  # target = x(t-lag)
        if lag <= K - 1:
            c = pearson_abs(taps[:, lag], tgt)
            print(f"  lag {lag:2d}: exact tap col {lag:2d} -> |corr|={c:.4f}")
        else:
            best = max(pearson_abs(taps[:, j], tgt) for j in range(K))
            print(f"  lag {lag:2d}: NO tap col (> K-1) -> best in-reg |corr|={best:.4f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
