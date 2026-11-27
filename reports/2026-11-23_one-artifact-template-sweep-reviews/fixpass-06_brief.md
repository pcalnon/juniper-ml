# Fix pass 6 brief: the port checker, after round 7 (checker only)

Written 2026-11-24 (~03:00Z) by orchestrator session `ffffd3` (worktree `ethereal-munching-peacock`).
`W=/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/ethereal-munching-peacock`. Work from `$W`.

**If you are a new session picking this up:** check `grep -n '^## ' $W/tmp/sweep/REVIEW_DISPOSITIONS.md`. A
`## Fix pass 6` section means this pass finished: go to round 8 (`$W/tmp/sweep/ROUND8_BRIEF.md`). No such section,
and the live checker matches neither its line in `$W/tmp/arc/sweep_scripts.sha256` nor
`$W/tmp/sweep/checker-r7/checker_r6_as_reviewed.py`: it is a half-edit. Restore that saved copy (`6b2443c6…`), then run
this brief with a fresh executor.

## Goal

Fix round 7's findings in the cross-repo port checker `$W/util/ad-hoc/2026-11-23_publish_port_template_identity.py`
(now sha256 `6b2443c6d24ee7692e606d0b010526f113aaf0070d9b7a5dd35597dd94d11f85`, fix pass 5), re-run every checker
proof, and write the round-8 brief. The checker is our own CI tooling: it gates the ports of juniper-cascor's publish
template (cascor#777, `f5ed3017`) into seven repos, and its mutants are negative test cases that prove it refuses
unsafe workflow edits. Keep the interdiff SMALL; rounds 4-7 found each pass's newest code to be its weakest part.

Read first: `$W/tmp/sweep/REVIEW_DISPOSITIONS.md` § "Round-7 review" (your work list and the decision), round 7's report
`$W/tmp/r7review/ROUND7_REPORT.md` and evidence `$W/tmp/r7review/evidence/`, then § "Fix pass 5".

## Scope

- **R7-1 (MINOR)**: in `check_install_job`, refuse any command on which the checker's two readers (`lex` and the
  `shlex`-based `pip_calls`) disagree about its pip commands. Round 7 measured 0 disagreements across the template and
  the 15 simulations (259 install commands, 21 pip commands). `$W/tmp/sweep/checker-r6/shlex-probe/S1.yml` must FAIL.
  Also EXECUTE S1 and a variant of your own, as round 6 executed its mutants, to settle whether the gap could change an
  outcome; report either way.
- **R7-2, R7-3 (NIT)**: give the escaped-blank and last-line continuation rules true messages, or narrow them to the
  cases where bash and the checker really diverge. Each narrowing needs a FAIL case for the divergent form.
- **R7-4 (NIT)**: in `check_loop`, set redirections aside before comparing; add a FAIL case for a redirection that would
  change what the fetch does (e.g. one that sends the fetched file elsewhere).
- **R7-5 (NIT)**: correct the docstring's "compared as YAML text" to what `:1625-1644` does.

Out of scope: the writer, every workflow, cascor's tree, every port.

## Re-run (logs under `$W/tmp/sweep/checker-r7/evidence/`)

Copy fix pass 5's drivers from `$W/tmp/sweep/checker-r6/` into `$W/tmp/sweep/checker-r7/` and adapt the copies (never
edit fix pass 5's). Same template as fix pass 5. Then:
1. cascor's three publishers: 3/3 PASS, from the landing tree and from cascor `main`.
2. The 15 port simulations: 15 of 15 PASS.
3. Every earlier mutant set (round 6's R6, fix pass 5's N6, fix pass 4's N5, round 5's R5, round 4's M, round 2's, fix
   pass 3's N): the same verdicts as fix pass 5 recorded; the controls PASS. Build at least 4 new EXECUTED mutants
   aimed at your changes; each must FAIL, or PASS only if executing it changes nothing.
4. `checker_proof_r7.py`, a copy of r6's: earlier cases keep their verdicts unless you state why; add FAIL and PASS
   cases for each change. Round 2's 43 cases keep their verdicts.
5. pre-commit and B914 on the checker; `--help`.

## Outputs

- BEFORE editing: copy the checker to `$W/tmp/sweep/checker-r7/checker_r6_as_reviewed.py` and the manifest to
  `$W/tmp/arc/sweep_scripts.r7.sha256`. AFTER: `checker-r7/checker_r6_to_r7.diff`; regenerate the manifest over the
  same six paths (the writer's line stays `c47940ad…`).
- APPEND `## Fix pass 6 (round 7's checker fixes; checker-r7)` to the dispositions file, in the earlier sections' style.
- Write `$W/tmp/sweep/ROUND8_BRIEF.md`: ROUND7_BRIEF.md's structure, re-aimed at the r6 -> r7 interdiff AND at
  completing what round 7 could not (round 7's report lists it: new executed mutants for reader divergences, the
  executed two-readers question, re-executing earlier mutants), with the new hashes. It must say plainly that the
  mutants are negative test cases for our own CI checker (defensive testing of a gate we own). The reviewer writes its
  report to `$W/tmp/r8review/ROUND8_REPORT.md` as well as returning it, and if any step is interrupted, it reports
  exactly which steps were not done. The same stopping rule: no port until a COMPLETE round reports no BLOCKER and no
  MAJOR.

## Rules

Fix pass 5's rules hold unchanged (`$W/tmp/sweep/FIXPASS5_BRIEF.md` § Rules), with `checker-r7/` as your directory:
never write under `/tmp`; edit only the checker, new files under `checker-r7/`, the manifest, `ROUND8_BRIEF.md` and the
dispositions file (append); delete nothing; read-only `gh` GETs only; never push, commit, open, comment on, approve or
merge anything; no secrets or personal data; write script files rather than complex command lines; return to `$W`
after any `cd`.

## Report (your last message, under 400 words)

Per R7 id: what changed. The new sha256 and the interdiff's size. Counts for every re-run. Whether S1 can change an
outcome. Any mutant that still passes; any simulation that fails; deviations; the path of `ROUND8_BRIEF.md`.
