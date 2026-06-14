"""Guard the load-bearing design property: ``import juniper_model_core`` pulls no numpy.

The contract references numpy only in type annotations (under ``TYPE_CHECKING``), so the
top-level package must import cleanly even when numpy is unavailable. This is what lets the
TestPyPI publish-verify use a clean ``--no-deps`` import check. We assert it by importing in a
subprocess that actively blocks ``numpy`` from importing.
"""

import subprocess
import sys
import textwrap


def test_top_level_import_does_not_require_numpy():
    code = textwrap.dedent(
        """
        import sys

        class _NumpyBlocker:
            def find_spec(self, name, path=None, target=None):
                if name == "numpy" or name.startswith("numpy."):
                    raise ImportError("numpy is intentionally blocked for this test")
                return None

        # Evict any pre-imported numpy, then block further imports of it.
        for mod in [m for m in list(sys.modules) if m == "numpy" or m.startswith("numpy.")]:
            del sys.modules[mod]
        sys.meta_path.insert(0, _NumpyBlocker())

        import juniper_model_core

        assert juniper_model_core.TrainableModel is not None
        assert juniper_model_core.validate_topology is not None
        assert "numpy" not in sys.modules, "top-level import unexpectedly pulled numpy"
        print("DEPENDENCY_FREE_OK")
        """
    )
    result = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
    assert result.returncode == 0, f"subprocess failed:\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
    assert "DEPENDENCY_FREE_OK" in result.stdout
