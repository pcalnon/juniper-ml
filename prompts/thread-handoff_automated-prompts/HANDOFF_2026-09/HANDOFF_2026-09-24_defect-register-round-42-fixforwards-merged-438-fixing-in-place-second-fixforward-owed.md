# Handoff: defect-register round 42. The fix-forwards are merged, data#438 is being fixed in place, and a second fix-forward is owed

**From:** session `8f86dec2` ("defect reg [977fa8]"), worktree `.claude/worktrees/hazy-beaming-map`. **Date:** 2026-09-24, about 11:10Z.
**Predecessor:** `HANDOFF_2026-09-23_defect-register-round-42-four-prs-armed-by-an-unseen-actor-two-merged-unvalidated.md`.

## Goal (paste this as the new thread's first prompt)

Continue defect-register round 42 for the Juniper ecosystem. The register is `notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md`; the API primer is `notes/JUNIPER_2026-08-13_JUNIPER-ECOSYSTEM_API-DESIGN-AND-IMPLEMENTATION-PRIMER.md`. The owner's policy: the PR sweeper is theirs, "validate after merge and fix forward", and merge approval is granted for this arc's PRs. Checks must still pass, and other sessions' PRs are not covered.

**Completed:**
- **juniper-ml#2074** MERGED at 09:57Z (`6aabe4cc`). It closed APD-ECO-008 and filed eight rows. Its body was corrected after merge.
- **juniper-ml#2080** MERGED at 10:18Z (`f2688a95`), the register fix-forward:
  - moved 50 primer anchors by +3, each proven by content (juniper-ml#1098 inserted three lines at primer line 5758 after the register was created);
  - filed APD-ECO-012 (canopy CORS inside auth, latent) and APD-DATA-057 (data batch-tags unlocked read-modify-write);
  - recorded both mixed-provenance owner rulings verbatim (`reports/2026-09-24_defect-register-round-42/owner-rulings-verbatim.md`).
- **juniper-ml#2075** MERGED at 10:25Z (`f4d050c6`), the primer correction v2+v3, with a curated squash body. Main counts: `register_open_set.py` gives 136 rows | 100 fixed | 36 open; the crosscheck says AGREE.
- **juniper-data#438** is open. It is the round-3 fix-forward of #428, built by the executor. My commit `28fced18` moved #437's CHANGELOG entry out of the released `[0.16.0]`.
- **v0.16.0.** Another session cut juniper-data v0.16.0 at 08:52Z (tag `39d1cab2`). Its notes equal the tagged section (`util/ad-hoc/2026-09-24_verify_data_0_16_0_notes_match_tag.py`). The PyPI publish (run 35977786108) is WAITING for the owner.
- **Validation reports.** Every lane report is archived verbatim through `util/ad-hoc/2026-09-24_archive_round42_reports.py`.

**In flight:**
1. **Executor `adf9f5dbe46b1b03c`,** resumed at about 11:05Z, is fixing #438 in place. The fixes come from `data438-round1-laneA-reprobe.md` and `data438-round1-laneB-refute.md`: create and batch-create are unlocked; lock files pile up for absent ids; the delete paths fail with ENOSPC; the cached-store claim; the RFC misquote in `http_cache.py`; the "Moved here" sub-bullet I added would publish in the next Release notes; and more.
   - It pushes one signed commit with `--expected-head 28fced18…` and PATCHes the PR body.
   - Its final report is the last assistant message in `/home/pcalnon/.claude/projects/-home-pcalnon-Development-python-Juniper-juniper-ml--claude-worktrees-hazy-beaming-map/8f86dec2-21ea-43f2-911a-bb2314a822ec/subagents/agent-adf9f5dbe46b1b03c.jsonl`. Read it with the archiver's `last_report()`, and never with `splitlines()`.
2. **juniper-ml#2081** (probe provenance, 205 files) is green on required checks but BLOCKED by CodeQL: 61 alerts in the probes. The two highs are false positives; the rest are lint-class. **This is the owner's decision:** a CodeQL `paths-ignore` config, dismissing the alerts, or storing the probes as a tarball. The probes are safe on the pushed branch meanwhile.
3. **Peer "defect reg [042116]"** (session `bc31e993`) is building, under the owner's new **"Key leaks"** ruling ("Fix everywhere now"):
   - cascor#686's v2 (branch `fix/shortfall-mixed-provenance-and-678-followups-v2`), which supersedes #686 and closes CASCOR-008/-013;
   - the canopy leak fix (`fix/secret-leaks-683-validation`);
   - bytes-compare PRs in juniper-ml (observability and service-core), juniper-data and juniper-cascor.
   - Its juniper-data PR opens only after #438 merges. It sends PR numbers and SHAs to "defect reg [977fa8]", so **message it with your own session's name to re-route them.**

**Remaining:**
1. **When the executor reports**, validate #438's fix with two lanes. Then merge (update-branch after every move on main) and archive both reports.
2. **Open the second register and primer fix-forward** from `ml2080-round1-laneA-reprobe.md` and `ml2080-round1-laneB-refute.md`; the detailed list is in the appendix. The HIGHs:
   - five primer citations are still three short (register L527, L1736, L1737);
   - APD-ML-008 and `docs/REFERENCE.md` ~L2972 are false: juniper-ml has **zero** links into juniper-data, so a missing data clone makes the drift gate silently green;
   - the primer's POST-create ETag is unpinned, and E.1 item 3's bold rule is too broad.
3. **Open the closes PR:**
   - close CASCOR-008/-013 after cascor v2 merges and is validated;
   - close DATA-017/-029/-032/-057 after #438;
   - file **APD-ECO-013** (S; a non-ASCII `X-API-Key` makes the str `compare_digest` raise, the 500 goes to Sentry, and its local-variable capture records the real key) and **APD-ECO-014** (S; canopy's padded outbound keys leak into logs, Sentry and a 409 body). Both are ruled and in flight, so not parked;
   - quote the "Key leaks" ruling verbatim, re-extracted from `bc31e993`'s JSONL (extend `util/ad-hoc/2026-09-24_extract_mixed_provenance_rulings.py`);
   - record the peer's residue.
4. **The canopy nit goes to the canopy E2E ledger, not the register.** `src/frontend/dashboard_manager.py:8410` cuts " The resulting dataset" and so drops juniper-data's truncation warning (`juniper_data/core/limits.py:168`). So do the peer's LOW 3/4, which the canopy leak PR fixes.
5. **Put the four untracked reports into the next PR**, with the archiver's local MISSING entries: `data438-round1-lane{A-reprobe,B-refute}.md` and `ml2080-round1-lane{A-reprobe,B-refute}.md`.
6. **Owner decisions** to surface:
   - #2081's CodeQL;
   - the v0.16.0 PyPI approval (it ships defects #438 fixes; 0.16.1 is the alternative);
   - #437's breaking marker;
   - MEMORY.md's structural compaction;
   - the arc's later items C-A…D-G, from the predecessor handoff.

**Key context and traps:**
- The ruleset's `strict: true` means an armed, BEHIND PR waits forever: run `update-branch` with `expected_head_sha` after each move on main (#2074 took four cycles).
- Uploads are whole-file. Rebuild every file from `origin/main` right before opening a PR. The worktree sits at `dcfc024f` with untracked files, so `git diff origin/main -- <untracked>` fakes deletions; compare with `git show origin/main:<p> | diff - <p>`.
- Never name an OPEN id on the register's §2 status line (about L177). The crosscheck reads every id there as closed.
- /tmp is a ~1M-inode tmpfs. Lane trees filled it to 100% today. Brief lanes to prune, and check with `df -i /tmp`.
- `gh pr edit` is broken; use `gh api -X PATCH`. To re-arm with a curated squash body, run `gh pr merge --disable-auto`, then `--auto --squash --subject … --body-file …`.

## Verification commands (run from the worktree)
```
git status --short | wc -l        # ~42 entries; the register/REFERENCE/primer M's equal main's content
git fetch origin && python3 util/ad-hoc/register_open_set.py | grep 'rows |'   # 136 rows | 100 fixed | 36 open
python3 util/ad-hoc/register_status_crosscheck.py | tail -1                    # AGREE
python3 util/ad-hoc/2026-09-24_archive_round42_reports.py --check              # all OK; 4 archived locally
gh pr view 438 --repo pcalnon/juniper-data --json state,headRefOid,mergeStateStatus
gh pr view 2081 --repo pcalnon/juniper-ml --json state,mergeStateStatus
df -i /tmp | tail -1
```

## Git status
- **Branch:** `worktree-hazy-beaming-map` at `dcfc024f`, never committed. All work shipped through signed API commits.
- **Modified (tracked):** `docs/REFERENCE.md`, the register and the primer, each equal to main's current content.
- **Untracked:** the `util/ad-hoc/2026-09-24_*` scripts (most are on main now), and `util/ad-hoc/2026-09-24_round42_probes/` (on #2081's branch). The four new reports and the snapshot ship with this handoff's PR. That snapshot is the full tracking list; its "SECOND fix-forward" section is the appendix below.

## Appendix: the second fix-forward, item by item

See `reports/2026-09-24_defect-register-round-42/pending-items-snapshot-2026-09-24T1110Z.md`, section "SECOND fix-forward". Both lanes agree on H1 and M1. Lane B's H2 and Lane A's L1 are the same defect, described with different reach. #2080's PR body rejected one nit; the validation says that nit was right (N6).
