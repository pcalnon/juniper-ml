"""``python -m juniper_config_tools`` entry point.

Provides ``--version`` for parity with the sibling juniper-ci-tools /
juniper-doc-tools packages' module-form invocations. There is no CLI
beyond ``--version`` in 0.1.0 — the helper is a library-only API.
"""

from __future__ import annotations

import argparse
import sys

from juniper_config_tools._version import __version__


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m juniper_config_tools",
        description="juniper-config-tools — stdlib-only config helpers.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.parse_args(argv)
    return 0


if __name__ == "__main__":
    sys.exit(main())
