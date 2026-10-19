#!/usr/bin/env python3
"""Apply W5.9 + the W5.8 (B) model half to a juniper-recurrence-model tree (exact-string edits).

Project: juniper-ml
Sub-Project: recurrence x equities (plan W5.8 (B) / W5.9)
Author: Paul Calnon
Created: 2026-10-19
Status: ad-hoc, single-use (kept for the record of exactly what the model PR changed)
Related: notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md
         (W5.8 Details, W5.9 row); juniper-recurrence#208 (W5.10, the attribute contract this fills)

Usage:
    python3 util/ad-hoc/2026-10-19_apply_w5_9_w5_8b_model.py --root <juniper-recurrence checkout> [--check]

Edits, every one an exact-string replacement that must match exactly once:

* ``juniper_recurrence_model/readouts.py`` -- ``_gcv_select`` returns a ``_GCVSelection`` carrying
  the GCV value at the selected lambda, the intercept-only (null-model) GCV ``n * ||yc||^2 / (n-1)^2``,
  and the two W5.9 flags; it logs a WARNING when the selection sits at a grid edge or the null model
  beats every grid point. ``LinearReadout`` / ``RFFReadout`` expose ``gcv_at_edge_`` / ``null_model_``
  (the names ``juniper_recurrence._readout.readout_diagnostics`` reads). ``LinearReadout`` standardises
  ``M`` on the train fold whenever ``ridge != 0.0`` (W5.8 (B)); the ``ridge == 0.0`` min-norm path is
  untouched; the statistics persist in ``save_state`` so a reload is bit-exact.
* ``juniper_recurrence_model/model.py`` -- the ``LMURegressor`` docstring stops promising that every
  ``ridge=`` value is byte-identical to the pre-DP-3 model (only ``0.0`` is).
* ``tests/test_readouts.py``, ``tests/test_lmu_model.py`` -- the new behaviour pinned.
* ``CHANGELOG.md`` -- ``[Unreleased]`` Added (W5.9) and Changed (W5.8 (B)) entries.
* ``README.md`` -- the readout table row and the GCV sentence.
"""

from __future__ import annotations

import argparse
import pathlib
import sys

EDITS: list[tuple[str, str, str]] = []


def edit(path: str, old: str, new: str) -> None:
    EDITS.append((path, old, new))


# --- readouts.py -------------------------------------------------------------------------------

R = "juniper_recurrence_model/readouts.py"

edit(
    R,
    """* **Rung 1** — regularised linear (``ridge>0.0``) + closed-form **GCV** penalty selection
  (``ridge="gcv"``). *This module (P1).*
""",
    """* **Rung 1** — regularised linear (``ridge>0.0``) + closed-form **GCV** penalty selection
  (``ridge="gcv"``). *This module (P1).* Since 0.5.0 this rung standardises the memory block on
  the train fold (W5.8 (B)) and reports when the GCV optimum sits at a grid edge or is the null
  model (W5.9) — see :class:`LinearReadout` and :func:`_gcv_select`.
""",
)

edit(
    R,
    """from __future__ import annotations

from dataclasses import dataclass
from typing import Any, ClassVar, Literal, Protocol

import numpy as np

__all__ = [
""",
    """from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, ClassVar, Literal, Protocol

import numpy as np

logger = logging.getLogger(__name__)

__all__ = [
""",
)

edit(
    R,
    """#: Log-spaced grid of candidate ridge penalties for GCV selection (Rung 1). One SVD of the
#: (centred) design matrix makes each grid evaluation O(rank), so a fine grid is cheap.
_GCV_GRID: np.ndarray = np.logspace(-6.0, 3.0, 60)
""",
    """#: Log-spaced grid of candidate ridge penalties for GCV selection (Rung 1). One SVD of the
#: (centred) design matrix makes each grid evaluation O(rank), so a fine grid is cheap. The grid is
#: deliberately **not** extended past 1e3 (plan W5.9): on the equities artifact the optimum beyond
#: the ceiling is the null model (λ → ∞) in every raw linear fold, so a wider grid would only move
#: the ceiling; :func:`_gcv_select` reports an at-edge / null-model selection instead.
_GCV_GRID: np.ndarray = np.logspace(-6.0, 3.0, 60)
""",
)

edit(
    R,
    """def _ridge_solve(design: np.ndarray, y: np.ndarray, ridge: float) -> np.ndarray:
    \"\"\"Ridge normal-equations solve for a ``[features | 1]`` design (the bias column is never penalised).\"\"\"
    gram = design.T @ design
    penalty = ridge * np.eye(gram.shape[0])
    penalty[-1, -1] = 0.0  # never regularise the bias column
    return np.linalg.solve(gram + penalty, design.T @ y)


def _gcv_select(features: np.ndarray, y: np.ndarray) -> tuple[np.ndarray, float]:
    \"\"\"Closed-form GCV ridge selection over :data:`_GCV_GRID` (Rung 1).

    Centres ``features`` / ``y`` (so the intercept is unpenalised and recovered separately), takes
    **one** thin SVD, then evaluates ``GCV(λ) = n·RSS(λ) / (n − tr H(λ))²`` for every grid λ in
    O(rank) using the projected coefficients ``g = Uᵀ yc`` — no held-out split and no inner-CV
    refit (design §4 Rung 1). ``tr H(λ) = Σ sᵢ²/(sᵢ²+λ)``; the unpenalised intercept contributes
    one further degree of freedom, so the effective trace is ``1 + tr H``. Returns the coefficient
    vector in the bias-augmented ``[features | 1]`` layout and the selected λ.
    \"\"\"
    n = features.shape[0]
""",
    """def _ridge_solve(design: np.ndarray, y: np.ndarray, ridge: float) -> np.ndarray:
    \"\"\"Ridge normal-equations solve for a ``[features | 1]`` design (the bias column is never penalised).\"\"\"
    gram = design.T @ design
    penalty = ridge * np.eye(gram.shape[0])
    penalty[-1, -1] = 0.0  # never regularise the bias column
    return np.linalg.solve(gram + penalty, design.T @ y)


def _standardize_fit(M: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    \"\"\"Per-column mean/std of ``M`` (train-fold-only). Zero-variance columns get std=1 (no NaN).\"\"\"
    mean = M.mean(axis=0)
    std = M.std(axis=0)
    std = np.where(std > 0.0, std, 1.0)  # guard: a constant column would otherwise yield 0/0 -> NaN
    return mean, std


@dataclass(frozen=True)
class _GCVSelection:
    \"\"\"What :func:`_gcv_select` resolved: the fit, the selected λ, and the W5.9 diagnostics.

    ``gcv_best`` is the GCV value at ``ridge``; ``gcv_null`` is the GCV of the intercept-only fit
    (the λ → ∞ limit, ``n·‖yc‖² / (n − 1)²``). ``at_edge`` says the selected λ is the grid's floor or
    ceiling; ``null_model`` says the intercept-only fit beats every grid point, so the true optimum
    lies beyond the ceiling and the returned fit — at the ceiling — is an abstention.
    \"\"\"

    coef: np.ndarray
    ridge: float
    gcv_best: float
    gcv_null: float
    at_edge: bool
    null_model: bool


def _gcv_select(features: np.ndarray, y: np.ndarray) -> _GCVSelection:
    \"\"\"Closed-form GCV ridge selection over :data:`_GCV_GRID` (Rung 1).

    Centres ``features`` / ``y`` (so the intercept is unpenalised and recovered separately), takes
    **one** thin SVD, then evaluates ``GCV(λ) = n·RSS(λ) / (n − tr H(λ))²`` for every grid λ in
    O(rank) using the projected coefficients ``g = Uᵀ yc`` — no held-out split and no inner-CV
    refit (design §4 Rung 1). ``tr H(λ) = Σ sᵢ²/(sᵢ²+λ)``; the unpenalised intercept contributes
    one further degree of freedom, so the effective trace is ``1 + tr H``. Returns the coefficient
    vector in the bias-augmented ``[features | 1]`` layout, the selected λ and the W5.9 diagnostics.

    **W5.9 — the grid's edges are reported, not moved.** As λ → ∞ every shrinkage factor → 1, so
    ``RSS → ‖yc‖²`` and ``tr H → 0``: the intercept-only (null-model) GCV is ``n·‖yc‖² / (n − 1)²``,
    the one point off the grid that is free to evaluate. When it is below the best grid value the
    optimum lies beyond the ceiling and the fit returned — at the ceiling λ — abstains (train r² ≈ 0);
    when the selected λ is the grid's floor or ceiling the optimum may lie off the grid either way.
    Both are logged at WARNING and returned as ``at_edge`` / ``null_model`` so the fitted readout,
    and through it the service response (W5.10), can say so. On the equities artifact of the W5.1
    note every raw linear fold and three of five RFF folds select the null model.
    \"\"\"
    n = features.shape[0]
""",
)

edit(
    R,
    """    filt = s / (s2 + best_lam)  # s_i/(s_i^2+λ)
    coef_feat = vt.T @ (filt[:, None] * g)  # (p, out)
    coef_bias = y_mean - feat_mean @ coef_feat  # (out,)
    return np.concatenate([coef_feat, coef_bias[None, :]], axis=0), best_lam


class LinearReadout:
    \"\"\"Rung 0/1 — a (optionally ridge-regularised) linear readout over ``[ M | extra | 1 ]``.

    ``ridge=0.0`` is the back-compat min-norm ``lstsq`` solve; ``ridge>0.0`` is the regularised
    normal-equation solve (the bias column is never penalised); ``ridge="gcv"`` selects the penalty
    by closed-form generalised cross-validation at ``fit`` and writes the selected λ back to
    :attr:`ridge` (so it is persisted for retraining fidelity).
    \"\"\"

    kind: ClassVar[str] = "linear"

    def __init__(self, ridge: RidgeParam = 0.0) -> None:
        self.ridge: RidgeParam = ridge
        self._coef: np.ndarray | None = None

    @property
    def is_fitted(self) -> bool:
        return self._coef is not None

    @property
    def coef(self) -> np.ndarray | None:
        return self._coef

    def _design(self, M: np.ndarray, extra: np.ndarray) -> np.ndarray:
        return _assemble_design(M, extra)

    def fit(self, M: np.ndarray, extra: np.ndarray, y: np.ndarray, *, M_val: np.ndarray | None = None, extra_val: np.ndarray | None = None, y_val: np.ndarray | None = None, random_seed: int | None = None) -> None:
        if isinstance(self.ridge, str):
            if self.ridge != "gcv":
                raise ValueError(f"unknown ridge mode {self.ridge!r}; expected a float or 'gcv'")
            features = np.concatenate([M, extra], axis=1)  # GCV centres internally; bias recovered separately
            self._coef, self.ridge = _gcv_select(features, y)
            return
        design = self._design(M, extra)
        if self.ridge > 0.0:
            self._coef = _ridge_solve(design, y, float(self.ridge))
        else:
            self._coef, *_ = np.linalg.lstsq(design, y, rcond=None)

    def predict(self, M: np.ndarray, extra: np.ndarray) -> np.ndarray:
        if self._coef is None:
            raise RuntimeError("readout is not fitted")
        return self._design(M, extra) @ self._coef

    def save_state(self) -> tuple[dict[str, np.ndarray], dict[str, Any]]:
        if self._coef is None:
            raise RuntimeError("cannot serialize an unfitted readout")
        return {"coef": self._coef}, {"kind": self.kind, "ridge": float(self.ridge)}

    @classmethod
    def from_state(cls, arrays: dict[str, np.ndarray], descriptor: dict[str, Any]) -> LinearReadout:
        readout = cls(ridge=float(descriptor.get("ridge", 0.0)))
        readout._coef = arrays["coef"]
        return readout
""",
    """    filt = s / (s2 + best_lam)  # s_i/(s_i^2+λ)
    coef_feat = vt.T @ (filt[:, None] * g)  # (p, out)
    coef_bias = y_mean - feat_mean @ coef_feat  # (out,)
    coef = np.concatenate([coef_feat, coef_bias[None, :]], axis=0)
    # W5.9: the λ → ∞ limit (intercept only) is the one off-grid point that costs nothing to evaluate.
    gcv_null = (n * yc_energy / (n - 1.0) ** 2) if n > 1 else np.inf
    at_edge = best_lam == float(_GCV_GRID[0]) or best_lam == float(_GCV_GRID[-1])
    null_model = bool(gcv_null < best_gcv)
    if null_model:
        logger.warning("GCV: the intercept-only model (GCV %.6g) beats every grid point (best %.6g at lambda=%.6g); the optimum lies beyond the grid ceiling %.6g and the fit abstains at the ceiling", gcv_null, best_gcv, best_lam, float(_GCV_GRID[-1]))
    elif at_edge:
        logger.warning("GCV selected lambda=%.6g at the edge of the grid [%.6g, %.6g]; the optimum may lie off the grid", best_lam, float(_GCV_GRID[0]), float(_GCV_GRID[-1]))
    return _GCVSelection(coef=coef, ridge=best_lam, gcv_best=float(best_gcv), gcv_null=float(gcv_null), at_edge=bool(at_edge), null_model=null_model)


class LinearReadout:
    \"\"\"Rung 0/1 — a (optionally ridge-regularised) linear readout over ``[ M | extra | 1 ]``.

    ``ridge=0.0`` is the back-compat min-norm ``lstsq`` solve on the **raw** memory block — the
    conformance baseline the bench ratifies, byte-identical to the pre-DP-3 model. ``ridge>0.0`` is
    the regularised normal-equation solve (the bias column is never penalised); ``ridge="gcv"``
    selects the penalty by closed-form generalised cross-validation at ``fit`` and writes the
    selected λ back to :attr:`ridge` (so it is persisted for retraining fidelity).

    **Standardisation (0.5.0, plan W5.8 (B)).** Whenever ``ridge != 0.0`` the memory block ``M`` is
    standardised per column with the **train-fold** mean / std (:func:`_standardize_fit`, the same
    statistics the RFF rung uses) before the solve, and the fitted statistics are applied again at
    ``predict``. A single penalty cannot be right for columns whose scales differ by orders of
    magnitude — on the W5.1 equities artifact GCV on the raw block scores −247 and standardisation
    with a fixed ``ridge=1.0`` −192, while the two together score −0.195 (a null-model abstention,
    reported through :attr:`gcv_at_edge_` / :attr:`null_model_`). The ``extra`` side-channel and
    the bias column are never standardised, and the ``ridge=0.0`` path is untouched (a standardised
    min-norm solve is a different, far worse, solution on that artifact: −8.8e12).

    Fit diagnostics (W5.9): after a ``ridge="gcv"`` fit :attr:`gcv_at_edge_` and :attr:`null_model_`
    are booleans; after a fixed-``ridge`` fit, and on a readout rebuilt by :meth:`from_state`, they
    are ``None`` (*not determined*). They are not persisted.
    \"\"\"

    kind: ClassVar[str] = "linear"

    def __init__(self, ridge: RidgeParam = 0.0) -> None:
        self.ridge: RidgeParam = ridge
        self._coef: np.ndarray | None = None
        self._mean: np.ndarray | None = None  # train-fold column statistics; set only when the fit standardised (ridge != 0.0)
        self._std: np.ndarray | None = None
        self.gcv_at_edge_: bool | None = None  # W5.9: the selected λ sits at the grid floor / ceiling (GCV fits only)
        self.null_model_: bool | None = None  # W5.9: the intercept-only fit beats every grid point (GCV fits only)

    @property
    def is_fitted(self) -> bool:
        return self._coef is not None

    @property
    def coef(self) -> np.ndarray | None:
        \"\"\"Coefficients in ``[block | extra | 1]`` layout, where ``block`` is the standardised ``M`` when the fit standardised.\"\"\"
        return self._coef

    @property
    def standardized(self) -> bool:
        \"\"\"``True`` when the fitted solve ran on the train-fold-standardised memory block (``ridge != 0.0``).\"\"\"
        return self._mean is not None

    def _block(self, M: np.ndarray) -> np.ndarray:
        return M if self._mean is None else (M - self._mean) / self._std

    def _design(self, M: np.ndarray, extra: np.ndarray) -> np.ndarray:
        return _assemble_design(self._block(M), extra)

    def fit(self, M: np.ndarray, extra: np.ndarray, y: np.ndarray, *, M_val: np.ndarray | None = None, extra_val: np.ndarray | None = None, y_val: np.ndarray | None = None, random_seed: int | None = None) -> None:
        self._mean = self._std = None
        self.gcv_at_edge_ = self.null_model_ = None
        if isinstance(self.ridge, str):
            if self.ridge != "gcv":
                raise ValueError(f"unknown ridge mode {self.ridge!r}; expected a float or 'gcv'")
            self._mean, self._std = _standardize_fit(M)  # W5.8 (B): train-fold statistics
            features = np.concatenate([self._block(M), extra], axis=1)  # GCV centres internally; bias recovered separately
            selection = _gcv_select(features, y)
            self._coef, self.ridge = selection.coef, selection.ridge
            self.gcv_at_edge_, self.null_model_ = selection.at_edge, selection.null_model
            return
        if self.ridge > 0.0:
            self._mean, self._std = _standardize_fit(M)  # W5.8 (B): train-fold statistics
            self._coef = _ridge_solve(self._design(M, extra), y, float(self.ridge))
        else:
            # ridge == 0.0: the raw min-norm solve, byte-identical to the pre-0.5.0 path (never standardised).
            self._coef, *_ = np.linalg.lstsq(self._design(M, extra), y, rcond=None)

    def predict(self, M: np.ndarray, extra: np.ndarray) -> np.ndarray:
        if self._coef is None:
            raise RuntimeError("readout is not fitted")
        return self._design(M, extra) @ self._coef

    def save_state(self) -> tuple[dict[str, np.ndarray], dict[str, Any]]:
        if self._coef is None:
            raise RuntimeError("cannot serialize an unfitted readout")
        arrays: dict[str, np.ndarray] = {"coef": self._coef}
        if self._mean is not None:
            arrays["mean"] = self._mean  # the train-fold statistics the coefficients were solved against
            arrays["std"] = self._std
        return arrays, {"kind": self.kind, "ridge": float(self.ridge), "standardized": self._mean is not None}

    @classmethod
    def from_state(cls, arrays: dict[str, np.ndarray], descriptor: dict[str, Any]) -> LinearReadout:
        readout = cls(ridge=float(descriptor.get("ridge", 0.0)))
        readout._coef = arrays["coef"]
        if "mean" in arrays:  # a 0.5.0+ standardised fit; a pre-0.5.0 state has no statistics and predicts on the raw block
            readout._mean = arrays["mean"]
            readout._std = arrays["std"]
        return readout
""",
)

edit(
    R,
    """# --- Rung 2a: random Fourier features (numpy nonlinear readout) -----------------------


def _standardize_fit(M: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    \"\"\"Per-column mean/std of ``M`` (train-fold-only). Zero-variance columns get std=1 (no NaN).\"\"\"
    mean = M.mean(axis=0)
    std = M.std(axis=0)
    std = np.where(std > 0.0, std, 1.0)  # guard: a constant column would otherwise yield 0/0 -> NaN
    return mean, std


def _median_gamma(""",
    """# --- Rung 2a: random Fourier features (numpy nonlinear readout) -----------------------


def _median_gamma(""",
)

edit(
    R,
    """        self.ridge: RidgeParam = ridge
        self._W: np.ndarray | None = None
        self._b: np.ndarray | None = None
        self._mean: np.ndarray | None = None
        self._std: np.ndarray | None = None
        self._beta: np.ndarray | None = None
""",
    """        self.ridge: RidgeParam = ridge
        self._W: np.ndarray | None = None
        self._b: np.ndarray | None = None
        self._mean: np.ndarray | None = None
        self._std: np.ndarray | None = None
        self._beta: np.ndarray | None = None
        self.gcv_at_edge_: bool | None = None  # W5.9: as on LinearReadout (GCV fits only; not persisted)
        self.null_model_: bool | None = None
""",
)

edit(
    R,
    """        phi = np.sqrt(2.0 / d_out) * np.cos(mz @ self._W + self._b)
        if isinstance(self.ridge, str):
            if self.ridge != "gcv":
                raise ValueError(f"unknown ridge mode {self.ridge!r}; expected a float or 'gcv'")
            self._beta, self.ridge = _gcv_select(np.concatenate([phi, extra], axis=1), y)
        elif self.ridge > 0.0:
""",
    """        phi = np.sqrt(2.0 / d_out) * np.cos(mz @ self._W + self._b)
        self.gcv_at_edge_ = self.null_model_ = None
        if isinstance(self.ridge, str):
            if self.ridge != "gcv":
                raise ValueError(f"unknown ridge mode {self.ridge!r}; expected a float or 'gcv'")
            selection = _gcv_select(np.concatenate([phi, extra], axis=1), y)
            self._beta, self.ridge = selection.coef, selection.ridge
            self.gcv_at_edge_, self.null_model_ = selection.at_edge, selection.null_model
        elif self.ridge > 0.0:
""",
)

# --- model.py ----------------------------------------------------------------------------------

MP = "juniper_recurrence_model/model.py"

edit(
    MP,
    """        An immutable readout **spec** (see :mod:`juniper_recurrence_model.readouts`). ``None``
        (default) builds a :class:`~juniper_recurrence_model.readouts.LinearReadoutSpec` from
        ``ridge`` — so ``LMURegressor(d, theta, ridge=…)`` is byte-identical to the pre-DP-3 model.
        Passing both a non-default ``ridge`` and a ``readout`` is rejected (one source of truth).
    ridge:
        Convenience for the default linear readout's L2 penalty (the bias column is never
        penalised). ``0.0`` (default) is the plain min-norm least-squares solve. A positive float
        is the regularised normal-equation solve. ``"gcv"`` selects the penalty by closed-form
        generalised cross-validation at ``fit`` (the selected λ is written back to ``self.ridge``).
        Ignored when an explicit ``readout`` spec is supplied.
""",
    """        An immutable readout **spec** (see :mod:`juniper_recurrence_model.readouts`). ``None``
        (default) builds a :class:`~juniper_recurrence_model.readouts.LinearReadoutSpec` from
        ``ridge`` — so ``LMURegressor(d, theta)`` (``ridge=0.0``) is byte-identical to the pre-DP-3
        model. Passing both a non-default ``ridge`` and a ``readout`` is rejected (one source of truth).
    ridge:
        Convenience for the default linear readout's L2 penalty (the bias column is never
        penalised). ``0.0`` (default) is the plain min-norm least-squares solve on the raw memory
        block. A positive float is the regularised normal-equation solve. ``"gcv"`` selects the
        penalty by closed-form generalised cross-validation at ``fit`` (the selected λ is written
        back to ``self.ridge``; the fitted readout's ``gcv_at_edge_`` / ``null_model_`` say whether
        the selection sits at the grid edge or abstains as the null model). Since 0.5.0 every
        non-zero ``ridge`` standardises the memory block with the train-fold statistics before the
        solve (plan W5.8 (B)); the ``0.0`` path is untouched. Ignored when an explicit ``readout``
        spec is supplied.
""",
)

# --- tests -------------------------------------------------------------------------------------

TR = "tests/test_readouts.py"

edit(
    TR,
    """from juniper_recurrence_model.readouts import READOUT_REGISTRY, LinearReadout, LinearReadoutSpec, RFFReadout, RFFReadoutSpec, build_readout_from_state
""",
    """from juniper_recurrence_model.readouts import _GCV_GRID, READOUT_REGISTRY, LinearReadout, LinearReadoutSpec, RFFReadout, RFFReadoutSpec, _gcv_select, _standardize_fit, build_readout_from_state
""",
)

edit(
    TR,
    """def test_gcv_invalid_ridge_string_raises():
""",
    """# --- W5.9: the GCV grid's edges are reported, not moved --------------------------------------


def _noise_block(seed: int = 1, n: int = 200, p: int = 10):
    \"\"\"A target with nothing to fit: the GCV optimum is the intercept-only (null) model.\"\"\"
    rng = np.random.default_rng(seed)
    return rng.normal(size=(n, p)), np.empty((n, 0)), rng.normal(size=(n, 1))


def test_gcv_select_reports_the_null_model_and_the_ceiling_on_pure_noise(caplog):
    M, extra, y = _noise_block()
    with caplog.at_level("WARNING", logger="juniper_recurrence_model.readouts"):
        selection = _gcv_select(np.concatenate([M, extra], axis=1), y)
    assert selection.ridge == float(_GCV_GRID[-1])  # the ceiling: no grid point beats the null model
    assert selection.at_edge is True
    assert selection.null_model is True
    assert selection.gcv_null < selection.gcv_best  # the one off-grid point that is free to evaluate
    n = M.shape[0]
    yc = y - y.mean(axis=0)
    assert selection.gcv_null == pytest.approx(n * float(np.sum(yc**2)) / (n - 1.0) ** 2)
    assert "intercept-only model" in caplog.text and "abstains at the ceiling" in caplog.text


def test_gcv_select_interior_optimum_sets_no_flags_and_logs_nothing(caplog):
    M, extra, rng = _block(n=200, p=16, k=1, seed=3)
    design = np.concatenate([M, extra, np.ones((200, 1))], axis=1)
    y = design @ rng.normal(size=(design.shape[1], 1)) + 0.1 * rng.normal(size=(200, 1))
    with caplog.at_level("WARNING", logger="juniper_recurrence_model.readouts"):
        selection = _gcv_select(np.concatenate([M, extra], axis=1), y)
    assert float(_GCV_GRID[0]) < selection.ridge < float(_GCV_GRID[-1])
    assert selection.at_edge is False
    assert selection.null_model is False
    assert selection.gcv_best < selection.gcv_null
    assert caplog.text == ""


def test_gcv_select_at_the_floor_is_an_edge_but_not_the_null_model(caplog):
    rng = np.random.default_rng(0)
    M = rng.normal(size=(200, 8))
    y = M @ rng.normal(size=(8, 1))  # exact linear target, no noise: the smallest penalty wins
    with caplog.at_level("WARNING", logger="juniper_recurrence_model.readouts"):
        selection = _gcv_select(M, y)
    assert selection.ridge == float(_GCV_GRID[0])
    assert selection.at_edge is True
    assert selection.null_model is False
    assert "edge of the grid" in caplog.text


def test_linear_gcv_fit_exposes_the_w5_9_flags_as_booleans():
    M, extra, y = _noise_block()
    ro = LinearReadout(ridge="gcv")
    assert ro.gcv_at_edge_ is None and ro.null_model_ is None  # not determined before a fit
    ro.fit(M, extra, y)
    assert ro.gcv_at_edge_ is True and ro.null_model_ is True
    assert ro.ridge == float(_GCV_GRID[-1])
    M2, extra2, rng = _block(n=200, p=16, k=1, seed=3)
    y2 = np.concatenate([M2, extra2, np.ones((200, 1))], axis=1) @ rng.normal(size=(18, 1)) + 0.1 * rng.normal(size=(200, 1))
    ro.ridge = "gcv"
    ro.fit(M2, extra2, y2)  # a re-fit resets and re-derives the flags
    assert ro.gcv_at_edge_ is False and ro.null_model_ is False


def test_fixed_ridge_fit_leaves_the_w5_9_flags_undetermined():
    M, extra, rng = _block(n=60, p=8, seed=2)
    y = rng.normal(size=(60, 1))
    for ridge in (0.0, 0.3):
        ro = LinearReadout(ridge=ridge)
        ro.fit(M, extra, y)
        assert ro.gcv_at_edge_ is None and ro.null_model_ is None  # not applicable: None, never False


def test_w5_9_flags_are_not_persisted_and_read_none_after_reload():
    M, extra, y = _noise_block()
    ro = LinearReadout(ridge="gcv")
    ro.fit(M, extra, y)
    arrays, descriptor = ro.save_state()
    assert "gcv_at_edge_" not in descriptor and "null_model_" not in descriptor
    restored = LinearReadout.from_state(arrays, descriptor)
    assert restored.gcv_at_edge_ is None and restored.null_model_ is None


def test_rff_gcv_fit_exposes_the_w5_9_flags_and_a_fixed_ridge_does_not():
    M, extra, y = _noise_block(p=6)
    gcv = RFFReadout(n_features_out=32, ridge="gcv")
    gcv.fit(M, extra, y, random_seed=0)
    assert isinstance(gcv.gcv_at_edge_, bool) and isinstance(gcv.null_model_, bool)
    assert gcv.gcv_at_edge_ == (gcv.ridge in (float(_GCV_GRID[0]), float(_GCV_GRID[-1])))
    fixed = RFFReadout(n_features_out=32, ridge=1.0)
    fixed.fit(M, extra, y, random_seed=0)
    assert fixed.gcv_at_edge_ is None and fixed.null_model_ is None


# --- W5.8 (B): the linear rung standardises the memory block on the train fold when ridge != 0 ---


def test_linear_ridge_zero_path_is_untouched_by_standardisation():
    M, extra, rng = _block(n=50, p=10, k=1, seed=5)
    y = rng.normal(size=(50, 1))
    ro = LinearReadout(ridge=0.0)
    ro.fit(M, extra, y)
    expected, *_ = np.linalg.lstsq(np.concatenate([M, extra, np.ones((50, 1))], axis=1), y, rcond=None)
    assert np.array_equal(ro.coef, expected)  # byte-identical to the raw min-norm solve (the conformance baseline)
    assert ro.standardized is False
    arrays, descriptor = ro.save_state()
    assert set(arrays) == {"coef"} and descriptor["standardized"] is False


@pytest.mark.parametrize("ridge", [0.3, "gcv"])
def test_linear_nonzero_ridge_standardises_with_train_fold_statistics(ridge):
    M, extra, rng = _block(n=80, p=6, k=1, seed=8)
    M = M * np.array([1.0, 10.0, 100.0, 1e3, 1e4, 1e5])  # columns of wildly different scale
    y = rng.normal(size=(80, 1))
    ro = LinearReadout(ridge=ridge)
    ro.fit(M, extra, y)
    mean, std = _standardize_fit(M)
    assert ro.standardized is True
    assert np.array_equal(ro._mean, mean) and np.array_equal(ro._std, std)
    # A later block is standardised with the TRAIN statistics, never its own.
    M_eval, extra_eval, _ = _block(n=30, p=6, k=1, seed=9)
    M_eval = M_eval * 7.0
    design_eval = np.concatenate([(M_eval - mean) / std, extra_eval, np.ones((30, 1))], axis=1)
    assert np.array_equal(ro.predict(M_eval, extra_eval), design_eval @ ro.coef)


def test_linear_fixed_ridge_is_column_scale_invariant_once_standardised():
    \"\"\"The reason for W5.8 (B): a single penalty on raw columns depends on their units; standardised, it does not.\"\"\"
    M, extra, rng = _block(n=120, p=5, k=0, seed=11)
    y = M @ rng.normal(size=(5, 1)) + rng.normal(size=(120, 1))
    scale = np.array([1.0, 1e-3, 1e3, 5.0, 0.02])
    a = LinearReadout(ridge=2.0)
    a.fit(M, extra, y)
    b = LinearReadout(ridge=2.0)
    b.fit(M * scale, extra, y)
    assert np.allclose(a.predict(M, extra), b.predict(M * scale, extra), rtol=1e-9, atol=1e-9)


def test_linear_standardised_fit_persists_its_statistics_and_reloads_bit_exact():
    M, extra, rng = _block(n=70, p=9, k=1, seed=12)
    y = rng.normal(size=(70, 1))
    ro = LinearReadout(ridge=0.5)
    ro.fit(M, extra, y)
    arrays, descriptor = ro.save_state()
    assert set(arrays) == {"coef", "mean", "std"} and descriptor["standardized"] is True
    restored = LinearReadout.from_state(arrays, descriptor)
    assert restored.standardized is True
    assert np.array_equal(ro.predict(M, extra), restored.predict(M, extra))


def test_linear_pre_0_5_0_state_without_statistics_predicts_on_the_raw_block():
    M, extra, rng = _block(n=40, p=4, k=0, seed=13)
    coef = rng.normal(size=(5, 1))
    restored = LinearReadout.from_state({"coef": coef}, {"kind": "linear", "ridge": 0.7})  # no mean / std, no flag
    assert restored.standardized is False
    assert np.array_equal(restored.predict(M, extra), np.concatenate([M, np.ones((40, 1))], axis=1) @ coef)


def test_linear_standardisation_guards_a_zero_variance_column():
    M, extra, rng = _block(n=40, p=4, k=0, seed=14)
    M[:, 2] = 3.0
    y = rng.normal(size=(40, 1))
    ro = LinearReadout(ridge="gcv")
    ro.fit(M, extra, y)
    assert np.all(np.isfinite(ro.predict(M, extra)))
    assert ro._std[2] == 1.0


def test_gcv_invalid_ridge_string_raises():
""",
)

TL = "tests/test_lmu_model.py"

edit(
    TL,
    """def test_linear_readout_spec_matches_ridge_kwarg_byte_identical():
""",
    """def test_model_ridge_zero_default_is_byte_identical_to_the_raw_lstsq_solve():
    \"\"\"W5.8 (B) leaves the conformance baseline alone: ridge=0.0 never standardises.\"\"\"
    X, dt, _ = _toy_3d(n=40, n_steps=6, n_features=2, seed=21)
    y = np.random.default_rng(21).normal(size=(40,))
    model = LMURegressor(d=8, theta=5.0)
    model.fit(X, y, dt=dt)
    assert model._readout.standardized is False
    block = model._memory_block(np.asarray(X, dtype=float), dt, None, None)
    design = np.concatenate([block, np.ones((40, 1))], axis=1)
    expected, *_ = np.linalg.lstsq(design, y.reshape(40, 1), rcond=None)
    assert np.array_equal(model._readout.coef, expected)


def test_model_nonzero_ridge_standardises_and_roundtrips_lossless(tmp_path):
    \"\"\"A ridge > 0 fit standardises the memory block (W5.8 (B)) and its statistics ride the envelope.\"\"\"
    X, dt, _ = _toy_3d(n=40, n_steps=6, n_features=2, seed=22)
    y = np.random.default_rng(22).normal(size=(40,))
    model = LMURegressor(d=8, theta=5.0, ridge=0.5)
    model.fit(X, y, dt=dt)
    assert model._readout.standardized is True
    before = model.predict(X, dt=dt)
    LMUSerializer().save(model, tmp_path / "m")
    restored = LMUSerializer().load(tmp_path / "m")
    assert restored._readout.standardized is True
    assert np.array_equal(before, restored.predict(X, dt=dt))


def test_model_gcv_fit_surfaces_the_w5_9_flags_on_the_readout():
    \"\"\"The attributes juniper-recurrence's readout_diagnostics reads (W5.10 contract) are set after a GCV fit.\"\"\"
    X, dt, _ = _toy_3d(n=60, n_steps=6, n_features=2, seed=23)
    y = np.random.default_rng(23).normal(size=(60,))  # noise: the flags are booleans either way
    model = LMURegressor(d=8, theta=5.0, ridge="gcv")
    model.fit(X, y, dt=dt)
    assert isinstance(model._readout.gcv_at_edge_, bool)
    assert isinstance(model._readout.null_model_, bool)
    fixed = LMURegressor(d=8, theta=5.0, ridge=0.1)
    fixed.fit(X, y, dt=dt)
    assert fixed._readout.gcv_at_edge_ is None and fixed._readout.null_model_ is None


def test_linear_readout_spec_matches_ridge_kwarg_byte_identical():
""",
)

edit(
    TL,
    """from juniper_recurrence_model import LinearReadoutSpec, LMURegressor, LMUSerializer, VariableStepLMUMemory
""",
    """from juniper_recurrence_model import LinearReadoutSpec, LMURegressor, LMUSerializer, VariableStepLMUMemory
from juniper_recurrence_model.readouts import _ridge_solve
""",
)

edit(
    TL,
    """def test_loads_pre_dp3_format_npz():
    \"\"\"A pre-DP-3 .npz (top-level 'coef', no meta['readout']) loads and predicts identically.\"\"\"
    X, dt, rng = _toy_3d(n=40, n_steps=8, n_features=3, seed=53)
    y = rng.normal(size=(40, 1))
    model = LMURegressor(d=10, theta=6.0, ridge=1e-3)
    model.fit(X, y, dt=dt)
    expected = model.predict(X, dt=dt)
    old_meta = {  # mirrors the pre-DP-3 LMUSerializer.save payload (no "schema"/"readout" keys)
""",
    """def test_loads_pre_dp3_format_npz():
    \"\"\"A pre-DP-3 .npz (top-level 'coef', no meta['readout']) loads and predicts identically.

    A pre-DP-3 ridge fit solved on the **raw** memory block (train-fold standardisation arrived with
    0.5.0, W5.8 (B), and persists its statistics beside the coefficients), so the fixture's
    coefficients are a raw-block ridge solve and the reload must predict on the raw block.
    \"\"\"
    X, dt, rng = _toy_3d(n=40, n_steps=8, n_features=3, seed=53)
    y = rng.normal(size=(40, 1))
    model = LMURegressor(d=10, theta=6.0, ridge=1e-3)
    model.fit(X, y, dt=dt)  # populates the envelope fields the old meta carried
    design = np.concatenate([model._memory_block(np.asarray(X, dtype=float), dt, None, None), np.ones((40, 1))], axis=1)
    old_coef = _ridge_solve(design, y, 1e-3)  # what a pre-DP-3 file stored
    expected = design @ old_coef
    old_meta = {  # mirrors the pre-DP-3 LMUSerializer.save payload (no "schema"/"readout" keys)
""",
)

edit(
    TL,
    """        np.savez(path, coef=model._coef, meta=json.dumps(old_meta))
        restored = LMUSerializer().load(path)
    assert np.array_equal(expected, restored.predict(X, dt=dt))
    assert restored.ridge == 1e-3
""",
    """        np.savez(path, coef=old_coef, meta=json.dumps(old_meta))
        restored = LMUSerializer().load(path)
    assert np.array_equal(expected, restored.predict(X, dt=dt))
    assert restored.ridge == 1e-3
    assert restored._readout.standardized is False  # no statistics in the file: the raw block, as fitted
""",
)

# --- CHANGELOG ---------------------------------------------------------------------------------

CL = "CHANGELOG.md"

edit(
    CL,
    """## [Unreleased]

## [0.4.0] - 2026-10-10
""",
    """## [Unreleased]

### Changed

- **The linear readout standardises the memory block on the train fold whenever `ridge != 0.0`**
  (W5.8 (B) of juniper-ml
  `notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md`;
  accepted by the owner 2026-10-18). `LinearReadout` now applies the per-column train-fold mean / std
  (`_standardize_fit`, the statistics the RFF rung already used) to `M` before a `ridge > 0.0` or
  `ridge="gcv"` solve, and again at `predict`; the `extra` side-channel and the bias column are
  never standardised. The statistics ride `save_state` (`mean` / `std` arrays, a `standardized`
  descriptor flag), so a reload is bit-exact, and a pre-0.5.0 state without them predicts on the raw
  block as before. The `ridge == 0.0` min-norm path -- the bench's ratified conformance baseline and
  `LMURegressor`'s default -- is byte-identical to 0.4.0. Measured on the W5.1 equities artifact
  (five expanding folds, `reports/2026-10-05_recurrence-equities-cv-consensus/reconciler-rederive.json`
  in juniper-ml): GCV on the raw block aggregates **−247**, a fixed `ridge=1.0` on the standardised
  block **−192**, GCV on the standardised block **−0.195** (λ at the grid ceiling in every fold, the
  null-model abstention below) and **−8.8e12** for a standardised min-norm solve -- which is why the
  `0.0` path is left alone. A fixed non-zero `ridge` therefore fits a different, scale-invariant
  solution from 0.4.0's; `ridge="gcv"` still writes the selected λ back and persists it.

### Added

- **GCV reports an at-edge or null-model selection instead of moving the grid** (plan W5.9; the
  contract `juniper-recurrence` 0.6.x's `readout_diagnostics` already reads, juniper-recurrence#208).
  `_gcv_select` now also evaluates the λ → ∞ limit -- the intercept-only fit's GCV
  `n·‖yc‖² / (n − 1)²`, the one off-grid point that costs nothing -- and returns a `_GCVSelection`
  (`coef`, `ridge`, `gcv_best`, `gcv_null`, `at_edge`, `null_model`). A fitted `LinearReadout` /
  `RFFReadout` exposes **`gcv_at_edge_`** (the selected λ is the grid floor `1e-6` or ceiling `1e3`)
  and **`null_model_`** (the intercept-only fit beats every grid point, so the optimum lies beyond
  the ceiling and the returned fit, at the ceiling, abstains). Both are `None` -- *not determined*,
  never *false* -- after a fixed-`ridge` fit and on a readout rebuilt by `from_state`; neither is
  persisted. Either condition logs a WARNING from `juniper_recurrence_model.readouts`. `_GCV_GRID`
  is unchanged at `logspace(-6, 3, 60)`: on the equities artifact the optimum beyond the ceiling is
  the null model in every raw linear fold and three of five RFF folds, so "re-run off the ceiling"
  is unsatisfiable and a wider grid would only move the edge.

## [0.4.0] - 2026-10-10
""",
)

# --- README ------------------------------------------------------------------------------------

RM = "README.md"

edit(
    RM,
    """| 0 / 1 | `LinearReadoutSpec` (default) | linear least squares, optional L2 | `ridge=` a float, or `"gcv"` for closed-form generalized-cross-validation selection |
""",
    """| 0 / 1 | `LinearReadoutSpec` (default) | linear least squares, optional L2 | `ridge=` a float, or `"gcv"` for closed-form generalized-cross-validation selection; any non-zero `ridge` standardises the memory block with the train-fold statistics first (`ridge=0.0`, the default, is the raw min-norm solve) |
""",
)

edit(
    RM,
    """findings). Default to `linear` + `ridge="gcv"`; reach for `rff` / `mlp` when the target has genuine
nonlinear structure.
""",
    """findings). Default to `linear` + `ridge="gcv"`; reach for `rff` / `mlp` when the target has genuine
nonlinear structure. After a `"gcv"` fit the readout's `gcv_at_edge_` / `null_model_` say whether the
selected penalty sits at the grid's edge or the GCV optimum is the intercept-only model (the fit
abstains at the grid ceiling rather than extrapolate); either condition also logs a WARNING.
""",
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--root", required=True, help="juniper-recurrence checkout root (holds juniper-recurrence-model/)")
    parser.add_argument("--check", action="store_true", help="report each edit's state; write nothing")
    args = parser.parse_args()
    root = pathlib.Path(args.root) / "juniper-recurrence-model"
    pending = applied = 0
    failed = []
    for rel, old, new in EDITS:
        path = root / rel
        text = path.read_text(encoding="utf-8")
        if text.count(new) == 1:  # an insertion edit keeps its anchor inside ``new``, so ``new`` present is the test
            applied += 1
            print(f"  = {rel}: already applied")
            continue
        count = text.count(old)
        if count != 1:
            failed.append((rel, count, old.splitlines()[0]))
            print(f"  ! {rel}: anchor matched {count} times: {old.splitlines()[0][:80]!r}")
            continue
        pending += 1
        if args.check:
            print(f"  ~ {rel}: WOULD apply: {old.splitlines()[0][:80]!r}")
        else:
            path.write_text(text.replace(old, new, 1), encoding="utf-8")
            print(f"  + {rel}: applied: {old.splitlines()[0][:80]!r}")
    print(f"applied {applied}, pending {pending}, failed {len(failed)}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
