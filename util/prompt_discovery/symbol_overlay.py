"""Serena symbol overlay (design OQ-8): merge Skill-resolved Serena facts into a bundle.

The path-invoked ``symbol_probe`` (``cli.py``) resolves symbols via grep because a standalone
script cannot reach the Serena MCP tools. The Template Agent **Skill** runs in the main
conversation, which DOES have MCP access, so it can call Serena ``find_symbol`` /
``find_declaration`` for the task's named symbols and merge the richer facts here:

- a Serena-**resolved** symbol replaces the grep entry (and records ``source: "serena"``);
- a Serena entry that did NOT resolve keeps the existing grep entry, if any (grep fallback);
- otherwise the symbol stays ``UNRESOLVED``.

This touches only the bundle *consumer*, NOT ``cli.py`` / ``symbol_probe.py``'s contract (it
adds the ``source`` / ``overlay`` keys here, on the overlay side). ``util/`` is not a package;
imported via the house ``sys.path.insert`` idiom or invoked by path. Tests:
``tests/test_symbol_overlay.py``.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def merge_symbol_probe(bundle: dict, serena: dict) -> dict:
    """Return a copy of ``bundle`` with ``serena`` facts overlaid onto its ``symbol_probe`` slice.

    ``serena`` maps a symbol name -> ``{"status": "resolved"|"unresolved", "definition": ...,
    "signature": ...}``. The input bundle is not mutated.
    """
    out = dict(bundle)
    slice_ = dict(out.get("symbol_probe") or {})
    symbols = {name: dict(fact) for name, fact in (slice_.get("symbols") or {}).items()}
    for name, fact in (serena or {}).items():
        fact = fact or {}
        grep = symbols.get(name)
        if fact.get("status") == "resolved" and fact.get("definition"):
            symbols[name] = {
                "status": "resolved",
                "definition": fact.get("definition"),
                "signature": fact.get("signature"),
                "source": "serena",
            }
        elif grep and grep.get("status") == "resolved":
            symbols[name] = {**grep, "source": grep.get("source", "grep")}
        else:
            symbols[name] = {"status": "unresolved", "definition": None, "signature": None, "source": "serena"}
    slice_["symbols"] = symbols
    slice_["overlay"] = "serena"
    out["symbol_probe"] = slice_
    return out


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Overlay Serena symbol facts onto a discovery bundle's symbol_probe (OQ-8).")
    parser.add_argument("--bundle", required=True, help="path to the grounding-bundle JSON")
    parser.add_argument("--serena", required=True, help="path to the Serena results JSON (name -> {status,definition,signature})")
    args = parser.parse_args(argv)
    bundle = json.loads(Path(args.bundle).read_text(encoding="utf-8"))
    serena = json.loads(Path(args.serena).read_text(encoding="utf-8"))
    print(json.dumps(merge_symbol_probe(bundle, serena), indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
