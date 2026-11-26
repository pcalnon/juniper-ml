#!/usr/bin/env python3
"""Archive the one-artifact template sweep's live record, review briefs and reports, and port reports, verbatim, into reports/.

Project: juniper-ml
Sub-Project: ad-hoc tooling (consolidated plan record)
Author: Paul Calnon
Created: 2026-11-26
Status: ad-hoc -- single-use archiver, with a re-check mode
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md v1.15.18 (which records this archive);
         util/ad-hoc/2026-11-15_archive_r_obs_sc_2_reviews.py (this archiver's model);
         util/ad-hoc/2026-11-23_publish_port_template_identity.py (the cross-repo checker the rounds reviewed)

Why
---
The one-artifact template sweep (2026-11-23 to 2026-11-26) swept juniper-cascor's one-artifact publish template
(juniper-cascor#777), reviewed the cross-repo port checker round by round until a round found no BLOCKER and no MAJOR
(fix pass 11 delivered the FINAL checker), and ported the swept template to the other seven publishing repositories:
juniper-cascor-client#206 and its follow-up #207, juniper-data-client#274, juniper-cascor-worker#238, juniper-canopy#844,
juniper-data#553, juniper-recurrence#241 and juniper-ml#2673. Its record existed only in the gitignored ``tmp/`` of two
session worktrees (ethereal-munching-peacock, the checker's arc; moonlit-percolating-sun, the ports), and
``git worktree remove`` deletes a worktree's ``tmp/``. So each file is copied here, verbatim: the arc's live record
(``REVIEW_DISPOSITIONS.md``), the review rounds' briefs and reports, the fix passes' briefs, the sweep's and the ports'
briefs, and each port's independent review and executor reports.

Each source is named relative to the juniper-ml primary checkout, which is found from this checkout's git common
directory, and its sha256 is pinned below. A copy is the source's bytes, plus one final newline only if the source
lacks one (none did on 2026-11-26). A run refuses to write when a source no longer hashes to its pin: the live record
in particular may still grow, and a moved source is re-pinned on purpose, never followed silently.

Usage
-----
    python3 util/ad-hoc/2026-11-26_archive_one_artifact_sweep_reviews.py [--check]

``--check`` writes nothing. It exits 1 when an archived file is missing or differs from its source (or, when a source
has gone, from its pin), when the README differs from the one this table renders, or when the archive holds a file the
table does not name. Without ``--check`` it writes every missing or differing file, and refuses (exit 1, nothing
written) while any source is missing or moved.
"""

from __future__ import annotations

import argparse
import hashlib
import subprocess
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
OUT = "reports/2026-11-23_one-artifact-template-sweep-reviews"
#: The two session worktrees the sources sit in, relative to the juniper-ml primary checkout.
W = ".claude/worktrees/ethereal-munching-peacock"
WT = ".claude/worktrees/moonlit-percolating-sun"
#: This record's own session worktree (plan v1.15.18's probes, landing prep and validation).
ME = ".claude/worktrees/purring-hugging-hippo"

#: archived name -> (source, relative to the juniper-ml primary checkout; its sha256; what it is)
FILES = {
    "dispositions.md": (f"{W}/tmp/sweep/REVIEW_DISPOSITIONS.md", "f70311a8ffdcbcd1346c40532154bd53058af7deb9c96fb934932a86e0c5feb3", "The arc's live record: every review round, fix pass, ruling of the Overtoad's and port, and the disposition of each finding"),
    "round-06_report.md": (f"{W}/tmp/r6review/ROUND6_REPORT.md", "d5f64ae4ba39fb9ac0b8c445a6fed4e3aa64e200337a896af6dec8dfea8cec69", "Round 6's report: the adversarial review of fix pass 4 (the checker, checker-r5)"),
    "round-07_report.md": (f"{W}/tmp/r7review/ROUND7_REPORT.md", "585d43f28bde041946e08c280dbcecbb9a7defd073675a0767438635785d19a8", "Round 7's report: the review of fix pass 5 (checker-r6)"),
    "round-08_report.md": (f"{W}/tmp/r8review/ROUND8_REPORT.md", "018ad06bb61a898ac1cc309acb60c3f746180980d86f7af2c449ad268231e859", "Round 8's report: the review of fix pass 6 (checker-r7)"),
    "round-09_report.md": (f"{W}/tmp/r9review/ROUND9_REPORT.md", "66ab6856643c04d4f7953c73fe8e0a537c7c24dc3cbb6376b997dff75c3968c3", "Round 9's report: the review of fix pass 7 (checker-r8, the Overtoad's exact-pins ruling)"),
    "round-10_report.md": (f"{W}/tmp/r10review/ROUND10_REPORT.md", "7d25ccad4a5b5a496ee48678b4ee58da028f7fa4b2b4329a0f7028280ca6eeef", "Round 10's report: the review of fix pass 8 (checker-r9)"),
    "round-11_report.md": (f"{W}/tmp/r11review/ROUND11_REPORT.md", "a5835dd1dea4d5df706c3672d90b2f4afe7d85ddca55c356d93e5c3624141cfa", "Round 11's report: the review of fix pass 9 (checker-r10)"),
    "round-12_report.md": (f"{W}/tmp/r12review/ROUND12_REPORT.md", "c21486863edf5ba7cfb5dc39a2d3b8817b9920162f7649d12d6240602852b3e8", "Round 12's report: the review of fix pass 10 (checker-r11), the round that cleared the gate"),
    "round-04_brief.md": (f"{W}/tmp/sweep/ROUND4_BRIEF.md", "14fbbdf1a925a434511815f010f8c5101bfbd0b2ff81be17e3acedf935aa242e", "Round 4's review brief: the cascor sweep's second fix pass (round 3)"),
    "round-05_brief.md": (f"{W}/tmp/sweep/ROUND5_BRIEF.md", "e9e7e584c5fbbd9a1cc1ecd7962d20a068985239e13d24166a498dd46276d196", "Round 5's review brief: the cascor sweep's third fix pass (tree cascor-r4)"),
    "round-06_brief.md": (f"{W}/tmp/sweep/ROUND6_BRIEF.md", "657ecd33fea2eb568d395c82f835e78f66ad4f69676da270c3699a924ecd1985", "Round 6's review brief: fix pass 4 on the checker (checker-r5)"),
    "round-07_brief.md": (f"{W}/tmp/sweep/ROUND7_BRIEF.md", "fd6a3caed7a2f587775e070eb2c1c2cff262fc6d1236f5a30916e59124ba33ca", "Round 7's review brief: fix pass 5 on the checker (checker-r6)"),
    "round-08_brief.md": (f"{W}/tmp/sweep/ROUND8_BRIEF.md", "c4bf141ae3cedc1f1d21543f334cc6e4300e776e21f30231c4cb4360cfad789e", "Round 8's review brief: fix pass 6 on the checker (checker-r7)"),
    "round-09_brief.md": (f"{W}/tmp/sweep/ROUND9_BRIEF.md", "c5f8ebcda8962d3bcc66cffe68ae4211dceec54b56cf0bd19b845bc5d785711d", "Round 9's review brief: fix pass 7 on the checker (checker-r8), the Overtoad's exact-pins ruling"),
    "round-10_brief.md": (f"{W}/tmp/sweep/ROUND10_BRIEF.md", "f8eded2b7c57c7c7729c9b673fc43a7a2f77c9900eb08c24d5271e36cf0058fc", "Round 10's review brief: fix pass 8 on the checker (checker-r9), the jobs' keys and YAML 1.2 typing"),
    "round-11_brief.md": (f"{W}/tmp/sweep/ROUND11_BRIEF.md", "1e685330eaa35d3c641d898cd092c770390a9950121311b582afad76a6ff8c63", "Round 11's review brief: fix pass 9 on the checker (checker-r10), upload inputs, extra jobs and action SHAs"),
    "round-12_brief.md": (f"{W}/tmp/sweep/ROUND12_BRIEF.md", "2641448130fe05291cbc177f3e63265eb3df3fdc357a5c2f5c0be7b15eae0c6d", "Round 12's review brief: fix pass 10 on the checker (checker-r11), what it prints, aliases, the build job's upload and file commands, concurrency"),
    "fixpass-03_brief.md": (f"{W}/tmp/sweep/FIXPASS3_BRIEF.md", "829480919a291d235ce6a359b6b8ba283620b963fa2acd6b5f20e5ade8f0e7c5", "Fix pass 3's brief: round 4's fixes, the tree cascor-r4, every proof re-run"),
    "fixpass-04_brief.md": (f"{W}/tmp/sweep/FIXPASS4_BRIEF.md", "3b6a29bfc03caa12de382aed8093a1fbdb2cb24400af6348d5c68b65cfd331ea", "Fix pass 4's brief: the checker, after round 5"),
    "fixpass-05_brief.md": (f"{W}/tmp/sweep/FIXPASS5_BRIEF.md", "0055b7faca0b0bfb1a5e3c1353e90ebc8ad469e589dc880b2e85fd71b1942116", "Fix pass 5's brief: the checker, after round 6"),
    "fixpass-06_brief.md": (f"{W}/tmp/sweep/FIXPASS6_BRIEF.md", "4a0052ea6baeb5e402c62e01b1eb35ce411f1a9c70fbdb160ea1d3166401afa9", "Fix pass 6's brief: the checker, after round 7"),
    "fixpass-07_brief.md": (f"{W}/tmp/sweep/FIXPASS7_BRIEF.md", "d98429059e1c0acc7cc3f9421e8a72aae3a18e5f3489d3b20e2cc28d50c2ab2f", "Fix pass 7's brief: pin exact install scripts (the Overtoad's ruling of 2026-11-24)"),
    "fixpass-08_brief.md": (f"{W}/tmp/sweep/FIXPASS8_BRIEF.md", "c0ee15d61d9aa041c6ffe3110d7246c34387f6bbe6aa9781003c246b2179ff21", "Fix pass 8's brief: the checker's job structure and YAML typing, after round 9"),
    "fixpass-09_brief.md": (f"{W}/tmp/sweep/FIXPASS9_BRIEF.md", "fab945bfc0e7b3474c82e8a9aa98607e59e697b35e47badcb6f235d5da6b23e6", "Fix pass 9's brief: upload inputs, extra jobs and action SHAs, after round 10"),
    "fixpass-10_brief.md": (f"{W}/tmp/sweep/FIXPASS10_BRIEF.md", "a45f1b5d4080f294c9620e583837fb292ff2d42dd05ae6f8e03ea1f6163eedde", "Fix pass 10's brief: output escaping, aliases, the build job's pre-build steps, concurrency, after round 11"),
    "fixpass-11_brief.md": (f"{W}/tmp/sweep/FIXPASS11_BRIEF.md", "5fa475644359846a7805c45897dacc3f72effdc24759be94d9a4068c292b8587", "Fix pass 11's brief: round 12's MINORs and NITs, with no further review round (the FINAL checker)"),
    "land_brief.md": (f"{W}/tmp/sweep/LAND_BRIEF.md", "b15613ee31544eb96e73fa4521269d7681e8c9c8e6b9d567d617efaa7b951228", "The landing-prep brief for the cascor sweep's pull request (juniper-cascor#777)"),
    "sweep_brief.md": (f"{W}/tmp/ports/SWEEP_BRIEF.md", "bc9bc3271db0e4e40a9d25df35e1f30a25b204ef70000ab76304509ecd556f0f", "The sweep's brief: juniper-cascor first, then every port"),
    "sweep_items.md": (f"{W}/tmp/ports/SWEEP_ITEMS.md", "b701d1d51b1a3841110b8d417205a2179a1a80a452ef5687d483688be0c1b05f", "The sweep's items, for one sweep across juniper-cascor and every port"),
    "plan_v1_15_18_inputs.md": (f"{W}/tmp/arc/plan_v1_15_18_inputs.md", "68a98f982ec998097bdd218fff6b072333137fff656bee5cdf0fda2fec385b1a", "Inputs for plan v1.15.18, collected by session ffffd3"),
    "sweep-port_brief.md": (f"{WT}/tmp/ports/SWEEP_PORT_BRIEF.md", "7f957d3a1acf94c7297f95c22ac77863d8dfb169c5147c71cf420c3c7d760b42", "The port brief: port juniper-cascor's swept template (#777) to one repository, its addenda included"),
    "sweep-port-review_brief.md": (f"{WT}/tmp/ports/SWEEP_PORT_REVIEW_BRIEF.md", "81948cf301c30d16e75ef80f650511e92066246ad4db7b7aedba02b5659d31b2", "The port review brief: an independent review of one port's pull request"),
    "port-juniper-canopy_review.txt": (f"{WT}/tmp/ports/juniper-canopy/review/REVIEW.txt", "280c5b45d334c55655b491fa714d564807e7c10fad652ae5f47b6a9296671550", "The independent review of juniper-canopy#844"),
    "port-juniper-cascor-client_review.txt": (f"{WT}/tmp/ports/juniper-cascor-client/review/REVIEW.txt", "7bf33cc1b8981f8f6563be1a4d24b1ca7a805b34663a0ecdb5050f83c395c25a", "The independent review of juniper-cascor-client#206"),
    "port-juniper-cascor-worker_review.txt": (f"{WT}/tmp/ports/juniper-cascor-worker/review/REVIEW.txt", "b2ab618aec9c082ca95424824b2add614cab28eeb3c527b54a7f9650ad1af1c6", "The independent review of juniper-cascor-worker#238"),
    "port-juniper-data-client_review.txt": (f"{WT}/tmp/ports/juniper-data-client/review/REVIEW.txt", "0580d958593f7e44bcba482c2cd0b480068d3eb95a4cb0008351c01f84a53608", "The independent review of juniper-data-client#274"),
    "port-juniper-data_review.txt": (f"{WT}/tmp/ports/juniper-data/review/REVIEW.txt", "f1ed10ed87b85d8c77748a841c0d5a1161a0d7519671614abb91bdcd77ffe488", "The independent review of juniper-data#553"),
    "port-juniper-ml_review.txt": (f"{WT}/tmp/ports/juniper-ml/review/REVIEW.txt", "8594470fdc5c2d0bddaa1c57c2dafd7e69568a2c082e58ef674475d6d054e80e", "The independent review of juniper-ml#2673"),
    "port-juniper-recurrence_review.txt": (f"{WT}/tmp/ports/juniper-recurrence/review/REVIEW.txt", "29bb699de04b319af287e3ebc1f6aaa5c5918b48dd9965dab5e796c43c2fbdcf", "The independent review of juniper-recurrence#241"),
    "port-juniper-canopy_report.txt": (f"{WT}/tmp/ports/juniper-canopy/REPORT.txt", "57412d98f039329a80b2101f7600fb3d7753d377209be2d1d64724e79b76f7f6", "The executor's report: the juniper-canopy port (#844)"),
    "port-juniper-canopy_report-fixup.txt": (f"{WT}/tmp/ports/juniper-canopy/REPORT_FIXUP.txt", "d7e2c57d8dd9058ee8d43f84bccf0ed0f8e77059a108235acb75329e005a443d", "The executor's report on #844's second commit: the three gaps the first report named"),
    "port-juniper-canopy_report-fixup2.txt": (f"{WT}/tmp/ports/juniper-canopy/REPORT_FIXUP2.txt", "c1e4ee978ce6d074e131a3a6bb54aa6a18b2e834d886a3bc19338c6e7af34141", "The executor's report on #844's third commit: its review's M1 and N1 in files, M2 and N3 in the body"),
    "port-juniper-cascor-client_report.txt": (f"{WT}/tmp/ports/juniper-cascor-client/REPORT.txt", "459aa340bb30f2ce348da4d899a9a358f9824f13b62a74b3289c4d806a3ad490", "The executor's report: the juniper-cascor-client port (#206)"),
    "port-juniper-cascor-client_report-fixup.txt": (f"{WT}/tmp/ports/juniper-cascor-client/REPORT_FIXUP.txt", "f9327bb767acccce39d3482a863b14fee5273b94eb9d115751b46a355091cb94", "The executor's report on #206's fix-up for its review (R1-R7)"),
    "port-juniper-cascor-client-followup_report.txt": (f"{WT}/tmp/ports/juniper-cascor-client-followup/REPORT.txt", "e4ce49d4d7cc111c3454c384d974b3c9a864823de78af8fa64c8b53612ea1c96", "The executor's report on #206's follow-up, juniper-cascor-client#207: both causes of a failed PyPI files check"),
    "port-juniper-cascor-worker_report.txt": (f"{WT}/tmp/ports/juniper-cascor-worker/REPORT.txt", "513628aeb3b2ae26baab8df78585118d6e589d6b5da0fb6f9f3fe3213b47100f", "The executor's report: the juniper-cascor-worker port (#238)"),
    "port-juniper-cascor-worker_report-fixup.txt": (f"{WT}/tmp/ports/juniper-cascor-worker/REPORT_FIXUP.txt", "adf6720d6b228638683b1ae4f3516f9ada26cdc67976978df9a57725dede8197", "The executor's report on #238's fix-up for its review's R-1"),
    "port-juniper-data-client_report.txt": (f"{WT}/tmp/ports/juniper-data-client/REPORT.txt", "20b34fc01ecf16bdbd5f6308954f987b1f9683fb752a56512c0aab3bf5f91fdc", "The executor's report: the juniper-data-client port (#274)"),
    "port-juniper-data-client_report-fixup.txt": (f"{WT}/tmp/ports/juniper-data-client/REPORT_FIXUP.txt", "4efe9ccb6fc61b859421f6d3dbc6446f122a5e9fc64e602b60254106445f2286", "The executor's report on #274's fix-up for its review"),
    "port-juniper-data_report.txt": (f"{WT}/tmp/ports/juniper-data/REPORT.txt", "5026924f407393b41293e76ad56f550d5e9747831b02d9c5c30fe27ca9c72935", "The executor's report: the juniper-data port (#553)"),
    "port-juniper-data_report-fixup.txt": (f"{WT}/tmp/ports/juniper-data/REPORT_FIXUP.txt", "cf29f40096fb8cbe72952a987dd1151ae0087a494fd22244d7155eb4c8e9b691", "The executor's report on #553's fix-up for its review (R-1, R-2, R-3, R-6)"),
    "port-juniper-ml_report.txt": (f"{WT}/tmp/ports/juniper-ml/REPORT.txt", "bdccfea6be770f104cc683429a66ba8dd1b17de90c74bd4046f9b889a82cea15", "The executor's report: the juniper-ml port (#2673), all seven publishers"),
    "port-juniper-ml_report-fixup.txt": (f"{WT}/tmp/ports/juniper-ml/REPORT_FIXUP.txt", "d14eec367449a71ad272ebe4340a815c8d69031dcfd11a6d7ae8fc67aa3f72f8", "The executor's report on #2673's fix-up for its review (F1-F3, N1-N5): stopped before the push when the head moved, then its outcome"),
    "port-juniper-ml_report-fixup-part2.txt": (f"{WT}/tmp/ports/juniper-ml/REPORT_FIXUP_part2.txt", "820ff9d0aab91da46acdb99633562df3999619006f80e94a23f0d3b40cf58176", "The outcome of #2673's fix-up, written on its own: pushed after the re-pin"),
    "port-juniper-recurrence_report.txt": (f"{WT}/tmp/ports/juniper-recurrence/REPORT.txt", "4ebfdc559c622794f43a719ab9567564b8d88beea0ff085562b210696fbf5242", "The executor's report: the juniper-recurrence port (#241), all three publishers"),
    "port-juniper-recurrence_report-fixup.txt": (f"{WT}/tmp/ports/juniper-recurrence/REPORT_FIXUP.txt", "40fbc5eda87135136cc247698d9b48dd3ba363ac05fa448c6e8707102a09b87d", "The executor's report on #241's fix-up, pushed"),
    "plan-v1-15-18-landing-prep_brief.md": (f"{ME}/tmp/v1_15_18/landing/LANDING_PREP_BRIEF.md", "05f3bbfbf1d0744f5084a6ba3e4e86778047bb5527dbbf41b497f88dff6b1c77", "Plan v1.15.18's landing-prep brief: the copies, the juniper-ml writer's CodeQL fix and its replay, the three promoted tools, this archive and the proof tools' archive"),
    "plan-v1-15-18-landing-prep_report.txt": (f"{ME}/tmp/v1_15_18/landing/REPORT.txt", "3deed96975ab34021250e1fd4891b7d3461f4b113b7409ab1375a9c46de21141", "The landing-prep agent's report: every file it created with its sha256, each proof's command and result, and its deviations"),
    "plan-v1-15-18-host-probe.txt": (f"{ME}/tmp/v1_15_18/probe_state.out", "61a783faa8d03b942fc504ded0905aa609c3fc1dcdfb559e54cdbbbda39a824d", "Plan v1.15.18's read-only host probe (2026-11-26 21:54:57Z): the primary's HEAD, the parent backups' sha256, running containers, listening ports, worktrees"),
    "plan-v1-15-18-validation_common-brief.md": (f"{ME}/tmp/v1_15_18/val/VALIDATION_BRIEF_COMMON.md", "3340e2e93d0e3385d6879219d8e95bb4a51c7962736bd4f1c4edeaf18f255fbc", "Plan v1.15.18's validation, round 1: the part of the brief both lenses shared (sources, rules, severities, output)"),
    "plan-v1-15-18-validation-facts_brief.md": (f"{ME}/tmp/v1_15_18/val/facts/BRIEF.md", "ac888519104d333f752b429acd97e3efc224f79f80748e3a0e9bd7c9c2028271", "Round 1, lens A's brief: the fact re-probe of draft 1"),
    "plan-v1-15-18-validation-facts_findings.txt": (f"{ME}/tmp/v1_15_18/val/facts/findings.txt", "96d758930c5c63424062083770da6b8946f90166c593163fd84392a137b9ad1b", "Round 1, lens A's findings on draft 1 (0 BLOCKER, 3 MAJOR, 11 MINOR, 10 NIT), as its agent wrote them"),
    "plan-v1-15-18-validation-facts_fixes.json": (f"{ME}/tmp/v1_15_18/val/facts/fixes.json", "6a9fc44e183a63f87f8abc496e3786e8f742c99c2ddd6faa2ea772c29b5eec12", "Round 1, lens A's proposed edits to draft 1"),
    "plan-v1-15-18-validation-attack_brief.md": (f"{ME}/tmp/v1_15_18/val/attack/BRIEF.md", "f0b6b883dcdb9d1aa578bfcfdcca502674d4c2143eb7f87e41add74b46c8da8c", "Round 1, lens B's brief: the completeness and consequence attack on draft 1"),
    "plan-v1-15-18-validation-attack_findings.txt": (f"{ME}/tmp/v1_15_18/val/attack/findings.txt", "4326942b7a76b20bc04a4a2d451cba6fc84dcd2ee89fe9993785f7f45d4c2f79", "Round 1, lens B's findings on draft 1 (1 BLOCKER, 8 MAJOR, 18 MINOR, 11 NIT), as its agent wrote them"),
    "plan-v1-15-18-validation-attack_fixes.json": (f"{ME}/tmp/v1_15_18/val/attack/fixes.json", "77b6bc84b837d3716099ee7c39c59d520b34b2a5fa47315fef3f393d13871e3a", "Round 1, lens B's proposed edits to draft 1"),
    "plan-v1-15-18-validation-round2_brief.md": (f"{ME}/tmp/v1_15_18/val/round2/BRIEF.md", "25d3829e53f4f445d88c4e3ed8ae1d2a2f62a7e2f73b684b5747c6e335612626", "Round 2's brief: the corrections in draft 2, adversarially"),
    "plan-v1-15-18-validation-round2_findings.txt": (f"{ME}/tmp/v1_15_18/val/round2/findings.txt", "bb7be254bde72bea2d948a63eaba92342c75a27ec9a8b48c3adb985857f11ccb", "Round 2's findings on draft 2 (0 BLOCKER, 1 MAJOR, 8 MINOR, 14 NIT), as its agent wrote them"),
    "plan-v1-15-18-validation-round2_fixes.json": (f"{ME}/tmp/v1_15_18/val/round2/fixes.json", "3047be121e9fedf4827efa77447e200bc64584ef1ab907bbc0b5be1b6a89e8fb", "Round 2's proposed edits to draft 2"),
}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def primary_checkout() -> Path:
    out = subprocess.run(["git", "rev-parse", "--path-format=absolute", "--git-common-dir"], cwd=_REPO, capture_output=True, text=True, check=True)
    return Path(out.stdout.strip()).parent


def copy_of(source: bytes) -> bytes:
    """The archived copy of a source: its bytes, plus one final newline only if it lacks one."""
    return source if source.endswith(b"\n") else source + b"\n"


def matches_pin(archived: bytes, pin: str) -> bool:
    """Whether an archived copy is the copy of a source that hashed to ``pin``."""
    return sha(archived) == pin or (archived.endswith(b"\n") and sha(archived[:-1]) == pin)


def render_readme() -> str:
    lines = [
        "# The one-artifact template sweep: its live record, reviews, briefs and port reports",
        "",
        "Archived on 2026-11-26 by `util/ad-hoc/2026-11-26_archive_one_artifact_sweep_reviews.py`, as plan v1.15.18 records",
        "(`notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md`). The sweep (2026-11-23 to",
        "2026-11-26) swept juniper-cascor's one-artifact publish template (juniper-cascor#777), reviewed the cross-repo port",
        "checker (`util/ad-hoc/2026-11-23_publish_port_template_identity.py`) round by round until a round found no BLOCKER and",
        "no MAJOR, and ported the swept template to the other seven publishing repositories (juniper-cascor-client#206 and its",
        "follow-up #207, juniper-data-client#274, juniper-cascor-worker#238, juniper-canopy#844, juniper-data#553,",
        "juniper-recurrence#241 and juniper-ml#2673). Before this archive every file here sat in the gitignored `tmp/` of one",
        "of two session worktrees, which `git worktree remove` deletes.",
        "",
        "Each file is a verbatim copy of its source, byte for byte (a source without a final newline would have gained one;",
        "none lacked it). Nothing was edited: each review's findings are as its reviewer wrote them, before any was checked,",
        "and `dispositions.md` records what became of each. Paths inside the files name the two worktrees as they were:",
        f"`$W` is `{W}` and `$WT` is `{WT}` in the juniper-ml primary checkout.",
        "",
    ]
    renamed = sorted(name for name in FILES if name.endswith(".md.txt"))
    if renamed:
        lines += [
            "Stored as `.md.txt`, the content still verbatim, because as a `.md` file it fails the doc-link check",
            f"(`juniper-check-doc-links`): {', '.join(f'`{name}`' for name in renamed)}.",
            "",
        ]
    lines += [
        "| File | What it is | Source (in the juniper-ml primary) | sha256 |",
        "| --- | --- | --- | --- |",
    ]
    for name, (src, pin, what) in FILES.items():
        lines.append(f"| [{name}]({name}) | {what} | `{src}` | `{pin[:16]}…` |")
    lines += [
        "",
        "Re-check (it writes nothing; when a source has gone, it checks the archived copy against its pinned sha256):",
        "",
        "```bash",
        "python3 util/ad-hoc/2026-11-26_archive_one_artifact_sweep_reviews.py --check",
        "```",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true", help="write nothing; exit 1 if the archive is missing a file, differs, or holds an extra one")
    args = parser.parse_args()
    out_dir = _REPO / OUT
    primary = primary_checkout()
    failures: list[str] = []
    want: dict[str, bytes] = {"README.md": render_readme().encode("utf-8")}
    for name, (src, pin, _what) in FILES.items():
        source = primary / src
        archived = out_dir / name
        if not source.is_file():
            ok = archived.is_file() and matches_pin(archived.read_bytes(), pin)
            print(f"{'PASS' if ok else 'FAIL'} {name}: source gone; archived copy {'matches' if ok else 'does not match'} its pin")
            if ok and args.check:
                want[name] = archived.read_bytes()
            else:
                failures.append(name)
            continue
        data = source.read_bytes()
        if sha(data) != pin:
            failures.append(name)
            print(f"FAIL {name}: the source hashes to {sha(data)}, not its pin {pin}")
            continue
        want[name] = copy_of(data)
    extra = sorted(p.name for p in out_dir.iterdir() if p.name not in want and p.name not in FILES) if out_dir.is_dir() else []
    if failures:
        print(f"refusing: {len(failures)} failure(s): {failures}")
        return 1
    pending = [name for name, data in want.items() if not (out_dir / name).is_file() or (out_dir / name).read_bytes() != data]
    if args.check:
        for name in sorted(want):
            print(f"{'FAIL' if name in pending else 'PASS'} {OUT}/{name}")
        for name in extra:
            print(f"FAIL {OUT}/{name}: a file the table does not name")
        return 1 if pending or extra else 0
    out_dir.mkdir(parents=True, exist_ok=True)
    for name in pending:
        (out_dir / name).write_bytes(want[name])
        print(f"wrote {OUT}/{name} (sha256 {sha(want[name])[:16]}…)")
    if not pending:
        print("nothing to write: the archive is current")
    for name in extra:
        print(f"NOTE {OUT}/{name}: a file the table does not name (left in place)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
