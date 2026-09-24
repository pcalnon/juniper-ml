#!/usr/bin/env python3
"""Lane A r2: census of every registered generator's `seed` default vs E.1 item 2's nonce rule.

E.1 item 2 (primer at b6129bf8, L9918-9920): "Since juniper-data#322 (2026-09-03) a generator's
documented default seed is DEFAULT_GENERATOR_SEED, so an omitted seed gives a deterministic id,
and only an explicit seed=None mixes in a per-call nonce."

For each generator in GENERATOR_REGISTRY this records: whether its params model has a `seed`
field, the field's default, whether None is admissible, and -- using the real
generate_dataset_id -- whether the omitted-seed id is stable across two calls and whether an
explicit seed=None id changes across two calls. Also computes the equities id twice from the
model's defaults (end_date=None) to show the id carries no date.
`get_secret` is stubbed first so no secret file can be read.
"""
from __future__ import annotations

import json
import sys
import typing
from pathlib import Path

HERE = Path(__file__).resolve().parent
TREE = HERE / "jd_main_1afc3484"
sys.path.insert(0, str(TREE))

import juniper_data.core.secrets as _secrets  # noqa: E402

_secrets.get_secret = lambda *a, **k: None

import juniper_data  # noqa: E402
from juniper_data.api.routes.generators import GENERATOR_REGISTRY  # noqa: E402
from juniper_data.core import constants as C  # noqa: E402
from juniper_data.core.dataset_id import generate_dataset_id  # noqa: E402

assert str(TREE) in juniper_data.__file__

rows = []
for name, info in GENERATOR_REGISTRY.items():
    pc = info["params_class"]
    version = str(info.get("version", "?"))
    f = pc.model_fields.get("seed")
    row = {"generator": name, "version": version, "params_class": pc.__name__, "has_seed": f is not None}
    if f is not None:
        row["seed_default"] = f.default
        row["seed_default_is_DEFAULT_GENERATOR_SEED_value"] = f.default == C.DEFAULT_GENERATOR_SEED
        ann = f.annotation
        row["seed_annotation"] = str(ann)
        row["none_admissible"] = type(None) in typing.get_args(ann) or ann is type(None)
    omitted = {"seed": f.default} if f is not None else {}
    ids_omitted = {generate_dataset_id(name, version, dict(omitted)) for _ in range(2)}
    ids_none = {generate_dataset_id(name, version, {"seed": None}) for _ in range(2)}
    row["omitted_seed_id_stable"] = len(ids_omitted) == 1
    row["explicit_none_id_varies"] = len(ids_none) == 2
    rows.append(row)

eq = GENERATOR_REGISTRY.get("equities")
eq_out = None
if eq is not None:
    dump = eq["params_class"].model_construct().model_dump()
    v = str(eq.get("version"))
    eq_out = {"end_date_default": dump.get("end_date"), "seed_default": dump.get("seed"),
              "id_twice_equal": generate_dataset_id("equities", v, dump) == generate_dataset_id("equities", v, dump)}

out = {"DEFAULT_GENERATOR_SEED": C.DEFAULT_GENERATOR_SEED, "n_generators": len(rows), "rows": rows, "equities": eq_out}
try:
    from juniper_data.generators.spiral import defaults as sd  # noqa: E402
    out["SPIRAL_DEFAULT_SEED"] = getattr(sd, "SPIRAL_DEFAULT_SEED", "n/a")
except Exception as exc:  # pragma: no cover
    out["SPIRAL_DEFAULT_SEED"] = f"lookup failed: {exc!r}"
(HERE / "probe_seed_census.json").write_text(json.dumps(out, indent=1, default=str), encoding="utf-8")
print(f"DEFAULT_GENERATOR_SEED={out['DEFAULT_GENERATOR_SEED']} SPIRAL_DEFAULT_SEED={out['SPIRAL_DEFAULT_SEED']} generators={len(rows)}")
for r in rows:
    print(f"{r['generator']:15s} v={r['version']:8s} seed={r.get('seed_default', '(no field)')!s:6s} "
          f"=DGS:{r.get('seed_default_is_DEFAULT_GENERATOR_SEED_value', '-')!s:5s} None_ok:{r.get('none_admissible', '-')!s:5s} "
          f"omitted_stable:{r['omitted_seed_id_stable']!s:5s} none_varies:{r['explicit_none_id_varies']}")
print("equities:", eq_out)
