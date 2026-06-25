"""scaffold_template.py -- generate a new prompts/templates/ template + its manifest stanza.

Writes a new ``prompts/templates/<id>.md`` pre-populated with the canonical section skeleton
(in order) and well-formed ``{{placeholder}}`` slots, so a new template cannot drift from the
skeleton/placeholder contract enforced by ``tests/test_template_library_drift.py``. It then
**prints** the ``manifest.yaml`` stanza for the owner to paste -- it deliberately does **not**
auto-edit ``manifest.yaml`` (the manifest is the human-curated selection contract, and
``prompts/**`` is unlinted, so a silent auto-edit could break selection). Refuses to overwrite
an existing template.

Path-invoked (``util/`` is not a package):

    python util/scaffold_template.py --id NEW_ID --title "..." --class execution \\
        --keywords "k1,k2" [--required-fields "a,b"] [--repo-root PATH] [--dry-run]

Exit 0 on success / dry-run; 1 on collision; 2 on bad arguments. Tests: ``tests/test_scaffold_template.py``.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

_ALLOWED_CLASSES = {"generic", "execution", "analysis", "planning", "review"}
_ID_RE = re.compile(r"^[a-z][a-z0-9-]*$")

# Plain string (NOT an f-string) so the literal {{...}} placeholders need no escaping; the two
# __TOKENS__ are substituted by render_template().
_TEMPLATE = """# __TITLE__ — {{!__SLOT__: the primary subject / target of this prompt}}

<!--
Scaffolded template for the Juniper custom-agent suite. The Template Agent fills a COPY (never
this source -- D-5) and validates it against RUBRIC.md before emission. Fill every required
slot; fill or drop optional slots. Convention: NAME fill, !NAME: hint required, ?NAME: hint
optional (each wrapped in double braces). TODO: tailor the hints to this template's purpose.
-->

## Role

{{!ROLE: the expert role the agent should adopt for this task}}

## Resources

{{!RESOURCES: the discovery grounding bundle -- real file:line anchors, repo/branch, dependency versions, and conventions. Cite real anchors, never invented ones.}}

## Primary Objective

{{!PRIMARY_OBJECTIVE: a faithful one-paragraph restatement of the task intent and the desired outcome}}

## Assigned Tasks / Directives

{{!DIRECTIVES: ordered, unambiguous, individually verifiable steps the agent must perform}}

## Key Deliverables & Requirements

{{!DELIVERABLES: enumerate deliverables with measurable acceptance criteria -- named tests pass, lint clean, specific files written, observable behavior; avoid adjective-only criteria}}

## Constraints

{{?CONSTRAINTS: hard limits -- do-not-touch areas, standing conventions, anti-hallucination doctrine}}

## Finalize / Validation

{{?VALIDATION: how to verify success and how to recover or abort}}
"""


def _find_repo_root(start: Path):
    for parent in [start, *start.parents]:
        if (parent / ".github" / "workflows").is_dir():
            return parent
    return None


def render_template(title: str, primary_field: str) -> str:
    slot = re.sub(r"[^A-Z0-9_]", "_", primary_field.upper().replace("-", "_"))
    return _TEMPLATE.replace("__TITLE__", title).replace("__SLOT__", slot)


def render_manifest_stanza(template_id: str, title: str, keywords: list, required_fields: list, class_: str) -> str:
    kw = ", ".join(f'"{k}"' for k in keywords)
    return "\n".join(
        [
            f"  - id: {template_id}",
            f'    title: "{title}"',
            '    when_to_use: "TODO: one sentence on when the Template Agent should select this template."',
            "    match_signals:",
            f"      keywords: [{kw}]",
            f"    file: {template_id}.md",
            f"    required_fields: [{', '.join(required_fields)}]",
            f"    class: {class_}",
        ]
    )


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Scaffold a new prompts/templates/ template + its manifest stanza (does NOT edit the manifest).")
    parser.add_argument("--id", required=True, help="template id (lowercase kebab-case)")
    parser.add_argument("--title", required=True, help="template title for the H1 + manifest")
    parser.add_argument("--class", dest="class_", required=True, help=f"one of {sorted(_ALLOWED_CLASSES)}")
    parser.add_argument("--keywords", default="", help="comma-separated match_signals keywords (required unless --class generic)")
    parser.add_argument("--required-fields", default="subject,resources", help="comma-separated required_fields")
    parser.add_argument("--repo-root", default=None, help="suite repo root (default: walk up for .github/workflows/)")
    parser.add_argument("--dry-run", action="store_true", help="print the template + stanza; write nothing")
    args = parser.parse_args(argv)

    if not _ID_RE.match(args.id):
        print(f"scaffold_template: --id must be lowercase kebab-case, got {args.id!r}", file=sys.stderr)
        return 2
    if args.class_ not in _ALLOWED_CLASSES:
        print(f"scaffold_template: --class must be one of {sorted(_ALLOWED_CLASSES)}, got {args.class_!r}", file=sys.stderr)
        return 2
    keywords = [k.strip() for k in args.keywords.split(",") if k.strip()]
    if args.class_ != "generic" and not keywords:
        print("scaffold_template: a non-generic template needs --keywords", file=sys.stderr)
        return 2
    required_fields = [f.strip() for f in args.required_fields.split(",") if f.strip()] or ["subject", "resources"]

    root = Path(args.repo_root).resolve() if args.repo_root else _find_repo_root(Path.cwd())
    if root is None:
        print("scaffold_template: could not locate repo root (no .github/workflows/)", file=sys.stderr)
        return 2
    dest = root / "prompts" / "templates" / f"{args.id}.md"
    if dest.exists():
        print(f"scaffold_template: refusing to overwrite existing {dest}", file=sys.stderr)
        return 1

    template = render_template(args.title, required_fields[0])
    stanza = render_manifest_stanza(args.id, args.title, keywords, required_fields, args.class_)
    paste_note = "Add this stanza to prompts/templates/manifest.yaml (before the 'generic' entry) -- this tool does NOT edit the manifest:"

    if args.dry_run:
        print(f"# DRY-RUN: would write {dest}\n")
        print(template)
        print(f"\n# {paste_note}\n")
        print(stanza)
        return 0

    dest.write_text(template, encoding="utf-8")
    print(f"wrote {dest}\n")
    print(paste_note + "\n")
    print(stanza)
    return 0


if __name__ == "__main__":
    sys.exit(main())
