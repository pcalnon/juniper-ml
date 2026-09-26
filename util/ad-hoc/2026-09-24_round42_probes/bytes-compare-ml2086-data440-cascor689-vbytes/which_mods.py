"""Print where each named module resolves from (proves PYTHONPATH precedence)."""
import importlib
import sys

for name in sys.argv[1:]:
    try:
        mod = importlib.import_module(name)
        print(f"{name:28} {getattr(mod, '__file__', None)}")
    except Exception as exc:  # noqa: BLE001
        print(f"{name:28} IMPORT FAILED: {exc!r}")
