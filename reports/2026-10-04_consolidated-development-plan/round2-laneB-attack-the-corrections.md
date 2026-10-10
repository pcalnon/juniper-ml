# Round 2 — Lane B (attack the corrections)

<!-- markdownlint-disable -->

> **Archived verbatim.** A round-2 validation lane report for `notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md`. Its findings are dispositioned in `round2-reconciliation.md` in this directory. Only this header was added; line numbers that other reports cite in this file refer to the text without it, so add 4.

- Instrument:
  - **Read in full**:
    - `notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md` v1.1.0, sha256 `b81c6afaa8580c0b`, verified. "Lnnn" is one of its lines;
    - the v1.0→v1.1 diff;
    - `round1-reconciliation.md` and the seven `round1-lane*.md`.
  - **Re-read where cited**: the named scripts; `…RECOVERY-PLAN.md` §6.3; `…INTEGRATED-DESIGN.md`; the P8 and INDEX handoffs; `extraction-*.md`; and the memory files, read-only.
  - **REST**:
    - three PRs;
    - repo visibility;
    - seven `.gitleaks.toml` files;
    - gitleaks-action at `e0c47f4f`.
  - **Host**: `findmnt`.
  - No scripts or tests were run. The only other writes are scratchpad copies of gitleaks-action's source.
- Entry point: the round-1 corrections (diff + reconciliation)

## Findings

| ID | Severity | Plan location (v1.1) | What the correction says | What it broke (evidence: section/line pairs) | Proposed correction |
| --- | --- | --- | --- | --- | --- |
| R2B-01 | BLOCKER | XC-PRESERVE, L217 | "Before any push, screen with `util/ad-hoc/2026-09-24_secret_shape_check.py`" (A1-05) | **Not a screen.** It tests four tools' regexes "against constructed FAKE values". `main()` reads no argv or file, and it has no `PASSPHRASE=` case, B2-01's B9 class in row a. The reconciler checked only that it exists (`ls`). Any content passes, restoring round 1's BLOCKER | Strike it. Until XC-LEAKS lands, run a local gitleaks scan with defaults + B9 before **every** public push, P1-09 and P1-10 included |
| R2B-02 | MAJOR | L213 | "Never push … rows a, b, g, i, j, k and l" to a public repository (B2-01) | Rows a and b are what P1-10 (the Phase B PR) and P1-09 ("archive Phase B reports verbatim into a `notes/` round record", `extraction-P1-backup.md`) push to juniper-ml. Row k exists because `…INTEGRATED-DESIGN.md` release limit 2 requires a "record merged to `main`" (A1-03). Taken literally, this bars P1-09 → P1-10 → STOP → Phase D | Limit the rule to preservation copies; a, b and k reach `main` via P1-09/P1-10, behind R2B-01's scan |
| R2B-03 | MAJOR | §9 L697 vs §3 L217 | Repository-destined preservation depends on XC-LEAKS, "Hard for any push" | §3 lets rows c and d push before XC-LEAKS; §9 forbids it. Under §9:<ul><li>row c is P5-09's PR, ordered before R-DATA (L659), so R-DATA, R-ML-a and P12 M1 wait on data's XC-LEAKS;</li><li>row d is P7-01, the head of the P7 lane;</li><li>row q is this plan's own PR.</li></ul>The B9-bearing P1-09/P1-10 have no such edge (L686) | Gate pushes on a rules-bearing local scan, not on XC-LEAKS landing |
| R2B-04 | MAJOR | S0.8, L375 | Scratch ports and `JUNIPER_E2E_RUN_DIR`; `--dry-run` first (B2-05) | The deletion it names (`isolated_stack.bash:530`) derives from `JUNIPER_E2E_PROJECT_DIR` (:74, :78), not RUN_DIR. A worktree session that points it at the ecosystem root so `--up` works — H-15's pattern — deletes the primary checkout's snapshots | Also set `JUNIPER_E2E_PROJECT_DIR` to scratch; read the dry run's `rm` path |
| R2B-05 | MAJOR | L55; H-18, L799 | "juniper-ml, juniper-data and juniper-canopy are public" | REST: **all nine** are public. Under "never push to a public repository", row i (equities evidence) could go to juniper-recurrence | "All nine are public" |
| R2B-06 | MAJOR | XC-LEAKS, L229–L231 | "land each on a branch first and watch the required `Security Scan` check. Expect the check to go red … baseline" | **CI mechanics:**<ul><li>`ci.yml` runs no CI on branch pushes. A check needs a PR (which the sweeper arms) or a dispatch.</li><li>gitleaks-action v3.0.0 scans only a PR's commits (`base^..head`); only `workflow_dispatch` scans history.</li></ul>**So:**<ul><li>The PR goes green, and no PR goes red from history.</li><li>The rule-less history is never scanned, and "expect red" reads as "clean".</li><li>No one rules on a real hit.</li></ul> | Run a one-off local full-history scan per public repo. A real hit goes to the owner to rotate; a baseline needs the owner's ruling |
| R2B-07 | MAJOR | L10; L64; XC-P12 L295/L311; S0.3; A1; XC-FLEET vs §12 L812 | Snapshot "validation probes … 21:27Z–22:00Z" | REST:<ul><li>ml#2130 merged at 21:41:44Z.</li><li>ml#2134 (the ml#2115 fix-forward, two lanes) merged at 21:56:09Z. Its body: it supersedes #2129, falsifies green #2119/#2128, and needs `--backup-id 2` redeployed.</li></ul>v1.1, written at 22:01Z, still calls #2130 "armed", dispatches S0.3, and defers fleet dispositions while §12 claims "Wave 0". The last PR probe is A4's, at 21:40Z | Re-probe. Close S0.3 and P1-03; make #2130's review post-merge; add the redeploy and the fleet dispositions to Wave 0 |
| R2B-08 | MAJOR | Wave 0 sitting L348–L357 vs A1 L521 | Source order restored (A5-13); Group A rulings come sixth | **The rulings:** A1 says "rule these first", and B1-05 was accepted as "first in the sitting". They now follow Phase C and step 8's hours-long runs (L640).<br>**The source:** "In this order" binds only `…RECOVERY-PLAN.md` §6.3 steps 1–9.<br>**O-10:** step 9 needs O-10 ruled, yet the sitting rules O-10 at item 6, after item 3.<br>**A5-13:** asked only for a stated reason | P12 rulings and O-10 first, then steps 1–9 in order |
| R2B-09 | MAJOR | §1.3 L156; §7.1 L607; L359 | "One arc mid-round at a time, at most three agents at once account-wide … A safety round may preempt" | **Source:** "Soft", a launch condition (INDEX L60).<br>**Already exceeded:** by the live P1, P12 and planning sessions; `Juniper/AGENTS.md` expects seven to eight. Wave 0's ten "parallel lanes" cannot start.<br>**"Preempt":** undefined; it covers ≥5 of §7.1's first seven rounds.<br>**Two weeks:** not re-derived. Six serial rounds gate the exit, and P3-09 has no slot.<br>**L156:** misquotes the P8 handoff L158 | Owner picks the rule. Define preemption, add P3-09, show the arithmetic |
| R2B-10 | MAJOR | XC-MEM L275–L281; H-11 | "24,993–25,251 characters … warns at 24.4 KB"; net-zero; gate fix first (A3-F7) | The plan's own source (`feedback_memory_index_target_is_20kb.md`) sets the load ceiling at ~25,000 **characters** and drops later lines. By its own figure the index was over. It is now 25,695 (22:16Z), so lines 87–89, three P12 hooks, are dropped. Net-zero keeps them out, and A3-F7 delays compaction | Say "over". Index edits stay net-negative until under 25,000 |
| R2B-11 | MAJOR | §9 L682; L395; L483; L502; XC-SENTRY L235; L122 | Lock-PR edge (B1-02); interim chain (B1-01); cap-PR step dropped | **Three rules:** §9 says "Hard"; data says "if R-OBS-SC is out"; canopy gets an option.<br>**Images only:** wheels resolve the patch within the caps (L483).<br>**The trio:** runs from conda envs (`extraction-P2-canopy.md` O13). Its path, env upgrade then restart, is unscheduled, so L122 has no driver.<br>**The caps:** "patch bumps" presumes D-02's "owner-named versions" | Scope the edge to images. Add the env upgrade; keep "cap PRs if D-02 names a minor" |
| R2B-12 | MINOR | App. A; §6 | Re-tiering | <ul><li>P7-18 is in Wave 2 (L435) but T5 (L893).</li><li>P5-09's T0 "harvest" (L876) has no T0 action left (L214).</li><li>"Done or in flight" (L910) is not a tier.</li><li>The mid-wave "D-12" (L534) lacks a prefix, and collides with P4's D-12.</li><li>W0.4 = P6-08 is both in flight and in Wave 4.</li><li>R-ML-a (Wave 1) needs P4 D-1, which is in Group B (L551).</li><li>"Plus eight" (L990) does not match L85</li></ul> | Align; move D-1 to the mid-wave sitting |
| R2B-13 | MINOR | L228; App. A L842 | P1-11 "moved here" | P1-11's pre-commit hook and its owner-only `secret_scanning_non_provider_patterns` (`extraction-P1-backup.md`) were dropped. The reconciliation says B2-13's owner marker was applied at L842; it is absent, and the setting is in no §6 group | Restore both; put the setting in A3 |
| R2B-14 | MINOR | L59; L353 | Tier 2 "protects none" of the rows | `juniper-backup.bash:202` leaves `--exclude-vcs` commented out, and the excludes are `<repo>/<dir>` (:348), so `.git` is archived. Row f's commits and row a's branch are inside Tier 2. Rows c, h and m fall outside the ten repos for a reason other than :142 | Name the rows and the reasons |
| R2B-15 | MINOR | Throughout | B2-16 applied "throughout" | **New bare references:**<ul><li>the lanes (L55, L210, L235, L710);</li><li>"the P12 plan" (L64), "that design's" (L757), "design §9.6.6" (L881);</li><li>"the CLI plan's" (L913), "§11.1" (L914), "the source rule" (L992).</li></ul>**Still unfixed:** "the register" (L126, L748), "Ledger item i13" (L723), "The spec's" (L740), "the handoff" (L746) | Add the filenames |
| R2B-16 | MINOR | Validation record L970–L992 | "Every finding was accepted, two in part"; "each rested on a single lane" | **Reversed:** A1-03 (R2B-02), B1-05 (R2B-08), B2-13 (R2B-13).<br>**Contradicted:** B1-14 put rows j–l after XC-CRED, though B2 found no token-shaped string in row j.<br>**Not single-lane:** three of the re-derived claims.<br>**Instruments:** `leak_rule_probe.py` and `id_coverage.py` are in `/tmp`, against `AGENTS.md` § Script placement, and unlisted | Record what was applied; copy rows j and l now; move the scripts to `util/ad-hoc/` |
| R2B-17 | NIT | H-16 L797; L476; L124 | — | S-7a (`…INTEGRATED-DESIGN.md` L499) protects the worktree "for unrelated reasons", so H-16's stated reason lapses at step 3. "Never approve a `pypi` gate" follows a sentence whose subject is the owner. juniper-deploy is not on PyPI | Reword |

## Corrections checked and sound (short)

- **XC-LEAKS shape.** juniper-data, juniper-canopy and juniper-deploy have no `[extend]`, `useDefault` or `[[rules]]` (REST), so this can say "measured". The other repos extend the defaults or have no config.
- **The durable target.** "Prefer the nvme root `/`" holds: `/` is `nvme0n1p5`, and `/home` is `sdc3`.
- **References and counts.** Every short form resolves to exactly one file. The lane counts (94) and the 375 IDs check.
- **H-15 and placements.** H-15's variables exist. O-2, O-7, O-8 and O-12 sit in A2, and O3 gates R-CANOPY-A.

## Could not check

- **Host**: the sticks, the timer, and the trio's environments and DSNs.
- **Transcripts**: rows k and l; I opened none.
- **Round 2's own concurrency.**
- **CI's gitleaks 8.24.3** with a rule-less config. Not run.
- **The W0.3–W0.5 PRs** after 22:00Z.

## What this report cannot support

- **Severities** are judgement. R2B-01 assumes, as round 1 did, that row a's B9 matches are real values.
- **Drift.** R2B-07 and R2B-10 rest on drift. They refute the "probes to 22:00Z" claim and the net-zero rule, not the author's diligence.
- **Coverage.** I read sources only where a correction touched them.

**Changed**: this file only, `reports/2026-10-04_consolidated-development-plan/round2-laneB-attack-the-corrections.md`.
