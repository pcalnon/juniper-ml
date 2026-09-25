"""Copy <head>/src to <out>/src and apply mutant NV1 there (scratch), so a probe can run against it."""

import os
import shutil
import sys

head, out = sys.argv[1], sys.argv[2]
shutil.rmtree(out, ignore_errors=True)
shutil.copytree(os.path.join(head, "src"), os.path.join(out, "src"), ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
path = os.path.join(out, "src/api/lifecycle/manager.py")
text = open(path, encoding="utf-8").read()
described = '        self._described_partitions = frozenset(name for name, tensor in (("train", new_train_x), ("val", new_val_x), ("test", new_test_x)) if tensor is not None)\n'
check = "        if refuse_wider_than is not None:\n"
assert text.count(described) == 1 and text.count(check) == 1
text = text.replace(described, "").replace(check, described + check)
open(path, "w", encoding="utf-8").write(text)
print("NV1 applied to", path)
