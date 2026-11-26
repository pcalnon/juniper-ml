# Handoff: one-artifact sweep. All 15 ports in 7 repos LANDED (`18 of 18 pass` on every `main`), plus juniper-cascor-client#207; every install pin reviewed and applied; next, plan v1.15.18

**Written**: 2026-11-26 (`date -u`, see the PR) by session `b71989`, ListAgents name `moonlit-percolating-sun-fa`.
**Worktrees** (keep BOTH until plan v1.15.18 lands their files and `tmp/` is archived; never `git worktree remove`
either before then):
- `WT=/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/moonlit-percolating-sun`: this session's.
  The 15 ports' briefs, evidence, writers, reviews and merge logs live here (`tmp/ports/`, `tmp/s2/`, `util/ad-hoc/`).
- `W=/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/ethereal-munching-peacock`: the arc's record.
  `tmp/sweep/REVIEW_DISPOSITIONS.md` holds every round, fix pass, ruling and port (this session appended its sections
  after "Fix pass 11"); `$WT`'s key files are mirrored to `tmp/ports/s2/`.

This file supersedes session `ffffd3`'s handoff of ml#2658
(`prompts/thread-handoff_automated-prompts/HANDOFF_2026-11-25_one-artifact-sweep-port-checker-cleared-round-12-fix-pass-11-final-ports-next.md`),
whose item 3 (plan v1.15.18) still holds as extended below. **Merge approval is per-session: ask the owner again.**

## Done (receipts in `$W/tmp/sweep/REVIEW_DISPOSITIONS.md`, `grep -n '^## '`)

Each port: a task-executor built it from `$WT/tmp/ports/SWEEP_PORT_BRIEF.md` (with its "Addenda from the pilots"),
opened ONE signed-commit PR, then a fresh `general-purpose` agent reviewed it cold
(`$WT/tmp/ports/SWEEP_PORT_REVIEW_BRIEF.md`; report `$WT/tmp/ports/<repo>/review/REVIEW.txt`). Fix-ups by the same
executor, checked by the orchestrator against the patch and the FINAL checker on the head as GitHub holds it
(`$WT/tmp/s2/check_pr_head.bash`). No review found a BLOCKER; one MAJOR (data-client F1) was fixed before its merge.

| repo | PR | merged (UTC) | merge commit | review |
|---|---|---|---|---|
| juniper-cascor-client | #206 | 11-26 03:13:03 | `beb6b349` | 0/0/1/6 |
| juniper-data-client | #274 | 04:15:39 | `4b78d540` | 0/1/3/1 |
| juniper-cascor-worker | #238 | 04:26:48 | `f9122a8a` | 0/0/1/2 |
| juniper-canopy | #844 | 05:14:24 | `aa9ac734` | 0/0/2/3 |
| juniper-data | #553 | 05:24:33 | `a0bb1558` | 0/0/1/5 |
| juniper-recurrence (3 publishers) | #241 | 06:12:43 | `8a5a062e` | 0/0/2/3 |
| juniper-ml (7 publishers) | #2673 | 13:08:46 | `e2e463ea` | 0/0/3/5 |
| juniper-cascor-client (follow-up: the PyPI check's two causes) | #207 | 11:27:26 | `7e1399d8` | orchestrator-read |

(review = BLOCKER/MAJOR/MINOR/NIT.) Every squash kept its `Allow-Symbol-Loss:` lines (COMMIT_MESSAGES in all 8 repos).

- **The pins file**: `$W/util/ad-hoc/2026-11-24_publish_port_install_pins.json` is now `faa198c2…`: all 18 pins are each
  port's reviewed final script (cascor's 3 unchanged). Applied one repo at a time by `$WT/tmp/s2/apply_pin.py`
  (it takes only that repo's entries; backups `$W/tmp/arc/pins.before-<repo>-*.json`). The manifest
  `$W/tmp/arc/sweep_scripts.sha256` was regenerated each time: 7 paths, all OK.
- **The done-check**: `bash $WT/tmp/s2/verify_all_mains_v3.bash` (v2 adapted: `--pins`, data's `notify-consumers.yml`,
  one checker run per repo) printed **`18 of 18 pass`** after 13:08:47Z, every repo `exit 0`, on `main`s cascor
  `5e3d9801`, canopy `374c0fb9`, data `a0bb1558`, data-client `51e34f71`, cascor-client `7e1399d8`, cascor-worker
  `f9122a8a`, recurrence `8a5a062e`, ml `e2e463ea`.
- **#2673's merge**: `safe_merge.py` first REFUSED (`main` moved BEHIND three times while CI ran) and disarmed its net;
  the retry merged it. A busy juniper-ml `main` can need more than one `safe_merge.py` run: retry, never bypass.
- **Owner rulings this session** (verbatim in the dispositions): "Approve all 7 (Recommended)" (merges, by 01:47:14Z);
  "Yes, merge it (Recommended)" (#207, by 11:27:00Z); "merge approval granted for this work arc" (11:27:00Z).

## Remaining work: plan v1.15.18

On a FRESH clone of juniper-ml `main` (`GIT_LFS_SKIP_SMUDGE=1`: the LFS smudge fails on this host's credentials), never
from `$W` or `$WT` (their tracked plan is stale). It records:
1. #777; checker rounds 1-12 and fix passes 1-11; the checker arc's three rulings; this session's three rulings.
2. The 7 port PRs and #207, with the table above, each review's verdict and dispositions (the dispositions file's
   sections "Review of …").
3. The residuals: § "Fix pass 10" and § "Fix pass 11" of the dispositions file, plus this session's:
   - **comment guard**: the checker compares parsed YAML, so template comments outside `run:` scripts are guarded only
     by repo digest pins where they exist (cascor-client, data-client, worker, ml normalized; data raw + parsed);
     canopy and recurrence have none (#844 M2, #241 F2: an edit alike in recurrence's three copies passes its suite);
   - the pinned find_spec comments' "installs and imports" (the template's wording; #238 N-1, #553 R-4): reword in a
     later pin round, all ports together; the banner comments' "runs/executes the package" likewise (cascor's text);
   - labels "R4-5" / "SWEEP item 23" in the ports' tests and CHANGELOGs (#238 N-2) and canopy's test citing the
     checker's path (#844 N2) resolve only once this plan and the checker land;
   - data's spelled-out try counts unpinned (#553 R-5); ml `ci.yml`'s actionlint with shellcheck/pyflakes does not finish
     (also on `main`).
4. SWEEP items 28 and 29 (round 10's R10-7 path for 28); every input in `$W/tmp/arc/plan_v1_15_18_inputs.md`.

It lands: the 7 manifest files from `$W` (with the pins file at `faa198c2…`); the 8 new writers in `$WT/util/ad-hoc/`
(`2026-11-26_<repo>_one_artifact_sweep_port.py` ×7 and `2026-11-26_juniper-cascor-client_pypi_check_two_causes.py`);
this session's tools in `$WT/tmp/s2/` that later work needs (`verify_all_mains_v3.bash`, `apply_pin.py`,
`check_pr_head.bash`; promote to `util/ad-hoc/` with headers, or archive); and promotes or archives the proof tools
under `$W/tmp/sweep/` (`cascor-r3`, `cascor-r4`, `checker-r5` … `checker-r12`). Run the CodeQL prescreen
(`util/ad-hoc/2026-10-05_codeql_python_prescreen.py`) and pre-commit on every new script first; every writer must pass
B914 (one had 39 implicit concatenations until its fix-up).

## Traps (new this session)

- **Agent worktrees are removed when the agent finishes**: every executor and reviewer must copy its deliverables into
  `$WT` before its final message (`$WT/tmp/s2/rescue_agent_outputs.py` rescued data-client's).
- **A worktree-isolated session cannot Write/Edit another worktree**: `$W` is written only through scripts
  (`$WT/tmp/s2/mirror_to_w.py`, `replace_in_w.py`); the Bash guard refuses complex lines naming `$W`.
- **The pins file moves as pins are applied**: a proposal built on an older canonical file still applies (only its
  repo's entries are taken); never copy a proposal file whole.
- **An owner dialog held this session ~5 hours** (asked after 06:13:35Z, answered by 11:27:00Z).
- **#2673's branch was synced and auto-merge armed outside this session** (11:42:13Z/11:42:15Z, the owner's account);
  the executor's stale `expected_head` stopped its push correctly; re-pinned after checking the merge touched none of
  its files.
- **Never estimate a time**: this session wrote four estimates and corrected each to `date -u` bounds.

## Verification (one per call)

```bash
bash /home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/moonlit-percolating-sun/tmp/s2/verify_all_mains_v3.bash   # "18 of 18 pass"
cd /home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/ethereal-munching-peacock && sha256sum -c tmp/arc/sweep_scripts.sha256   # 7 x OK
grep -n '^## ' /home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/ethereal-munching-peacock/tmp/sweep/REVIEW_DISPOSITIONS.md | tail -40
```

## Git state

- `$WT`: branch `worktree-moonlit-percolating-sun` at `966cdb13` (behind `main`), nothing staged; untracked: the 8
  writers in `util/ad-hoc/` and this handoff (landed by its own PR); gitignored `tmp/` holds the clones
  (`tmp/ports/clones/`), every port's scratch dir, the reviews and the merge logs.
- `$W`: unchanged branch state (`81b8eaf7`); its untracked files and `tmp/` as ml#2658's handoff lists, plus this
  session's appended sections, the pins and manifest backups in `tmp/arc/`, and `tmp/ports/s2/`.

## Documents referenced / changed

- **Referenced**: ml#2658's handoff (above); `$W/tmp/sweep/REVIEW_DISPOSITIONS.md`; `$W/tmp/ports/SWEEP_BRIEF.md`;
  `$WT/tmp/ports/SWEEP_PORT_BRIEF.md`; `$WT/tmp/ports/SWEEP_PORT_REVIEW_BRIEF.md`; each `$WT/tmp/ports/<repo>/review/REVIEW.txt`.
- **Changed on GitHub**: the 8 PRs above (each repo's publishers, publish tests, docs and CHANGELOG).
- **Changed in `$W`**: `util/ad-hoc/2026-11-24_publish_port_install_pins.json`, `tmp/arc/sweep_scripts.sha256`,
  `tmp/sweep/REVIEW_DISPOSITIONS.md`, `tmp/ports/s2/`.
- This handoff lands through its own one-file PR.
