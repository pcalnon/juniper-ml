"""agent_suite_doctor.py -- health check for the Juniper custom-agent suite.

One read-only command that reports the existence + structural validity of every suite
component -- agents, the Template Agent Skill, the template library, RUBRIC, the data layer,
the discovery CLI, and the ``~/.claude`` mirror -- plus the owner-directed frontmatter
defaults (``model: opus`` + ``effort: max``). Because it CONSUMES every layer's contract at
runtime, running it validates the suite end-to-end. It writes nothing.

Path-invoked (``util/`` is not a package):

    python util/agent_suite_doctor.py [--repo-root PATH] [--json] [--strict] [--no-discovery]

Exit codes: 0 = healthy (WARN allowed unless ``--strict``); 1 = >=1 FAIL (or >=1 WARN under
``--strict``); 2 = bad arguments.

Built as a dogfood of the suite: the ``planner`` agent designed it
(``notes/JUNIPER_juniper-ml_agent-suite-convenience-utilities_DESIGN_2026-06-25.md`` §P1), and
the ``implement-plan`` template + ``prompt-validator`` validated the spec. Behavioural
coverage: ``tests/test_agent_suite_doctor.py``.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover - PyYAML is normally present
    yaml = None

OK, WARN, FAIL = "OK", "WARN", "FAIL"

_RUBRIC_HARD_GATES = ("R2.0", "R3.4")
_DATA_FILES = ("standing_rules", "anti_hallucination", "conventions", "ecosystem", "known_misses")
_CORE_AGENT = "prompt-validator"  # load-bearing: the Skill delegates to it


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


def _tool_set(value):
    if value is None:
        return set()
    if isinstance(value, list):
        return {str(v).strip() for v in value if str(v).strip()}
    return {tok.strip() for tok in re.split(r"[,\s]+", str(value)) if tok.strip()}


def _is_opus(model) -> bool:
    base = str(model or "").split(":")[0].strip().lower()
    return base == "opus" or base.startswith("claude-opus")


# --- individual checks: each returns (name, status, reason) ----------------------


def check_agents(root: Path):
    agents_dir = root / ".claude" / "agents"
    files = sorted(agents_dir.glob("*.md")) if agents_dir.is_dir() else []
    if not files:
        return ("agents", FAIL, f"no agents at {agents_dir}")
    if yaml is None:
        return ("agents", WARN, "PyYAML unavailable; cannot validate frontmatter")
    offenders = []
    names = set()
    for path in files:
        front = _frontmatter(path.read_text(encoding="utf-8"))
        if not front:
            offenders.append(f"{path.name}: no frontmatter")
            continue
        names.add(front.get("name"))
        if front.get("name") != path.stem:
            offenders.append(f"{path.name}: name != filename")
        if not _is_opus(front.get("model")):
            offenders.append(f"{path.name}: model not opus ({front.get('model')!r})")
        if str(front.get("effort", "")).strip().lower() != "max":
            offenders.append(f"{path.name}: effort not max ({front.get('effort')!r})")
    if _CORE_AGENT not in names:
        offenders.append(f"core agent '{_CORE_AGENT}' missing")
    if offenders:
        return ("agents", FAIL, "; ".join(offenders))
    return ("agents", OK, f"{len(files)} agent(s), all opus+max; {_CORE_AGENT} present")


def check_skill(root: Path):
    skill = root / ".claude" / "skills" / "template-agent" / "SKILL.md"
    if not skill.exists():
        return ("skill", FAIL, f"missing {skill}")
    front = _frontmatter(skill.read_text(encoding="utf-8")) if yaml is not None else None
    if yaml is None:
        return ("skill", WARN, "PyYAML unavailable; SKILL.md present but frontmatter unchecked")
    if not front:
        return ("skill", FAIL, "SKILL.md has no parseable frontmatter")
    if "Agent" not in _tool_set(front.get("allowed-tools")):
        return ("skill", FAIL, "SKILL.md allowed-tools missing 'Agent' (needed to delegate to the validator)")
    return ("skill", OK, "template-agent Skill present; allowed-tools includes Agent")


def check_templates(root: Path):
    manifest = root / "prompts" / "templates" / "manifest.yaml"
    if not manifest.exists():
        return ("templates", FAIL, f"missing {manifest}")
    if yaml is None:
        return ("templates", WARN, "PyYAML unavailable; cannot parse manifest.yaml")
    data = yaml.safe_load(manifest.read_text(encoding="utf-8")) or {}
    templates = data.get("templates") or []
    if not templates:
        return ("templates", FAIL, "manifest declares no templates")
    missing = [t.get("file") for t in templates if not (manifest.parent / t.get("file", "")).exists()]
    if missing:
        return ("templates", FAIL, f"manifest references missing file(s): {missing}")
    always = [t for t in templates if (t.get("match_signals") or {}).get("always") is True]
    if len(always) != 1 or always[0].get("id") != "generic":
        return ("templates", FAIL, f"expected exactly one always-match 'generic', found {[t.get('id') for t in always]}")
    return ("templates", OK, f"{len(templates)} templates registered, all files present; generic fallback ok")


def check_rubric(root: Path):
    rubric = root / "prompts" / "templates" / "RUBRIC.md"
    if not rubric.exists():
        return ("rubric", FAIL, f"missing {rubric}")
    text = rubric.read_text(encoding="utf-8")
    missing = [g for g in _RUBRIC_HARD_GATES if g not in text]
    if missing:
        return ("rubric", FAIL, f"RUBRIC.md missing hard-gate id(s): {missing}")
    return ("rubric", OK, f"RUBRIC.md present; hard gates {list(_RUBRIC_HARD_GATES)} declared")


def check_data_layer(root: Path):
    data_dir = root / "prompts" / "templates" / "data"
    if not data_dir.is_dir():
        return ("data_layer", WARN, f"no data layer at {data_dir} (optional until PR 6b)")
    if yaml is None:
        return ("data_layer", WARN, "PyYAML unavailable; cannot load data layer")
    missing = [f"{name}.yaml" for name in _DATA_FILES if not (data_dir / f"{name}.yaml").exists()]
    if missing:
        return ("data_layer", FAIL, f"data layer missing file(s): {missing}")
    for name in _DATA_FILES:
        try:
            loaded = yaml.safe_load((data_dir / f"{name}.yaml").read_text(encoding="utf-8"))
        except (ValueError, OSError) as exc:
            return ("data_layer", FAIL, f"{name}.yaml unreadable: {exc}")
        if not isinstance(loaded, dict):
            return ("data_layer", FAIL, f"{name}.yaml is not a mapping")
    return ("data_layer", OK, f"data layer loads ({len(_DATA_FILES)} files)")


def check_discovery(root: Path):
    cli = root / "util" / "prompt_discovery" / "cli.py"
    if not cli.exists():
        return ("discovery", FAIL, f"missing {cli}")
    proc = subprocess.run(  # noqa: S603 - fixed argv, no shell
        [sys.executable, str(cli), "--repo-root", str(root)],
        capture_output=True,
        text=True,
        check=False,
        timeout=120,
    )
    if proc.returncode != 0:
        return ("discovery", FAIL, f"cli.py exited {proc.returncode}: {proc.stderr.strip()[:120]}")
    try:
        bundle = json.loads(proc.stdout)
    except ValueError:
        return ("discovery", FAIL, "cli.py output is not valid JSON")
    if "schema_version" not in bundle or not (bundle.get("provenance") or {}).get("head_sha"):
        return ("discovery", FAIL, "bundle missing schema_version / provenance.head_sha")
    return ("discovery", OK, "discovery cli.py emits a well-formed bundle")


def check_mirror(root: Path):
    import os

    installer = root / "util" / "install_agents.bash"
    if not installer.exists():
        return ("mirror", WARN, f"installer absent at {installer}")
    env = {"JUNIPER_ML_REPO_ROOT": str(root), "PATH": _path_env(), "HOME": str(Path.home())}
    if os.environ.get("JUNIPER_CLAUDE_HOME"):  # honour the same override install_agents.bash uses
        env["JUNIPER_CLAUDE_HOME"] = os.environ["JUNIPER_CLAUDE_HOME"]
    proc = subprocess.run(  # noqa: S603 - fixed argv, no shell
        ["bash", str(installer), "--dry-run"],
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
        env=env,
    )
    if proc.returncode != 0:
        return ("mirror", WARN, f"install_agents.bash --dry-run exited {proc.returncode}")
    if re.search(r"^\[install_agents\] link:", proc.stdout, re.MULTILINE):
        return ("mirror", WARN, "~/.claude mirror not fully installed (optional; run util/install_agents.bash)")
    return ("mirror", OK, "~/.claude mirror present (or nothing to link)")


def _path_env() -> str:
    import os

    return os.environ.get("PATH", "/usr/bin:/bin")


def run_checks(root: Path, no_discovery: bool = False):
    checks = [check_agents, check_skill, check_templates, check_rubric, check_data_layer]
    if not no_discovery:
        checks.append(check_discovery)
    checks.append(check_mirror)
    return [fn(root) for fn in checks]


def _render_text(results, root: Path) -> str:
    lines = [f"agent-suite-doctor: {root}"]
    for name, status, reason in results:
        lines.append(f"  [{status:<4}] {name:<12} {reason}")
    counts = {s: sum(1 for _, st, _ in results if st == s) for s in (OK, WARN, FAIL)}
    lines.append(f"summary: {counts[OK]} OK, {counts[WARN]} WARN, {counts[FAIL]} FAIL")
    return "\n".join(lines)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Health check for the Juniper custom-agent suite (read-only).")
    parser.add_argument("--repo-root", default=None, help="suite repo root (default: walk up for .github/workflows/)")
    parser.add_argument("--json", action="store_true", help="machine-readable report")
    parser.add_argument("--strict", action="store_true", help="treat WARN as failure")
    parser.add_argument("--no-discovery", action="store_true", help="skip the discovery-CLI subprocess")
    args = parser.parse_args(argv)

    if args.repo_root:
        root = Path(args.repo_root).resolve()
        if not root.is_dir() or not (root / ".github" / "workflows").is_dir():
            print(f"agent-suite-doctor: --repo-root {root} is not a repo (no .github/workflows/)", file=sys.stderr)
            return 2
    else:
        root = _find_repo_root(Path.cwd())
        if root is None:
            print("agent-suite-doctor: could not locate repo root (no .github/workflows/ above CWD)", file=sys.stderr)
            return 2

    results = run_checks(root, no_discovery=args.no_discovery)
    counts = {s: sum(1 for _, st, _ in results if st == s) for s in (OK, WARN, FAIL)}
    if args.json:
        print(
            json.dumps(
                {
                    "repo_root": str(root),
                    "checks": [{"name": n, "status": s, "reason": r} for n, s, r in results],
                    "summary": counts,
                },
                indent=2,
            )
        )
    else:
        print(_render_text(results, root))

    if counts[FAIL] > 0:
        return 1
    if args.strict and counts[WARN] > 0:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
