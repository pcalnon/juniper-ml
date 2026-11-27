# Handoff: one-artifact sweep. Plan v1.15.18 is LANDED (juniper-ml#2685); what is left is the Overtoad's (two decisions, retention, worktree removals) and four unowned session items

**Written**: 2026-11-27 (`date -u`, see the PR) by session `d769e173`, worktree
`ME=/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/purring-hugging-hippo`.
It supersedes session `3792e0cc`'s handoff of ml#2676
(`prompts/thread-handoff_automated-prompts/HANDOFF_2026-11-26_one-artifact-sweep-all-ports-landed-18-of-18-plan-v1-15-18-next.md`),
whose remaining work (plan v1.15.18) is done. **Merge approval is per-session: ask the Overtoad again.**

## Done (the record is the plan; read it, not this list)

- **juniper-ml#2685 MERGED** at 2026-11-27T00:17:32Z as `26915cbb`, by `util/safe_merge.py`'s armed auto-merge net once the required checks were green. Its head was `d7a2b134`, after one BEHIND refresh that brought in ml#2684. It carried 13 signed commits and 91 files.
  - On `main`, all 91 files are byte-identical to what was built.
  - The landed done-check printed `18 of 18 pass` against every `main` at 00:18Z, juniper-ml at `26915cbb` included.
- **`notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md` v1.15.18**: §5's new note "The template sweep and its ports, 2026-11-23 to 2026-11-26", `v1.15.18:` notes under the passages it made stale, §6's "Left with the Overtoad by the template sweep", the Validation record's v1.15.18 entry, and "Changed by this plan". It was written by `util/ad-hoc/2026-11-26_consolidated_plan_v1_15_18_template_sweep.py` (50 anchored edits; `--check` exits 0 on `main`).
- **Landed scripts** (`util/ad-hoc/`): the port checker `2026-11-23_publish_port_template_identity.py` (`a452db3d…`) and its pins `2026-11-24_publish_port_install_pins.json` (`faa198c2…`), the sweep's other five, the eight port writers, and three promoted tools: `2026-11-26_publish_port_verify_all_mains.bash` (the done-check), `…_check_pr_head.bash` and `…_apply_install_pin.py`. They run from any juniper-ml checkout with a PyYAML `PYTHON`.
- **The review archive** `reports/2026-11-23_one-artifact-template-sweep-reviews/` (70 files: the arc's record `dispositions.md`, every brief, rounds 6 to 12's reports, the ports' reviews and executor reports, and this session's validation and landing prep), built by `util/ad-hoc/2026-11-26_archive_one_artifact_sweep_reviews.py` (`--check`).
- **The proof archive** `juniper-ml/tmp/worktree-archive-2026-11-26/` (outside git): the ten fix-pass directories' top-level files and `evidence/` from `ethereal-munching-peacock/tmp/sweep/` (1,580 files, `MANIFEST.sha256`).
- **Validation**: draft 1, a fact re-probe (0/3/11/10) and a completeness attack (1/8/18/11); draft 2, a round-2 agent on the corrections (0/1/8/14). Every finding was re-checked at its source and applied.
- **The Overtoad's rulings this session**: "merge approval granted" (queued 21:40:06Z) and "merge approval granted for this work arc" (21:40:15Z), by this session's transcript.

## Remaining work

The plan's §5 note, "What remains", and §6's mid-wave sitting are the authority. In short:

1. **With the Overtoad** (ask; do not act):
   - the two decisions the arc's record leaves to the plan: pin the build job's steps before the build, as install scripts are (M11-C, R11-1), or not; and accept in writing that the publish action's container image is named by a re-pushable tag, or record the image digest the template's review saw (M11-E);
   - the retention of `juniper-ml/tmp/worktree-archive-2026-11-23/` (R18) and of `…/worktree-archive-2026-11-26/`. The plan now records what the first backs: three of the five files it cites are SUBSTITUTED copies (the parent `AGENTS.md` copy `d8ab5749…`, `fixpass_r1.md` `76bc0754…`, 44 of `review-763/`'s 89 files);
   - R16 (`giggly-foraging-sunbeam`, `sparkling-percolating-meadow`, `agent-a54a0a279acc3a863`) and R17 (`juniper-ml/tmp/retry-after-guard-ssq1mano`), from `notes/JUNIPER_2026-11-23_JUNIPER-ECOSYSTEM_R-OBS-SC-2-FOLLOW-UPS-REMAINING-TASKS.md`;
   - removing `ethereal-munching-peacock` and `moonlit-percolating-sun` (R41), only once ALL of their `tmp/` is archived. That is NOT done: the review-round directories, `tmp/sweep/land/`, `cascor`, `cascor-r2`, `cascor-r3-prep`, `tmp/arc/`, `tmp/ports/`, the audit dirs and the record's 37 backups in the first, and all of the second's `tmp/` but `SW/`'s copies. And this worktree, `purring-hugging-hippo`: archive its `tmp/v1_15_18/` and `tmp/publish-port-*/` first;
   - the trusted-publisher check (v1.15.17's), and juniper-observability 0.4.3's `pypi` gate (another lane's; run 45739959764; day 30 is 2026-12-26, day 35 2026-12-31).
2. **Unowned session work** (no session holds any of it):
   - once 0.4.3's gate is approved: re-read PyPI's and TestPyPI's JSON for 0.4.3 and compare sha256 (gap 16);
   - SWEEP items 28 (tie `SHA256SUMS`' version to the tag) and 29 (a check job before the `pypi` gate): a template change through cascor, then every port, then a new reviewed checker pass;
   - the residuals' wording (the `find_spec` comments' "installs and imports", the banners' "runs the package"): a pin round over all ports together;
   - the first Release through a swept publisher: the same sha256 check.

## Traps (new this session)

- **This session is worktree-isolated, and its guard refuses ANY Bash line in which it reads "git" in a complex form**: a grep pattern or a heredoc containing the word, a path into another checkout's `.git/`. Put such commands in a script file and run the script; read other checkouts' files with `cat`/`python3`.
- **The pre-push gate prints only the last 3 lines of each scan's log**: it showed 3 ACCEPTED findings beside `exit 2` while a fourth was OPEN. Read `PAYLOAD/files.log` whole.
- **The token-triage tool reads 0 lines and exits 0** unless its directory holds `*.md` files and `tmp/plan-pr/tracked.txt` exists. Check "lines read".
- **An archive README's "proven" equality can be false after a restore** (the 2026-11-23 archive's parent copy). Re-hash before citing it.
- **G-TMP flags prose**: `<worktree>/tmp/` matched. Reword, or end a line that must quote a `/tmp` path with `# tmp-path-literal: allow`.
- **`main` moved under the PR** (`557490fb` → `b91cecbc`, ml#2682 among others). The upload driver refuses a batch whose paths `main` changed; the writer replays on any base.

## Verification (one per call, from a checkout of `main` after the merge)

```bash
gh pr view 2685 --repo pcalnon/juniper-ml --json state,mergedAt,mergeCommit
python3 util/ad-hoc/2026-11-26_consolidated_plan_v1_15_18_template_sweep.py --check
python3 util/ad-hoc/2026-11-26_archive_one_artifact_sweep_reviews.py --check
PYTHON=/opt/miniforge3/envs/JuniperCascor1/bin/python3 bash util/ad-hoc/2026-11-26_publish_port_verify_all_mains.bash
cd /home/pcalnon/Development/python/Juniper/juniper-ml/tmp/worktree-archive-2026-11-26 && sha256sum -c --quiet MANIFEST.sha256
```

Expected: MERGED; `--check` exit 0 ("already applied" 50 times); 70 PASS; `18 of 18 pass`; no output.

## Git state

- `$ME`: branch `worktree-purring-hugging-hippo` at `b91cecbc` (fast-forwarded from `557490fb`), nothing staged. Its untracked files are the 91 that #2685 landed (byte-identical, read back by blob sha) plus this handoff. Its gitignored `tmp/` holds `v1_15_18/` (probes, landing prep with replay trees, validation, the landing driver and its logs) and `publish-port-*/` (the promoted tools' runs). Keep it until those are archived.
- `ethereal-munching-peacock` and `moonlit-percolating-sun`: unchanged by this session, apart from its done-check output `tmp/ports/verify-all-mains-v3/20261126T214015Z/` in the second.

## Documents referenced / changed

- **Referenced**:
  - ml#2676's handoff (above);
  - `notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md` (v1.15.18);
  - `notes/JUNIPER_2026-11-23_JUNIPER-ECOSYSTEM_R-OBS-SC-2-FOLLOW-UPS-REMAINING-TASKS.md`;
  - `reports/2026-11-23_one-artifact-template-sweep-reviews/dispositions.md`;
  - `juniper-ml/tmp/worktree-archive-2026-11-23/README.md`.
- **Changed by juniper-ml#2685**: the plan; the 20 `util/ad-hoc/` files listed in its body; `reports/2026-11-23_one-artifact-template-sweep-reviews/` (new).
- **Changed outside the repository**:
  - `juniper-ml/tmp/worktree-archive-2026-11-26/` (new);
  - the auto-memory file `reference_commit_pr_mechanics_hub.md` (four bullets appended: the gate's 3-line tail, the triage tool's inputs, batching at 3.76 MB, the archive README trap). `MEMORY.md` is unchanged.
- This handoff lands through its own one-file PR.
