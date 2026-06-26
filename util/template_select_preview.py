"""template_select_preview.py -- offline preview of the Template Agent's category selection.

Given a task description, prints which ``prompts/agent_templates/`` template the Template Agent
Skill's ``match_signals`` step would pick, with the matched keyword(s) and the ranked
runner-ups. This is an **offline preview heuristic** of the selection the Skill performs
interactively -- NOT a byte-for-byte reproduction of the Skill's LLM judgement (the Skill may
additionally ask the owner on a thin margin). It consumes ``prompts/agent_templates/manifest.yaml``
``match_signals`` and *executes* the selection design the selection lint
(``tests/test_template_selection.py``) only checks statically.

Scoring (deliberately simple, documented): case-insensitive substring count of each template's
``match_signals.keywords`` in the task text; ties broken by manifest order; ``generic`` (the
always-match fallback) is selected iff no keyword matches.

Path-invoked (``util/`` is not a package):

    python util/template_select_preview.py "TASK TEXT" [--repo-root PATH] [--json] [--top N]

Exit 0 always -- ``generic`` is the guaranteed fallback. Tests: ``tests/test_template_select_preview.py``.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover - PyYAML is normally present
    yaml = None


def _find_repo_root(start: Path):
    for parent in [start, *start.parents]:
        if (parent / ".github" / "workflows").is_dir():
            return parent
    return None


def _load_manifest(root: Path):
    path = root / "prompts" / "agent_templates" / "manifest.yaml"
    if not path.exists() or yaml is None:
        return None
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else None


def rank(task: str, templates) -> list:
    """Rank non-fallback templates by descending keyword-match count, then manifest order."""
    low = task.lower()
    ranked = []
    for order, tmpl in enumerate(templates):
        signals = tmpl.get("match_signals") or {}
        if signals.get("always") is True:
            continue  # the generic fallback is handled separately
        keywords = signals.get("keywords") or []
        matched = [k for k in keywords if k.lower() in low]
        ranked.append({"id": tmpl.get("id"), "class": tmpl.get("class"), "score": len(matched), "matched": matched, "order": order})
    ranked.sort(key=lambda r: (-r["score"], r["order"]))
    return ranked


def select(task: str, manifest: dict):
    """Return (selected, ranked). selected is the top scorer, else the generic fallback."""
    templates = manifest.get("templates") or []
    ranked = rank(task, templates)
    if ranked and ranked[0]["score"] > 0:
        return ranked[0], ranked
    fallback = next((t for t in templates if (t.get("match_signals") or {}).get("always") is True), None)
    selected = {
        "id": fallback.get("id") if fallback else "generic",
        "class": fallback.get("class") if fallback else "generic",
        "score": 0,
        "matched": [],
        "order": -1,
    }
    return selected, ranked


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Preview which template the Template Agent would select for a task (offline heuristic).",
        epilog="Preview heuristic only -- the Skill may additionally ask the owner on a thin selection margin.",
    )
    parser.add_argument("task", nargs="+", help="the task description text")
    parser.add_argument("--repo-root", default=None, help="suite repo root (default: walk up for .github/workflows/)")
    parser.add_argument("--json", action="store_true", help="machine-readable output")
    parser.add_argument("--top", type=int, default=3, help="how many ranked candidates to show")
    args = parser.parse_args(argv)

    root = Path(args.repo_root).resolve() if args.repo_root else _find_repo_root(Path.cwd())
    manifest = _load_manifest(root) if root else None
    task = " ".join(args.task)

    if manifest is None:
        # Degraded: cannot read the manifest; the guaranteed fallback is still 'generic'.
        selected = {"id": "generic", "class": "generic", "score": 0, "matched": [], "order": -1}
        ranked = []
        print("template_select_preview: could not load manifest.yaml; defaulting to 'generic'", file=sys.stderr)
    else:
        selected, ranked = select(task, manifest)

    if args.json:
        print(json.dumps({"task": task, "selected": selected, "candidates": ranked[: args.top]}, indent=2))
    else:
        print(f"task: {task}")
        print(f"selected: {selected['id']} (class={selected['class']}); matched keywords: {selected['matched'] or '(none -> generic fallback)'}")
        if ranked:
            print(f"top {min(args.top, len(ranked))} candidates (score / id / matched):")
            for cand in ranked[: args.top]:
                print(f"  {cand['score']}  {cand['id']:<22} {cand['matched']}")
        print("(preview heuristic; the Skill may ask the owner on a thin margin)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
