"""
Apply the turing bring-up E6 errata (X6, X10) and the E-CQ record correction, idempotently.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon (authored via Claude Code)
Created: 2026-10-19
Status: ad-hoc — one-off (turing bring-up task E6: errata X6 and X10)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md (§3 errata X6 and X10, §16);
         prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-19_turing-session-1-six-code-prs-landed-owner-steps-next.md

Why:
- X6. Eight archived handoffs (2026-09-11 to 2026-10-03) and the P4-27 row of
  reports/2026-10-04_consolidated-development-plan/extraction-P4-release-P11-k8s.md call turing down, or
  the only Pi-pull candidate. turing is the owner's Intel MacBook Pro, a laptop in active use away from
  yamaguchi, and it was probed at a stale address. Each file gets one dated correction under its first
  such statement, the archived-handoff idiom (HANDOFF_2026-09/HANDOFF_2026-09-12_…:310). The original
  text stays.
- X10. AGENTS.md § Ecosystem Context and docs/REFERENCE.md § Worktree Procedures Reference name
  /home/pcalnon paths, and turing's home is /Users/pcalnon. Per plan D12 they become ~/ ($HOME inside a
  quoted shell string). REFERENCE.md's other /home/pcalnon hits document literals hard-coded in scripts,
  so they change with those scripts (G5), not here.
- E-CQ. The 2026-10-19 handoff asked for CodeQL's py/import-and-import-from to be folded into
  util/ad-hoc/2026-10-05_codeql_python_prescreen.py. The pre-screen already has that rule, and on the
  file CodeQL flagged in juniper-ml#2242 it reports exactly that alert. The one-off screen's header
  claimed otherwise; it gets a correction, and the plan records it.
- AGENTS.md's **Last Updated** is set to today's UTC date, which the advisory check wants.

Each edit names an anchor that must occur exactly once, unless its replacement is already there (then
it is skipped). A re-run on a newer main therefore either applies cleanly or stops loudly.

Usage:
    python3 -I util/ad-hoc/2026-10-19_turing_e6_errata.py [--root REPO_ROOT] [--dry-run]

Exit 0 = every edit applied or already present; 1 = an anchor is missing or ambiguous (nothing written).
"""

import argparse
import datetime
import re
import sys
from pathlib import Path

PLAN = "notes/JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md"
H = "prompts/thread-handoff_automated-prompts/"
H9 = H + "HANDOFF_2026-09/"
EXTRACTION = "reports/2026-10-04_consolidated-development-plan/extraction-P4-release-P11-k8s.md"
ONE_OFF = "util/ad-hoc/2026-10-18_codeql_import_and_import_from_screen.py"


def correction(prefix: str, whole_file: bool) -> str:
    lines = [
        f"**Correction, 2026-10-19 (erratum X6 of `{PLAN}`).**",
        "`turing` was not down, and it was never a Pi-pull candidate. It is the owner's 15-inch 2018 Intel",
        "MacBook Pro (x86_64, macOS), a development laptop in active use away from yamaguchi",
        "(`notes/JUNIPER_2026-08-22_JUNIPER-ECOSYSTEM_BYPASS-CANDIDATE-DETERMINATION.md:174`), so it cannot",
        "meet the pull's 64-bit Pi OS precondition. `192.168.50.222` comes from",
        "`juniper-k8s/util/node_scripts/testing/hosts:7`, but turing's Wi-Fi address is DHCP-assigned",
        "(`192.168.50.131` on 2026-10-15, `192.168.50.180` on 2026-10-19), so a failed probe of `.222` did",
        "not show turing down. The Pi pull still needs a real arm64 Pi." + (" This covers every `turing` statement in this file." if whole_file else ""),
    ]
    return "".join(f"{prefix}{line}\n" for line in lines)


def edits():
    """(repo path, anchor, replacement) triples."""
    x6 = [
        (
            H9 + "HANDOFF_2026-09-11_ci-tools-0-9-0-shipped-and-every-no-owner-item-is-closed.md",
            "- `yamaguchi` is this x86_64 workstation, not a candidate.\n",
            "- `yamaguchi` is this x86_64 workstation, not a candidate.\n\n" + correction("> ", True),
        ),
        (
            H9 + "HANDOFF_2026-09-15_all-five-images-published-and-the-pi-gate-wave-3-still-owes.md",
            "  no analysis exists for either anywhere in `notes/`.\n",
            "  no analysis exists for either anywhere in `notes/`.\n" + correction("  > ", False),
        ),
        (
            H9 + "HANDOFF_2026-09-17_container-registry-wave-3-complete-and-everything-left-is-owner-gated.md",
            "  > binfmt handler, `docker buildx` offers `linux/amd64` only.\n",
            "  > binfmt handler, `docker buildx` offers `linux/amd64` only.\n  >\n" + correction("  > ", True),
        ),
        (
            H9 + "HANDOFF_2026-09-22_ten-prs-landed-and-the-published-worker-still-reports-0-4-0.md",
            "  **`yamaguchi` is this workstation** (x86_64, 192.168.50.192), not a second candidate host.\n",
            "  **`yamaguchi` is this workstation** (x86_64, 192.168.50.192), not a second candidate host.\n" + correction("  > ", False),
        ),
        (
            H9 + "HANDOFF_2026-09-22_worker-0-6-1-shipped-equities-joins-the-data-image-lock-and-wave-4-waits-on-the-owner-token.md",
            "- `turing` was reported down on 09-22.\n",
            "- `turing` was reported down on 09-22.\n" + correction("  > ", False),
        ),
        (
            H9 + "HANDOFF_2026-09-24_data-0-16-0-cut-at-one-commit-item-5-closed-in-five-repos-wave-4-waits-on-the-token.md",
            "200 pulls per 6 h. None of that applies to the GHCR pull.\n",
            "200 pulls per 6 h. None of that applies to the GHCR pull.\n\n" + correction("> ", True),
        ),
        (
            H + "HANDOFF_2026-09-24_data-0-16-0-on-pypi-and-pinned-the-stack-generates-equities-wave-4-waits-on-the-token.md",
            "of that applies to the GHCR pull.\n",
            "of that applies to the GHCR pull.\n\n" + correction("> ", False),
        ),
        (
            H + "HANDOFF_2026-10-03_release-and-distribution-consolidated.md",
            "`turing` was reported down 09-22. [UNVERIFIED — from the data handoff]\n",
            "`turing` was reported down 09-22. [UNVERIFIED — from the data handoff]\n" + correction("  > ", False),
        ),
        (
            EXTRACTION,
            '["turing down 09-22": UNVERIFIED — from DH]',
            '["turing down 09-22": UNVERIFIED — from DH] [CORRECTED 2026-10-19 (X6 of …TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md): turing is an amd64 Intel Mac in active use, not a Pi, so it cannot run this pull; ".222" is a stale address]',
        ),
    ]
    x10 = [
        ("AGENTS.md", "`/home/pcalnon/Development/python/Juniper/CLAUDE.md`", "`~/Development/python/Juniper/CLAUDE.md`"),
        ("docs/REFERENCE.md", "centralized in **`/home/pcalnon/Development/python/Juniper/worktrees/`** using", "centralized in **`~/Development/python/Juniper/worktrees/`** using"),
        ("docs/REFERENCE.md", "- All worktrees reside in `/home/pcalnon/Development/python/Juniper/worktrees/`\n", "- All worktrees reside in `~/Development/python/Juniper/worktrees/`\n"),
        ("docs/REFERENCE.md", "cd /home/pcalnon/Development/python/Juniper/juniper-ml\n", "cd ~/Development/python/Juniper/juniper-ml\n"),
        ("docs/REFERENCE.md", 'WORKTREE_DIR="/home/pcalnon/Development/python/Juniper/worktrees/', 'WORKTREE_DIR="$HOME/Development/python/Juniper/worktrees/'),
        ("docs/REFERENCE.md", "All worktrees go in `/home/pcalnon/Development/python/Juniper/worktrees/`. Never", "All worktrees go in `~/Development/python/Juniper/worktrees/`. Never"),
    ]
    record = [
        (
            PLAN,
            "- **Version**: 1.1.0 — v1.0.0 plus the Session 1 record and errata (§16, 2026-10-19). Where §16 and an earlier section disagree, §16 wins.",
            "- **Version**: 1.1.1 — v1.1.0 plus task E6 closed (errata X6 and X10) and erratum E-CQ, 2026-10-19. v1.1.0 added the Session 1 record and errata (§16). Where §16 and an earlier section disagree, §16 wins.",
        ),
        (
            PLAN,
            "| E6 | X7 done (B8); **X6 and X10 remain** | — |",
            "| E6 | done 2026-10-19 | X7 by B8 (juniper-ml#2249). X6: a dated correction under the first stale statement in each of the eight archived handoffs (2026-09-11 to 2026-10-03) that call turing down or the Pi-pull candidate, and on the P4-27 row of `reports/2026-10-04_consolidated-development-plan/extraction-P4-release-P11-k8s.md`. X10: `AGENTS.md` § Ecosystem Context and `docs/REFERENCE.md` § Worktree Procedures Reference now say `~/`. REFERENCE.md's other `/home/pcalnon` hits document literals hard-coded in scripts and change with those scripts (G5, D12). Applied by `util/ad-hoc/2026-10-19_turing_e6_errata.py` |",
        ),
        (
            PLAN,
            "so no `Allow-Symbol-Loss` trailer was needed (juniper-ml#2249).\n",
            "so no `Allow-Symbol-Loss` trailer was needed (juniper-ml#2249).\n"
            "- **E-CQ (the CodeQL follow-up in the 2026-10-19 handoff).** That handoff asked for CodeQL's `py/import-and-import-from` to be folded into `util/ad-hoc/2026-10-05_codeql_python_prescreen.py`. "
            "The pre-screen has had that rule, for standard-library modules, since it landed (juniper-ml#2183). "
            "On the file CodeQL flagged in juniper-ml#2242 (`tests/test_claude_agent_guard.py` at `afb75f71`) it reports exactly that alert, at line 50, and nothing else, so nothing was folded. "
            f"The one-off `{ONE_OFF}` claimed the pre-screen lacked the query; its header now carries a correction.\n",
        ),
        (
            ONE_OFF,
            "remaining Session 1 files before their PRs opened; it found nothing.\n",
            "remaining Session 1 files before their PRs opened; it found nothing.\n"
            "\n"
            "Correction (2026-10-19): the general pre-screen does cover this query. Its `import-and-import-from` rule\n"
            "(standard-library modules only, as calibrated on juniper-ml#2157) has been there since it landed in\n"
            "juniper-ml#2183, and on the file CodeQL flagged in #2242 (`tests/test_claude_agent_guard.py` at `afb75f71`)\n"
            "it reports exactly that alert. This screen differs mainly in also flagging non-standard-library modules,\n"
            "which CodeQL did not flag on #2157.\n",
        ),
    ]
    return x6 + x10 + record


def main(argv) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    ap.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)

    texts, failed = {}, 0
    for rel, anchor, repl in edits():
        text = texts.get(rel)
        if text is None:
            text = (args.root / rel).read_text(encoding="utf-8")
        if repl in text:
            print(f"present  {rel}: {anchor[:60]!r}")
        elif text.count(anchor) == 1:
            text = text.replace(anchor, repl)
            print(f"apply    {rel}: {anchor[:60]!r}")
        else:
            print(f"FAIL     {rel}: anchor found {text.count(anchor)} times: {anchor[:60]!r}")
            failed += 1
        texts[rel] = text

    today = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
    agents, n = re.subn(r"^\*\*Last Updated\*\*: \d{4}-\d{2}-\d{2}$", f"**Last Updated**: {today}", texts["AGENTS.md"], count=1, flags=re.M)
    if n != 1:
        print("FAIL     AGENTS.md: no **Last Updated** line")
        failed += 1
    texts["AGENTS.md"] = agents
    print(f"date     AGENTS.md: **Last Updated** = {today} (UTC)")

    if failed:
        print(f"{failed} edit(s) failed; nothing written")
        return 1
    changed = [rel for rel, text in texts.items() if (args.root / rel).read_text(encoding="utf-8") != text]
    for rel in changed:
        if not args.dry_run:
            (args.root / rel).write_text(texts[rel], encoding="utf-8")
    print(f"{'would change' if args.dry_run else 'changed'} {len(changed)} file(s): " + ", ".join(changed))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
