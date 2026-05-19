"""``python -m juniper_doc_tools`` entry point.

Provides the module-form invocation alongside the ``juniper-check-doc-links``
console script (decided in plan §8.3). Both route through :func:`cli.main`
so they cannot diverge.
"""

import sys

from juniper_doc_tools.cli import main

if __name__ == "__main__":
    sys.exit(main())
