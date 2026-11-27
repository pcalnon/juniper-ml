# Fix pass 11 brief: round 12's MINORs and NITs (no further review round)

Written 2026-11-25 (~02:05Z) by orchestrator session `ffffd3` (worktree `ethereal-munching-peacock`).
`W=/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/ethereal-munching-peacock`. Work from `$W`.

**If you are a new session picking this up**, run `grep -n '^## ' $W/tmp/sweep/REVIEW_DISPOSITIONS.md`.
- A `## Fix pass 11` section means this pass has finished: the checker is final, and the ports may start.
- If there is no such section, compare the live checker with its line in `$W/tmp/arc/sweep_scripts.sha256` and with
  `$W/tmp/sweep/checker-r12/checker_r11_as_reviewed.py` (`b807d3ca…`). If it matches neither, it is a half-edit:
  restore that copy, then run this brief with a fresh executor.

## Goal

Round 12 was the first complete round with no BLOCKER and no MAJOR, so the stopping rule clears the ports. See
§ "Round-12 review" of `$W/tmp/sweep/REVIEW_DISPOSITIONS.md`, including the orchestrator's decision on M12-C. Under the
same rule, the MINOR and NIT findings are fixed without another review round.

Fix them in the port checker `$W/util/ad-hoc/2026-11-23_publish_port_template_identity.py` (sha256
`b807d3ca9c45f14ba3a5771c562fecb5df5f82dc905fb294b88c5622628ea92d`, fix pass 10). Because no reviewer follows, prove
every change yourself: re-run every proof, and give each change a FAIL and a PASS case. Keep the change SMALL and
conservative. This pass must not weaken anything rounds 4-12 established.

Read first:
- the work list: § "Round-12 review";
- round 12's report, `$W/tmp/r12review/ROUND12_REPORT.md`, and its tools: `tools/m12_*.py`, `render_wrap_r12.bash`;
- § "Fix pass 10".

## Scope

- **M12-A:**
  - Before reading a workflow or a called file, refuse anything that is not a regular file. Use `lstat`, or `O_NOFOLLOW
    | O_NONBLOCK` plus an `fstat` `S_ISREG` check.
  - Decide whether a symlink to a regular file stays admitted. Round 12's C12-1 shows the checker follows one today.
    Say what you chose, and why.
  - Read the called file through `read_text`'s size bound.
  - Correct the claims at the old `:291-294` and `:244-250`.
  - Guard `--pins` and `--template` the same way.
  - N12-1b, N12-2b and N12-3 must end at once with FAIL, and the next workflow must still be judged.
- **M12-B:**
  - State the residual truly: only literal spellings are stopped, and only pinning the steps before the build closes
    the class.
  - Optionally refuse `github['env']`, `github['path']` and the `_runner_file_c` prefix. If you do, all 37 files round
    11 listed must still pass.
- **M12-C:**
  - Route every workflow-derived value the checker prints through `shown()` (the cut), and collapse runs of blanks in
    shown values. Alternatively, hard-wrap every printed line at 72-80 columns with indented continuation lines.
  - Re-render N12-5b in tmux at 80x50 and 200x50, as round 12 did. No fake PASS row or summary row may appear.
  - Restate the residual for narrower terminals, if one remains.
- **n12-a to n12-g:**
  - keep a place's tail or index when cutting;
  - reword the concurrency-group claim;
  - optionally refuse a duplicate step id;
  - make `seen` a set;
  - give the size refusal its own message prefix;
  - record `timeout-minutes` values as unread (fail-closed);
  - record the brief's path slip.

Out of scope: the writer, every workflow, cascor's tree, every port and the pins file.

## Re-run (logs under `$W/tmp/sweep/checker-r12/evidence/`)

Copy fix pass 10's drivers from `$W/tmp/sweep/checker-r11/` into `$W/tmp/sweep/checker-r12/` and adapt the copies. Copy
round 12's tools rather than running them in place.

1. cascor's three: 3/3 PASS, from the landing tree and from cascor `main`. Fetch `main` again: it is now
   `5e3d9801` or later.
2. The 15 simulations: 15/15 PASS, with juniper-data's called file. The 18 pins must re-derive equal.
3. Mutants:
   - Round 12's N12-* and every earlier set: no verdict may move, except as you state. Every bypass FAILS, and every
     control PASSES.
   - Build at least 4 new negative tests aimed at your changes, executed where execution applies. For example: a FIFO,
     a symlink loop, a socket path, and a long value placed at a wrap offset.
4. `checker_proof_r12.py`, a copy of r11's: all pass.
5. The YAML fuzz and the typing differential.
6. pre-commit and B914 on the checker, and `--help`.

## Outputs

- **Before editing:** copy the checker to `checker-r12/checker_r11_as_reviewed.py` and the manifest to
  `$W/tmp/arc/sweep_scripts.r12.sha256`.
- **After:** write the interdiff, and regenerate the manifest over its seven paths. The writer's line stays
  `c47940ad…`.
- **Append** `## Fix pass 11 (round 12's MINORs and NITs; checker-r12; FINAL for the ports)` to the dispositions file.
  It must state:
  - the final checker sha256;
  - the residuals for plan v1.15.18: fix pass 10's three, plus any this pass adds;
  - how to run the checker on a port: the `--repo`, `--template` and `--pins` arguments, and juniper-data's called
    file. That run is how the ports are checked.
- No round-13 brief.

## Rules

Fix pass 10's rules apply, with `checker-r12/` as your directory:
- never write under `/tmp`, and delete nothing;
- read-only `gh` GETs only;
- never push, commit, open, comment on, approve or merge anything;
- no secrets or personal data;
- use script files, and run Python with `-B`;
- return to `$W` after any `cd`.

## Report (your last message, under 350 words)

- What changed, per round-12 id.
- The final sha256 and the interdiff's size.
- The counts for every re-run.
- Any mutant that still passes, and any simulation that fails.
- Every deviation from this brief.
- The residual list.
