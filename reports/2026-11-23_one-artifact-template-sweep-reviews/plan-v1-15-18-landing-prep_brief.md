# Landing prep for plan v1.15.18 (the one-artifact template sweep's files)

You prepare, in ONE juniper-ml worktree, the files that plan v1.15.18's PR lands. You do not write the plan, open a PR,
commit, push or merge: the orchestrator (session `d769e173`, worktree `purring-hugging-hippo`) does that.

## Paths

- `ME=/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/purring-hugging-hippo` (your worktree;
  the ONLY place you create files, except item 5's archive). Its HEAD is juniper-ml `main` `557490fb`.
- `W=/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/ethereal-munching-peacock` (READ ONLY).
- `WT=/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/moonlit-percolating-sun` (READ ONLY).
- `PRIMARY_TMP=/home/pcalnon/Development/python/Juniper/juniper-ml/tmp` (item 5 only, through Bash; the Write tool
  refuses it).
- Python with PyYAML: `/opt/miniforge3/envs/JuniperCascor1/bin/python3`. flake8 with bugbear 26.11.22:
  `/home/pcalnon/.cache/pre-commit/repo0tnh18pd/py_env-python3/bin/flake8`.
- Read first: `$ME/util/ad-hoc/README.md` (the header format), `$ME/util/ad-hoc/2026-11-15_archive_r_obs_sc_2_reviews.py`
  (the archive pattern), `$W/tmp/sweep/REVIEW_DISPOSITIONS.md` § "Fix pass 11" ("How to run the checker on a port").

## Rules

- NEVER write under `/tmp` or `/var/tmp`. Scratch goes in `$ME/tmp/v1_15_18/landing/`.
- NEVER delete, move or modify anything in `$W`, `$WT` or the primary checkout (copy with `cp -p` only). Never
  `git commit`, `git push`, `git stash`, or touch `$ME/notes/`, `$ME/docs/`, `$ME/prompts/` or any existing tracked file.
- Network: read-only `gh` / GitHub API GETs only.
- Times from `date -u`, never estimated. If a step cannot be done as written, do not improvise around it: record why in
  the report and go on to the next item.
- Copy your deliverables' paths into the report; your worktree IS `$ME`, so nothing needs rescuing, but write the report
  file BEFORE your final message.

## 1. Verbatim copies into `$ME/util/ad-hoc/`

- The 7 files named in `$W/tmp/arc/sweep_scripts.sha256`, from `$W` (`cp -p`). Then `cd $ME && sha256sum -c
  $W/tmp/arc/sweep_scripts.sha256` must print 7 OK (the checker `a452db3d…`, the pins file `faa198c2…`).
- The 8 writers `$WT/util/ad-hoc/2026-11-26_*.py` (`cp -p`). Write `$ME/tmp/v1_15_18/landing/writers.sha256`
  (`sha256sum` format, repo-relative paths). For each, look for its hash (16-hex prefix or 8-hex prefix) in
  `$W/tmp/sweep/REVIEW_DISPOSITIONS.md` and `$WT/tmp/ports/*/REPORT*.txt`, and report which writer's FINAL hash a
  source states and which none does (a later fix-up may have moved it; say which report states the last value).

## 2. The juniper-ml port writer: CodeQL's unused locals

`util/ad-hoc/2026-10-05_codeql_python_prescreen.py` predicts 5 `unused-local` alerts in
`2026-11-26_juniper-ml_one_artifact_sweep_port.py` (tuple targets never read: `install_job()` `package` at :670;
`install_step_old()` `package`, `prod_id`, `step_name` at :688; `workflow_edit()` `step_name` at :761). An unresolved
CodeQL thread blocks the merge, and the rule is to restructure, never suppress. So, in `$ME`'s copy ONLY:

- replace exactly those 5 targets with `_`, and add one docstring sentence naming the change (e.g. "Landed with plan
  v1.15.18 on 2026-11-26 with five unused tuple targets renamed `_` (CodeQL's unused-local), its output unchanged.");
- prove the output unchanged: run the ORIGINAL (`$WT`'s) and the MODIFIED writer the same way on identical fresh inputs
  (the executor's reports `$WT/tmp/ports/juniper-ml/REPORT*.txt` say how it ran and on which base) and compare every
  file each writes, byte for byte. If a replay is impossible, say exactly why, and instead show with `ast` that the two
  modules differ only in those 5 `Name` nodes and the docstring, and that no renamed name is read in its function;
- re-run the prescreen on the modified copy: 0 alerts.

## 3. Promote three session tools to `$ME/util/ad-hoc/`, with the README's header

- `$WT/tmp/s2/verify_all_mains_v3.bash` -> `2026-11-26_publish_port_verify_all_mains.bash`;
- `$WT/tmp/s2/check_pr_head.bash` -> `2026-11-26_publish_port_check_pr_head.bash`;
- `$WT/tmp/s2/apply_pin.py` -> `2026-11-26_publish_port_apply_install_pin.py`.

Keep each tool's behaviour, except: run from any juniper-ml checkout (repo root from the script's own location, e.g.
`git -C "$(dirname "$0")" rev-parse --show-toplevel`); the checker and pins file are the checkout's own
`util/ad-hoc/2026-11-23_publish_port_template_identity.py` and `util/ad-hoc/2026-11-24_publish_port_install_pins.json`
(overridable as the originals allow); Python from `${PYTHON:-python3}` (it needs PyYAML; say so); outputs under the
checkout's `tmp/` in a new timestamped directory; no `/home/pcalnon` and no `/tmp` literal; for the pin tool, the pins
file in the checkout is the canonical one (git is its manifest now: drop the `$W` manifest regeneration, keep the
backups, under `tmp/`). Keep check_pr_head's refusal of a checker whose sha256 is not `a452db3d…`.

Prove each: `bash -n` and shellcheck clean; `verify_all_mains` run from `$ME` prints `18 of 18 pass` (every `main`);
`check_pr_head` on `juniper-cascor-client 207` (merged; its head `faaf6538`) with the canonical pins prints PASS;
the pin tool given the canonical pins file itself as the proposal for one repo changes nothing (`--dry-run` and a real
run on a COPY under `$ME/tmp/`), and refuses a proposal that moves another repo's pin. Keep each run's output.

## 4. The reviews' archive (in git): `$ME/reports/2026-11-23_one-artifact-template-sweep-reviews/`

Built by a new `$ME/util/ad-hoc/2026-11-26_archive_one_artifact_sweep_reviews.py`, modelled on the 2026-11-15 archiver:
verbatim copies (plus one final newline only if a source lacks it), each source's sha256 pinned in the script, a
`README.md` table (file, what it is, source path, sha256 prefix), and `--check` (writes nothing; exit 1 when a copy is
missing or differs from its source, or, when a source has gone, from its pin). Sources (flat names in the archive, e.g.
`dispositions.md`, `round-06_report.md`, `round-04_brief.md`, `fixpass-03_brief.md`, `land_brief.md`,
`port-juniper-canopy_review.txt`, `port-juniper-canopy_report.txt`, `port-juniper-canopy_report-fixup.txt`):

- `$W/tmp/sweep/REVIEW_DISPOSITIONS.md` (the arc's live record, every round, fix pass, ruling and port);
- `$W/tmp/r{6..12}review/ROUND{6..12}_REPORT.md`;
- `$W/tmp/sweep/ROUND{4..12}_BRIEF.md`, `FIXPASS{3..11}_BRIEF.md`, `LAND_BRIEF.md`;
- `$W/tmp/ports/SWEEP_BRIEF.md`, `$W/tmp/ports/SWEEP_ITEMS.md`, `$W/tmp/arc/plan_v1_15_18_inputs.md`;
- `$WT/tmp/ports/SWEEP_PORT_BRIEF.md`, `$WT/tmp/ports/SWEEP_PORT_REVIEW_BRIEF.md`;
- `$WT/tmp/ports/<repo>/review/REVIEW.txt` (7) and every `$WT/tmp/ports/<repo>/REPORT*.txt` (17, the cascor-client
  follow-up's included).

Then: (a) grep every archived file for credentials and personal data (token prefixes `ghp_`, `gho_`, `github_pat_`,
`pypi-`, `AKIA`, private-key headers, e-mail addresses) and report each hit with its line; change nothing; (b) run the
doc-link check exactly as CI does, from `$ME`: `juniper-check-doc-links --exclude templates --exclude history --exclude
legacy --exclude pull_requests --exclude releases --exclude analysis --exclude fixes --exclude development --exclude
CHANGELOG.md --exclude tmp --cross-repo skip`. If an archived `.md` makes it fail, store that file as `<name>.md.txt`
(content still verbatim), say so in the README, and re-run until clean.

## 5. The proof tools' archive (outside git, in the primary's `tmp/`)

`$PRIMARY_TMP/worktree-archive-2026-11-26/ethereal-munching-peacock/tmp/sweep/<dir>/` for each `<dir>` of `cascor-r3`,
`cascor-r4`, `checker-r5` ... `checker-r12` in `$W/tmp/sweep/`: copy (`cp -p`, never `mv`) every TOP-LEVEL regular file
of the dir and, recursively, its `evidence/` subdirectory if it has one. Measure first (`du`); if the total exceeds 1 GB,
copy only the top-level files and report the evidence sizes. Then write `MANIFEST.sha256` (paths relative to the
archive root) and `README.md` there: what this is (each round's proof drivers and evidence, the tools that produced the
counts `REVIEW_DISPOSITIONS.md` records), its source, when (`date -u`) and by which session, that the trees (clones,
mutants, simulations) were NOT copied and remain in `$W/tmp/sweep/` until the Overtoad rules on `$W`'s removal, and
that it is kept under the 2026-10-26 retention rule. Verify: `sha256sum -c MANIFEST.sha256` from the archive root, all OK.

## 6. Gates on every new file under `$ME/util/ad-hoc/`

- `python3 util/ad-hoc/2026-10-05_codeql_python_prescreen.py <every new .py>`: 0 predicted alerts;
- the flake8 above with `--select=B914` and with `--max-line-length=512 --select=F,E9`: 0 findings;
- `python3 -m py_compile` each `.py`; `shellcheck` each `.bash`;
- `python3 util/tmp_path_literal_check.py` and `python3 util/home_path_literal_check.py` (whole scope): PASS;
- `pre-commit run --files <the new util/ad-hoc files>` (use `/opt/miniforge3/bin/pre-commit` if the one on PATH is
  broken). If a hook would CHANGE a verbatim file (items 1-2), do not keep the change: restore the verbatim bytes with
  `cp -p` and report the hook and the file.

## Report

Write `$ME/tmp/v1_15_18/landing/REPORT.txt` (plain text): for each item, what you did, every file created (path,
sha256, source), each proof's command and result, and anything not done or deviating, with the reason. Then end with a
final message that summarizes the report and gives its path.
