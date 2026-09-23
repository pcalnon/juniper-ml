"""Apply one named mutation to the item-5 worktree (restore from the .bak files between runs)."""

import sys
from pathlib import Path

ROOT = Path("/home/pcalnon/Development/python/Juniper/worktrees/juniper-canopy--feat--request-nn-model-mirror--20260923-0230--2f973ca2/src")
MUTATIONS = {
    # M10: the stage route forwards the routing key to the backend.
    "M10": (
        "main.py",
        '        params = body.model_dump(exclude_none=True, exclude={"nn_model"})\n        result = await offload(backend.stage_dataset, **params)',
        "        params = body.model_dump(exclude_none=True)  # MUTATION M10\n        result = await offload(backend.stage_dataset, **params)",
    ),
    # M11: apply-dataset never mirrors the model.
    "M11": (
        "frontend/dashboard_manager.py",
        '        if nn_model:\n            payload["nn_model"] = nn_model',
        "        pass  # MUTATION M11",
    ),
    # M12: the routing key leaks into params (the applied store).
    "M12": (
        "frontend/dashboard_manager.py",
        '        body = {**params, "nn_model": nn_model} if nn_model else params',
        '        if nn_model:\n            params["nn_model"] = nn_model  # MUTATION M12\n        body = params',
    ),
}

name = sys.argv[1]
rel, old, new = MUTATIONS[name]
path = ROOT / rel
text = path.read_text()
assert text.count(old) == 1, f"{name}: expected one match, found {text.count(old)}"
path.write_text(text.replace(old, new))
print(f"applied {name} to {rel}")
