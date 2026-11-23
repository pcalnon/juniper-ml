#!/usr/bin/env python3
"""Consolidated development plan v1.15.16 -> v1.15.17: the one-artifact publish, from 2026-11-15 to 2026-11-23.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-23
Status: ad-hoc — one-off (a record revision of notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: juniper-cascor#763 and #767 (the fix); juniper-recurrence#236, juniper-ml#2592, juniper-canopy#823, juniper-data#543,
         juniper-cascor-client#199, juniper-data-client#264, juniper-ml#2593 and juniper-cascor-worker#232 (the ports and
         the release-train fix); handoffs ml#2591, ml#2594 and ml#2603; the rename PRs juniper-ml#2605 and #2606,
         juniper-cascor#772, juniper-canopy#830, juniper-data#547, juniper-data-client#267, juniper-cascor-client#201 and
         juniper-cascor-worker#234; util/ad-hoc/2026-11-15_consolidated_plan_v1_15_16_r_obs_sc_2_followups.py (the pattern)

Why
---
v1.15.16 recorded the owner's directive of 2026-11-15 (PyPI must receive the very files TestPyPI took, checked by hash)
and left the fix as "a session's work in progress". Four sessions then carried it out (b9dfa450, d67643b8, 85756bf1 and
e71d3e, 2026-11-15 to 2026-11-23):

- juniper-cascor#763 and #767 fixed cascor's three publishers, after an independent review, and added the owner's
  recovery ladder (dialog 2 of 2026-11-15); an audit of all 18 publish workflows in 8 repositories preceded them;
- seven ports and a release-train fix (ml#2592) merged by 2026-11-16, each after an independent review, and all 15
  ported workflows matched cascor's template on 2026-11-16 and again on 2026-11-23;
- the owner ruled the template sweep's two questions on 2026-11-16, and on 2026-11-23 the sweep's order was set
  around the owner's eight open rename PRs, whose substitution had also rewritten files on disk in sibling worktrees.

This revision records that in the plan's own structure: a header bullet, three handoffs in "Documents referenced", a
note in section 5 after R-OBS-SC-2's follow-ups, the owner's new item in section 6's mid-wave sitting, a Validation
record entry, and the landed scripts in "Changed by this plan". It also gives juniper-ml's docs/REFERENCE.md the
version row juniper-ml#2592 never added (SWEEP item 18): 0.6.77 -> 0.6.78.

The plan calls the person "the owner" today. The rename PRs may change that word to "Overtoad" before this lands, so
the word is read from the plan at run time, and every anchor and every new sentence that names the person is built
from it. Quoted records keep their own words.

Usage
-----
    python3 util/ad-hoc/2026-11-23_consolidated_plan_v1_15_17_one_artifact.py [--tree DIR] [--check]

An edit already present is skipped, so a re-run is a no-op. An anchor found other than its expected number of times
refuses the whole run before anything is written, and so does any rise in the number of plan lines over 512
characters (19 before this revision). ``--check`` writes nothing and exits 1 while an edit is pending.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
PLAN = "notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md"
REFERENCE = "docs/REFERENCE.md"
MAX_LINE = 512
W = "{W}"  # replaced by the word the plan uses for the person ("owner", or "Overtoad" after the rename)

# Multi-line texts are bound to names here rather than written inside a list display: adjacent literals inside a list
# or tuple trip CodeQL's py/implicit-string-concatenation-in-list, whose unresolved thread blocks a merge.

_ONOTE = "§5, the note on the one-artifact publish"
_HO_LANDED = "`…one-artifact-landed-ports-plan-v1-15-17-next.md`"
_HO_PORTS = "`…8-prs-open-reviews-then-merge-plan-v1-15-17-next.md`"
_HO_MERGED = "`…sweep-ruled-brief-cascor-plan-v1-15-17-next.md`"
_EVIDENCE = "`juniper-ml/tmp/2026-11-23-plan-v1-15-17-evidence/`"
_SWEEP_BRIEF = "`tmp/ports/SWEEP_BRIEF.md`"
_SWEEP_ITEMS = "`tmp/ports/SWEEP_ITEMS.md`"
_MERGES = "ml#2593 at 08:26:37Z, cascor-client#199 at 08:29:22Z, cascor-worker#232 at 08:29:42Z and data-client#264 at 08:30:47Z"
#: The owner's words of 2026-11-15 05:14:10Z (session b9dfa450), the second paragraph of that message, verbatim.
_DIRECTIVE = (
    "\"this needs to be fixed. deploy to pypi should send the same artifact that was already sent to testpypi. "
    "an identical hash check, of the artifacts after testpypi deploy and prior to pypi deploy, might also be helpful here to prevent this from slipping through the cracks again.\""
)
#: Dialog 2 of 2026-11-15 (session b9dfa450, asked 06:27:42Z, answered 11:47:38Z): the typed answer, verbatim.
_LADDER = (
    "\"attempt option 2 first. if that fails, within 30 days, fall back to option 1, part 1, pypi job re-run. "
    "if option 1, part 1, fails or if greater than 30 days, revert to option 1, part 2, cut a new patch version\""
)

# --- Header -------------------------------------------------------------------------------------------------------
_DATE_OLD = "juniper-deploy's pins and the parent `AGENTS.md` edit probed 2026-11-15)\n"
_DATE_NEW = (
    "juniper-deploy's pins and the parent `AGENTS.md` edit probed 2026-11-15; "
    "the one-artifact publish (juniper-cascor#763 and #767, the eight PRs after them, the audit, the identity check and the two indexes' files) and the template sweep's order probed 2026-11-23)\n"
)

_WIP_OLD = "the fix is a session's work in progress."
_WIP_NEW = "the fix is a session's work in progress (v1.15.17: it reached all 18 publishers by 2026-11-16; " + _ONOTE + ")."

_STATUS_ANCHOR = "  - Planning only: this plan changes no code,"
_STATUS_NEW = (
    "  - v1.15.17 (2026-11-23) records the one-artifact publish (" + _ONOTE + "). All 18 publish workflows of the 8 repositories that publish now give PyPI the very files TestPyPI took, checked by sha256: "
    "juniper-cascor#763 and #767 fixed cascor's three on 2026-11-15, and seven ports and a release-train fix (ml#2592) merged by 2026-11-16. No Release has run them yet. Like v1.15.0, no round checks it.\n"
    "    - It records the {W}'s rulings of 2026-11-15 (the directive, the fix's scope and the recovery ladder) and of 2026-11-16 (the template sweep's two questions), the audit, each PR's review, "
    "the identity check, the findings, and the sweep's 27 items with their dispositions.\n"
    "    - On 2026-11-23 the sweep's order was set around the PRs that rename \"owner\" to \"Overtoad\": juniper-cascor#772 first, then the cascor sweep PR, then the ports. Three client rename PRs merged at 12:30Z, touching no publish file. "
    "The rename's substitution had also rewritten files on disk in sibling worktrees; the arc's 26 uncommitted scripts were restored, proved against their sha256 manifests, and land with this version.\n"
    "    - `docs/REFERENCE.md` moves to 0.6.78 for ml#2592's edit, which had no version row (SWEEP item 18). What stays with the {W} is in " + _ONOTE + " and in §6's mid-wave sitting.\n"
    "  - Planning only: this plan changes no code,"
)

# --- Documents referenced -------------------------------------------------------------------------------------------
_DOCS_ANCHOR = "| `…guard-pr-plan-v1-15-16-next.md` | `HO/HANDOFF_2026-11-15_r-obs-sc-2-cascor-0-14-0-canopy-0-10-0-at-pypi-gates-guard-pr-plan-v1-15-16-next.md` (the two cuts of 2026-11-15) |\n"
_DOCS_NEW = (
    _DOCS_ANCHOR
    + "| " + _HO_LANDED + " | `HO/HANDOFF_2026-11-15_r-obs-sc-2-cascor-one-artifact-landed-ports-plan-v1-15-17-next.md` (cascor's fix: #763 merged and #767 merging; dialog 2's answer verbatim; ml#2591) |\n"
    "| " + _HO_PORTS + " | `HO/HANDOFF_2026-11-15_one-artifact-ports-8-prs-open-reviews-then-merge-plan-v1-15-17-next.md` (the eight PRs and their reviews; ml#2594) |\n"
    "| " + _HO_MERGED + " | `HO/HANDOFF_2026-11-16_one-artifact-ports-merged-verified-sweep-ruled-brief-cascor-plan-v1-15-17-next.md` (the merges, the identity check, the rulings of 2026-11-16; ml#2603) |\n"
)

# --- Section 5: the R-OBS-SC-2 follow-ups note's two in-progress passages -----------------------------------------------
_OPEN_PR_OLD = "No juniper-cascor PR for it was open at 06:05Z.\n"
_OPEN_PR_NEW = "No juniper-cascor PR for it was open at 06:05Z (v1.15.17: juniper-cascor#763 opened at 06:11:13Z and merged at 11:26:51Z; the next note).\n"

_NOT_OWNER_OLD = "Not the {W}'s: the publish-artifact fix (above), a session's work under ruling 2 of 2026-11-15.\n"
_NOT_OWNER_NEW = "Not the {W}'s: the publish-artifact fix (above), a session's work under ruling 2 of 2026-11-15 (v1.15.17: done by 2026-11-16; the next note).\n"

# --- Section 5: the note on the one-artifact publish ---------------------------------------------------------------------
_N_HEAD = (
    "**The one-artifact publish, 2026-11-15 to 2026-11-23** (v1.15.17; sessions `b9dfa450`, `d67643b8` and `85756bf1`, and the orchestrating session `e71d3e`, a ListAgents reference). "
    "All 18 publish workflows of the 8 repositories that publish (of the nine the audit reads, juniper-deploy publishes none) now give PyPI the very files TestPyPI took, checked by sha256; no Release has run them yet.\n"
    "Option labels and texts are quoted verbatim, \"(Recommended)\" markers included, and each answer is dated from its transcript's `tool_result`. "
    "Each fact below was re-read on 2026-11-23 from `gh`, from PyPI's and TestPyPI's JSON, from the transcripts, or from the file it names (the Validation record).\n\n"
)
_N_RULINGS = (
    "- **The {W}'s directive and rulings of 2026-11-15** (session `b9dfa450`; the directive and dialog 1 are also in the note above):\n"
    "  - the directive (05:14:10Z): " + _DIRECTIVE + "\n"
    "  - dialog 1 (asked 05:17:06Z, answered 05:24:49Z), its \"Fix scope\" question: \"cascor, then every other (Recommended)\": \"The cascor PR first. "
    "Then one PR per repo: the same change wherever the audit finds a per-job rebuild, and the hash check in every publish workflow, canopy's included "
    "(it shares one build but compares no hashes, so a stale TestPyPI upload could still slip through). I merge each once green, under this session's merge approval.\"\n"
    "  - dialog 2, \"Recovery\" (asked 06:27:42Z, answered 11:47:38Z), on how the ports should recover a release whose `pypi` gate expired, since a rebuilt file now fails the TestPyPI hash check. Its two options:\n"
    "    1. \"Re-run within 30 days, else a new patch (Recommended)\": \"Re-run the original run's PyPI job (its artifact is kept 90 days), which works while GitHub allows the approval and the re-run (30 days). "
    "Past that, cut a new patch version. skip-existing and the dispatch-from-tag recovery are removed, and the publish procedure doc says so. Simplest, and every upload is the tested build.\"\n"
    "    2. \"Dispatch that republishes TestPyPI's files\": \"Keep a dispatch from the tag, but instead of building, it downloads TestPyPI's exact files, checks them against TestPyPI's sha256, and uploads those to PyPI. "
    "Recovery then works past 30 days without a new version, at the cost of more workflow code to write and test in both repos.\"\n"
    "    - The answer, typed rather than chosen: " + _LADDER + ". The template calls these rung 1 (the republish dispatch), rung 2 (\"Re-run failed jobs\") and rung 3 (a new patch version).\n"
)
_N_CASCOR = (
    "- **juniper-cascor#763** (opened 06:11:13Z; merged 11:26:51Z as `a1b0409d`, head `4d69a4c1`, under the {W}'s account, with its first commit only), "
    "on all three cascor publishers (`publish.yml`, `publish-cascor-model.yml`, `publish-protocol.yml`):\n"
    "  - one `Build and Validate` job builds the sdist and wheel once and keeps them, with a `SHA256SUMS`, for 90 days, and both publish jobs upload that one artifact;\n"
    "  - the files are checked by sha256 against TestPyPI's JSON after the TestPyPI upload and again before the PyPI upload, and against PyPI's after its own; `skip-existing` stays off. "
    "55 cases, and 24 of 24 mutations fail them.\n"
    "  - Its independent review (agent `a9d1e555c14451d8f` of session `b9dfa450`, 06:27Z to 06:58Z; scratch in `.claude/worktrees/humble-humming-flask/tmp/review-763/`) said \"merge after fixes\":\n"
    "    - 2 MAJORs: \"Re-run all jobs\" rebuilds, and under the new workflow fails closed at TestPyPI and burns the version (juniper-ci-tools 0.9.1's run 38045867684 had re-run its build that way, so PyPI took a rebuild); "
    "and `id-token: write` was granted to the whole workflow, the build job included;\n"
    "    - 4 MINORs (an expired gate's recovery undocumented; two test gaps; a dispatch example no environment admits; a build failure that files no halt issue, juniper-ml's to fix) and NITs.\n"
    "- **juniper-cascor#767** (merged 13:15:15Z as `67588488`, head `f56915e1`, by `util/safe_merge.py`; its log is `tmp/cascor-767/safe_merge_767.log` in `humble-humming-flask`) applies every finding but the release-train one, "
    "which went to ml#2592: a re-run reuses attempt 1's artifact (`Reuse an earlier attempt's artifact`); `id-token: write` sits only on the jobs that upload; and dialog 2's ladder.\n"
    "  - Rung 1 is a `workflow_dispatch` from the release tag with `republish_from_testpypi`, whose job `Republish the tested files (dispatch only)` uploads TestPyPI's exact files and builds nothing. "
    "87 cases, and 43 of 43 mutations fail them. #767 was not reviewed on its own; most of the sweep's items, which the ports' reviews found, are gaps in the template it carries (below).\n"
    "  - The squash keeps #767's `Allow-Symbol-Loss:` lines, as cascor's main-branch symbol-loss screen needs. cascor's `publish.yml` has not changed since `675884888f5a` (read 2026-11-23).\n"
)
_N_AUDIT = (
    "- **The audit** (`util/ad-hoc/2026-11-15_publish_workflow_artifact_audit.py`, which lands with v1.15.17) reads every publish workflow on each `main`: 18 workflows in 8 repositories. "
    "Before #763 none compared a sha256 with TestPyPI, 5 rebuilt in each publish job (cascor's `publish.yml`, data, data-client, cascor-client and cascor-worker), "
    "12 set `skip-existing` (canopy, data-client, recurrence's 3 and juniper-ml's 7), and every shared artifact expired after 7 days (#763's body).\n"
    "  - Its third run, after #763 (`audit_run3.txt` in `.claude/worktrees/agent-a54a0a279acc3a863/tmp/cascor-publish-artifact/`, 12:55:57Z by its mtime), printed "
    "\"4 rebuild per publish job, 15 compare no sha256 with TestPyPI before PyPI, 12 can skip an existing TestPyPI file\": " + _HO_LANDED + "'s \"4 rebuild per job, 12 use `skip-existing`, none checked sha256 before #763\".\n"
    "  - Re-run on 2026-11-23 at 12:17Z: \"0 rebuild per publish job, 0 compare no sha256 with TestPyPI before PyPI, 0 can skip an existing TestPyPI file.\"\n"
)
_N_PRS = (
    "- **The eight PRs**, all MERGED (time; squash commit; head):\n"
    "  - juniper-recurrence#236, all three publishers (2026-11-15 23:07:44Z; `f34c69f4`; `8b36cbe4`). Its review found no BLOCKER or MAJOR, and the second commit applies its four fixes: "
    "the README's plain-dispatch and older-tag recovery, `AGENTS.md` calling the publishers tag-guarded rather than path-scoped, and the client `AGENTS.md`'s version, 0.3.0 → 0.3.1.\n"
    "  - juniper-ml#2592, the release-train monitor (23:36:08Z; `6541b2cc`; `fe230b5b`), the two gaps " + _HO_LANDED + " named: a failed `Build and Validate` now reads as `HALT_BUILD` and files a `build-failed` issue "
    "(#763's review had found that it filed none), and the monitor lists the publisher's own `workflow_dispatch` runs on the tag, so it sees a republish run.\n"
    "    - Its two review rounds (three agents) found a third gap, applied: the monitor could read `Publish Container Image`, which five repositories run on each Release and whose run had the larger id in 11 of 20 Releases sampled, "
    "so a failed PyPI build would have read as `RELEASED`. It now reads only workflows named \"… to PyPI\", and orders finished runs by their latest attempt. 182 tests; 13 of 13 mutations.\n"
    "  - juniper-canopy#823 (2026-11-16 08:27:14Z; `01079b77`; `1e8a8ece`). The review of `2c0e55b6` found no BLOCKER and one MAJOR; the fixes: no check may fail open (`continue-on-error` or `if:` on a check had passed the inherited test, the MAJOR), "
    "the install check imports the wheel from `$RUNNER_TEMP` (from the checkout's root it passed with no wheel installed: SWEEP item 10), each job's exact steps, and the runbook.\n"
    "    - The runbook corrects the review's claim that a re-run fails at the upload: warehouse answers a byte-identical file with 200 and refuses only new bytes under a name it holds (SWEEP item 11).\n"
    "  - juniper-data#543 (08:30:29Z; `3904f581`; `6fc7d53f`). The review of `a77a30fe` found no BLOCKER or MAJOR; the fixes: each job's exact step list (a `pyproject-build` rebuild before the PyPI upload had passed), "
    "the pinned template digests named as cascor `675884888f5a`'s, a merge-order section, and doc nits.\n"
    "  - juniper-cascor-client#199 (08:31:25Z; `217e9a68`; `fe962b7b`), juniper-data-client#264 (08:36:20Z; `47f5df62`; `61d6b44b`) and juniper-cascor-worker#232 (08:49:11Z; `efb4a2c7`; `a0b5e363`), under one review of the three. "
    "No BLOCKER or MAJOR; the fixes: rung 1 applies only after a TestPyPI job that succeeded or failed on index lag alone, a `TestExactly` class pinning each job's steps, the install check's script and both uploads' inputs, and each doc's version and date.\n"
    "  - juniper-ml#2593, the seven publishers (08:47:08Z; `9d9ec797`; `67e9aab1`). Its review's MAJOR, the ladder's precondition (a real install-check failure is a new patch version, never rung 1), and its MINORs are fixed in `acc5c262`: "
    "the runbook's responses, the cheatsheet's retry row, and tests pinning each job's steps, the 90-day retention and the \"… to PyPI\" names. `docs/REFERENCE.md` became 0.6.77.\n"
    "  - Session `d67643b8` merged recurrence#236 and ml#2592 with `util/safe_merge.py` (ml#2592 through the auto-merge net it armed at 23:22:09Z). "
    "The other six merged under the {W}'s account, each at the head carrying its review's fixes, the four that add a build job (data, data-client, cascor-client, cascor-worker) after ml#2592, as SWEEP item 16 required.\n"
    "    - GitHub records auto-merge armed on four of the six (" + _MERGES + ") and none on canopy#823 or data#543, which were merged directly. "
    "So " + _HO_MERGED + "'s \"The owner's armed auto-merge merged the last six\" holds for those four.\n"
    "    - ml#2593's and cascor-worker#232's heads are update-branch merges on top of their reviewed `acc5c262` and `41933886`.\n"
)
_N_IDENTITY = (
    "- **The identity check** (`util/ad-hoc/2026-11-15_publish_port_template_identity.py`, which lands with v1.15.17): each of the 15 ported workflows matches cascor `main`'s `publish.yml`, the template. "
    "\"15 of 15 pass\" on 2026-11-16 at 15:29:40Z (session `85756bf1`; its log is `tmp/ports/verify_all_mains.log` in `.claude/worktrees/sparkling-percolating-meadow`), "
    "and on 2026-11-23 at 11:47:45Z (session `e71d3e`) and again at 12:16:54Z, with cascor `main` at `802399ab`.\n"
)
_N_FIND = (
    "- **Findings**, open unless a line says otherwise:\n"
    "  - **TestPyPI's and PyPI's files differ by sha256** (" + _HO_MERGED + ", § Findings; every PyPI release of the 18 publishers' packages re-read on 2026-11-23):\n"
    "    - juniper-data, every release from 0.4.2 to 0.17.1 (15); juniper-data-client (6), juniper-cascor-client (8) and juniper-cascor-worker (7), every release: "
    "21 versions and 42 files, which the handoffs give to data-client and cascor-client alone;\n"
    "    - juniper-cascor, every release (11, from 0.3.17 to 0.14.0), its 0.13.0 and 0.14.0 wheels `eda26e26…` and `b70f3d39…` on PyPI against `f5dbc1b6…` and `c5c9a5dc…` on TestPyPI; juniper-canopy 0.3.0 only (0.5.0 to 0.10.0 match);\n"
    "    - juniper-ci-tools 0.9.1, `1dc8e01e…` on PyPI against `ade363e8…` on TestPyPI, because run 38045867684's attempt 2 re-ran its build on 2026-10-21 after attempt 1's PyPI job failed; "
    "and juniper-service-core 0.3.0, which the handoffs do not name (found 2026-11-23).\n"
    "    - All 26 recurrence releases match, as do juniper-ml's other packages, cascor's model and protocol packages, canopy's other seven, ci-tools' other ten and service-core's other nine. "
    "An index never takes a second file under a name it holds, so the differing releases keep their files; no release has been cut since (canopy `v0.10.0`, 2026-11-15 01:41:30Z, is the newest).\n"
    "  - **Fixed**: before ml#2592 the monitor could read `Publish Container Image`'s run (above).\n"
    "  - **Provenance** (re-read 2026-11-23): canopy 0.10.0's TestPyPI files carry `environment: null` where its PyPI files carry `pypi` (SWEEP item 13). "
    "On PyPI, cascor 0.14.0's and juniper-data 0.17.1's files carry `null`, while juniper-ml 0.11.5's, juniper-recurrence 0.8.1's and juniper-observability 0.4.2's carry `pypi`. It is the evidence for the next item.\n"
    "  - **Still unverified, and the {W}'s to check**: whether the PyPI trusted publishers are bound to the `pypi` environment. It needs the {W}'s PyPI login.\n"
    "  - **Old tags**: a tag cut before its repository's port has no republish job, so rung 1 cannot recover it (SWEEP item 7 puts this in every port's docs).\n"
    "  - **Re-runs are safe; re-cuts are not**: warehouse answers a byte-identical re-upload with 200, so \"Re-run failed jobs\" repeats both checks harmlessly, while a re-cut brings new bytes under names the index holds and is refused (SWEEP item 11).\n"
)
_N_1116 = (
    "- **The {W}'s rulings of 2026-11-16** (session `85756bf1`, asked 15:32:57Z, answered 22:08:20Z), the template sweep's two design questions:\n"
    "  1. \"Ladder gate\", **\"Gate it in the job (Recommended)\"** (SWEEP items 11, 21 and 26): \"The republish job reads the newest release run for the tag and refuses unless its TestPyPI job(s) concluded success in the latest attempt, "
    "and refuses if no release run exists. The docs say an index-lag failure goes to 'Re-run failed jobs' and a failed install check to a new patch version.\"\n"
    "  2. \"Install job\", **\"Yes, in this sweep (Recommended)\"** (SWEEP item 6, which also covers item 10): \"Add a job 'Verify the TestPyPI install' (needs the TestPyPI job, contents: read only, imports from outside any checkout) "
    "and make PyPI's job need it. The ceremony already reads any job with 'TestPyPI' in its name, so a failure there reads HALT_TESTPYPI with no ceremony change. "
    "It also fixes item 10, where an import from the checkout root passes without the wheel.\"\n"
    "  - " + _HO_MERGED + " quotes ruling 2 without its last sentence; the transcript has it.\n"
)
_N_PROBES = (
    "- **Two probes of 2026-11-23** (session `e71d3e`):\n"
    "  - Whether `GET actions/runs/{id}/jobs?filter=latest` lists the jobs that a \"Re-run failed jobs\" attempt carried over is UNVERIFIED: `util/ad-hoc/2026-11-23_jobs_filter_latest_after_rerun_failed_probe.py` "
    "found no run with a carried job among the 12 re-run runs its two logs read (2 in juniper-cascor, 10 in juniper-ml). So the sweep's gate for ruling 1 is to read `filter=all` and take each job name's latest attempt, which holds under either behaviour.\n"
    "  - Ruling 2's claim holds: `classify_publish_run` (`util/release_train/ceremony.py:637`) reads a failed `Verify the TestPyPI install` as `HALT_TESTPYPI`, a running one as `IN_PROGRESS`, "
    "and both TestPyPI-named jobs green with PyPI parked as `PENDING_PYPI_APPROVAL`: 6 of 6 cases of `util/ad-hoc/2026-11-23_ceremony_install_job_simulation.py`, on `main` at `81b8eaf7`.\n"
    "    - The job's name must keep \"TestPyPI\": named with neither \"TestPyPI\" nor \"PyPI\", the same cases read a failed install check as `HALT_PUBLISH` and a running one as `PENDING_PYPI_APPROVAL` (2 of 6 fail).\n"
)
_N_SWEEP = (
    "- **The template sweep** (" + _SWEEP_BRIEF + " in `.claude/worktrees/ethereal-munching-peacock`, session `e71d3e`, 2026-11-23; its 27 items are " + _SWEEP_ITEMS + " there, "
    "collected on 2026-11-15 and 2026-11-16, most of them from the ports' and ml#2592's reviews): one change to the template, juniper-cascor first, then every port.\n"
    "  - It adds ruling 2's install job and ruling 1's republish gate, a third template parameter, `PUBLISH_TAG_PREFIX`, that keeps a sub-package publisher off the meta-package's `v` tag, "
    "corrected comments and ladder docs, and test hardening with a mutation proof. A successor to the identity checker, which compares each `uses:` by action name, is being written with it.\n"
    "  - In the sweep: items 1, 2, 3 with 22, 4, 5, 6 with 10, 7, 8, 9, 11 with 21 and 26, 12, 14, 15, 17, 19, 20, 23 and 25.\n"
    "  - Recorded only: 13 (the provenance finding, above); 16 (done: ml#2592 merged first); 18 (done here: `docs/REFERENCE.md` 0.6.78); and 24 and 27 (status notes of 2026-11-15 and 2026-11-16).\n"
)
_N_RENAME = (
    "- **2026-11-23: the rename and the sweep's order.**\n"
    "  - Eight PRs that rename \"owner\" to \"Overtoad\" in the publishing repositories were open at 12:03Z: juniper-ml#2605 and #2606, juniper-cascor#772, juniper-canopy#830, juniper-data#547, juniper-data-client#267, "
    "juniper-cascor-client#201 and juniper-cascor-worker#234. A ninth, juniper-harcot#28, is outside them. The rename-repair session (worktree `crispy-forging-falcon`, [5da5c3]) repairs them.\n"
    "  - Its dialog (transcript `0f9a729e`, asked 11:39:29Z, answered 11:46:13Z): \"Template\", **\"Propagate via cascor re-pin\"**: \"Merge cascor#772 first, then update each client's pinned commit and SHA constants to the new template. "
    "Ordered merges are required.\" And \"Records\", **\"Revert edits to records (Recommended)\"**: \"Records keep their original text; the rename applies only to living docs, code comments and config. "
    "This greens harcot's tests and the archive guard without waivers.\"\n"
    "    - The same dialog chose \"Fix #2606 only\" for juniper-ml's two rename PRs, and, on a lint question, \"Merge the literals (Recommended)\" for flake8-bugbear 26.11.22's new rule B914.\n"
    "    - Its fifth question, \"Symlinks\" (asked 12:26:19Z), was unanswered at 12:58Z: how cascor#772, data#547 and canopy#830, which turned symlinks into regular files, should land, since GitHub's signed-commit API cannot write a symlink. "
    "Its answer gates cascor#772.\n"
    "  - The agreed order: juniper-cascor#772 merges first, and the {W} merges it; then the cascor sweep PR, built on cascor `main` after #772; then the ports, one PR per repository.\n"
    "    - Three client rename PRs merged at 12:30Z by the auto-merge armed on them on 2026-11-20: juniper-data-client#267 (12:30:10Z, `246b3a4d`), juniper-cascor-client#201 (12:30:16Z, `a17109c2`) "
    "and juniper-cascor-worker#234 (12:30:38Z, `dcd2c2a9`). None of their files is a publish workflow or a publish test, so their template re-pin still follows cascor#772.\n"
    "    - At 12:57Z juniper-ml#2605 (armed 2026-11-20 22:47:44Z), juniper-cascor#772 (armed 2026-11-20 22:32:21Z) and juniper-canopy#830 (armed 2026-11-23 11:01:05Z) were open with auto-merge armed, "
    "and juniper-ml#2606 and juniper-data#547 were open without it.\n"
    "  - Between 2026-11-20 and 2026-11-22 the rename's blind substitution also rewrote files on disk in sibling worktrees, tracked and untracked: `tmp/` evidence in `sparkling-percolating-meadow` and `giggly-foraging-sunbeam`, "
    "copies of cascor's files in `humble-humming-flask`'s `tmp/review-763/` and `agent-a54a0a279acc3a863`'s `tmp/cascor-publish-artifact/`, and the arc's 26 uncommitted scripts (rewritten on 2026-11-21 and 2026-11-22).\n"
    "    - The files this note quotes from those worktrees were checked: `audit_run3.txt`, the 2026-11-16 identity log and #767's merge log keep their 2026-11-15 and 2026-11-16 mtimes and hold no rewritten word.\n"
    "    - `util/ad-hoc/2026-11-23_one_artifact_carry_scripts_verified.py` restored the 26 by the inverse substitution and proved each byte-identical to the sha256 manifests of 2026-11-15 and 2026-11-16: "
    "\"verbatim=0 inverse=26 failed=0\", from either worktree. They land with v1.15.17 (Changed by this plan).\n"
    "    - Text quoted from those worktrees' files that predates 2026-11-20 reads \"Overtoad\" where it was written \"owner\"; this record quotes `gh`, git history and the transcripts instead.\n"
)
_N_NEXT = (
    "- **What remains**:\n"
    "  - the {W}'s answer to the rename-repair session's \"Symlinks\" question, which gates juniper-cascor#772;\n"
    "  - the cascor sweep PR, built and reviewed locally while juniper-cascor#772 waits, and opened once #772 merges;\n"
    "  - the ports, one PR per repository, each moving its pinned template digests;\n"
    "  - plan v1.15.18, which records them;\n"
    "  - with the {W}: the juniper-deploy stack's restart, the trio's environment upgrade and juniper-deploy's `juniper-recurrence:0.8.0` (`docker-compose.yml:598`, still there on deploy `main` on 2026-11-23), "
    "which " + _HO_LANDED + " lists as still open, and the trusted-publisher check, which it lists as unverified (above; §6, mid-wave sitting).\n"
    "    - Session `r-obs-sc-2-cascor-one-artifact-landed-ports-plan-v1-15-17-next` [9660dc] holds those items and the worktree housekeeping. None is done.\n"
)
_NOTE_ANCHOR = "\n**R-DC-PATCH's branch.** "
_NOTE_NEW = "\n" + _N_HEAD + _N_RULINGS + _N_CASCOR + _N_AUDIT + _N_PRS + _N_IDENTITY + _N_FIND + _N_1116 + _N_PROBES + _N_SWEEP + _N_RENAME + _N_NEXT + "\n**R-DC-PATCH's branch.** "

# --- Section 6: the mid-wave sitting ---------------------------------------------------------------------------------
_SIT_ANCHOR = "  - Done since: juniper-deploy's pins (deploy#278) and the parent `Juniper/AGENTS.md`'s second edit (ruling 3 of 2026-11-15).\n"
_SIT_NEW = (
    _SIT_ANCHOR
    + "- **Left with the {W} by the one-artifact publish** (v1.15.17; " + _ONOTE + "): whether the PyPI trusted publishers are bound to the `pypi` environment, which needs the {W}'s PyPI login "
    "(the provenance of cascor 0.14.0's and juniper-data 0.17.1's PyPI files shows `environment: null`). The sweep's two questions were ruled on 2026-11-16. "
    "The rename-repair session's first four were answered on 2026-11-23; its fifth, \"Symlinks\", is open and gates juniper-cascor#772.\n"
)

# --- Validation record and "Changed by this plan" ------------------------------------------------------------------------
_VALIDATION_ANCHOR = (
    "      - Every finding of both is applied, each re-checked at its source first, and none is declined. Both are archived, briefs and reports, in `reports/2026-11-15_r-obs-sc-2-follow-ups-reviews/`, "
    "beside the four other reviews v1.15.16 cites (the guard's two and the release bodies' two) and the five PRs' fix pass.\n"
)
_VALIDATION_NEW = (
    _VALIDATION_ANCHOR
    + "  - v1.15.17 is a record of the one-artifact publish (2026-11-15 to 2026-11-23). No round checks it ({W} ruling 2026-10-24). "
    "Its rulings are dated from three sessions' transcripts, `b9dfa450`, `85756bf1` and `0f9a729e` (session `crispy-forging-falcon`), each question read with its options, and the directive from `b9dfa450`'s.\n"
    "    - Its facts were re-read on 2026-11-23: from `gh`, the PRs' states, merge and head commits, auto-merge events and bodies, the Releases, and run 38045867684's jobs; "
    "from PyPI's and TestPyPI's JSON, every PyPI release of the 18 publishers' packages, and two releases' provenance; and the logs and files it names.\n"
    "    - The audit and the identity check were re-run on every `main`, and the simulation on `main` at `81b8eaf7`. Their outputs are kept in " + _EVIDENCE + ".\n"
    "    - An independent fact-check (an Opus agent of this record's session) read the draft before its PR: 1 MAJOR (three rename PRs merged at 12:30Z, after the draft's read), 8 MINORs and 7 NITs, no BLOCKER. "
    "Each was re-checked at its source and applied; none is declined. Its report and scripts are kept in " + _EVIDENCE + " too.\n"
)

_SCRIPTS_OLD = "    - and with v1.15.16's, `2026-11-15_consolidated_plan_v1_15_16_r_obs_sc_2_followups.py` (the writer)"
_SCRIPTS_NEW = "    - with v1.15.16's, `2026-11-15_consolidated_plan_v1_15_16_r_obs_sc_2_followups.py` (the writer)"

_TOOLS_ANCHOR = "`2026-11-15_cascor_0_14_0_canopy_0_10_0_security_notes_header.py` and `2026-11-15_cascor_canopy_release_notes_corrections.py`;\n"
_TOOLS_NEW = (
    _TOOLS_ANCHOR
    + "    - and with v1.15.17's, `2026-11-23_consolidated_plan_v1_15_17_one_artifact.py` (the writer), `2026-11-23_one_artifact_carry_scripts_verified.py`, "
    "`2026-11-23_jobs_filter_latest_after_rerun_failed_probe.py` and `2026-11-23_ceremony_install_job_simulation.py`, and the one-artifact arc's 26 scripts, uncommitted until then:\n"
    "      - the audit, `2026-11-15_publish_workflow_artifact_audit.py`; cascor's writers, `2026-11-15_cascor_one_artifact_publish_edits.py` and `2026-11-15_cascor_one_artifact_followup_tree.py`; "
    "`2026-11-15_cascor_one_artifact_live_index_rehearsal.py`; and the ten helpers in `2026-11-15_cascor_one_artifact_helpers/`;\n"
    "      - the seven port writers, `2026-11-15_<repo>_one_artifact_publish_port.py` (canopy, cascor-client, cascor-worker, data, data-client, juniper-ml and recurrence); "
    "and `2026-11-15_publish_port_clone.py`, `2026-11-15_publish_port_survey.py`, `2026-11-15_publish_port_template_identity.py`, `2026-11-15_fetch_pr_files.py` and `2026-11-15_build_gate_payload.py`.\n"
)

_HANDOFFS_ANCHOR = (
    "  - with v1.15.16's PR, the reviews' archive `reports/2026-11-15_r-obs-sc-2-follow-ups-reviews/`, 14 files: its `README.md`, six reviews' briefs and reports, "
    "and the five PRs' fix pass, built by `util/ad-hoc/2026-11-15_archive_r_obs_sc_2_reviews.py`.\n"
)
_HANDOFFS_NEW = (
    _HANDOFFS_ANCHOR
    + "  - the one-artifact publish's handoffs, each landed by its own PR (not this plan's): " + _HO_LANDED + " (ml#2591), " + _HO_PORTS + " (ml#2594) and " + _HO_MERGED + " (ml#2603).\n"
)

_OUTSIDE_ANCHOR = "- **Modified outside the repository**:\n"
_OUTSIDE_NEW = (
    "  - by v1.15.17's writer session (2026-11-23): " + _EVIDENCE + ", the 2026-11-23 re-reads' outputs, kept under the 2026-10-26 retention rule.\n"
    + _OUTSIDE_ANCHOR
)

# --- docs/REFERENCE.md: the version row juniper-ml#2592 never added (SWEEP item 18) ----------------------------------------
_REF_ROW_ANCHOR = "and the sibling pipeline's step 3 names model-core's `_version.py` |\n"
_REF_ROW_NEW = (
    _REF_ROW_ANCHOR
    + "| 0.6.78  | 2026-11-23 | juniper-ml#2592's edits, which merged without a version row (2026-11-15, `6541b2cc`): the Test Suite Reference's `tests/test_release_train_ceremony.py` entry covers the monitor's `HALT_BUILD`, "
    "and the Utility Script Reference's `util/release_train/ceremony.py` entry says the monitor reads only workflows named `... to PyPI`, orders finished runs by their latest attempt, "
    "lists the Release's runs with `--branch <tag>` and adds the publisher's `workflow_dispatch` runs on the tag |\n"
)

#: Plan edits: (old, new). ``old`` must occur exactly once, unless ``new`` is already there and ``old`` is gone.
PLAN_EDITS = [
    (_DATE_OLD, _DATE_NEW),
    ("- **Version**: 1.15.16\n", "- **Version**: 1.15.17\n"),
    (_WIP_OLD, _WIP_NEW),
    (_STATUS_ANCHOR, _STATUS_NEW),
    (_DOCS_ANCHOR, _DOCS_NEW),
    (_OPEN_PR_OLD, _OPEN_PR_NEW),
    (_NOT_OWNER_OLD, _NOT_OWNER_NEW),
    (_NOTE_ANCHOR, _NOTE_NEW),
    (_SIT_ANCHOR, _SIT_NEW),
    (_VALIDATION_ANCHOR, _VALIDATION_NEW),
    (_SCRIPTS_OLD, _SCRIPTS_NEW),
    (_TOOLS_ANCHOR, _TOOLS_NEW),
    (_HANDOFFS_ANCHOR, _HANDOFFS_NEW),
    (_OUTSIDE_ANCHOR, _OUTSIDE_NEW),
]

#: REFERENCE edits: (old, new, how many times ``old`` must occur). Both version lines and both dates move together.
REFERENCE_EDITS = [
    ("**Version:** 0.6.77\n", "**Version:** 0.6.78\n", 2),
    ("**Last Updated:** 2026-11-16\n", "**Last Updated:** 2026-11-23\n", 2),
    (_REF_ROW_ANCHOR, _REF_ROW_NEW, 1),
]


def person_word(plan: str) -> str:
    """The word the plan uses for the person, read from v1.15.16's status bullet."""
    found = [w for w in ("owner", "Overtoad") if f"restarting the juniper-deploy stack is the {w}'s." in plan]
    if len(found) != 1:
        raise SystemExit(f"REFUSED: cannot tell the plan's word for the person (found {found})")
    return found[0]


def long_lines(text: str) -> list[tuple[int, int]]:
    return [(n, len(line)) for n, line in enumerate(text.split("\n"), 1) if len(line) > MAX_LINE]


def apply(name: str, text: str, edits: list[tuple[str, str, int]], check: bool) -> tuple[str, int, int]:
    """Apply each (old, new, count) edit; return the new text, the pending count and the refused count."""
    pending = refused = 0
    for old, new, count in edits:
        site = old.strip()[:72]
        if new in text and text.count(old) <= text.count(new) and (count == 1 or text.count(old) == 0):
            # ``new`` may contain ``old`` (an insertion after an anchor); applied means each old sits inside a new.
            print(f"  = {name}: {site}... already applied")
            continue
        if text.count(old) != count:
            print(f"  ! {name}: {site}... REFUSED: found {text.count(old)} times, expected {count}")
            refused += 1
            continue
        text = text.replace(old, new)
        pending += 1
        print(f"  ~ {name}: {site}... {'pending' if check else 'applied now'}")
    return text, pending, refused


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--tree", type=Path, default=_REPO, help="the juniper-ml checkout to edit (default: this script's own)")
    ap.add_argument("--check", action="store_true", help="write nothing; exit 1 while an edit is pending")
    args = ap.parse_args()

    plan_path, ref_path = args.tree / PLAN, args.tree / REFERENCE
    plan0, ref0 = plan_path.read_text(encoding="utf-8"), ref_path.read_text(encoding="utf-8")
    word = person_word(plan0)
    print(f"  the plan's word for the person: {word!r}")
    plan_edits = [(old.replace(W, word), new.replace(W, word), 1) for old, new in PLAN_EDITS]
    plan1, p_pending, p_refused = apply("plan", plan0, plan_edits, args.check)
    ref1, r_pending, r_refused = apply("REFERENCE", ref0, REFERENCE_EDITS, args.check)

    before, after = long_lines(plan0), long_lines(plan1)
    grown = len(after) > len(before)
    if grown:
        print(f"  ! plan lines over {MAX_LINE} characters: {len(before)} before, {len(after)} after: {after}")
    ref_grown = len(long_lines(ref1)) > len(long_lines(ref0))
    if ref_grown:
        print(f"  ! REFERENCE lines over {MAX_LINE} characters grew: {len(long_lines(ref0))} -> {len(long_lines(ref1))}")
    if p_refused or r_refused or grown or ref_grown:
        print(f"REFUSED: {p_refused + r_refused} anchor(s); {len(after) - len(before)} new long plan line(s); nothing written", file=sys.stderr)
        return 1
    print(f"  plan lines over {MAX_LINE} characters: {len(before)} before, {len(after)} after")
    if args.check:
        return 1 if (p_pending or r_pending) else 0
    if p_pending:
        plan_path.write_text(plan1, encoding="utf-8")
    if r_pending:
        ref_path.write_text(ref1, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
