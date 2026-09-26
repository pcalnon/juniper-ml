# HANDOFF 2026-09-24 — backup arc: D-8/STOP change paused mid-round-8 (not yet PR'd)

Continue the Juniper backup arc (host `yamaguchi`). Design of record: `notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-INFRASTRUCTURE-INTEGRATED-DESIGN.md` ("D"). Tier 1 down since 2026-09-18, tier 2 since 2026-09-07. **Unvalidated handoff** (owner asked for minimal tokens).

## State

- Worktree `juniper-ml/.claude/worktrees/typed-skipping-salamander`, branch `worktree-typed-skipping-salamander`, **local-only** commits over `main` `6c23fdde`: `2c9efe85` (round-6 pass), `f90a87e7` (round-7 pass), `2072e45a` (paused WIP). Tree clean. Never `reset --soft origin/main` (stages a revert of others' work); rebuild from pinned `6c23fdde`.
- The change (7 files): D; `notes/JUNIPER_2026-09-22_…ROUND-2-RECORD.md` (one sentence); `notes/JUNIPER_2026-09-24_…ROUND-4-RECORD.md` ("R", rounds 4–8 reports verbatim); `util/ad-hoc/2026-09-24_amend_d8_and_repair_backup_design.py` ("E", anchor-asserted edits from `6c23fdde`, gates, `--self-test`); `util/ad-hoc/2026-09-24_archive_round4_reports.py`; `util/ad-hoc/smart_checks_backup-sda.bash`; and in `util/ad-hoc/2026-09-22_backup-design-round2/`: `PR_BODY_D8_AMENDMENT.md`, `COMMIT_BODY_D8.txt`, `ROUND4_RECORD_HEADER.md` (R's authored preamble — archiver `--header`).
- Owner rulings 2026-09-24 (final): D-8 amended (one scrub before P0 = P0.5a item 4); P0 gate = items 1, 2, 4 before P0, items 5–7 "run in the same session"; narrow PR, §8 fixes in a follow-up; SMART refactor adopted (one clock read); STOP scope, verbatim: hold "P0.5a items 2 and 4, P0, P0.5b, P1, P2 and P4"; release "P0.5a items 1, 5, 6 and 7 (item 1 still runs before item 4), P3's tier-2 fix, §6's sink checklist and S-4's `chmod 0600`, with two limits: no history file is wiped before P0 step 3 tests the keys it may hold, and no transcript is purged before this arc's reports are archived. Read-only steps may run." Owner granted merge approval for this arc's PRs in the 2026-09-24 session — re-confirm.

## Next: finish round 8 → PR

E already carries (in `2072e45a`, **not yet rebuilt**): round-8 lens A 1–5 (§10.2 step 2's moved-aside `.env`; front-matter STOP bullet; "four only after round 7"; "reads that change nothing outside a scratch directory"; §5.4 root's files); lens B: STOP bullets and note 10.1g quote the owner's words, with the design's two narrow readings marked as readings; "P3's tier-2 fix" + P3 marker + P3 step 2 "scheduler and three user units landed with ml#1999; installer and `juniper-backup-failure.service` have not"; §7.11 drops `bin/`; front-matter no-move bullet; P0 preamble/P0.5a intro say item 1 is released; item 5 copy (destination must not exist, `chmod 0700` after `cp -a`); transcript row → new note sink-c; re-measuring row.

Still to do:
1. Lens B #3: §5.3 → "…the one place left to look, and only without printing a line — a Repair command there may carry `--passphrase`, and §6's row for the file says never print; no §8 step lists that search or a way to run it without printing, and once P0 step 3 has tested the file, the release's first limit no longer keeps it (note 10.1g)." §11 "(no shell history names it)" → "(pcalnon's shell history does not name it; root's is unread, §5.3)".
2. Rounds "4–7"→"4–8" everywhere in E (front matter ×3, STOP heading, §11 state line, "seven rounds"→"eight", §12 row, note 12b "Rounds 4–7"/"all four rounds", §11 "four rounds' reports", docstring). Add §11 **Round 8** entry (a correction recorded as applied but never made; ruling wording not the owner's own; item 5's copy group-writable; two released instructions with no safe method).
3. Add STALE phrases for replaced text (e.g. "P3 but its step 3", "count-grep now", "look before then", "except the one escrow copy named in P1 step 4", "step 3 still waits on D-5.*", "`/home/duplicati/bin/` entirely\n(it holds").
4. Rebuild: `git restore --source=6c23fdde --worktree -- <D> <round-2 record>`; run E (fix any FAIL/OVER-WIDTH — table rows ≤512); re-run → "no change"; `--self-test` → 8 of 8.
5. R: in `ROUND4_RECORD_HEADER.md` add "What round 8 was for/found/Disposition of round 8" (A: 4 refuted, 1 unverifiable, 155 confirmed; B: 11 refuted, 1 unverifiable, 95 confirmed, 3 of round 7's 25 dispositions false; B13 row: §7.11 and P3 step 2 only in round 8); title/artifact line → rounds 4–8, "round 8 read `f90a87e7`". Regenerate R with the 11 `--report` args (headings as in R; ids below).
6. Gates: `util/ad-hoc/2026-09-22_stage_design_artifacts.py --check` (exit 0 even on drift — read "0 staged"); `util/ad-hoc/2026-09-21_lint_design_snippets.py --doc D --workdir <scratch>`; markdownlint `/home/pcalnon/.cache/pre-commit/repoft72ba_k/node_env-default/bin/markdownlint --config .markdownlint.yaml` (pre-commit skips `notes/`); `python3 -m flake8 --max-line-length=512` (pre-commit skips `util/ad-hoc/`); `/opt/miniforge3/bin/pre-commit run --files …`; `util/markdown_structure_delta.py --base 6c23fdde --head <wip>`; `juniper-symbol-loss-check` / `juniper-docs-additions-check` same refs.
7. SOP: validate round 8's corrections before opening (the owner's sweeper arms open PRs) — a narrow round scoped to the delta.
8. Fill placeholders (ROUND_LAST, EDIT_COUNT, VALIDATION_PLACEHOLDER) in the PR/commit bodies; check `git diff --stat 6c23fdde origin/main -- <7 files>` is empty; `python3 util/open_signed_pr.py --repo juniper-ml --base main --branch <b> --add F:F … --message … --commit-body-file …/COMMIT_BODY_D8.txt --title … --body-file …/PR_BODY_D8_AMENDMENT.md`; arm `gh pr merge N --squash --auto`; `util/ad-hoc/2026-09-22_shepherd_automerge.bash N`.

Archive ids (`--tasks-dir`: `~/.claude/projects/-home-pcalnon-Development-python-Juniper-juniper-ml--claude-worktrees-typed-skipping-salamander/0a852d44-65ca-46ac-953b-84e8bae98e9c/subagents`; if moved after this session ends, find by session id `0a852d44-…`): R4 A `a33654134593ec9e5`, B `a57877766ba2b23a2`, C `a8f24f03a0369020a`; R5 A `a966210ea522cee20`, B `a43c655c58fa3c7d3`; R6 A `a841de27cfb79b907`, B `a3c38866fe3a3c00e`; R7 A `a87a13ad93fbc1532`, B `a0467007773f20047`; R8 A `a3b34b2844d99f420`, B `aabb0e6fb4eee5891`. R already holds all eleven reports.

## After it merges

- **§8 follow-up change** (own validation round; removes the STOP): STOP items 1–5 (step 0(a) flag/blessed file + D-1 flag's durable home under D-6; P1 step 1 overwrites the old key; step 10 guard dry-run on empty `TargetURL` + step 9 client change unlanded; timer restart after step 8 copies A0's cleartext DB; `ProtectSystem=strict` without `ReadWritePaths=`); D-9 flags installed by nothing; D13 `.env` path; no-print key-candidate extraction for P0 step 3; P1 step 4 `cp -a` nesting; `InaccessiblePaths=` misses `/mnt/Backups/Ubuntu/_yamaguchi_keys`; transcript count-by-value method (sink-c); P0.5b's need/placement; Procedure B start before step 8; items 5/7 triggers; R's follow-up rows (round 4's B11, B13–B18, B24, B26, B27, U1–U4; AC-8 "hardening timestamp"; wrapper v2 `die` path; `confirm_a0_premise.bash` "here" — tagged block + landed copy together; P0 step 8 mode sentence; sign-in URL logged regardless of flag; §10.2 step 7 local set; AC-14 raw `\|`; P0 step 1's second listing; §4.1/§7.3.1 "P0.5 closes 0777 .config").
- **Owner decisions**: confirm/widen the two narrow readings (note 10.1g); P0.5b's fate; D-1 flag home; D13; S-3c (frozen 811 volumes + `PASSPHRASE_OLD`); release item 2's timer stop alone? (timer still runs the primary checkout's script as root daily).
- **Owner may act now**: P0.5a items 1, 5 (per its new text), 6, 7; P3 steps 1–2; count-only `sudo grep -c -i -e encryption -e passphrase -e password /home/duplicati/.bash_history` — never print, never wipe on the count.
- **Memory**: in `MEMORY.md` fix "sda … never SMART-tested" (two lines; PASSED 2026-09-23) and add links to `reference_uutils_ls_plus_is_any_xattr.md`, `reference_soft_reset_to_a_moving_ref_stages_a_revert.md`, `reference_a_ruling_made_from_a_stale_recommendation_column.md`; append a 2026-09-24 section to `project_backup_service_user_migration_2026-09-21.md`.

## Hard rules

Never start/stop/restart `duplicati.service` (PID 1397393, `Restart=always`) or run a Duplicati binary; nothing under `/mnt/Backups/Ubuntu/` deleted or moved; never read secret files (`.env`, `~/.config/duplicati-backup/*`, `/etc/credstore/*`, `_yamaguchi_keys/`, history/viminfo files — `stat` only); no journal/syslog greps; isolation layer refuses compound git and heredoc harnesses — use plain commands and E's `--self-test`.

## Verify

```bash
cd /home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/typed-skipping-salamander
git log --oneline -4          # 2072e45a, f90a87e7, 2c9efe85, 6c23fdde
git status --short            # clean
python3 util/ad-hoc/2026-09-24_amend_d8_and_repair_backup_design.py --self-test | tail -1
systemctl is-active duplicati.service
```
