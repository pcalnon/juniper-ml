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

The `round3-4_*`, `ml2074-*` and `primer-correction-round2-*` directories were filled by
`util/ad-hoc/2026-09-24_copy_round42_probe_scripts.py`.
The four predecessor-session directories were copied by hand, from that session's scratchpad
(`bc31e993`), when round 42 was picked up in session `8f86dec2`.
