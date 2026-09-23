"""AST-read juniper-data origin/main's GENERATOR_REGISTRY keys + task_type (item 10). Scratch analysis only."""

import ast
import subprocess

REPO = "/home/pcalnon/Development/python/Juniper/juniper-data"
source = subprocess.run(["git", "-C", REPO, "show", "origin/main:juniper_data/api/routes/generators.py"], check=True, capture_output=True, text=True).stdout
tree = ast.parse(source)

registry = None
for node in ast.walk(tree):
    if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) and node.target.id == "GENERATOR_REGISTRY":
        registry = node.value
    elif isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "GENERATOR_REGISTRY" for t in node.targets):
        registry = node.value

assert isinstance(registry, ast.Dict), type(registry)
names = []
for key, value in zip(registry.keys, registry.values):
    name = ast.literal_eval(key) if isinstance(key, ast.Constant) else ast.unparse(key)
    task = None
    if isinstance(value, ast.Dict):
        for k2, v2 in zip(value.keys, value.values):
            if isinstance(k2, ast.Constant) and k2.value == "task_type":
                task = ast.unparse(v2)
    names.append(name)
    print(f"{name!s:16} task_type={task}")

print(f"count={len(names)}")
KNOWN_2026_09_09 = {"spiral", "xor", "gaussian", "circles", "moon", "checkerboard", "csv_import", "equities", "equities_seq", "multi_sine", "mackey_glass", "ar_p", "irregular_sine", "delay_product", "mnist", "arc_agi"}
print("added_upstream:", sorted(set(names) - KNOWN_2026_09_09))
print("removed_upstream:", sorted(KNOWN_2026_09_09 - set(names)))
