# Fix pass 4 brief: the port checker, after round 5 (checker only)

Written 2026-11-23 (~23:45Z) by orchestrator session `ffffd3` (worktree `ethereal-munching-peacock`).
`W=/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/ethereal-munching-peacock`. Work from `$W`.

## Goal

Fix the cross-repo port checker `$W/util/ad-hoc/2026-11-23_publish_port_template_identity.py` (now sha256
`c826ab875ecb5d6ad95891e341fb3b27020cfddf25d0161a4a44e04c74f88236`) for round 5's checker findings, and re-run every
checker proof, so that a round-6 reviewer can review ONLY the checker's interdiff. The checker gates the ports of
juniper-cascor's publish template into seven repos; it is NOT part of the cascor PR, which lands separately and in
parallel (do not touch anything under `$W/tmp/sweep/land/`).

Read first, in full: `$W/tmp/sweep/REVIEW_DISPOSITIONS.md` § "Round-5 review" (your work list: R5-F1, R5-F2, R5-F3,
R5-F4, R5-F7), then § "Fix pass 3" (what the checker claims and why), then round 5's evidence in `$W/tmp/r5review/`
(mutant builders `s4_new_mutants*.py`, outputs `s4_*.out`, `bash_semantics_probe.*`, `overstrict/`). The round-5
reviewer's full report is summarised in that § and in this brief; the mutants are on disk.

## Scope

- **R5-F1 (MAJOR)**: the plain-echo relaxation. An echo is plain only if, once simple `$NAME`/`${NAME}` references are
  removed, it holds no `$`, no backtick and no unquoted `{ } [ ] * ?`. Every echo in the 15 port simulations must still
  qualify. R5-1, R5-2 and R5-11 become FAIL cases beside EPa-EPd. Correct the docstring's claims (`:89-96` in the
  reviewed file).
- **R5-F2**: R4-3's class. PREFER the positive allow-list round 5 proposed: command names read after quote removal and
  with no glob or brace characters, from a fixed set (`cd`, `set`, `sleep`, `echo`, `pip`/`pip3`, `python`/`python3`,
  `ls`, `[`, `break`, `exit 1`, `for`/`do`/`done`/`if`/`then`/`fi`/`else`/`elif` as the 15 ports need them, plus
  `grep`/`head`/`sed`/`mktemp` inside `$(…)` only, and anything else a FAITHFUL port among the 15 needs: derive the set
  from the 15 simulations and the template, never from a mutant). Refuse `[[`, `((`/`$((`, `let`, `declare`/`local`,
  `mapfile`/`readarray`, `printf -v`, `${…@…}`, `${!…}`; run the pip scan on the body of every `$(…)` after quote
  removal. If you keep any deny-list part, list every form round 5 used under "What this cannot see" instead of
  claiming the class closed. R5-3, R5-4, R5-8, R5-9, R5-14, R5-15, R5-16, R5-17, R5-18 must FAIL.
- **R5-F3**: run the exit/trap/`set +`/`PIP_*`/`UV_*`/`PATH`/`PYTHON*`/`GITHUB_ENV`/`pip.conf` rules on quote-removed
  words and every `$(…)` body; a command named `exit` only as `exit 1`; refuse `trap`; refuse `set` with a `+…`
  argument. R5-5, R5-6, R5-7, R5-10, R5-12 must FAIL.
- **R5-F4**: refuse `BASH_ENV`, `ENV`, `BASHOPTS` and `SHELLOPTS` as env keys at every level (workflow, job, step).
  R5-13 must FAIL.
- **R5-F7 (NIT)**: drop redirections from both sides before comparing a runtime install line (O1), and admit a
  standalone `[ … ]` test or reword the message and docstring to "an if's [ ] test" (O2). Round 5's O1 and O2 edits
  (`$W/tmp/r5review/overstrict/`, `s4_overstrict.out`) must then PASS, or carry a true reason.
- Any rule you add beyond these: name it in the docstring and give it a negative and a positive case.

Out of scope: the writer, cascor's tree, every workflow file, R5-F5 (a juniper-ml port item), R5-F6 and R5-F8 (texts).

## Re-run (logs under `$W/tmp/sweep/checker-r5/evidence/`)

The template for every run: `$W/tmp/sweep/cascor-r4/main/juniper-cascor/.github/workflows/publish.yml` (unchanged
since fix pass 3: the landing tree differs only in `CHANGELOG.md`). Every checker call takes `--repo`.
1. cascor's three workflows from that tree: PASS (`--repo juniper-cascor`).
2. The 15 port simulations (`$W/tmp/sweep/cascor-r4/port-sim/` and its driver `run_port_sim.bash` /
   `port_sim_table_r4.py`; copy and adapt into `$W/tmp/sweep/checker-r5/`): 15 of 15 PASS. A faithful simulation that
   fails means the checker is over-strict: fix the checker.
3. Mutants: round 5's R5-1..R5-18 (`$W/tmp/r5review/mutants-r5*`), round 4's M1-M15 (`$W/tmp/r4review/mutants/`), round
   2's 7 (`$W/tmp/r2review/neg/`), fix pass 3's 14 (`$W/tmp/sweep/cascor-r4/mutants-new/`): every one FAILS; the
   controls (T0, P0, ML0 and the repo-scoping controls) PASS. Then build at least 6 NEW mutants aimed at your own
   changes (the allow-list's edges, quote removal, `$(…)` body scanning, the env keys) and EXECUTE each install script
   the way round 5 did (stand-in pip/python/sleep, `bash -e`) so each is shown to change the outcome; each must FAIL.
4. The checker proof: copy `$W/tmp/sweep/cascor-r4/checker_proof_r4.py` to `checker-r5/checker_proof_r5.py`; every
   earlier case keeps its verdict unless you state why; add a FAIL case per R5 mutant class and a PASS case per
   relaxation or allow-list entry. All pass.
5. Round 2's 43 negative cases keep their verdicts.
6. pre-commit and B914 on the checker under juniper-ml's own config (as fix pass 3 did); `python3 -I <checker> --help`.

## Outputs

- `$W/tmp/sweep/checker-r5/checker_r4_to_r5.diff` (from `$W/tmp/sweep/cascor-r4/checker_r4_as_reviewed.py`, which
  already holds the reviewed copy; do not overwrite it).
- BEFORE regenerating the manifest, copy `$W/tmp/arc/sweep_scripts.sha256` to `$W/tmp/arc/sweep_scripts.r5nit.sha256`.
  AFTER, regenerate `$W/tmp/arc/sweep_scripts.sha256` over the same six paths; `sha256sum -c` must pass. (The writer's
  line there must stay `c47940ad…`: you do not touch the writer.)
- APPEND `## Fix pass 4 (round 5's checker fixes; checker-r5)` to `$W/tmp/sweep/REVIEW_DISPOSITIONS.md`, in the earlier
  sections' style: the checker's new sha256, the interdiff, what was applied per R5 id, every rule added or relaxed
  (named), the proof counts, and residual risks (what the checker still cannot see). Append only.
- Write `$W/tmp/sweep/ROUND6_BRIEF.md` for ONE fresh reviewer: copy `$W/tmp/sweep/ROUND5_BRIEF.md`'s structure, re-aimed
  at the CHECKER's r4->r5 interdiff only (no cascor tree, no writer), with the new hashes filled in, the same stopping
  rule, and a step that builds at least 8 new executed bypass mutants and re-checks all 15 port simulations.

## Rules

- Never write under `/tmp` or `/var/tmp`. Everything new goes under `$W/tmp/sweep/checker-r5/` except the outputs named
  above.
- Edit only the checker, new files under `checker-r5/`, the manifest, `ROUND6_BRIEF.md` and the dispositions file
  (append). Everything else under `$W/tmp/` and `$W/util/` is READ-ONLY; delete nothing.
- Read-only `gh` GETs only. Never push, commit, open, comment on, approve or merge anything.
- The Bash guard refuses `git -C`, `cd` into another worktree combined with git, and some heredocs (a command line that
  names `.github` paths can trip it too): write small script files under `checker-r5/` and run those.
- Run Python that reads cloned trees with `python3 -I`. Take times from `date -u`; never estimate one.
- No secrets, tokens, e-mail addresses or personal data in any output. Several sibling worktrees had files rewritten by
  an unrelated blind "owner -> Overtoad" substitution: use only files inside `$W`.

## Report (your last message, under 600 words)

Per R5 id: what changed. The new checker sha256 and the interdiff's size. Counts for every re-run. Any mutant that still
passes; any faithful simulation that fails; every deviation from this brief; residual risks; the path of
`ROUND6_BRIEF.md`.
