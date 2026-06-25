"""generated_prompt_index.py -- index (and optionally prune) the Template Agent's output dir.

The Template Agent Skill emits validated prompts to ``prompts/generated/`` with a dated,
collision-safe name ``PROJECT_APPLICATION_SUBJECT_TASK-TYPE_YYYY-MM-DD_HHMM.md``. This utility
lists those generated prompts (parsed by that naming contract) and -- with explicit opt-in --
prunes or archives stale ones, keeping the working surface tidy.

The generated-prompt directory is read from the data layer
(``prompts/templates/data/conventions.yaml`` ``deliverable_locations.generated_prompts``), so
the location is authoritative, not hard-coded.

Path-invoked (``util/`` is not a package):

    python util/generated_prompt_index.py [--repo-root PATH] [--json]
        [--older-than DAYS [--prune | --archive DIR] [--yes]] [--dry-run]

SAFETY: ``--prune`` / ``--archive`` only ACT with an explicit ``--yes`` and never under
``--dry-run`` -- otherwise they preview. Only files matching the naming convention are ever
candidates (a ``.gitkeep`` or a hand-placed file is never touched). Tests:
``tests/test_generated_prompt_index.py``.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from datetime import date
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover - PyYAML is normally present
    yaml = None

# Anchor the convention on the trailing _YYYY-MM-DD_HHMM.md; the prefix is PROJECT_APP_SUBJECT_TASK-TYPE.
_NAME_RE = re.compile(r"^(?P<prefix>.+)_(?P<date>\d{4}-\d{2}-\d{2})_(?P<time>\d{4})\.md$")
_DEFAULT_GENERATED = "prompts/generated/"


def _find_repo_root(start: Path):
    for parent in [start, *start.parents]:
        if (parent / ".github" / "workflows").is_dir():
            return parent
    return None


def _generated_dir(root: Path) -> Path:
    """Resolve the generated-prompt dir from the data layer (authoritative), else the default."""
    conventions = root / "prompts" / "templates" / "data" / "conventions.yaml"
    location = _DEFAULT_GENERATED
    if conventions.exists() and yaml is not None:
        data = yaml.safe_load(conventions.read_text(encoding="utf-8")) or {}
        location = ((data.get("deliverable_locations") or {}).get("generated_prompts")) or _DEFAULT_GENERATED
    return root / location


def parse_name(filename: str):
    """Return parsed fields for a convention-named file, or None if it does not match."""
    match = _NAME_RE.match(filename)
    if not match:
        return None
    prefix_parts = match.group("prefix").split("_")
    return {
        "file": filename,
        "project": prefix_parts[0] if prefix_parts else None,
        "application": prefix_parts[1] if len(prefix_parts) > 1 else None,
        "subject_tasktype": "_".join(prefix_parts[2:]) if len(prefix_parts) > 2 else None,
        "date": match.group("date"),
        "time": match.group("time"),
    }


def _age_days(date_str: str, today: date) -> int:
    yr, mo, dy = (int(x) for x in date_str.split("-"))
    return (today - date(yr, mo, dy)).days


def index(generated_dir: Path, older_than=None, today=None):
    """Return (prompts, malformed). prompts is convention-named files (with parsed fields +
    age_days + stale flag); malformed is the names that don't match the convention (.gitkeep
    and any hand-placed file) -- never prune candidates."""
    today = today or date.today()
    prompts, malformed = [], []
    for path in sorted(generated_dir.glob("*")) if generated_dir.is_dir() else []:
        if not path.is_file() or path.name == ".gitkeep":
            continue
        parsed = parse_name(path.name)
        if parsed is None:
            malformed.append(path.name)
            continue
        parsed["age_days"] = _age_days(parsed["date"], today)
        parsed["stale"] = older_than is not None and parsed["age_days"] >= older_than
        prompts.append(parsed)
    return prompts, malformed


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Index (and optionally prune) the Template Agent's prompts/generated/ output.")
    parser.add_argument("--repo-root", default=None, help="suite repo root (default: walk up for .github/workflows/)")
    parser.add_argument("--json", action="store_true", help="machine-readable output")
    parser.add_argument("--older-than", type=int, default=None, metavar="DAYS", help="mark prompts older than DAYS as stale")
    action = parser.add_mutually_exclusive_group()
    action.add_argument("--prune", action="store_true", help="delete stale prompts (needs --older-than and --yes)")
    action.add_argument("--archive", metavar="DIR", default=None, help="move stale prompts to DIR (needs --older-than and --yes)")
    parser.add_argument("--yes", action="store_true", help="actually perform --prune / --archive (otherwise preview)")
    parser.add_argument("--dry-run", action="store_true", help="never act; always preview")
    args = parser.parse_args(argv)

    root = Path(args.repo_root).resolve() if args.repo_root else _find_repo_root(Path.cwd())
    if root is None:
        print("generated-prompt-index: could not locate repo root (no .github/workflows/)", file=sys.stderr)
        return 2

    generated_dir = _generated_dir(root)
    prompts, malformed = index(generated_dir, older_than=args.older_than)

    acting = (args.prune or args.archive) and args.older_than is not None
    # SAFETY: act only with explicit --yes and never under --dry-run.
    do_act = acting and args.yes and not args.dry_run
    actions = []
    if acting:
        archive_dir = Path(args.archive).resolve() if args.archive else None
        for entry in prompts:
            if not entry["stale"]:
                continue
            src = generated_dir / entry["file"]
            verb = "archive" if args.archive else "prune"
            if do_act:
                if archive_dir is not None:
                    archive_dir.mkdir(parents=True, exist_ok=True)
                    shutil.move(str(src), str(archive_dir / entry["file"]))
                else:
                    src.unlink()
                actions.append({"file": entry["file"], "action": verb, "done": True})
            else:
                actions.append({"file": entry["file"], "action": f"would-{verb}", "done": False})

    if args.json:
        print(json.dumps({"generated_dir": str(generated_dir), "prompts": prompts, "malformed": malformed, "actions": actions}, indent=2))
    else:
        print(f"generated dir: {generated_dir}")
        for entry in prompts:
            flag = " [STALE]" if entry.get("stale") else ""
            print(f"  {entry['file']}  ({entry['date']} {entry['time']}, {entry['age_days']}d){flag}")
        if malformed:
            print(f"  (ignored {len(malformed)} non-convention file(s): {malformed})")
        for act in actions:
            print(f"  -> {act['action']}: {act['file']}")
        if acting and not do_act:
            print("  (preview only -- pass --yes (and not --dry-run) to actually act)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
