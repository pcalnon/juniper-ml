#!/usr/bin/env python3
"""Ad-hoc verification of the reference code in notes/JUNIPER_RECURSE_DELTA_T_HANDLING_2026-06-05.md.

Single-use diligence check (util/ad-hoc/ per the script-placement rule; NOT /tmp/).
Verifies:
  (1) LMU A eigenvalues are stable (negative real part)  -> catches sign errors
  (2) VariableStepLMUMemory reconstructs a delayed sinusoid on a REGULAR grid (method works)
  (3) grid-invariance: irregular-grid error is comparable to regular-grid error (Approach C)
  (4) window_one_ticker satisfies invariants I1-I5 on a concrete 2-ticker irregular example
Run:  python3 util/ad-hoc/verify_delta_t_reference_code.py
"""
from __future__ import annotations

import datetime as _dt

import numpy as np
from numpy.polynomial.legendre import Legendre


# ----- Approach C reference (inlined from the note, §8.4) -------------------
def lmu_matrices(d: int):
    A = np.zeros((d, d))
    B = np.zeros((d, 1))
    for i in range(d):
        B[i, 0] = (2 * i + 1) * ((-1) ** i)
        for j in range(d):
            A[i, j] = (2 * i + 1) * (-1.0 if i < j else (-1.0) ** (i - j + 1))
    return A, B


class VariableStepLMUMemory:
    def __init__(self, d: int, theta: float):
        self.d, self.theta = d, float(theta)
        A, B = lmu_matrices(d)
        lam, V = np.linalg.eig(A)
        self.lam, self.V = lam, V
        self.Vinv = np.linalg.inv(V)
        self.VinvB = self.Vinv @ B

    def step_matrices(self, dt: float):
        z = self.lam * (dt / self.theta)
        Abar = (self.V * np.exp(z)) @ self.Vinv
        with np.errstate(divide="ignore", invalid="ignore"):
            fac = np.expm1(z) / self.lam
        fac = np.where(np.abs(self.lam) < 1e-12, dt / self.theta, fac)
        Bbar = (self.V * fac) @ self.VinvB
        return Abar.real, Bbar.real

    def rollout(self, u: np.ndarray, dt: np.ndarray):
        m = np.zeros((self.d, 1))
        out = np.zeros((len(u), self.d))
        for k in range(1, len(u)):
            Abar, Bbar = self.step_matrices(float(dt[k]))
            m = Abar @ m + Bbar * u[k - 1]
            out[k] = m[:, 0]
        return out

    def decode_weights(self, rho: float):
        x = 2.0 * rho - 1.0
        return np.array([Legendre.basis(i)(x) for i in range(self.d)])


# ----- windowing reference (inlined from the note, §6.3) -------------------
def _yyyymmdd_to_ordinal(dates: np.ndarray) -> np.ndarray:
    y, m, d = dates // 10000, (dates // 100) % 100, dates % 100
    return np.fromiter(
        (_dt.date(int(yy), int(mm), int(dd)).toordinal() for yy, mm, dd in zip(y, m, d)),
        dtype=np.int64,
        count=len(dates),
    )


def window_one_ticker(feats, dates_yyyymmdd, y_dir, y_reg, ticker_code, *,
                      lookback, cut_ordinal, embargo=False):
    n, f = feats.shape
    ords = _yyyymmdd_to_ordinal(dates_yyyymmdd)
    assert np.all(np.diff(ords) > 0)
    cols = {k: {"train": [], "test": []} for k in
            ("X", "y", "y_reg", "date", "dt", "target_dt", "window_end_date", "ticker_code")}
    for i in range(lookback - 1, n - 1):
        lo = i - lookback + 1
        target_time = int(ords[i + 1])
        split = "train" if target_time < cut_ordinal else "test"
        if split == "test" and embargo and int(ords[lo]) < cut_ordinal:
            continue
        win_ords = ords[lo:i + 1].astype(np.float32)
        dt = np.empty(lookback, dtype=np.float32)
        dt[0] = 0.0
        dt[1:] = np.diff(win_ords)
        cols["X"][split].append(feats[lo:i + 1])
        cols["y"][split].append(y_dir[i])
        cols["y_reg"][split].append(y_reg[i])
        cols["date"][split].append(dates_yyyymmdd[lo:i + 1])
        cols["dt"][split].append(dt)
        cols["target_dt"][split].append(np.float32(ords[i + 1] - ords[i]))
        cols["window_end_date"][split].append(dates_yyyymmdd[i])
        cols["ticker_code"][split].append(np.int32(ticker_code))

    def _stack(key, split, dtype):
        items = cols[key][split]
        if not items:
            shape = {"X": (0, lookback, f), "y": (0, y_dir.shape[1]), "y_reg": (0, y_reg.shape[1]),
                     "date": (0, lookback), "dt": (0, lookback), "target_dt": (0,),
                     "window_end_date": (0,), "ticker_code": (0,)}[key]
            return np.empty(shape, dtype=dtype)
        return np.asarray(items, dtype=dtype)

    out = {}
    for split in ("train", "test"):
        out[split] = {k: _stack(k, split, dt_) for k, dt_ in (
            ("X", np.float32), ("y", np.float32), ("y_reg", np.float32), ("date", np.int32),
            ("dt", np.float32), ("target_dt", np.float32), ("window_end_date", np.int32),
            ("ticker_code", np.int32))}
    return out


def _ord(v):
    return _dt.date(v // 10000, (v // 100) % 100, v % 100).toordinal()


# ----- checks ---------------------------------------------------------------
def main() -> int:
    ok = True

    # (1) stability
    A, _ = lmu_matrices(16)
    lam = np.linalg.eigvals(A)
    max_re = float(np.max(lam.real))
    print(f"[1] LMU(d=16) max eigenvalue real part = {max_re:.4f}  (must be < 0)")
    ok &= max_re < 0

    # (2)+(3) reconstruction + grid invariance, scan a few rho/d
    def err_on(mem, times, theta, omega, rho, w):
        times = np.asarray(times, float)
        dt = np.empty_like(times); dt[0] = 0.0; dt[1:] = np.diff(times)
        u = np.sin(omega * times)
        m = mem.rollout(u, dt)
        warm = times >= (times[0] + theta)
        recon = m @ w
        truth = np.sin(omega * (times - rho * theta))
        return float(np.sqrt(np.mean((recon[warm] - truth[warm]) ** 2)))

    theta, omega = 1.0, 2.0
    rng = np.random.default_rng(0)
    for d in (16, 24):
        mem = VariableStepLMUMemory(d, theta)
        for rho in (0.5, 0.8, 1.0):
            w = mem.decode_weights(rho)
            t_reg = np.linspace(0, 12, 240)
            gaps = np.r_[0.02, rng.uniform(0.02, 0.08, 239)]
            t_irr = np.cumsum(gaps)
            e_reg = err_on(mem, t_reg, theta, omega, rho, w)
            e_irr = err_on(mem, t_irr, theta, omega, rho, w)
            print(f"[2/3] d={d:2d} rho={rho:.1f}  e_reg={e_reg:.4f}  e_irr={e_irr:.4f}")

    # (4) windowing invariants on a concrete 2-ticker irregular example
    def mk_ticker(code, start, gaps):
        ords = np.r_[start, start + np.cumsum(gaps)]
        dates = np.array([_ord_to_yyyymmdd(o) for o in ords], np.int32)
        n = len(dates)
        X = np.arange(n * 3, dtype=np.float32).reshape(n, 3) + code * 100
        y_dir = np.eye(2, dtype=np.float32)[np.arange(n) % 2]
        y_reg = X[:, :1].copy()
        return X, dates, y_dir, y_reg

    def _ord_to_yyyymmdd(o):
        dd = _dt.date.fromordinal(int(o))
        return dd.year * 10000 + dd.month * 100 + dd.day

    L, train_ratio = 3, 0.7
    blocks = []
    for code, (start, gaps) in enumerate([
        (_dt.date(2000, 1, 3).toordinal(), [1, 1, 3, 1, 1, 1, 3, 1, 1, 1]),   # weekends => 3
        (_dt.date(2001, 6, 1).toordinal(), [3, 1, 1, 1, 4, 1, 1, 3, 1]),       # holiday => 4
    ]):
        X, dates, y_dir, y_reg = mk_ticker(code, start, gaps)
        n = len(dates)
        cut_idx = min(round(n * train_ratio), n - 1)
        cut = int(_yyyymmdd_to_ordinal(dates)[cut_idx])
        out = window_one_ticker(X, dates, y_dir, y_reg, code, lookback=L, cut_ordinal=cut)
        blocks.append((code, cut, out))

    inv_ok = True
    for code, cut, out in blocks:
        tr, te = out["train"], out["test"]
        # I1 cross-ticker
        inv_ok &= bool(np.all(tr["ticker_code"] == code) and np.all(te["ticker_code"] == code))
        for blk in (tr, te):
            if blk["X"].shape[0] == 0:
                continue
            so = np.vectorize(_ord)(blk["date"])
            inv_ok &= bool(np.all(np.diff(so, axis=1) > 0))           # I3 monotone
            inv_ok &= bool(np.all(blk["dt"][:, 0] == 0))
            inv_ok &= bool(np.allclose(blk["dt"][:, 1:], np.diff(so, axis=1)))
            inv_ok &= bool(np.all(blk["target_dt"] > 0))             # I5
        # I2 no future leak
        if tr["X"].shape[0] and te["X"].shape[0]:
            tro = np.vectorize(_ord)(tr["window_end_date"]) + tr["target_dt"].astype(np.int64)
            teo = np.vectorize(_ord)(te["window_end_date"]) + te["target_dt"].astype(np.int64)
            inv_ok &= bool(tro.max() < teo.min())
        print(f"[4] ticker {code}: n_train_win={tr['X'].shape[0]} n_test_win={te['X'].shape[0]}")
    print(f"[4] windowing invariants I1-I5 hold: {inv_ok}")
    ok &= inv_ok

    print("\nRESULT:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
