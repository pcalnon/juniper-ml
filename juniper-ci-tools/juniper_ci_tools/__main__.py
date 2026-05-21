"""``python -m juniper_ci_tools`` entry point.

Provides the module-form invocation alongside the
``juniper-generate-dep-docs`` console script (mirrors the doc-tools pattern).
Both route through :func:`cli.main` so they cannot diverge.
"""

import sys

from juniper_ci_tools.cli import main

if __name__ == "__main__":
    sys.exit(main())
