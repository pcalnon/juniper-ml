"""Resolver for the custom-agent suite data layer (``prompts/agent_templates/data/*.yaml``).

Loads the curated, versioned YAML the Template Agent maps into template slots and that
RUBRIC R2.5 checks injected conventions against (design §5.7). ``util/`` is not a package,
so this is imported via the house ``sys.path.insert`` idiom or invoked by path:

    python util/template_data_resolver.py conventions.handoff_threshold

Behavioural coverage: ``tests/test_template_data_resolver.py``.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml

# The data files that make up the layer (without the .yaml suffix), in load order.
DATA_FILES = ("standing_rules", "anti_hallucination", "conventions", "ecosystem", "known_misses")


def _repo_root_default() -> Path:
    # util/template_data_resolver.py -> util/ -> repo root
    return Path(__file__).resolve().parent.parent


def data_dir(repo_root=None) -> Path:
    root = Path(repo_root) if repo_root else _repo_root_default()
    return root / "prompts" / "agent_templates" / "data"


def load(repo_root=None) -> dict:
    """Load every ``prompts/agent_templates/data/<name>.yaml`` into a dict keyed by ``<name>``."""
    base = data_dir(repo_root)
    out: dict = {}
    for name in DATA_FILES:
        path = base / f"{name}.yaml"
        if path.exists():
            out[name] = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return out


def resolve(key_path: str, repo_root=None, default=None):
    """Dotted lookup across the merged data, e.g. ``resolve('conventions.line_length')``."""
    cur = load(repo_root)
    for part in key_path.split("."):
        if isinstance(cur, dict) and part in cur:
            cur = cur[part]
        else:
            return default
    return cur


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Resolve custom-agent-suite data-layer values.")
    parser.add_argument("key", nargs="?", help="dotted key path, e.g. conventions.handoff_threshold")
    parser.add_argument("--repo-root", default=None)
    parser.add_argument("--json", action="store_true", help="emit JSON")
    args = parser.parse_args(argv)
    if args.key:
        value = resolve(args.key, args.repo_root)
        print(json.dumps(value, indent=2) if args.json else value)
        return 0 if value is not None else 1
    print(json.dumps(load(args.repo_root), indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
