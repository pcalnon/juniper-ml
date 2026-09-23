"""Item 14 grounding: print each seeded generator's size-determining param defaults at juniper-data origin/main. Scratch only."""

from juniper_data.api.routes.generators import GENERATOR_REGISTRY

SEEDED = ["spiral", "xor", "mnist", "circles", "moon", "gaussian", "checkerboard", "equities", "multi_sine", "mackey_glass", "irregular_sine", "ar_p", "delay_product", "equities_seq"]
SIZE_WORDS = ("n_", "num", "length", "window", "symbols", "max_", "samples", "points", "steps", "dataset", "pad", "start_date", "end_date", "horizon", "stride", "lag", "order", "seq")

for name in SEEDED:
    info = GENERATOR_REGISTRY[name]
    fields = info["params_class"].model_fields
    shown = {k: f.default for k, f in fields.items() if any(w in k for w in SIZE_WORDS)}
    print(f"{name:15} task_type={info['task_type']!s:15} {shown}")
