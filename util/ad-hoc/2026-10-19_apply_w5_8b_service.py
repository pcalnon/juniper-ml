#!/usr/bin/env python3
"""Apply the W5.8 (B) service half to a juniper-recurrence tree (exact-string edits).

Project: juniper-ml
Sub-Project: recurrence x equities (plan W5.8 (B), service half; recurrence 0.7.0)
Author: Paul Calnon
Created: 2026-10-19
Status: ad-hoc, single-use (kept for the record of exactly what the service PR changed)
Related: notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md
         (W5.8 Details); util/ad-hoc/2026-10-19_apply_w5_9_w5_8b_model.py (the model half, model
         0.5.0, which this floor requires); util/ad-hoc/2026-10-19_w5_8b_eh_acceptance.py (the
         numbers quoted)

Usage:
    python3 util/ad-hoc/2026-10-19_apply_w5_8b_service.py --root <juniper-recurrence checkout> [--check]

Edits (each an exact-string replacement that must match exactly once):

* ``juniper-recurrence/juniper_recurrence/settings.py`` -- ``default_ridge`` ``0.0`` -> ``"gcv"``.
* ``juniper-recurrence/pyproject.toml`` -- the three ``juniper-recurrence-model`` floors move to
  ``>=0.5.0,<0.6.0`` (the standardising model is what makes the GCV default safe).
* ``juniper-recurrence/requirements.lock`` -- the image pin ``juniper-recurrence-model==0.5.0``.
* ``conf/experiments/irregular-sine-rff.yaml`` -- ``service.default_ridge: gcv`` (the E-H suite's base config).
* ``juniper-recurrence/tests/test_settings.py``, ``tests/test_readout_diagnostics.py`` -- the default
  pinned; the W5.9 flags are booleans on a GCV fit now that the model reports them.
* ``juniper-recurrence/README.md``, ``CHANGELOG.md`` -- the route prose and the ``[Unreleased]`` Changed entry.
"""

from __future__ import annotations

import argparse
import pathlib
import sys

EDITS: list[tuple[str, str, str]] = []


def edit(path: str, old: str, new: str) -> None:
    EDITS.append((path, old, new))


APP = "juniper-recurrence/"

# --- settings ----------------------------------------------------------------------------------

edit(
    APP + "juniper_recurrence/settings.py",
    """    # --- LMU hyperparameter defaults (consumed by the PR-2 training path) -------------
    default_d: int = 16
    default_theta: float | None = None
    default_ridge: float | Literal["gcv"] = 0.0
""",
    """    # --- LMU hyperparameter defaults (consumed by the PR-2 training path) -------------
    default_d: int = 16
    default_theta: float | None = None
    # ``"gcv"`` since 0.7.0 (W5.8 (B) of the juniper-ml recurrence x equities plan; owner ruling
    # 2026-10-18). A linear-readout request that omits ``ridge`` -- a bare ``/v1/train`` or
    # ``/v1/crossval``, canopy's registry seed, the ``train`` CLI without ``--ridge`` -- used to get
    # ``0.0``, the raw min-norm solve, which extrapolates on a drifting input: -2.1e4 aggregate r2 on
    # the W5.1 equities artifact. GCV on the train-fold-standardised block (juniper-recurrence-model
    # 0.5.0 standardises for any non-zero ridge) abstains instead (-0.195, lambda at the grid ceiling,
    # ``null_model: true``), and the response's ``diagnostics`` block says so (W5.10). An explicit
    # ``ridge`` in the request still wins; ``LMURegressor``'s own constructor default stays ``0.0``.
    default_ridge: float | Literal["gcv"] = "gcv"
""",
)

# --- pyproject / lock --------------------------------------------------------------------------

edit(
    APP + "pyproject.toml",
    """dependencies = [
    "fastapi>=0.110",
""",
    """# Floor raised to juniper-recurrence-model >=0.5.0 (W5.8 (B) + W5.9, 2026-10-19): the "gcv"
# default_ridge the service ships from 0.7.0 is safe only on a model that standardises the linear
# rung's memory block on the train fold (GCV on the raw block scores -247 on the W5.1 artifact);
# 0.5.0 does, and sets the gcv_at_edge_ / null_model_ fit diagnostics the W5.10 response block reads.
dependencies = [
    "fastapi>=0.110",
""",
)

edit(
    APP + "pyproject.toml",
    """    "juniper-recurrence-model>=0.4.0,<0.5.0",
    "juniper-data-client>=0.6.0,<0.7.0",
""",
    """    "juniper-recurrence-model>=0.5.0,<0.6.0",
    "juniper-data-client>=0.6.0,<0.7.0",
""",
)

edit(
    APP + "pyproject.toml",
    """torch = [
    "juniper-recurrence-model[torch]>=0.4.0,<0.5.0",
]
""",
    """torch = [
    "juniper-recurrence-model[torch]>=0.5.0,<0.6.0",
]
""",
)

edit(
    APP + "pyproject.toml",
    """bench-torch = [
    "juniper-recurrence-model[torch]>=0.4.0,<0.5.0",
]
""",
    """bench-torch = [
    "juniper-recurrence-model[torch]>=0.5.0,<0.6.0",
]
""",
)

edit(
    APP + "requirements.lock",
    """# pre-flight is unaffected. The ``pyproject.toml`` floors do not move: both ranges already admit
# these releases.
annotated-doc==0.0.5
""",
    """# pre-flight is unaffected. The ``pyproject.toml`` floors do not move: both ranges already admit
# these releases.
#
# MOVED 2026-10-19, TARGETED, for the 0.7.0 image (W5.8 (B) + W5.9 of the same plan):
# ``juniper-recurrence-model`` 0.4.0 -> **0.5.0** (train-fold standardisation on the linear rung for
# any non-zero ridge, and the ``gcv_at_edge_`` / ``null_model_`` fit diagnostics the W5.10 response
# block reads). The ONLY pin change; the count is unchanged at 31. 0.5.0 changed none of its own
# requirements (its PyPI ``requires_dist`` equals 0.4.0's), so no other pin can move; the line was
# moved by hand as on 2026-10-17, and the pin is a pure-Python wheel (the arm64 pre-flight is
# unaffected). The ``pyproject.toml`` floor moves with it this time: the service's new
# ``default_ridge: "gcv"`` is safe only on a model that standardises the linear rung's memory block.
annotated-doc==0.0.5
""",
)

edit(
    APP + "requirements.lock",
    """juniper-recurrence-model==0.4.0
""",
    """juniper-recurrence-model==0.5.0
""",
)

# --- the E-H suite's base config ---------------------------------------------------------------

edit(
    "conf/experiments/irregular-sine-rff.yaml",
    """  default_theta: null                  # null = data-driven θ
  default_ridge: 0.0
""",
    """  default_theta: null                  # null = data-driven θ
  default_ridge: gcv                   # the 0.7.0 service default (W5.8 (B)); the train: block below pins its own ridge
""",
)

# --- tests -------------------------------------------------------------------------------------

edit(
    APP + "tests/test_settings.py",
    """    assert settings.default_theta is None
    assert settings.default_ridge == 0.0
""",
    """    assert settings.default_theta is None
    assert settings.default_ridge == "gcv"  # W5.8 (B), 0.7.0: a bare linear request abstains rather than extrapolates
""",
)

edit(
    APP + "tests/test_settings.py",
    """def test_default_ridge_accepts_gcv():
    \"\"\"default_ridge widens to float | Literal['gcv'] (DP-3 P1); the 0.0 default is unchanged.\"\"\"
    assert Settings(default_ridge="gcv").default_ridge == "gcv"
    assert Settings().default_ridge == 0.0
""",
    """def test_default_ridge_accepts_gcv_and_a_float():
    \"\"\"default_ridge is float | Literal['gcv'] (DP-3 P1); 'gcv' is the default since 0.7.0 (W5.8 (B)) and 0.0 opts back out.\"\"\"
    assert Settings().default_ridge == "gcv"
    assert Settings(default_ridge=0.0).default_ridge == 0.0
    assert Settings(default_ridge=0.5).default_ridge == 0.5
""",
)

TD = APP + "tests/test_readout_diagnostics.py"

edit(
    TD,
    """def test_diagnostics_linear_service_default_ridge_is_fixed_zero() -> None:
    # A bare request: ridge=None falls back to default_ridge (0.0 today), and the block says so.
    diag = readout_diagnostics(_fitted(theta=2.0, ridge=None, default_ridge=0.0))
    assert diag.ridge_mode == "fixed"
    assert diag.ridge_selected == 0.0
""",
    """def test_diagnostics_linear_service_default_ridge_is_gcv_and_an_explicit_zero_is_fixed() -> None:
    # A bare request: ridge=None falls back to Settings().default_ridge -- "gcv" since 0.7.0 (W5.8 (B)) --
    # and the block says so; a deployment that sets default_ridge back to 0.0 is reported as fixed 0.0.
    diag = readout_diagnostics(_fitted(theta=2.0, ridge=None, default_ridge=Settings().default_ridge))
    assert diag.ridge_mode == "gcv"
    assert GCV_FLOOR <= diag.ridge_selected <= GCV_CEILING
    assert isinstance(diag.gcv_at_edge, bool) and isinstance(diag.null_model, bool)  # the model reports both (W5.9)
    diag = readout_diagnostics(_fitted(theta=2.0, ridge=None, default_ridge=0.0))
    assert diag.ridge_mode == "fixed"
    assert diag.ridge_selected == 0.0
""",
)

edit(
    TD,
    """def test_diagnostics_gcv_reports_the_selected_lambda_and_the_edge_flag() -> None:
    diag = readout_diagnostics(_fitted(theta=2.0, ridge="gcv"))
    assert diag.ridge_mode == "gcv"
    assert diag.ridge_selected is not None
    assert GCV_FLOOR <= diag.ridge_selected <= GCV_CEILING
    assert isinstance(diag.gcv_at_edge, bool)
    assert diag.gcv_at_edge == (diag.ridge_selected in (GCV_FLOOR, GCV_CEILING))
""",
    """def test_diagnostics_gcv_reports_the_selected_lambda_and_the_edge_flag() -> None:
    diag = readout_diagnostics(_fitted(theta=2.0, ridge="gcv"))
    assert diag.ridge_mode == "gcv"
    assert diag.ridge_selected is not None
    assert GCV_FLOOR <= diag.ridge_selected <= GCV_CEILING
    assert isinstance(diag.gcv_at_edge, bool)
    assert diag.gcv_at_edge == (diag.ridge_selected in (GCV_FLOOR, GCV_CEILING))
    assert isinstance(diag.null_model, bool)  # model 0.5.0 (W5.9) sets null_model_ on every GCV fit


def test_diagnostics_take_the_models_w5_9_flags_verbatim() -> None:
    # juniper-recurrence-model 0.5.0 sets gcv_at_edge_ / null_model_ on the fitted readout after a GCV
    # fit; the block carries exactly those, not a re-derivation.
    model = _fitted(theta=2.0, ridge="gcv")
    assert isinstance(model._readout.gcv_at_edge_, bool) and isinstance(model._readout.null_model_, bool)
    diag = readout_diagnostics(model)
    assert diag.gcv_at_edge is model._readout.gcv_at_edge_
    assert diag.null_model is model._readout.null_model_
""",
)

edit(
    TD,
    """    # The flag is a function of the selected lambda and the grid's two ends; pin it at both ends and
    # in the middle by overriding what the fitted readout reports as its selection.
    model = _fitted(theta=2.0, ridge="gcv")
    model._readout.ridge = selected
    assert readout_diagnostics(model).gcv_at_edge is expected
""",
    """    # The flag is a function of the selected lambda and the grid's two ends; pin it at both ends and
    # in the middle by overriding what the fitted readout reports as its selection. The model's own
    # flag (set since model 0.5.0) wins when present, so clear it to exercise the fallback derivation.
    model = _fitted(theta=2.0, ridge="gcv")
    model._readout.ridge = selected
    model._readout.gcv_at_edge_ = None
    assert readout_diagnostics(model).gcv_at_edge is expected
""",
)

edit(
    TD,
    """    model = _fitted(theta=2.0, ridge="gcv")  # the fit itself needs the grid; hide it only from the read
    monkeypatch.delattr(model_readouts, "_GCV_GRID")
    diag = readout_diagnostics(model)
""",
    """    model = _fitted(theta=2.0, ridge="gcv")  # the fit itself needs the grid; hide it only from the read
    model._readout.gcv_at_edge_ = None  # and pretend the readout did not report its own flag (pre-0.5.0 model)
    monkeypatch.delattr(model_readouts, "_GCV_GRID")
    diag = readout_diagnostics(model)
""",
)

edit(
    TD,
    """def test_train_response_carries_the_fits_diagnostics(fake_data) -> None:
    body = _client(api_keys=None).post("/v1/train", json={"dataset": {"dataset_id": "ds-1"}, "d": 4, "theta": 3.0}).json()
    assert set(body["diagnostics"]) == DIAGNOSTIC_KEYS
    assert body["diagnostics"] == {"readout": "linear", "theta": 3.0, "ridge_mode": "fixed", "ridge_selected": 0.0, "gamma": None, "gcv_at_edge": None, "null_model": None}
""",
    """def test_train_response_carries_the_fits_diagnostics(fake_data) -> None:
    body = _client(api_keys=None).post("/v1/train", json={"dataset": {"dataset_id": "ds-1"}, "d": 4, "theta": 3.0, "ridge": 0.0}).json()
    assert set(body["diagnostics"]) == DIAGNOSTIC_KEYS
    assert body["diagnostics"] == {"readout": "linear", "theta": 3.0, "ridge_mode": "fixed", "ridge_selected": 0.0, "gamma": None, "gcv_at_edge": None, "null_model": None}


def test_bare_train_request_gets_the_gcv_default_and_the_response_says_so(fake_data) -> None:
    # W5.8 (B): a request that omits ``ridge`` is GCV-selected since 0.7.0, and the block announces the
    # lambda it chose and whether the fit abstained -- the default must not be silent.
    body = _client(api_keys=None).post("/v1/train", json={"dataset": {"dataset_id": "ds-1"}, "d": 4, "theta": 3.0}).json()
    diag = body["diagnostics"]
    assert diag["readout"] == "linear" and diag["ridge_mode"] == "gcv"
    assert GCV_FLOOR <= diag["ridge_selected"] <= GCV_CEILING
    assert isinstance(diag["gcv_at_edge"], bool) and isinstance(diag["null_model"], bool)


def test_bare_train_request_honours_a_deployment_that_opts_back_to_zero(fake_data) -> None:
    body = _client(api_keys=None, default_ridge=0.0).post("/v1/train", json={"dataset": {"dataset_id": "ds-1"}, "d": 4, "theta": 3.0}).json()
    assert body["diagnostics"]["ridge_mode"] == "fixed" and body["diagnostics"]["ridge_selected"] == 0.0
""",
)

edit(
    TD,
    """    assert diag["ridge_mode"] == "gcv"
    assert GCV_FLOOR <= diag["ridge_selected"] <= GCV_CEILING
    assert isinstance(diag["gcv_at_edge"], bool)
    assert diag["null_model"] is None


# --- /v1/crossval carries one block per fold, and the status re-serves it -----------------------


def test_crossval_response_carries_per_fold_diagnostics(fake_full_data) -> None:
    body = _client(api_keys=None).post("/v1/crossval", json={"dataset": {"dataset_id": "ds-1"}, "n_folds": 3, "d": 4, "ridge": "gcv"}).json()
    assert len(body["folds"]) == 3
    for fold in body["folds"]:
        diag = fold["diagnostics"]
        assert set(diag) == DIAGNOSTIC_KEYS
        assert diag["readout"] == "linear"
        assert diag["theta"] > 0  # each fold resolved its own data-driven theta
        assert diag["ridge_mode"] == "gcv"
        assert GCV_FLOOR <= diag["ridge_selected"] <= GCV_CEILING
        assert isinstance(diag["gcv_at_edge"], bool)
        assert diag["gamma"] is None
        assert diag["null_model"] is None
""",
    """    assert diag["ridge_mode"] == "gcv"
    assert GCV_FLOOR <= diag["ridge_selected"] <= GCV_CEILING
    assert isinstance(diag["gcv_at_edge"], bool)
    assert isinstance(diag["null_model"], bool)  # reported by model 0.5.0 (W5.9)


# --- /v1/crossval carries one block per fold, and the status re-serves it -----------------------


@pytest.mark.parametrize("request_ridge", [{"ridge": "gcv"}, {}], ids=["explicit-gcv", "bare-request"])
def test_crossval_response_carries_per_fold_diagnostics(fake_full_data, request_ridge) -> None:
    # Explicit ``ridge="gcv"`` and the bare request (the W5.8 (B) default) are the same fit, and every
    # fold's block reports the lambda it selected -- the response half of W5.8's acceptance.
    body = _client(api_keys=None).post("/v1/crossval", json={"dataset": {"dataset_id": "ds-1"}, "n_folds": 3, "d": 4, **request_ridge}).json()
    assert len(body["folds"]) == 3
    for fold in body["folds"]:
        diag = fold["diagnostics"]
        assert set(diag) == DIAGNOSTIC_KEYS
        assert diag["readout"] == "linear"
        assert diag["theta"] > 0  # each fold resolved its own data-driven theta
        assert diag["ridge_mode"] == "gcv"
        assert GCV_FLOOR <= diag["ridge_selected"] <= GCV_CEILING
        assert isinstance(diag["gcv_at_edge"], bool)
        assert diag["gamma"] is None
        assert isinstance(diag["null_model"], bool)
""",
)

# --- README / CHANGELOG ------------------------------------------------------------------------

edit(
    APP + "README.md",
    """extra; returns `503` if torch is not installed). `ridge` accepts a float or `"gcv"` (closed-form
generalized-cross-validation selection). See the `juniper-recurrence-model` README for the spectrum.
""",
    """extra; returns `503` if torch is not installed). `ridge` accepts a float or `"gcv"` (closed-form
generalized-cross-validation selection). A linear-readout request that omits `ridge` gets the
service's `default_ridge`, **`"gcv"` since 0.7.0** (plan W5.8 (B)): the penalty is GCV-selected on
the train-fold-standardised memory block, so on a drifting input the fit abstains (lambda at the grid
ceiling, `null_model: true` in `diagnostics`) rather than extrapolate as the former `0.0` min-norm
default did. An explicit `ridge: 0.0`, or `JUNIPER_RECURRENCE_DEFAULT_RIDGE=0.0` on the service,
restores the old behaviour. See the `juniper-recurrence-model` README for the spectrum.
""",
)

edit(
    APP + "CHANGELOG.md",
    """  made null-model-aware without it, and the W5.8 (B) default (`default_ridge: "gcv"`), which
  abstains silently, is gated on the response announcing the lambda it chose.

## [0.6.1] - 2026-10-18
""",
    """  made null-model-aware without it, and the W5.8 (B) default (`default_ridge: "gcv"`), which
  abstains silently, is gated on the response announcing the lambda it chose.

### Changed

- **The service's `default_ridge` is `"gcv"`; the floor is `juniper-recurrence-model>=0.5.0`**
  (W5.8 (B) of juniper-ml
  `notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md`;
  accepted by the owner 2026-10-18, gated on W5.10 above). A linear-readout request that omits
  `ridge` -- a bare `POST /v1/train` or `POST /v1/crossval`, canopy's registry seed (no `readout`,
  no `ridge`), the `train` CLI without `--ridge` -- used to get `0.0`, the raw min-norm solve, which
  extrapolates on a non-stationary input (the W5.1 cause of record). It now gets closed-form GCV on
  the memory block that juniper-recurrence-model 0.5.0 standardises with the train-fold statistics
  for any non-zero ridge, and the response's `diagnostics` block reports the lambda it chose and
  whether the fit abstained (`gcv_at_edge` / `null_model`, both booleans now that the model sets
  them). Measured on the W5.1 equities artifact, five expanding folds
  (`util/ad-hoc/2026-10-19_w5_8b_eh_acceptance.py` in juniper-ml, mirroring the route's per-fold
  fit): the old default aggregates **−2.1e4** eval r² (embargo 2; −2.3e4 with the route's default
  embargo 0), the new default **−0.195** (−0.190), with lambda = 1000 at the grid ceiling and
  `null_model: true` in every fold -- the abstention the consensus re-derivation measured
  (`reports/2026-10-05_recurrence-equities-cv-consensus/reconciler-rederive.json`: GCV alone on the
  raw block −247, standardisation alone with `ridge=1.0` −192, both together −0.195). The
  alternative that retains a fit, a default *readout* change, was declined (W5.11). An explicit
  `ridge: 0.0` in the request, or `JUNIPER_RECURRENCE_DEFAULT_RIDGE=0.0` on the deployment, restores
  the old behaviour; `LMURegressor`'s own constructor default is unchanged. The floor moves to
  `juniper-recurrence-model>=0.5.0,<0.6.0` (also the `[torch]` / `[bench-torch]` extras and the
  image lock) because GCV without the standardisation scores −247: the default is safe only on the
  standardising model. `conf/experiments/irregular-sine-rff.yaml` sets `service.default_ridge: gcv`
  in the same change (its `train:` block pins the RFF readout at `ridge: 1.0` and is unaffected).

## [0.6.1] - 2026-10-18
""",
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--root", required=True, help="juniper-recurrence checkout root")
    parser.add_argument("--check", action="store_true", help="report each edit's state; write nothing")
    args = parser.parse_args()
    root = pathlib.Path(args.root)
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
