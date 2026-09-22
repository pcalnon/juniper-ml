#!/usr/bin/env python3
"""Patch juniper-recurrence's bench/datasets.py to derive the retired ``*_full`` view.

Project:     Juniper
Sub-Project: juniper-ml
Application: ad-hoc cross-repo fix tooling
Author:      Paul Calnon
Created:     2026-09-21
Version:     0.1.0
License:     MIT License
Status:      single-use (decision-11 bench consumer break)

Why this exists
---------------
``bench/datasets.py`` reads ``out[f"{key}_full"]`` straight off the generator output.
Decision 11 (juniper-data#369) retired that family, so every one of the seven bench
datasets raises ``KeyError: 'X_full'``. Proven end-to-end:
``datasets.irregular_sine(n_steps=200, lookback=8)`` raises, and the generator emits
exactly the three partitions and no ``_full``.

The fix routes the generator output through
``juniper_recurrence_model.data.derive_full_split`` -- the canonical reconstruction,
already an installed dependency of bench. A hand-rolled ``np.concatenate`` is NOT
adequate, because ``equities_seq`` is one of the seven datasets: juniper-data built its
``_full`` ENTITY-major while the partitions are SPLIT-major, so a plain concatenation
holds the same rows in a different order as soon as ``symbols`` names more than one
ticker -- and walk-forward CV slices by row index. The default is a single ticker, where
the two orders coincide; the parameter is caller-supplied, so the difference is reachable.

Patching ``_full`` alone, rather than the six generator call sites, keeps the change to
one function. ``derive_full_split`` returns a NEW dict, so the derived keys are merged
back into ``out`` in place and the reconstruction happens once per dataset even though
``_full`` is called four times.

This runs against a COPY of the tree (``--root``), never the sibling checkout directly,
because ~20 concurrent sessions share these working trees.

Idempotent: exits 0 without writing if the patch is already present.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_ANCHOR = '''def _full(out: dict[str, np.ndarray], key: str) -> np.ndarray:
    return np.asarray(out[f"{key}_full"])
'''

_REPLACEMENT = '''def _full(out: dict[str, np.ndarray], key: str) -> np.ndarray:
    """Read one array from the whole-dataset view, deriving it on first use.

    Decision 11 (juniper-data#369) retired the ``*_full`` family from the NPZ contract,
    so the generators below emit only ``train`` / ``val`` / ``test`` and this used to be
    a bare ``KeyError`` on every dataset.

    ``derive_full_split`` rebuilds the view ENTITY-major, stable-sorting on
    ``ticker_code`` when the artifact carries one. That is load-bearing for
    ``equities_seq``: juniper-data laid its ``_full`` down entity-major while the
    partitions are split-major, so a plain ``np.concatenate`` would hold the same rows in
    a DIFFERENT order for any multi-ticker request, and walk-forward CV slices by row
    index -- a change to what the benchmark measures, not a refactor. A legacy artifact
    that still ships ``*_full`` keeps the producer's own arrays, byte for byte.

    The derived keys are merged back into ``out`` so the reconstruction runs once per
    dataset rather than once per call.
    """
    full_key = f"{key}_full"
    if full_key not in out:
        from juniper_recurrence_model.data import derive_full_split

        out.update(derive_full_split(out))
    if full_key not in out:
        available = ", ".join(sorted(out)) or "<empty>"
        raise KeyError(f"{full_key!r} could not be derived; generator emitted: {available}")
    return np.asarray(out[full_key])
'''


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", required=True, help="path to the tree holding bench/datasets.py")
    ap.add_argument("--check", action="store_true", help="report only; write nothing")
    args = ap.parse_args()

    target = Path(args.root) / "bench" / "datasets.py"
    if not target.is_file():
        print(f"ERROR: no such file: {target}", file=sys.stderr)
        return 1

    text = target.read_text(encoding="utf-8")

    if "derive_full_split" in text:
        print("already patched; nothing to do")
        return 0

    if text.count(_ANCHOR) != 1:
        print(f"ERROR: expected exactly one _full helper in its known form, found {text.count(_ANCHOR)}", file=sys.stderr)
        return 1

    if args.check:
        print(f"WOULD PATCH: {target}")
        return 1

    target.write_text(text.replace(_ANCHOR, _REPLACEMENT, 1), encoding="utf-8")
    print(f"patched {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
