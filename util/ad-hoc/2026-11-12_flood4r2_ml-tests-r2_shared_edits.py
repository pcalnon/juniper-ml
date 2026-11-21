#!/usr/bin/env python3
"""
Apply round 2's edits to the shared files of the flood-4 "ml-tests" carrier that are not suite registrations.

Run it AFTER `2026-11-09_flood4r2_ml-tests_wire.py` has registered the fifteen suites. Every number it writes is
derived from the tree, never typed: main's suite count and document version are read from HEAD's blobs, the
carrier's count from the wired ci.yml, and the new document version is main's with its patch raised by one.

Edits, each by an exact anchor that must occur exactly once (a file whose edit is already present is left alone;
nothing is written when any anchor is missing):

  docs/REFERENCE.md
    - the `Running every suite` tally gains "**<count>** on <date> with the flood-4 round-2 tests carrier's fifteen";
    - juniper-ml#2512's sentence on the predict_merge `ERROR` row (how `screen_coverage` counts it);
    - juniper-ml#2481's and #2512's Repository Structure tree lines;
    - the two statements of the macOS host-tooling suite list (the gate's Test Suite Reference entry and the
      CI/CD Pipeline Reference item) gain the agent guard's suites;
    - the document stamp, once: **Version:** (header and footer), **Last Updated:** (header and footer) and one
      Version History row after main's newest.
  AGENTS.md
    - the suite count in the "Run all tests" comment, and **Last Updated** set to <date>.
  .github/workflows/ci.yml
    - HOST_TOOLING_SUITES gains the eight agent-guard suites that were not in it (the Overtoad's ruling of
      2026-11-12), with a comment in the job's env block and banner, and the regression step's comment on the
      gate follows.

Usage (from the worktree root):
    python3 util/ad-hoc/2026-11-12_flood4r2_ml-tests-r2_shared_edits.py --date YYYY-MM-DD [--out derived.json]

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-12
Status: ad-hoc — one-off (flood-4 round-2 ml-tests carrier, round 2 of its build)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: util/ad-hoc/2026-11-09_flood4r2_ml-tests_shared_edits.py (round 1's, which typed its numbers)
"""

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

REFERENCE, AGENTS, CI = Path("docs/REFERENCE.md"), Path("AGENTS.md"), Path(".github/workflows/ci.yml")
SUITE_LINE = re.compile(r"^\s*python3 -m unittest -v (tests/[A-Za-z0-9_./-]+\.py)\s*$", re.M)
CARRIED = (
    "tests/test_claude_agent_guard_nest_depth.py",
    "tests/test_claude_agent_guard_push_signed.py",
    "tests/test_claude_agent_guard_ansi_escapes.py",
    "tests/test_claude_agent_guard_gpgsign_off.py",
    "tests/test_claude_agent_guard_sign_edges.py",
    "tests/test_launcher_empty_version_output.py",
    "tests/test_prompt_file_boolean_tokens.py",
    "tests/test_prompt_file_kind.py",
    "tests/test_wake_spacer_flags.py",
    "tests/test_launcher_prompt_and_version_edges.py",
    "tests/test_predict_merge_scratch_edges.py",
    "tests/test_predict_merge_shallow_worktree.py",
    "tests/test_predict_merge_guard_edges.py",
    "tests/test_predict_merge_error_screen.py",
    "tests/test_cascor_eval_zero_and_enabled.py",
)
# The agent-guard suites the macOS job did not run: one on main since juniper-ml#2517, two since #2554, five carried here.
GUARD_SUITES = (
    "claude_agent_guard_brace_cap",
    "claude_agent_guard_git_sign_abbrev",
    "claude_agent_guard_push_signed_abbrev",
    "claude_agent_guard_nest_depth",
    "claude_agent_guard_push_signed",
    "claude_agent_guard_ansi_escapes",
    "claude_agent_guard_gpgsign_off",
    "claude_agent_guard_sign_edges",
)

ERROR_OLD = "| `ERROR` | `--batch` only: soft-fail row when a single PR cannot be simulated (e.g. unresolvable `origin/<headRefName>`); `true_delta=[]` and the rest of the open-PR set still runs |"
ERROR_NEW = (
    "| `ERROR` | `--batch` only: soft-fail row when a single PR cannot be simulated (e.g. unresolvable `origin/<headRefName>`); `true_delta=[]`, `gates` empty, and the rest of the open-PR set still runs. "
    "`screen_coverage` counts each of that row's gates as `absent`: the row stays in the denominator and out of `evaluated`, so an all-`ERROR` batch reports a screened fraction of 0. It is not a pass, and not `unscreened` |"
)
TREE_OLD = "│   ├── test_predict_merge.py             # Behavioral: util/fleet_triage/predict_merge.py predicted-merge (4 verdicts, TRUE-delta, cluster/order, no-mutate, exit codes; hermetic)\n"
TREE_NEW = (
    TREE_OLD + "│   ├── test_predict_merge_scratch_edges.py # Behavioral: a shallow worktree's common objects, a sha256 scratch, each LFS protection alone\n"
    "│   ├── test_predict_merge_error_screen.py # screen_coverage: an ERROR row's empty gates are absent, not a pass; empty batch does not divide by zero\n"
)
GATE_ENTRY_OLD = "H4's `tests/test_mcp_setup.py` made the list twelve."
GATE_ENTRY_NEW = (
    GATE_ENTRY_OLD + " The agent guard's {added} other suites made it {total} (the Overtoad's ruling of 2026-11-12): `util/claude_agent_guard.py` is the hook the macOS host runs, "
    "so every `tests/test_claude_agent_guard*.py` on disk must be in the list, and the gate compares the two."
)
JOB_ITEM_OLD = "with its own `!= success` arm, never as a separate ruleset context. Gate: `tests/test_ci_host_tooling_macos.py`."
JOB_ITEM_NEW = (
    "with its own `!= success` arm, never as a separate ruleset context. The list holds every agent-guard suite (`tests/test_claude_agent_guard*.py`, {on_disk} files) beside the turing suites, "
    "by the Overtoad's ruling of 2026-11-12; the {added} beside `tests/test_claude_agent_guard.py` start no shell, and run here because the guard is the hook the macOS host runs. Gate: `tests/test_ci_host_tooling_macos.py`."
)
TALLY_START = "The complete ordered list, generated from"
TALLY_TAIL = ". The drift script above counts, so re-run it rather than trusting this figure."

CI_LIST_OLD = "        juniper_clone find_encryption_readme_notes macvm_ctl claude_agent_guard\n"
CI_LIST_NEW = CI_LIST_OLD + "        " + " ".join(GUARD_SUITES[:3]) + "\n        " + " ".join(GUARD_SUITES[3:]) + "\n"
CI_ENV_OLD = "      # tests/redacted_env.py and this workflow always count. G1's check suite pins the conf/hosts/turing/\n      # files listed here against each other.\n"
CI_ENV_NEW = (
    CI_ENV_OLD + "      # Every tests/test_claude_agent_guard*.py is listed (the Overtoad's ruling of 2026-11-12), and\n"
    "      # tests/test_ci_host_tooling_macos.py compares the list with the files on disk.\n"
)
CI_BANNER_OLD = "  # is not turing's Intel /usr/local, so a green run also shows the scripts are prefix-independent.\n"
CI_BANNER_NEW = (
    CI_BANNER_OLD + "  # The agent guard's other suites are the exception: they start no shell, and run here because the\n"
    "  # guard is the hook the macOS host runs (the Overtoad's ruling of 2026-11-12).\n"
)
CI_GATE_OLD = "          # the suite list equal to the turing host-tooling set, /bin/bash 3.x and a non-/usr/local brew\n"
CI_GATE_NEW = "          # the suite list equal to the host-tooling set (the turing suites and every agent-guard suite on disk), /bin/bash 3.x and a non-/usr/local brew\n"


def _head(path: Path) -> str:
    out = subprocess.run(["git", "show", f"HEAD:{path.as_posix()}"], capture_output=True, text=True, check=True)
    return out.stdout


def _once(text: str, old: str, new: str, name: str) -> str:
    if new in text:
        return text
    if text.count(old) != 1:
        raise SystemExit(f"{name}: anchor found {text.count(old)} times: {old[:100]!r}")
    return text.replace(old, new)


def _suite_count(ci_text: str) -> int:
    return len(set(SUITE_LINE.findall(ci_text)))


def _reference(text: str, main_text: str, date: str, count: int, host: dict) -> tuple:
    main_version = re.search(r"^\*\*Version:\*\* (\d+)\.(\d+)\.(\d+)$", main_text, re.M)
    main_date = re.search(r"^\*\*Last Updated:\*\* (\d{4}-\d{2}-\d{2})$", main_text, re.M)
    if main_version is None or main_date is None:
        raise SystemExit("REFERENCE: main's stamp not found")
    old_version = ".".join(main_version.groups())
    new_version = f"{main_version.group(1)}.{main_version.group(2)}.{int(main_version.group(3)) + 1}"
    gate_entry = GATE_ENTRY_NEW.format(added=len(GUARD_SUITES), total=host["total"])
    job_item = JOB_ITEM_NEW.format(on_disk=host["guard_suites_on_disk"], added=len(GUARD_SUITES))
    for old, new, name in ((ERROR_OLD, ERROR_NEW, "ERROR row"), (TREE_OLD, TREE_NEW, "tree lines"), (GATE_ENTRY_OLD, gate_entry, "macOS gate entry"), (JOB_ITEM_OLD, job_item, "macOS job item")):
        text = _once(text, old, new, f"REFERENCE {name}")
    lines = text.split("\n")
    tally = [i for i, line in enumerate(lines) if line.startswith(TALLY_START)]
    if len(tally) != 1 or lines[tally[0]].count(TALLY_TAIL) != 1:
        raise SystemExit("REFERENCE: the tally sentence was not found exactly once")
    entry = f", **{count}** on {date} with the flood-4 round-2 tests carrier's fifteen (" + ", ".join(f"`{suite}`" for suite in CARRIED) + ")"
    if entry not in lines[tally[0]]:
        if "tests carrier's fifteen" in lines[tally[0]]:
            raise SystemExit("REFERENCE: the tally already names this carrier with other values; start from main's copy")
        lines[tally[0]] = lines[tally[0]].replace(TALLY_TAIL, entry + TALLY_TAIL)
    text = "\n".join(lines)
    row = (
        f"| {new_version}  | {date} | Cursor flood-4 round-2 tests carrier: fifteen suites registered ({count} in all) and juniper-ml#2507's Ecosystem Compatibility pins added to "
        "`tests/test_pyproject_extras.py`; the predict_merge `ERROR` row says how `screen_coverage` counts it; two Repository Structure tree lines; "
        f"ci.yml's `host-tooling-macos` job runs every agent-guard suite, {host['total']} suites in all. |"
    )
    if row not in text:
        anchors = [m for m in re.finditer(rf"^\| {re.escape(old_version)}  \| .*$", text, re.M)]
        if len(anchors) != 1:
            raise SystemExit(f"REFERENCE: Version History row {old_version} found {len(anchors)} times")
        text = text[: anchors[0].end()] + "\n" + row + text[anchors[0].end() :]
    if text.count(f"**Version:** {new_version}\n") != 2:
        if text.count(f"**Version:** {old_version}\n") != 2:
            raise SystemExit("REFERENCE: the header and footer Version lines were not found exactly twice")
        text = text.replace(f"**Version:** {old_version}\n", f"**Version:** {new_version}\n")
    if text.count(f"**Last Updated:** {date}\n") != 2:
        if text.count(f"**Last Updated:** {main_date.group(1)}\n") != 2:
            raise SystemExit("REFERENCE: the header and footer Last Updated lines were not found exactly twice")
        text = text.replace(f"**Last Updated:** {main_date.group(1)}\n", f"**Last Updated:** {date}\n")
    return text, {"main_version": old_version, "version": new_version, "main_last_updated": main_date.group(1), "last_updated": date}


def _agents(text: str, main_text: str, date: str, main_count: int, count: int) -> tuple:
    text = _once(text, f"# Run all tests -- the full ordered list of {main_count} `python3 -m unittest`", f"# Run all tests -- the full ordered list of {count} `python3 -m unittest`", "AGENTS count")
    main_date = re.search(r"^\*\*Last Updated\*\*: (\d{4}-\d{2}-\d{2})$", main_text, re.M)
    if main_date is None:
        raise SystemExit("AGENTS: main's Last Updated not found")
    if main_date.group(1) != date:
        text = _once(text, f"**Last Updated**: {main_date.group(1)}\n", f"**Last Updated**: {date}\n", "AGENTS Last Updated")
    return text, {"main_last_updated": main_date.group(1), "last_updated": date, "line_changes_in_the_diff": main_date.group(1) != date}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--date", required=True, help="the UTC date of the day the carrier lands")
    ap.add_argument("--out")
    args = ap.parse_args()
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", args.date):
        raise SystemExit("--date must be YYYY-MM-DD")
    ci = CI.read_text(encoding="utf-8")
    main_count, count = _suite_count(_head(CI)), _suite_count(ci)
    missing = [suite for suite in CARRIED if suite not in SUITE_LINE.findall(ci)]
    if missing or count != main_count + len(CARRIED):
        raise SystemExit(f"ci.yml: run the wiring tool first (main {main_count}, here {count}, not wired: {missing})")
    for old, new, name in ((CI_LIST_OLD, CI_LIST_NEW, "HOST_TOOLING_SUITES"), (CI_ENV_OLD, CI_ENV_NEW, "env comment"), (CI_BANNER_OLD, CI_BANNER_NEW, "job banner"), (CI_GATE_OLD, CI_GATE_NEW, "gate comment")):
        ci = _once(ci, old, new, f"ci.yml {name}")
    listed = re.search(r"^      HOST_TOOLING_SUITES: >-\n((?:        \S.*\n)+)", ci, re.M)
    if listed is None:
        raise SystemExit("ci.yml: HOST_TOOLING_SUITES not found")
    suites = listed.group(1).split()
    on_disk = sorted(path.stem[len("test_") :] for path in Path("tests").glob("test_claude_agent_guard*.py"))
    unlisted = [name for name in on_disk if name not in suites]
    if unlisted or len(suites) != len(set(suites)):
        raise SystemExit(f"ci.yml: HOST_TOOLING_SUITES lacks agent-guard suites on disk {unlisted}, or repeats a name; add them to GUARD_SUITES here")
    host = {"total": len(suites), "guard_suites_on_disk": len(on_disk), "guard_suites_added": len(GUARD_SUITES)}
    reference, ref_stamp = _reference(REFERENCE.read_text(encoding="utf-8"), _head(REFERENCE), args.date, count, host)
    agents, agents_stamp = _agents(AGENTS.read_text(encoding="utf-8"), _head(AGENTS), args.date, main_count, count)
    CI.write_text(ci, encoding="utf-8")
    REFERENCE.write_text(reference, encoding="utf-8")
    AGENTS.write_text(agents, encoding="utf-8")
    derived = {"date": args.date, "main_suite_count": main_count, "suite_count": count, "carried_suites": len(CARRIED), "host_tooling": host, "host_tooling_guard_suites_added": list(GUARD_SUITES), "docs/REFERENCE.md": ref_stamp, "AGENTS.md": agents_stamp}
    print(json.dumps(derived, indent=2))
    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            json.dump(derived, fh, indent=2)
            fh.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
