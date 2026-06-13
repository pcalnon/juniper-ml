"""
Numpy-only PoC for the "P6" design: a P4-FIR FROZEN hidden cascade feeding a
TRAINED, recurrent OUTPUT MAP that is a HIDDEN MLP (a true NARX network), rather
than P5's single self-recurrent output neuron.

WHY P6 EXISTS.  The P5 evaluation (verify_p5_recurrent_output_eval.py /
JUNIPER_RECURSE_DELAY_LINE_NODE_DESIGN_EVAL_2026-06-09.md P5 update) showed that a
*single* self-recurrent output node CANNOT lift the star-free / no-count ceiling:
parity o(t)=XOR(x(t),o(t-1)) needs the second-order cross-term x(t).o(t-1), and a
single linear-threshold neuron cannot represent XOR (Minsky & Papert 1969). That
doc explicitly flagged the ONE untested escape: "A richer output map -- a hidden
MLP making it a true NARX net -- could clear the bar, but that is a recurrent
sub-network, not 'a recurrent output layer,' and would warrant a separate
proposal."  P6 IS that separate proposal, tested here.

ARCHITECTURE (the only change from P5 is the output MAP becomes a 2-layer MLP):

    FIR drive (frozen, output-state-blind):  h(t) = [x(t), x(t-1), ..., x(t-K_h+1)]
    feedback state:                          o_hist(t) = [o(t-1), ..., o(t-K_fb)]
    HIDDEN MLP layer (the NEW part):         z(t) = tanh( Wih . h(t) + Wfh . o_hist(t) + bh )   # (Hd,)
    OUTPUT:                                  o(t) = Wo . z(t) + bo                              # scalar

The fed-back outputs o(t-k) enter the SAME hidden layer as the input features, so
the hidden units CAN form the multiplicative x(t).o(t-1) interaction (a 2-layer
MLP represents XOR).  This is precisely the NARX-with-hidden-MLP-output-map whose
computational universality is proven by Siegelmann, Horne & Giles 1997 (NARX <=>
fully-recurrent net, REQUIRES an MLP output map) -- the universality that does
*not* transfer to P5's single-neuron output.

The hidden cascade stays FIR-FROZEN (output-state-blind, matches cascor
_compute_hidden_outputs which never reads any output; cascade_correlation.py
:1942-1946), so live recurrence exists ONLY in the trained output map, trained by
BACKPROPAGATION-THROUGH-TIME over the window.  cascor's output today is a bare
static affine map (output = matmul(output_input, output_weights) + output_bias;
cascade_correlation.py:1979; train_output_layer retrains a stock nn.Linear each
round, :1986) -- so P6, like P5, is a genuinely new TRAINING MODE for cascor;
the question is only whether the richer (MLP, multi-hidden-unit) recurrent output
lifts the expressivity class P5 could not.

DECISIVE TEST (mirrors P5's PE7).  Train the recurrent MLP output on running
parity from ONE Bernoulli stream, FREEZE all weights, evaluate on a DISJOINT
stream.  If P6 truly COMPUTES parity (lifts the ceiling), held-out accuracy stays
high.  If it only memorized finite-sample correlation, it collapses to the
majority-class floor (~0.50) -- the same collapse P5 showed.  This is the single
number that answers "does a hidden-MLP recurrent output map break the ceiling?".

METHOD / anti-hallucination: numpy-only, seed-fixed, deterministic.  The BPTT
gradient is checked against central finite differences as a HARD ASSERT (P6E0)
before any training result is trusted -- same discipline as P5's PE3.  Every code
claim about cascor cites file:line against the live tree; the impossibility
results are the literature's (Giles 1995 / Kremer 1996 / Knorozova & Ronca 2024 /
Minsky & Papert 1969 / Siegelmann-Horne-Giles 1997), not this PoC's -- the PoC
shows learn/GENERALIZE-or-not, which is consistent with (not a proof of) the
ceiling.

Project:    Juniper ML Research Platform -- juniper-recurse (OQ-4 model-pick PoC)
Sub-Project: recurrent Cascade-Correlation -- P6 (NARX hidden-MLP recurrent output)
Application: ad-hoc design-evaluation harness
Author:     Paul Calnon
Version:    0.1.0
License:    MIT License
"""

from __future__ import annotations

import datetime as _dt
import sys
import time

import numpy as np

# --------------------------------------------------------------------------- #
SEED = 20260612
RNG = np.random.default_rng(SEED)

# Frozen FIR hidden depth (the P4-FIR embedding dim; design ~35 -- matches P5).
K_H_DEFAULT = 35
# Output feedback order K (number of o(t-k) taps fed back into the MLP).
K_FB_DEFAULT = 8
# Hidden-MLP width (the NEW capacity P6 adds over P5's single output neuron).
HID_DEFAULT = 16

EQUITIES_NPZ = (
    "/home/pcalnon/Development/python/Juniper/juniper-data/"
    "juniper_data/data/equities-1.0.0-6db8f4eb77108875.npz"
)


def _rec(label: str, msg: str) -> None:
    print(f"[{label}] {msg}", flush=True)


# --------------------------------------------------------------------------- #
# FIR feature basis h(t) -- the FROZEN P4-FIR cascade output (reused, identical
# newest-first semantics to the P5 PoC's fir_features).  OUTPUT-STATE-BLIND.
# --------------------------------------------------------------------------- #
def fir_features(x_stream: np.ndarray, K_h: int) -> np.ndarray:
    T = x_stream.shape[0]
    xpad = np.concatenate([np.zeros(K_h - 1, dtype=np.float64), x_stream.astype(np.float64)])
    win = np.lib.stride_tricks.sliding_window_view(xpad, K_h)  # (T, K_h) ascending
    return win[:, ::-1].copy()  # newest-first: col0 = x(t), col1 = x(t-1), ...


def fir_features_multi(X_seq: np.ndarray, K_h: int) -> np.ndarray:
    cols = [fir_features(X_seq[:, j], K_h) for j in range(X_seq.shape[1])]
    return np.concatenate(cols, axis=1)


# --------------------------------------------------------------------------- #
# Correlation objective (Fahlman |Pearson|) + helpers -- reused from P5 PoC.
# --------------------------------------------------------------------------- #
def pearson_abs(out: np.ndarray, err: np.ndarray) -> float:
    o = out - out.mean()
    e = err - err.mean()
    denom = np.linalg.norm(o) * np.linalg.norm(e) + 1e-8
    return float(abs(float(o @ e) / denom))


def signed_pearson(out: np.ndarray, err: np.ndarray) -> float:
    o = out - out.mean()
    e = err - err.mean()
    denom = np.linalg.norm(o) * np.linalg.norm(e) + 1e-8
    return float((o @ e) / denom)


def standardize(X: np.ndarray) -> np.ndarray:
    mu = X.mean(axis=0, keepdims=True)
    sd = X.std(axis=0, keepdims=True)
    sd[sd < 1e-8] = 1.0
    return (X - mu) / sd


def binary_accuracy(pred: np.ndarray, target_pm1: np.ndarray) -> float:
    return float(np.mean(np.sign(pred) == np.sign(target_pm1)))


def _yyyymmdd_to_ordinal(dates: np.ndarray) -> np.ndarray:
    y, m, d = dates // 10000, (dates // 100) % 100, dates % 100
    return np.fromiter(
        (_dt.date(int(yy), int(mm), int(dd)).toordinal() for yy, mm, dd in zip(y, m, d)),
        dtype=np.int64,
        count=len(dates),
    )


# =========================================================================== #
# P6 PARAMETERS bundle.  A 2-layer recurrent MLP output map.
#   Wih : (Hd, Dh)  input->hidden     (Dh = FIR drive dim)
#   Wfh : (Hd, K)   feedback->hidden  (K  = feedback order; THIS is what lets the
#                                       hidden layer build x(t).o(t-k) cross-terms)
#   bh  : (Hd,)     hidden bias
#   Wo  : (Hd,)     hidden->output
#   bo  : scalar    output bias
# =========================================================================== #
class P6Params:
    __slots__ = ("Wih", "Wfh", "bh", "Wo", "bo")

    def __init__(self, Wih, Wfh, bh, Wo, bo):
        self.Wih = Wih
        self.Wfh = Wfh
        self.bh = bh
        self.Wo = Wo
        self.bo = float(bo)

    def copy(self) -> "P6Params":
        return P6Params(self.Wih.copy(), self.Wfh.copy(), self.bh.copy(), self.Wo.copy(), self.bo)


def p6_init(Dh: int, K: int, Hd: int, *, w_scale: float | None = None, v_scale: float = 0.3) -> P6Params:
    if w_scale is None:
        w_scale = 1.0 / np.sqrt(Dh)
    Wih = RNG.standard_normal((Hd, Dh)) * w_scale
    Wfh = RNG.standard_normal((Hd, K)) * v_scale  # feedback weights start modest
    bh = np.zeros(Hd)
    Wo = RNG.standard_normal(Hd) * (1.0 / np.sqrt(Hd))
    bo = 0.0
    return P6Params(Wih, Wfh, bh, Wo, bo)


def p6_rollout(H: np.ndarray, p: P6Params):
    """Forward rollout of the recurrent MLP output. Returns (o, Z, A) where
    o:(T,) outputs, Z:(T,Hd) hidden pre-activations, A:(T,Hd) hidden activations.
    o(t-k)=0 for t-k<0. The input->hidden drive H@Wih.T is precomputed; the
    feedback (hence the recurrence) is sequential."""
    T = H.shape[0]
    Hd = p.Wo.shape[0]
    K = p.Wfh.shape[1]
    drive = H @ p.Wih.T + p.bh  # (T, Hd) feed-forward (output-state-blind) drive
    o = np.zeros(T)
    Z = np.zeros((T, Hd))
    A = np.zeros((T, Hd))
    hist = np.zeros(K)  # hist[k-1] = o(t-k), newest at idx0
    for t in range(T):
        z = drive[t] + p.Wfh @ hist  # (Hd,)  -- feedback enters the HIDDEN layer
        a = np.tanh(z)
        ot = float(p.Wo @ a + p.bo)
        Z[t] = z
        A[t] = a
        o[t] = ot
        hist[1:] = hist[:-1]
        hist[0] = ot
    return o, Z, A


def _bptt(H: np.ndarray, p: P6Params, dL_do_direct: np.ndarray):
    """Shared reverse-mode BPTT core. Given the DIRECT dL/do(t) (the loss's
    explicit dependence on each output, NOT through the recurrence), returns the
    parameter gradients (gWih, gWfh, gbh, gWo, gbo) by unrolling the feedback.

    Recurrence: o(t)=Wo.a(t)+bo; a(t)=tanh(z(t)); z(t)=drive(t)+Wfh.o_hist(t),
    o_hist(t)[k-1]=o(t-k). o(t) influences future via o(t+k) through Wfh[:,k-1].
    adj_o(t) = dL_do_direct(t) + sum_k (adj_z(t+k) . Wfh[:,k-1])
    adj_z(t) = (Wo * adj_o(t)) * (1-a(t)^2)   # back through Wo then tanh
    """
    T, Hd = H.shape[0], p.Wo.shape[0]
    K = p.Wfh.shape[1]
    o, Z, A = p6_rollout(H, p)
    dtanh = 1.0 - A * A  # (T, Hd)
    adj_o = np.zeros(T)
    adj_z = np.zeros((T, Hd))
    for t in range(T - 1, -1, -1):
        s = dL_do_direct[t]
        kmax = min(K, T - 1 - t)
        for k in range(1, kmax + 1):
            s += float(adj_z[t + k] @ p.Wfh[:, k - 1])
        adj_o[t] = s
        adj_z[t] = (p.Wo * adj_o[t]) * dtanh[t]
    # parameter grads
    gWo = A.T @ adj_o  # (Hd,)
    gbo = float(adj_o.sum())
    drive = H @ p.Wih.T + p.bh  # noqa: F841 (kept for clarity; not needed below)
    gWih = adj_z.T @ H  # (Hd, Dh)
    gbh = adj_z.sum(axis=0)  # (Hd,)
    # feedback weights: z(t) += Wfh @ o_hist(t); d z(t)[i]/d Wfh[i,k-1] = o(t-k)
    gWfh = np.zeros((Hd, K))
    for t in range(T):
        for k in range(1, K + 1):
            if t - k >= 0:
                gWfh[:, k - 1] += adj_z[t] * o[t - k]
    return o, (gWih, gWfh, gbh, gWo, gbo)


def p6_mse_loss_and_bptt(H, target, p: P6Params):
    """L = mean (o(t)-target(t))^2 + analytic BPTT (supervised; cascor-faithful
    output training is MSE, cascade_correlation.py:2018)."""
    T = H.shape[0]
    o, _z, _a = p6_rollout(H, p)
    diff = o - target
    L = float(np.mean(diff * diff))
    dL_do_direct = (2.0 / T) * diff
    _o, grads = _bptt(H, p, dL_do_direct)
    return L, grads


def p6_corr_loss_and_bptt(H, residual, p: P6Params):
    """L = -|corr(o, residual)| + analytic BPTT (Fahlman objective, for residual
    fitting / horizon probes). Only the DIRECT dL/do term differs from MSE."""
    T = H.shape[0]
    o, _z, _a = p6_rollout(H, p)
    r = signed_pearson(o, residual)
    L = -abs(r)
    oc = o - o.mean()
    e = residual - residual.mean()
    no = np.linalg.norm(oc) + 1e-12
    ne = np.linalg.norm(e) + 1e-12
    dabs = 1.0 if r >= 0 else -1.0
    dr_do = dabs * ((e / (no * ne)) - (oc * (oc @ e)) / (no**3 * ne))
    dL_do_direct = -dr_do
    _o, grads = _bptt(H, p, dL_do_direct)
    return L, grads


def _flatten(grads):
    gWih, gWfh, gbh, gWo, gbo = grads
    return np.concatenate([gWih.ravel(), gWfh.ravel(), gbh.ravel(), gWo.ravel(), [gbo]])


def _apply(p: P6Params, grads, lr: float, *, fb_clip: float):
    gWih, gWfh, gbh, gWo, gbo = grads
    p.Wih -= lr * gWih
    p.Wfh -= lr * gWfh
    p.bh -= lr * gbh
    p.Wo -= lr * gWo
    p.bo -= lr * gbo
    np.clip(p.Wfh, -fb_clip, fb_clip, out=p.Wfh)  # keep recurrence bounded


def train_p6_output(
    H: np.ndarray,
    target: np.ndarray,
    K_fb: int,
    Hd: int,
    *,
    mode: str = "mse",
    epochs: int = 600,
    lr: float = 0.05,
    n_restart: int = 6,
    fb_clip: float = 1.5,
    grad_clip: float = 5.0,
):
    """Train the recurrent MLP output by BPTT. Multi-restart; returns best
    (|corr|, P6Params). mode='mse' fits target by MSE; mode='corr' maximizes
    |corr|. GENEROUS capacity (Hd hidden units, n_restart) so any failure on
    parity is a representational ceiling, not under-fitting."""
    Dh = H.shape[1]
    best = None  # (score, params)
    for _ in range(n_restart):
        p = p6_init(Dh, K_fb, Hd)
        for _ep in range(epochs):
            if mode == "mse":
                _L, grads = p6_mse_loss_and_bptt(H, target, p)
            else:
                _L, grads = p6_corr_loss_and_bptt(H, target, p)
            gn = float(np.linalg.norm(_flatten(grads)))
            if gn > grad_clip:
                sc = grad_clip / (gn + 1e-12)
                grads = tuple(g * sc for g in grads)
            _apply(p, grads, lr, fb_clip=fb_clip)
        o, _z, _a = p6_rollout(H, p)
        ac = pearson_abs(o, target)
        if best is None or ac > best[0]:
            best = (ac, p.copy())
    return best


# --------------------------------------------------------------------------- #
# Task builders (parity / counting) -- identical semantics to the P5 PoC.
# --------------------------------------------------------------------------- #
def make_bits(T: int) -> tuple[np.ndarray, np.ndarray]:
    bits = RNG.integers(0, 2, size=T).astype(np.float64)
    return bits, bits * 2.0 - 1.0


def parity_last_m(bits: np.ndarray, m: int) -> np.ndarray:
    T = bits.shape[0]
    par = np.zeros(T)
    for t in range(T):
        lo = max(0, t - m + 1)
        par[t] = (bits[lo : t + 1].sum() % 2) * 2 - 1
    return par


def running_parity(bits: np.ndarray) -> np.ndarray:
    """o(t)=XOR over all bits up to t == o(t)=XOR(x(t),o(t-1)). The crux task."""
    return (np.cumsum(bits) % 2) * 2 - 1


def mod3_count(bits: np.ndarray) -> np.ndarray:
    cnt = (np.cumsum(bits) % 3).astype(np.float64)
    return cnt - cnt.mean()


# =========================================================================== #
# P6E0  GRADIENT CHECK (HARD ASSERT) -- run FIRST, before trusting training.
# =========================================================================== #
def exp_P6E0() -> None:
    global RNG
    RNG = np.random.default_rng(SEED + 7)
    T, K_h, K_fb, Hd = 40, 6, 3, 5
    bits, X = make_bits(T)
    H = fir_features(X, K_h)
    target = running_parity(bits)
    p = p6_init(H.shape[1], K_fb, Hd)

    for mode, fn in (("mse", p6_mse_loss_and_bptt), ("corr", p6_corr_loss_and_bptt)):
        L0, grads = fn(H, target, p)
        g = _flatten(grads)
        # finite-diff a random subset of coords (full set is fine but slower)
        theta = np.concatenate(
            [p.Wih.ravel(), p.Wfh.ravel(), p.bh.ravel(), p.Wo.ravel(), [p.bo]]
        )
        shapes = [p.Wih.shape, p.Wfh.shape, p.bh.shape, p.Wo.shape, (1,)]
        sizes = [np.prod(s) for s in shapes]

        def _set(vec):
            i = 0
            mats = []
            for s, sz in zip(shapes, sizes):
                mats.append(np.array(vec[i : i + sz]).reshape(s))
                i += sz
            return P6Params(mats[0], mats[1], mats[2], mats[3], float(mats[4][0]))

        eps = 1e-6
        idxs = RNG.choice(theta.size, size=min(24, theta.size), replace=False)
        num = np.zeros_like(g)
        for j in idxs:
            tp = theta.copy(); tp[j] += eps
            tm = theta.copy(); tm[j] -= eps
            Lp, _ = fn(H, target, _set(tp))
            Lm, _ = fn(H, target, _set(tm))
            num[j] = (Lp - Lm) / (2 * eps)
        denom = np.maximum(np.abs(g[idxs]), np.abs(num[idxs])) + 1e-9
        rel = np.abs(g[idxs] - num[idxs]) / denom
        max_rel = float(rel.max())
        _rec("P6E0", f"BPTT vs finite-diff [{mode}]: max rel err = {max_rel:.2e} "
                     f"(checked {len(idxs)} coords) {'PASS' if max_rel < 1e-4 else 'FAIL'}")
        assert max_rel < 1e-4, f"P6 {mode} BPTT gradient WRONG (max rel {max_rel:.2e})"
    _rec("P6E0", "gradient verified for BOTH modes -> training results below are trustworthy")


# =========================================================================== #
# P6E1  In-sample parity/counting LEARNING (cf. P5 PE1).
# =========================================================================== #
def exp_P6E1() -> None:
    global RNG
    RNG = np.random.default_rng(SEED + 1)
    T = 800
    K_h, K_fb, Hd = K_H_DEFAULT, K_FB_DEFAULT, HID_DEFAULT
    bits, X = make_bits(T)
    H = fir_features(X, K_h)
    tasks = [
        ("parity-running(XOR)", running_parity(bits), True),
        ("parity-last3(in-win)", parity_last_m(bits, 3), True),
        ("parity-last60(out-win)", parity_last_m(bits, 60), True),
        ("mod3-count(unbounded)", mod3_count(bits), False),
    ]
    for name, tgt, is_par in tasks:
        best = train_p6_output(H, tgt, K_fb, Hd, mode="mse",
                               epochs=300, lr=0.05, n_restart=3)
        o, _z, _a = p6_rollout(H, best[1])
        acc = binary_accuracy(o, tgt) if is_par else float("nan")
        if is_par:
            _rec("P6E1", f"{name}: in-sample |corr|={best[0]:.2f} acc={acc:.2f} (chance=0.50)")
        else:
            _rec("P6E1", f"{name}: in-sample |corr|={best[0]:.2f} (regression target)")
    _rec("P6E1", "NOTE: in-sample numbers can be SPURIOUS finite-sample fit; "
                 "the decisive ceiling answer is P6E3 (held-out generalization).")


# =========================================================================== #
# P6E2  One-step XOR micro-test: o(t)=XOR(x(t),o(t-1)) directly (cf. P5 PE2).
# The MLP hidden layer is built to express XOR; this checks the in-sample reach.
# =========================================================================== #
def exp_P6E2() -> None:
    global RNG
    RNG = np.random.default_rng(SEED + 2)
    T = 800
    K_h, K_fb, Hd = 4, K_FB_DEFAULT, HID_DEFAULT
    bits, X = make_bits(T)
    H = fir_features(X, K_h)
    tgt = running_parity(bits)  # = XOR(x(t), o(t-1)) chained
    best = train_p6_output(H, tgt, K_fb, Hd, mode="mse",
                           epochs=400, lr=0.05, n_restart=4)
    o, _z, _a = p6_rollout(H, best[1])
    acc = binary_accuracy(o, tgt)
    _rec("P6E2", f"running-XOR in-sample: |corr|={best[0]:.2f} acc={acc:.2f} "
                 f"(Hd={Hd}, K_fb={K_fb}); high in-sample acc here would mean the MLP "
                 f"hidden layer DID form x(t).o(t-1) -- verify it GENERALIZES in P6E3")


# =========================================================================== #
# P6E3  DECISIVE held-out parity generalization (mirrors P5 PE7 EXACTLY).
# THE single number that answers "does a hidden-MLP recurrent output map lift the
# star-free ceiling?".  Train on one stream, FREEZE, test on a DISJOINT stream.
# =========================================================================== #
def exp_P6E3() -> None:
    global RNG
    K_h, K_fb, Hd, T = K_H_DEFAULT, K_FB_DEFAULT, HID_DEFAULT, 900

    def _acc(pred, tgt_pm1):
        return float(np.mean(np.sign(pred) == np.sign(tgt_pm1)))

    rows = []
    # Sweep a couple of capacities to be FAIR -- a ceiling claim must not hinge on
    # too-small a hidden layer. If ANY capacity generalizes, the ceiling is lifted.
    for Hd_try in (Hd, 32):
        rng = np.random.default_rng(SEED)  # same train/test streams across capacities
        bits_tr = rng.integers(0, 2, size=T).astype(np.float64)
        H_tr = fir_features(bits_tr * 2.0 - 1.0, K_h)
        tgt_tr = (np.cumsum(bits_tr) % 2) * 2 - 1
        RNG = np.random.default_rng(SEED + 100 + Hd_try)  # deterministic init/restarts
        best = train_p6_output(H_tr, tgt_tr, K_fb, Hd_try, mode="mse",
                               epochs=400, lr=0.05, n_restart=4)
        p = best[1]
        tr_acc = _acc(p6_rollout(H_tr, p)[0], tgt_tr)
        bits_te = rng.integers(0, 2, size=T).astype(np.float64)
        H_te = fir_features(bits_te * 2.0 - 1.0, K_h)
        tgt_te = (np.cumsum(bits_te) % 2) * 2 - 1
        o_te = p6_rollout(H_te, p)[0]
        te_acc, te_corr = _acc(o_te, tgt_te), pearson_abs(o_te, tgt_te)
        p_pos = float(np.mean(tgt_te > 0))
        floor = max(p_pos, 1.0 - p_pos)
        rows.append((te_acc, floor))
        _rec("P6E3", f"running-parity Hd={Hd_try}: TRAIN acc={tr_acc:.3f} -> "
                     f"TEST acc={te_acc:.3f} |corr|={te_corr:.3f} (majority floor={floor:.3f})")
    collapsed = all(abs(te - fl) < 0.05 for te, fl in rows)
    if collapsed:
        _rec("P6E3", "DECISIVE: held-out acc collapses to majority floor for ALL "
                     "capacities -> P6 does NOT compute parity; ceiling NOT lifted by a "
                     "hidden-MLP recurrent OUTPUT map either (FIR drive is output-state-"
                     "blind, cascade_correlation.py:1942-1946).")
    else:
        _rec("P6E3", "*** held-out acc EXCEEDS the majority floor -> P6 GENERALIZES "
                     "parity: a hidden-MLP recurrent output map LIFTS the ceiling P5 "
                     "could not. This would be a material OQ-4 finding -- re-verify.")


# =========================================================================== #
# P6E3b  CONTROL: give the MLP an OUTPUT-AWARE drive (feed o(t-1) as a genuine
# input feature, not just via the frozen FIR).  This is NO LONGER cascor-faithful
# (cascor's hidden features are output-state-blind) -- it is the diagnostic that
# tells us WHETHER the obstruction is "output-state-blindness" vs "single-stream".
# If THIS generalizes but P6E3 does not, the obstruction is precisely the
# output-state-blind FIR drive (so the fix is feeding state, i.e. real recurrence
# in the HIDDEN cascade -- P1/P2 territory -- not a richer output map).
# =========================================================================== #
def exp_P6E3b() -> None:
    global RNG
    K_h, K_fb, Hd, T = K_H_DEFAULT, K_FB_DEFAULT, HID_DEFAULT, 1200

    def _acc(pred, tgt_pm1):
        return float(np.mean(np.sign(pred) == np.sign(tgt_pm1)))

    # The hidden MLP already receives o(t-1..K) via Wfh, so structurally P6E3b's
    # feedback path IS output-aware. The distinction P6E3b isolates is whether a
    # *deterministic, teacher-forced* o(t-1) (the TRUE previous label) lets the MLP
    # fit XOR -- i.e. is the architecture's XOR capacity real when the recurrence
    # is not relied upon to BUILD the signal it needs?
    rng = np.random.default_rng(SEED)
    bits_tr = rng.integers(0, 2, size=T).astype(np.float64)
    tgt_tr = (np.cumsum(bits_tr) % 2) * 2 - 1
    bits_te = rng.integers(0, 2, size=T).astype(np.float64)
    tgt_te = (np.cumsum(bits_te) % 2) * 2 - 1

    # Teacher-forced design matrix: [x(t), o_true(t-1)] -> a plain (non-recurrent)
    # 2-layer MLP must learn XOR of these two inputs. This is the Minsky-Papert
    # XOR a 2-layer MLP CAN solve -- the positive control proving the harness can
    # represent XOR when the cross-term inputs are both present and clean.
    def _tf_xor_fit(bits, tgt, train_pack=None):
        x = bits * 2.0 - 1.0
        o_prev = np.concatenate([[0.0], tgt[:-1]])  # teacher-forced true o(t-1)
        Xd = np.stack([x, o_prev], axis=1)  # (T,2)
        return Xd, tgt

    Xtr, ytr = _tf_xor_fit(bits_tr, tgt_tr)
    Xte, yte = _tf_xor_fit(bits_te, tgt_te)
    # tiny 2-layer tanh MLP trained by full-batch GD (no recurrence at all)
    RNG = np.random.default_rng(SEED + 555)
    Hd_c = 8
    W1 = RNG.standard_normal((Hd_c, 2)) * 0.8
    b1 = np.zeros(Hd_c)
    W2 = RNG.standard_normal(Hd_c) * 0.5
    b2 = 0.0
    for _ep in range(3000):
        Zc = Xtr @ W1.T + b1
        Ac = np.tanh(Zc)
        pred = Ac @ W2 + b2
        diff = pred - ytr
        gpred = (2.0 / len(ytr)) * diff
        gW2 = Ac.T @ gpred
        gb2 = float(gpred.sum())
        gA = np.outer(gpred, W2) * (1 - Ac * Ac)
        gW1 = gA.T @ Xtr
        gb1 = gA.sum(axis=0)
        W1 -= 0.1 * gW1; b1 -= 0.1 * gb1; W2 -= 0.1 * gW2; b2 -= 0.1 * gb2
    tr_acc = _acc(np.tanh(Xtr @ W1.T + b1) @ W2 + b2, ytr)
    te_acc = _acc(np.tanh(Xte @ W1.T + b1) @ W2 + b2, yte)
    _rec("P6E3b", f"CONTROL teacher-forced XOR(x(t),o_true(t-1)) via plain 2-layer MLP: "
                  f"TRAIN acc={tr_acc:.3f} TEST acc={te_acc:.3f} -- if ~1.0, the MLP CAN "
                  f"represent the XOR cross-term WHEN o(t-1) is a clean input; the P6E3 "
                  f"collapse is then about the recurrence having to BOOTSTRAP o(t-1) from "
                  f"an output-state-blind drive, not about XOR-capacity.")


# =========================================================================== #
# P6E4  REAL equities residual probe (cf. P5 PE6) -- does the richer recurrent
# output buy any residual signal the persistence baseline leaves?
# =========================================================================== #
def exp_P6E4() -> None:
    global RNG
    RNG = np.random.default_rng(SEED + 4)
    try:
        z = np.load(EQUITIES_NPZ, allow_pickle=False)
    except Exception as exc:  # pragma: no cover
        _rec("P6E4", f"SKIP: could not load equities npz: {exc!r}")
        return
    vocab = list(z["ticker_vocab"])
    pick = ["AAPL", "MSFT", "KO", "BRK.B"]
    X_full, yreg_full = z["X_full"], z["y_reg_full"]
    date_full, code_full = z["date_full"], z["ticker_code_full"]

    seqs = {}
    for nm in pick:
        try:
            code = vocab.index(np.str_(nm))
        except ValueError:
            continue
        mask = code_full == code
        order = np.argsort(date_full[mask])
        Xt = X_full[mask][order].astype(np.float64)
        yr = yreg_full[mask][order].reshape(-1)
        seqs[nm] = (standardize(Xt), yr)
    if not seqs:
        _rec("P6E4", "SKIP: none of the picked tickers were in vocab")
        return
    nm = max(seqs, key=lambda k: seqs[k][0].shape[0])
    Xstd, yr = seqs[nm]
    NMAX = 1500
    capped = Xstd.shape[0] > NMAX
    if capped:
        Xstd, yr = Xstd[-NMAX:], yr[-NMAX:]
    K_h, K_fb, Hd = K_H_DEFAULT, K_FB_DEFAULT, HID_DEFAULT
    close = Xstd[:, 3]
    ytgt = (yr - yr.mean()) / (yr.std() + 1e-8)
    A0 = np.stack([close, np.ones_like(close)], axis=1)
    c0, *_ = np.linalg.lstsq(A0, ytgt, rcond=None)
    residual = ytgt - A0 @ c0
    base_corr = pearson_abs(close, ytgt)
    H = fir_features(close, K_h)
    best = train_p6_output(H, residual, K_fb, Hd, mode="corr",
                           epochs=300, lr=0.03, n_restart=4)
    _rec("P6E4", f"[{nm}, n={Xstd.shape[0]} days{' (recent cap)' if capped else ''}] "
                 f"baseline |corr(last_close,next_close)|={base_corr:.3f}; day-axis P6 NARX "
                 f"output vs residual |corr|={best[0]:.3f} "
                 f"(P5 ref tanh 0.081 / lin 0.048; P4 ref FIR 0.196 / IIR 0.018)")


# =========================================================================== #
def main() -> int:
    t0 = time.time()
    print(
        f"P6 NARX hidden-MLP recurrent-output PoC  (seed={SEED}, K_h={K_H_DEFAULT}, "
        f"K_fb={K_FB_DEFAULT}, Hd={HID_DEFAULT}, numpy {np.__version__}, "
        f"py {sys.version.split()[0]})",
        flush=True,
    )
    print("=" * 80, flush=True)
    exp_P6E0()  # gradient HARD ASSERT first
    exp_P6E1()
    exp_P6E2()
    exp_P6E3b()  # positive control (clean teacher-forced XOR) before the decisive test
    exp_P6E3()  # DECISIVE held-out ceiling answer
    exp_P6E4()  # equities residual probe
    print("=" * 80, flush=True)
    print(f"P6 PoC complete in {time.time() - t0:.1f}s", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
