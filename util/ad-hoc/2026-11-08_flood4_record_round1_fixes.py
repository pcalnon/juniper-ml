#!/usr/bin/env python3
"""
Apply the flood-4 record PR's first validation round: every correction the three validators' findings called for.

Project: juniper-ml
Sub-Project: ad-hoc tooling (Cursor-fleet flood-4 consolidation)
Author: Paul Calnon
Created: 2026-11-08
Status: ad-hoc — one-off (flood-4 disposition record PR)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md; the validators' findings in the session
         worktree's tmp/flood4/val-record/{v1,v2,v3}/findings.json (facts, conclusions and artifacts lenses)

WHY THIS EXISTS
Three independent validators read the record, its CHANGELOG entry and the reports README with different lenses.
Their findings overlap. This applies the union as exact, single-occurrence replacements, in one pass, and refuses
the whole pass if any old text is missing or ambiguous, so a half-applied correction cannot ship. The finding ids
in each comment name the validator (v1 facts, v2 conclusions, v3 artifacts) and its finding.

Usage:
  2026-11-08_flood4_record_round1_fixes.py [--check]
"""

import sys

REC = "notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md"
CHG = "CHANGELOG.md"
RDM = "reports/2026-11-08_flood4-disposition/README.md"

FIXES = [
    # v1 F4, v2 F14: 67 of the 68 are carried; #2440 was closed uncarried.
    (REC, "round 1 is complete (six carriers merged, and all 68 census drafts they carry are closed)",
          "round 1 is complete (six carriers merged; all 68 census drafts assigned to them are closed, 67 of them carried)"),
    # v2 F15: four of sec 4's rows were open, not three.
    (REC, "have the three open defect rows of §4 fixed now, and settle the launcher's effort default and juniper-ml#2271's setting.",
          "have three of §4's four open rows fixed now, settle the fourth (the launcher's effort default), and settle juniper-ml#2271's setting."),
    # v1 F2, v2 F3, v2 F18: six of the 35 change code, two more among the folded 13; #2484's base is #2480's branch.
    (REC, "- **Second wave (owner, 2026-11-07):** 35 Cursor drafts opened in juniper-ml after the census, #2469 .. #2509",
          "- **Second wave (owner, 2026-11-07):** the 35 Cursor drafts juniper-ml received after the census, up to #2509"),
    (REC, "and four code fixes that fit neither a tests nor a docs carrier. #2484 is stacked on a `cursor/` branch.",
          "and six code fixes that fit neither a tests nor a docs carrier: #2480, #2493, #2502, #2504, #2505 and #2508. #2484 is stacked on #2480's own branch (`cursor/critical-bug-resolution-68c6`)."),
    (REC, "Round 2 therefore holds 48 drafts.",
          "Round 2 therefore holds 48 drafts, two more of them code fixes (#2513 and #2514)."),
    # v2 F20.
    (REC, "The builders rejected one finding outright: R8 targeted a tests-carrier docstring, so it was moved to that carrier.",
          "The builders applied one finding elsewhere: R8 targeted a tests-carrier docstring, so it moved to that carrier."),
    # v2 F6: round 6 still found a MAJOR, and no seventh round checked its fix.
    (REC, "The text converged only once it was cut down to each package's first fixed release, read from the published wheels.\n"
          "- Round 6 found juniper-canopy's own `APIKeyAuth` copy missing from every list of the copies. It was added before #2519 opened.",
          "From round 5 the text states only each package's first fixed release, read from the published wheels.\n"
          "- Round 6 still found a MAJOR: juniper-canopy's own `APIKeyAuth` copy was missing from every list of the copies. The builder added it before #2519 opened, checked by its own census; no seventh round ran."),
    # v2 F21; v1 F14.
    (REC, "was wrong as submitted, beyond lint:", "was wrong as submitted, beyond formatting:"),
    (REC, "a value the real Claude Code CLI rejects (§4)", "a value the real Claude Code CLI ignores with a warning (§4)"),
    # v1 F3.
    (REC, "Claude Code accepts only `low`, `medium`, `high`, `xhigh` and `max`.",
          "Claude Code's `--help` lists only `low`, `medium`, `high`, `xhigh` and `max`, and no `auto` (its parser also takes the aliases `med` and `ultracode`)."),
    # v1 F7.
    (REC, "until a stop or reset (`routes/training.py:61`, `state_machine.py:87`).",
          "until a stop or reset: the refusal is `lifecycle/manager.py:165-166`, the 409 `routes/training.py:61`, and `mark_completed` refuses any state but `STARTED` (`lifecycle/state_machine.py:239-247`)."),
    # v1 F6, v2 F13: no fix PR exists yet.
    (REC, "| **being fixed** (owner, 2026-11-08: \"Fix now\"; §8). Until the fix lands, #2519 describes it as current behaviour |",
          "| **ruled: fix now** (owner, 2026-11-08; §8). A fix is built and under validation; no PR yet. Until it lands, #2519 describes the wedge as current behaviour |"),
    (REC, "| **being fixed** (owner, 2026-11-08; §8). The race was reproduced",
          "| **ruled: fix now** (owner, 2026-11-08; §8). A fix is built and under validation; no PR yet. The race was reproduced"),
    # v1 F6 / v2 F13, and the M-1 fix's builder (2026-11-08): the page is the OLDEST 30, and it has happened.
    (REC, "| **being fixed** (owner, 2026-11-08; §8). Not reproduced: no recent PR exceeds 30 commits |",
          "| **ruled: fix now** (owner, 2026-11-08; §8). A fix is built and under validation; no PR yet. The fix's builder found the page to be the PR's **oldest** 30 commits, so commit 31 onward, the head included, is never scanned, and `--first-parent` also drops commits a merge brought in (`src/gitleaks.js:113-117, 160-172` at the pinned SHA). juniper-ml#1797's run scanned 12 commits of its 88. Seven Juniper repositories run the action the same way |"),
    # v2 F4: a re-render needs gh auth, shows live states, and degrades silently without auth.
    (REC, "and each PR's live state. A draft split across two carriers has one row naming both.",
          "and each PR's live state. A re-render therefore shows the states at that moment, and needs an authenticated `gh`: without one the renderer still exits 0, printing every carrier as \"(open)\" and every state as \"?\". A draft split across two carriers has one row naming both."),
    # v1 F12, v2 F10: two data drafts came after a carrier merged, and the fleet has drawn none since 00:58Z.
    (REC, "The fleet also opens new drafts about a carrier's subjects within minutes of the carrier **opening**, before it merges:",
          "The fleet also opened new drafts about a carrier's subjects within minutes of the carrier **opening**, mostly before it merged:"),
    (REC, "  - juniper-data #520–#524, 7–32 minutes after #518 and #519 opened;\n  - juniper-canopy #798–#801, 6–10 minutes after #797 opened.\n",
          "  - juniper-data #520–#524, 7–32 minutes after #518 and #519 opened; #523 came after #519 had merged, and #524 after both had;\n  - juniper-canopy #798–#801, 6–10 minutes after #797 opened, all before it merged.\n"),
    (REC, "  Every PR this program opens, this record's included, should be expected to draw them (§8).",
          "  Then it stopped. No Cursor draft has followed a PR opened after 00:58Z, #802 and #2519 among them, and on #2519 all five `Cursor Automation` checks finished `neutral` within a second (03:22:39–40Z). Whether this record's PR draws any is open (§8)."),
    # v1 F13.
    (REC, "juniper-ml#2510 rewrote `docs/QUICK_START.md` after", "juniper-ml#2510 changed eight lines of `docs/QUICK_START.md` after"),
    # v2 F7: the reason is update-branch refusing a conflicting merge, not a general superset rule.
    (REC, "  GitHub does not resolve a branch-side superset of `main`'s hunks, so pushing only the merged files would have left the PR `DIRTY`. Afterwards",
          "  Three of the four files conflicted three ways with `main`, and `update-branch` refuses a merge that conflicts, so the branch first had to carry `main`'s copies. Afterwards"),
    # v1 F11, v2 F8; v3 F1/F2 (the gates that HAVE landed).
    (REC, "Four harvested validator probes named the system temp directory in 11 lines: detectors that read it to prove nothing was written there, and docstrings.",
          "Four validator probes named the system temp directory in 11 lines: detectors that read it to prove nothing was written there, a guard that refuses a `TMPDIR` under it, and docstrings."),
    (REC, "Their detector lines now carry G-TMP's allow pragma, and the docstrings were reworded; no behaviour changed.\n",
          "The detector and guard lines now carry G-TMP's allow pragma, and the docstrings were reworded; no behaviour changed.\n"
          "- **The gates already on `main` caught what the local screens missed.** The record PR's validator found two failures of required checks in the harvested scripts:\n"
          "  - G-PATH (`util/home_path_literal_check.py`) refuses the owner's home directory spelled out, and 8 lines in 7 scripts did. The paths now come from `os.path.expanduser` or `Path.home()`, which give the same strings on this host; one line of recorded findings text keeps its literal under G-PATH's pragma.\n"
          "  - One probe sent RFC 6455's sample `Sec-WebSocket-Key` nonce, which gitleaks' generic-api-key rule matches. It is now built at run time from its decoded text.\n\n"
          "  The repository's pre-commit secrets hook had passed only because it scans staged changes, and nothing was staged.\n"),
    # v1 F9, v2 F9: not "14 tests"; run 41757850549 covers the ci-tools tests only; the cause is likely, not isolated.
    (REC, "- **This host's `TMPDIR` sits inside a checkout and the ecosystem root.**\n"
          "  - 14 juniper-ml tests fail locally for that reason alone: 5 regression suites run alone, and 9 ci-tools tests. Those 9 also trip the per-file coverage gate.\n"
          "  - Each fails identically on a clean `main` and passes on GitHub at identical content (run 41757850549). CI is the authority there.",
          "- **Some juniper-ml tests fail only on this host.**\n"
          "  - Five regression suites run alone, and 9 juniper-ci-tools tests, fail locally, identically on a clean `main`. Those 9 also trip the per-file coverage gate.\n"
          "  - The 9 ci-tools tests pass on GitHub at identical content (juniper-ci-tools workflow run 41757850549), and the five suites pass in the required Regression Tests jobs that every juniper-ml carrier merged with. CI is the authority there.\n"
          "  - The likely cause is this host's `TMPDIR`, which sits inside a checkout and the ecosystem root. A run with `TMPDIR` elsewhere has not isolated it."),
    # v1 F5.
    (REC, "They ship in this record's PR, harvested from this arc's nine worktrees:",
          "They ship in this record's PR, harvested from the nine of this arc's worktrees that held them:"),
    # v1 F8, v2 F17.
    (REC, "not as the host's 0.8.0 does.", "not as the host's 0.8.0 did before its upgrade on 2026-11-08 (§8)."),
    # v3 F1/F2, v2 F5: the further passes, and the true script count (158).
    (REC, "  - `…_splice_sec5.py` writes the rendered tables into §5.\n",
          "  - `…_gpath_secret_pass.py` makes the harvested scripts pass G-PATH and the secret scan (§6), with exact single-occurrence edits.\n"
          "  - `…_splice_sec5.py` writes the rendered tables into §5.\n"
          "  - `…_record_round1_fixes.py` applies this record's first validation round.\n"),
    (REC, "  With these, the PR ships 157 scripts.",
          "  With these, the PR ships 159 scripts. Before upload, the harvested scripts were also edited without changing what they compute:\n"
          "  - 21 of 28 predicted CodeQL alerts were fixed in 16 scripts. The other 7 are the fields of a pydantic model defined inside a function, which the prescreen misreads as unused locals and CodeQL's unused-variable query does not consider.\n"
          "  - 29 probes gained the `util/ad-hoc/README.md` provenance fields: 26 full headers, while three round-5 probes gained only `Related:`, which their usage text now prints as well."),
    # v2 F11.
    (REC, "It covers this record's PR, the round-2 carriers and the defect-fix PRs.",
          "It covers this record's PR and the round-2 carriers. Ruling 5's chosen option extends it to the defect-fix PRs (\"merged under this session's approval\")."),
    # v1 F1.
    (REC, "   - The repo-root `settings.local.json` is tracked but never read. Only the primary checkout holds an untracked `.claude/settings.local.json` copy, which no worktree gets.",
          "   - The repo-root `settings.local.json` is tracked but never read. Claude Code reads `.claude/settings.local.json`, which 2.1.319 resolves, for a worktree session, to the main checkout's untracked copy (as `main`'s `docs/REFERENCE.md` also says). That copy holds no `idleCompaction` key. User settings were chosen because every repository's sessions read them."),
    # v2 F12: the check gated all three upgrades; the ci-tools upgrade is a per-environment reading, disclosed.
    (REC, "   - **Done**: the host's juniper-ci-tools went from 0.8.0 to CI's 0.9.1. It lives in `JuniperCascor1`, which supplies the `pre-commit` and `juniper-check-doc-links` on `PATH`. A dry run first showed no dependency changes, and no live service used that environment.\n"
          "   - **Deferred**: the check failed for `JuniperCanopy1`. Four live canopy E2E legs run from it (ports 8052, 8053, 8058 and 8059, up since 2026-10-10). Its juniper-observability 0.4.0 and juniper-service-core 0.5.0, both below canopy's floors, are upgraded only once those legs stop.",
          "   The check the ruling named was for `JuniperCanopy1`, and it preceded all three upgrades.\n"
          "   - **Not done**: the check failed. Four live canopy E2E legs, another arc's, run from `JuniperCanopy1` (ports 8052, 8053, 8058 and 8059, up since 2026-10-10). Its juniper-observability 0.4.0 and juniper-service-core 0.5.0, both below canopy's floors, stay until the owner decides.\n"
          "   - **Done anyway, on a per-environment reading of the ruling**: the host's juniper-ci-tools went from 0.8.0 to CI's 0.9.1. It lives in `JuniperCascor1`, which supplies the `pre-commit` and `juniper-check-doc-links` on `PATH`, and that environment got its own check: no live Python service (only five Serena MCP launchers running its `uv` binary) and a dry run with no dependency changes. It is reversible with `pip install juniper-ci-tools==0.8.0` there."),
    # v1 F2, v2 F3 (sec 8 side).
    (REC, "  They are triaged against current `main`, then carried in tests and docs carriers per repository. One juniper-ml code carrier takes #2480, #2493, #2502 and #2504, and the launcher's effort fix. #2484 is stacked on a `cursor/` branch, and #2513 follows up #2474.",
          "  Eight of them change code: #2480, #2493, #2502, #2504, #2505, #2508, #2513 and #2514. They were triaged against `main` on 2026-11-08 and are carried in per-repository tests, docs and code carriers; the launcher's effort fix rides in the juniper-ml code carrier. #2484 is stacked on #2480's own branch, and #2513 follows up #2474. The next update of this record holds the triage table."),
    # v2 F10, v2 F19.
    (REC, "- **The drafts this record's PR draws.** The fleet opens them within minutes of a PR opening (§6), and no ruling covers them yet.",
          "- **Any drafts this record's PR draws.** None had followed a PR since 00:58Z (§6). Any that do are covered by no ruling.\n"
          "- **The manifests' evidence.** The archived manifests cite their builders' `tmp/` logs (194 paths, such as `claim_check.log`), which are not in `reports/`. They are archived before the worktree cleanup (ruling 7) removes them."),
    # The CHANGELOG entry: v1 F4/F5/F10, v2 F4/F14/F16, v3 F3, and the script count.
    (CHG, "  disposed of: six carriers (juniper-data#518 and #519, juniper-canopy#797 and #802, juniper-ml#2517 and #2519) and\n"
          "  all 68 census drafts they carry closed.",
          "  disposed of: six carriers (juniper-data#518 and #519, juniper-canopy#797 and #802, juniper-ml#2517 and #2519) merged,\n"
          "  and all 68 census drafts assigned to them closed, 67 of them carried."),
    (CHG, "  `reports/2026-11-08_flood4-disposition/`, from which §5 re-renders byte for byte. The arc's 157\n"
          "  `util/ad-hoc/2026-11-07_flood4_*` and `2026-11-08_flood4_*` scripts, harvested from its nine worktrees, are kept\n"
          "  as provenance. Where a validator probe reads the system temp directory, the line carries gate G-TMP's allow\n"
          "  pragma, and the scripts' predicted CodeQL alerts are fixed.",
          "  `reports/2026-11-08_flood4-disposition/`, from which §5 re-rendered byte for byte (the renderer also reads each\n"
          "  PR's live state). The arc's 159 `util/ad-hoc/2026-11-07_flood4_*` and `2026-11-08_flood4_*` scripts, harvested\n"
          "  from the nine of its worktrees that held them, are kept as provenance. Before upload they were made to pass\n"
          "  gates G-TMP and G-PATH and the secret scan, 21 of 28 predicted CodeQL alerts were fixed (the other 7 are pydantic\n"
          "  fields the prescreen misreads), and 29 probes gained provenance headers; nothing they compute changed."),
    # v3 F8, v2 F4/F19: the README.
    (RDM, "archived because their originals lived in the builders' worktree `tmp/` directories, which `git worktree remove` deletes.",
          "archived because their originals lived in worktree `tmp/` directories (four in the orchestrator's, two in the juniper-ml builders'), which `git worktree remove` deletes."),
    (RDM, "The renderer asks GitHub for each PR's live state, so a re-render shows the state at that moment, not at the record's date.",
          "The renderer asks GitHub, through an authenticated `gh`, for each PR's live state and title, so a re-render shows the state at that moment, not at the record's date. Without `gh` authentication it still exits 0, but prints every carrier as \"(open)\" and every state as \"?\".\n\n"
          "The manifests cite their builders' `tmp/` logs as evidence (such as `claim_check.log`); those logs are not part of this archive."),
]


def main():
    check = "--check" in sys.argv[1:]
    texts = dict()
    for path, _, _ in FIXES:
        if path not in texts:
            with open(path, encoding="utf-8") as fh:
                texts[path] = fh.read()
    done = 0
    for path, old, new in FIXES:
        s = texts[path]
        # Already applied. Test the NEW text, not the old one: an insertion keeps its anchor line, so its old text
        # still occurs once after the edit, and an old-text test would insert it again.
        if new in s:
            continue
        if s.count(old) != 1:
            raise SystemExit("REFUSING (nothing written): %d occurrences in %s of: %r" % (s.count(old), path, old[:100]))
        texts[path] = s.replace(old, new)
        done += 1
    if not check:
        for path, s in texts.items():
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(s)
    print("%s: %d of %d corrections %s" % ("check" if check else "apply", done, len(FIXES), "pending" if check else "applied"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
