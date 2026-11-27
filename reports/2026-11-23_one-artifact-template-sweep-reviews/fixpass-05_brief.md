# Fix pass 5 brief: the port checker, after round 6 (checker only)

Written 2026-11-24 (~01:25Z) by orchestrator session `ffffd3` (worktree `ethereal-munching-peacock`).
`W=/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/ethereal-munching-peacock`. Work from `$W`.

## Goal

Close round 6's BLOCKER in the cross-repo port checker `$W/util/ad-hoc/2026-11-23_publish_port_template_identity.py`
(now sha256 `ebeb75562d61c43e071a77855a10c92841d5967addb2d4c60f9723f92e9207b8`, fix pass 4), re-run every checker proof,
and write the round-7 brief. The checker gates the ports of juniper-cascor's publish template (cascor#777 merged it,
`f5ed3017`) into seven repos. Make the interdiff SMALL: this pass must not reopen anything rounds 4-6 closed.

Read first: `$W/tmp/sweep/REVIEW_DISPOSITIONS.md` § "Round-6 review" (your work list), then round 6's full report
`$W/tmp/r6review/ROUND6_REPORT.md` and its mutants and probes in `$W/tmp/r6review/` (`r6_mutants_final.out`,
`verify_roundtrip.out`, `check_continuations.out`, `overstrict.out`), then § "Fix pass 4" (how the allow-list works).

## Scope

- **R6-F1 (BLOCKER)**: `commands()` joins a line continuation with a space where bash deletes `\<newline>`.
  - Refuse any continuation whose backslash is NOT preceded by whitespace (round 6 measured all 66 continuations in
    the template and the 15 ports: each has whitespace before `\`). If you can soundly also reconcile the two joins
    (bash's: delete `\<newline>`, keep the next line's leading whitespace; the checker's: strip + one space) and refuse
    when they tokenize differently, do both; the whitespace rule alone is acceptable.
  - Refuse a NUL byte anywhere in a run script (and say why: bash drops it).
  - Check the same divergence everywhere text is joined or split before judging: `$(…)` bodies, heredoc-free echoes,
    the retry loop, the build window's allow-list, and any other place a continuation or a NUL could change what bash
    runs. Name in the docstring every place you checked.
  - Correct the docstring's claims (`:83`, `:114` in the reviewed file) and add the shell-lexing divergence to "What
    this cannot see" for anything you do not close.
  - R6-1..R6-6 must FAIL (`$W/tmp/r6review/`; read how round 6 built and executed them).
- **R6-N1 (NIT)**: either admit a trailing unquoted `# comment` outside `$( )` (with PASS and FAIL proof cases: a `#`
  inside quotes, inside `$(…)`, and after a continuation must not change the verdict) or leave it and document it.
- **R6-N2 (NIT)**: leave `${NAME##…}` / `${NAME%…}` refused unless admitting them is trivially sound; document either way.

Out of scope: the writer, every workflow, cascor's tree, every port.

## Re-run (logs under `$W/tmp/sweep/checker-r6/evidence/`)

Copy fix pass 4's drivers from `$W/tmp/sweep/checker-r5/` (`rerun_all.bash`, `run_*.bash`, `port_sim_table_r5.py`,
`judge_mutants_r5.py`, `checker_proof_r5.py`) into `$W/tmp/sweep/checker-r6/` and adapt the copies; never edit fix
pass 4's. The template: `$W/tmp/sweep/cascor-r4/main/juniper-cascor/.github/workflows/publish.yml` (its workflows equal
cascor `main`'s after #777; confirm with a read-only fetch of cascor `main`'s three publishers through
`$W/util/ad-hoc/2026-11-15_fetch_pr_files.py`, and say if they differ).
1. cascor's three workflows: PASS (`--repo juniper-cascor`), from the r4 tree AND from the fetched `main` copies.
2. The 15 port simulations: 15 of 15 PASS.
3. Every mutant: R6-1..R6-6, fix pass 4's N5-1..N5-16, round 5's R5-1..R5-18, round 4's M1..M15, round 2's 7, fix pass
   3's N1..N14: each FAILS; the controls PASS. Then build at least 6 NEW executed mutants aimed at YOUR changes (a
   continuation preceded by a tab, by `\\`, inside single quotes, inside `$(…)`, at end of file, a CRLF line end,
   a NUL inside quotes, a comment that hides a continuation); execute each as round 6 did; each must FAIL, or PASS
   only if executing it changes nothing (then say so).
4. `checker_proof_r6.py` (a copy of r5's): every earlier case keeps its verdict unless you state why; add FAIL and PASS
   cases for each change. All pass. Round 2's 43 cases keep their verdicts.
5. pre-commit and B914 on the checker (juniper-ml's config), `--help`.

## Outputs

- BEFORE editing: copy the checker to `$W/tmp/sweep/checker-r6/checker_r5_as_reviewed.py` (sha256 `ebeb7556…`) and
  `$W/tmp/arc/sweep_scripts.sha256` to `$W/tmp/arc/sweep_scripts.r6.sha256`. AFTER: `checker-r6/checker_r5_to_r6.diff`,
  and regenerate `$W/tmp/arc/sweep_scripts.sha256` over the same six paths (`sha256sum -c` passes; the writer's line
  stays `c47940ad…`).
- APPEND `## Fix pass 5 (round 6's checker fixes; checker-r6)` to `$W/tmp/sweep/REVIEW_DISPOSITIONS.md` in the earlier
  sections' style: the new sha256, the interdiff's size, what was applied per R6 id, every rule added, the counts,
  residual risks. Append only.
- Write `$W/tmp/sweep/ROUND7_BRIEF.md`: ROUND6_BRIEF.md's structure, re-aimed at the r5 -> r6 interdiff, the new hashes
  filled in, the same stopping rule, at least 8 new EXECUTED bypass mutants aimed at line joining, NUL and comment
  handling, a re-check of all 15 simulations, AND this instruction: the reviewer writes its full report to
  `$W/tmp/r7review/ROUND7_REPORT.md` as well as returning it (the orchestrating session may hand off before the
  report arrives; the file is what the next session reads).

## Rules

- Never write under `/tmp` or `/var/tmp`; everything new goes under `$W/tmp/sweep/checker-r6/` except the outputs above.
- Edit only the checker, new files under `checker-r6/`, the manifest, `ROUND7_BRIEF.md` and the dispositions file
  (append). Everything else under `$W/tmp/` and `$W/util/` is READ-ONLY; delete nothing.
- Read-only `gh` GETs only. Never push, commit, open, comment on, approve or merge anything.
- The Bash guard refuses `git -C`, `cd` into another worktree combined with git, some heredocs, and some command lines
  that name `.github` paths: write small script files under `checker-r6/` and run those. A `cd` in one Bash call
  persists into the next: return to `$W` afterwards.
- Run Python that reads cloned trees with `python3 -I`. Take times from `date -u`; never estimate one.
- No secrets, tokens, e-mail addresses or personal data in any output.

## Report (your last message, under 500 words)

Per R6 id: what changed. The new checker sha256 and the interdiff's size. Counts for every re-run. Any mutant that still
passes; any simulation that fails; every deviation from this brief; residual risks; the path of `ROUND7_BRIEF.md`.
