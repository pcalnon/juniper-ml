"""agent_suite_summary.py -- quick reference for the Juniper custom-agent suite.

A ``--list``-style summary so you can recall "which agent / which template" without opening
eight files: one section for the agents (name, one-line description, tools, model/effort) and
one for the templates (id, class, when-to-use, required_fields). The human counterpart to the
machine-readable ``agent_suite_doctor.py``; building it proves the agent frontmatter and the
manifest are machine-summarizable.

Path-invoked (``util/`` is not a package):

    python util/agent_suite_summary.py [--repo-root PATH] [--agents | --templates] [--json | --markdown]

Read-only; exit 0. Tests: ``tests/test_agent_suite_summary.py``.
(Shares trivial frontmatter/manifest readers with ``agent_suite_doctor.py`` -- a future cleanup
could factor them into one stdlib module; kept inline here so each utility stays standalone.)
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

_TRUNC = 96  # keep summary lines (and --markdown rows) well under the 512 line-length cap


def _find_repo_root(start: Path):
    for parent in [start, *start.parents]:
        if (parent / ".github" / "workflows").is_dir():
            return parent
    return None


def _frontmatter(text: str):
    if not text.startswith("---") or yaml is None:
        return None
    parts = text.split("---", 2)
    if len(parts) < 3:
        return None
    front = yaml.safe_load(parts[1])
    return front if isinstance(front, dict) else None


def _short(value, limit: int = _TRUNC) -> str:
    text = " ".join(str(value or "").split())
    return text if len(text) <= limit else text[: limit - 1] + "…"


def collect_agents(root: Path) -> list:
    agents_dir = root / ".claude" / "agents"
    out = []
    for path in sorted(agents_dir.glob("*.md")) if agents_dir.is_dir() else []:
        front = _frontmatter(path.read_text(encoding="utf-8")) or {}
        out.append(
            {
                "name": front.get("name", path.stem),
                "model": front.get("model"),
                "effort": front.get("effort"),
                "tools": front.get("tools"),
                "description": _short(front.get("description")),
            }
        )
    return out


def collect_templates(root: Path) -> list:
    manifest = root / "prompts" / "agent_templates" / "manifest.yaml"
    if not manifest.exists() or yaml is None:
        return []
    data = yaml.safe_load(manifest.read_text(encoding="utf-8")) or {}
    out = []
    for tmpl in data.get("templates") or []:
        out.append(
            {
                "id": tmpl.get("id"),
                "class": tmpl.get("class"),
                "required_fields": tmpl.get("required_fields"),
                "when_to_use": _short(tmpl.get("when_to_use")),
            }
        )
    return out


def _render_text(agents, templates, sections) -> str:
    lines = []
    if "agents" in sections:
        lines.append("AGENTS")
        for a in agents:
            lines.append(f"  {a['name']:<18} {str(a['model']):<6} {str(a['effort']):<4} {a['description']}")
    if "templates" in sections:
        lines.append("TEMPLATES")
        for t in templates:
            lines.append(f"  {str(t['id']):<22} {str(t['class']):<10} {t['when_to_use']}")
    return "\n".join(lines)


def _render_markdown(agents, templates, sections) -> str:
    lines = []
    if "agents" in sections:
        lines += ["## Agents", "", "| name | model | effort | description |", "|------|-------|--------|-------------|"]
        lines += [f"| {a['name']} | {a['model']} | {a['effort']} | {a['description']} |" for a in agents]
        lines.append("")
    if "templates" in sections:
        lines += ["## Templates", "", "| id | class | when_to_use |", "|----|-------|-------------|"]
        lines += [f"| {t['id']} | {t['class']} | {t['when_to_use']} |" for t in templates]
    return "\n".join(lines).rstrip()


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Quick reference for the Juniper custom-agent suite (read-only).")
    parser.add_argument("--repo-root", default=None, help="suite repo root (default: walk up for .github/workflows/)")
    parser.add_argument("--agents", action="store_true", help="show only the agents section")
    parser.add_argument("--templates", action="store_true", help="show only the templates section")
    fmt = parser.add_mutually_exclusive_group()
    fmt.add_argument("--json", action="store_true", help="machine-readable output")
    fmt.add_argument("--markdown", action="store_true", help="pasteable markdown tables")
    args = parser.parse_args(argv)

    root = Path(args.repo_root).resolve() if args.repo_root else _find_repo_root(Path.cwd())
    if root is None:
        print("agent-suite-summary: could not locate repo root (no .github/workflows/)", file=sys.stderr)
        return 2

    sections = set()
    if args.agents:
        sections.add("agents")
    if args.templates:
        sections.add("templates")
    if not sections:
        sections = {"agents", "templates"}

    agents = collect_agents(root) if "agents" in sections else []
    templates = collect_templates(root) if "templates" in sections else []

    if args.json:
        print(json.dumps({"agents": agents, "templates": templates}, indent=2))
    elif args.markdown:
        print(_render_markdown(agents, templates, sections))
    else:
        print(_render_text(agents, templates, sections))
    return 0


if __name__ == "__main__":
    sys.exit(main())
