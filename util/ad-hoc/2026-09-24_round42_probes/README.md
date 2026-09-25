# Defect-register round 42 — the validators' probe scripts

Round 42 of the defect-register arc validated six merged PRs after the fact: juniper-data#428,
juniper-canopy#660 and #678, juniper-cascor#678, and juniper-ml#2032 and #2059. It also validated the
API primer's artifact-validator correction (two rounds) and its own register PR, juniper-ml#2074. Each validation lane ran in a session scratchpad under
`/tmp`, which is tmpfs and is lost when the session or machine goes. The lanes' reports, archived
verbatim in `reports/2026-09-24_defect-register-round-42/`, cite these scripts by those scratch paths.
This directory keeps the Python probes so a reader can re-run a measurement a report relies on.

These are **evidence, not tools.** They are copied as the lanes wrote them, apart from the end-of-file
newline the repo's pre-commit hook adds. Paths inside them still point at scratch directories that no
longer exist, and many expect an extracted tree or a running service beside them. The lanes' shell
runners and their extracted repository trees are not kept: the runners are environment-specific
wrappers that do not pass the repo's shellcheck hook, and the trees are copies of code already in git.

| Directory | Lane | Report |
|---|---|---|
| `data428-round2-v428r2/` | juniper-data#428, round 2 (predecessor session) | `data428-round2-validation.md` |
| `data428-fix-d428fix/` | juniper-data#428, the round-2 fix agent's regex-equivalence check | `data428-round2-fix-report.md` |
| `cascor678-postmerge-v678/` | juniper-cascor#678, post-merge (predecessor session) | `cascor678-postmerge-validation.md` |
| `canopy678-postmerge-v678c/` | juniper-canopy#678, post-merge (predecessor session) | `canopy678-postmerge-validation.md` |
| `round3-4_data428-laneA1/` | juniper-data#428, round 3, security | `data428-round3-laneA1-security.md` |
| `round3-4_data428-laneA2/` | juniper-data#428, round 3, claims | `data428-round3-laneA2-claims.md` |
| `round3-4_data428-laneB/` | juniper-data#428, round 3, refutation | `data428-round3-laneB-refute.md` |
| `round3-4_ml-laneA/` | juniper-ml#2032 round 4 + #2059, re-probe | `ml2032-2059-round4-laneA-reprobe.md` |
| `round3-4_ml-laneB/` | juniper-ml#2032 round 4 + #2059, refutation | `ml2032-2059-round4-laneB-refute.md` |
| `round3-4_primer-laneA/` | the API primer correction, round 1, re-probe | `primer-correction-round1-laneA-reprobe.md` |
| `round3-4_primer-laneB/` | the API primer correction, round 1, refutation | `primer-correction-round1-laneB-refute.md` |
| `ml2074-round1-laneA/` | juniper-ml#2074 (this round's register PR), post-merge, re-derivation | `ml2074-round1-laneA-reprobe.md` |
| `ml2074-round1-laneB/` | juniper-ml#2074, post-merge, refutation | `ml2074-round1-laneB-refute.md` |
| `primer-correction-round2-laneA/` | the API primer correction v2 (juniper-ml#2075), round 2, re-derivation | `primer-correction-round2-laneA-reprobe.md` |
| `primer-correction-round2-laneB/` | the API primer correction v2, round 2, refutation | `primer-correction-round2-laneB-refute.md` |
| `register-fixforward2-round1-laneA/` | the second register and primer fix-forward (juniper-ml#2088), pre-PR round 1, re-derivation | `register-fixforward2-round1-laneA-reprobe.md` |
| `register-fixforward2-round1-laneB/` | the same, pre-PR round 1, refutation | `register-fixforward2-round1-laneB-refute.md` |
| `register-fixforward2-round2-laneA/` | the same, pre-PR round 2, re-derivation | `register-fixforward2-round2-laneA-reprobe.md` |
| `register-fixforward2-round2-laneB/` | the same, pre-PR round 2, refutation | `register-fixforward2-round2-laneB-refute.md` |
| `data438-fixforward-round1-laneA/` | juniper-data#438's fix-forward (branch `fix/conditional-requests-round4-followups`), pre-PR round 1, re-derivation | `data438-fixforward-round1-laneA-reprobe.md` |
| `data438-fixforward-round1-laneB/` | the same, pre-PR round 1, refutation | `data438-fixforward-round1-laneB-refute.md` |
| `cascor686-v686/` | juniper-cascor#686 (superseded by #688), follow-up lane | `cascor686-validation.md` |
| `canopy683-v683/` | juniper-canopy#683, follow-up lane | `canopy683-validation.md` |
| `cascor688-v688/` | juniper-cascor#688, follow-up lane | `cascor688-validation.md` |
| `bytes-compare-ml2086-data440-cascor689-vbytes/` | juniper-ml#2086, juniper-data#440 and juniper-cascor#689, follow-up lane | `bytes-compare-ml2086-data440-cascor689-validation.md` |

The `round3-4_*`, `ml2074-*` and `primer-correction-round2-*` directories were filled by
`util/ad-hoc/2026-09-24_copy_round42_probe_scripts.py`.
The four predecessor-session directories were copied by hand, from that session's scratchpad
(`bc31e993`), when round 42 was picked up in session `8f86dec2`.
The `register-fixforward2-*` and `data438-fixforward-*` directories hold the lanes of session `2fba4397`,
which took the round over from `8f86dec2`. They were filled by
`util/ad-hoc/2026-09-24_copy_round42_session2fba4397_probe_scripts.py`, by the same rules.
Their reports also name shell runners (`*.bash`, `*.sh`), which are not kept.

The four follow-up-lane directories (`cascor686-v686/`, `canopy683-v683/`, `cascor688-v688/`
and `bytes-compare-…-vbytes/`) come from the same `bc31e993` scratchpad, where that session went on
to run the round's cascor and canopy follow-ups. They were filled by
`util/ad-hoc/2026-09-24_copy_followup_lane_probe_scripts.py`, which also leaves out four
whole-file copies of repository code the lanes kept beside their probes.
