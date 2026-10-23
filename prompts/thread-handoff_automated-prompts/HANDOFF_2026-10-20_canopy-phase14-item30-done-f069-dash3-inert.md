# HANDOFF 2026-10-20 — P2 canopy Lane A: Phase 14 recorded. Item 30 is DONE: F-CANOPY-001, -012, -013, -018 and -032 are FIXED on canopy 571743db; F-CANOPY-028 reproduced (1 of 8 on the record) and is re-diagnosed; F-CANOPY-069 (P0) is filed: canopy's dashboard is inert under every dash 3.x. 1 open P0, 5 open P1, 10 open P2. Next are items 32, 31, 27, 25 and 28

> **SUPERSEDED 2026-10-21** by `HANDOFF_2026-10-21_canopy-phase15-items-31-32-done-f069-f028-fixed.md`.
> Its item 1 (juniper-ml#2291 merged 2026-10-20T13:59:34Z), item 2 (item 32: canopy#760, F-CANOPY-069 FIXED, the dash
> floor 4.0.0) and item 3 (item 31: canopy#761, F-CANOPY-028 FIXED, the manual's row idiom) are done, recorded as
> Phase 15 of `notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md`; its items 4 to 6 carry there as
> items 27, 25, 28, 29 and 26's second step, and its item 7 (the parent's items 5 and 7, the owner batch) as that
> handoff's last remaining item; new items 33 and 34.

**Written**: 2026-10-20 by the session in juniper-ml worktree `.claude/worktrees/serialized-noodling-cray` on host
turing (macOS; no trio; throwaway legs from the E2 tree), at a phase boundary, as its PR was opened.
**Consensus**: round 1 on 2026-10-20, three lanes (measurement re-creation, adversarial analysis, replay and
conventions): SOUND / SOUND-WITH-FIXES / SOUND-WITH-FIXES; round 2, two lanes on the corrections, changed one
action's parameter (item 31's pin window); round 3 on that pass changed wording only, so the review ended there
(ledger Phase 14, Consensus record).
**Parent**: `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-03_canopy-consolidated.md`, authoritative for P2.
Its items 5 and 7 and the owner batch O1–O17 carry over. This file supersedes
`HANDOFF_2026-10-19_canopy-phase13-manual-sweep-five-p2s-now-p1-item-30-owed.md`.
**Merge approval**: the owner granted it for this session's PR. It is NOT carried: ask again.

## Goal statement (paste as the new thread's first prompt)

Continue P2 Lane A (the juniper-canopy E2E validation arc) from
`prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-20_canopy-phase14-item30-done-f069-dash3-inert.md`
(juniper-ml). Read it in full, then the parent `HANDOFF_2026-10-03_canopy-consolidated.md`. Run the verification
commands first. Merge approval is not carried: ask before the first merge. Items 31 and 32 are canopy code (fix
PRs on juniper-canopy, verified on a leg; a leg on this host runs dash 4.x until 32 lands); items 25 and 28 need
the trio on the Linux host; item 27 needs a demo leg that trains (this host can serve it).

**Completed:**

- **juniper-ml#2278 merged** on 2026-10-20T02:22:45Z: Phase 13 of
  `notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md` and
  `HANDOFF_2026-10-19_canopy-phase13-manual-sweep-five-p2s-now-p1-item-30-owed.md`.
- **The ledger's Phase 14** (`notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md`, 2026-10-20) does
  item 30 on turing, from canopy `main` `571743db` proved by git blob id, on legs under dash 4.4.1 with Chrome 145
  under Playwright:
  - **FIXED**: F-CANOPY-018 (C2.9-05: the toast stands, Apply disables, no latch), F-CANOPY-001 (C2.1-01/-02: the
    glyph syncs after a reload), F-CANOPY-012 (M-NETWORK-EDITOR-17: 4 of 4 targets; the manual's semicolon and
    newline flat forms are rejected as Phase 13's residue said), F-CANOPY-013 (M-NETWORK-EDITOR-09/-13: real index
    and count), F-CANOPY-032 (M-WORKERS-02: the alert renders with cascor down, not under the control-stream
    induction; closed on the F-CANOPY-027 reading). M-METRICS-03 PASS on a live cascor run.
  - **F-CANOPY-028 stays OPEN (P1), re-diagnosed**: 1 of 8 drives on the record lost a pin (run 1 is unrecorded);
    the complete record shows a table re-render from a stale pin set persisted by the store writer, which
    canopy#533 did not address; a validator lane's four arms and the reconciler's five kept arms show the same
    second render 7.9–10.2 s after the mount render, and every pin made after it survived: the window is the
    seconds before it.
  - **F-CANOPY-069 (P0, new)**: three callback pairs with one `allow_duplicate` output and identical inputs collide;
    dash 3's renderer drops the whole graph, dash 4 does not validate. Inert on 3.0.4/3.2.0/3.3.0/3.4.0, alive on
    4.4.1 (`reports/e2e-canopy-2026-09-02/item30-turing/dash_version_matrix.json`). canopy's floor is
    `dash>=3.0.0`; its `conda_environment.yaml` pins 3.3.0; the lock, CI and the Linux host are on 4.x.
  - **Counts**: 80 findings, 61 fixed, 1 accepted, 2 withdrawn, 16 open: 1 P0 (F-CANOPY-069), 5 P1 (F-CANOPY-028,
    -064, -065, F-CASCOR-001, -002), 10 P2.
- **This session's PR** carries `notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md`,
  `notes/JUNIPER_2026-08-08_JUNIPER-CANOPY_E2E-CLICK-BY-CLICK-TEST-MATRIX.md`, this file, the SUPERSEDED banner on
  `HANDOFF_2026-10-19_canopy-phase13-manual-sweep-five-p2s-now-p1-item-30-owed.md`, the pointer in
  `HANDOFF_2026-10-03_canopy-consolidated.md`, the P2 row of `HANDOFF_2026-10-03_INDEX_consolidated-development-paths.md`,
  the records under `reports/e2e-canopy-2026-09-02/item30-turing/` (JSON and the force-added `transcripts/`; the
  screenshots stay on turing, LFS), Phase 14's consensus records and the scripts `util/ad-hoc/2026-10-20_*`. Find it with
  `gh pr list --repo pcalnon/juniper-ml --head docs/canopy-e2e-phase14 --state all`.

**Remaining, in order:**

1. **Land this session's PR** if it has not merged: `python3 util/wait_for_checks.py`, query
   `reviewThreads(isResolved:false)`, ask the owner, then `python3 util/safe_merge.py --execute` and read its
   `MERGED` line. Afterwards re-check `origin/main`:
   `python3 -B util/ad-hoc/e2e_finding_triage.py | grep -c -E '^FIXED +P[012] +F-CANOPY-0(01|12|13|18|32) '` should
   print 5 (two of those headers wrap across lines, so a `grep` on the header line alone prints 3).
2. **Item 32, F-CANOPY-069** (canopy code): read which member of each colliding pair runs under dash 4.4.1; fix the
   pairs (distinct inputs or one callback; `running=` for the progress alerts); decide the floor; correct
   `conda_environment.yaml`; a test over `app.callback_map`; verify with
   `util/ad-hoc/2026-10-20_canopy_dash_duplicate_outputs_probe.py` on a dash 3.3.0 leg of the fix (ALIVE closes it).
3. **Item 31, F-CANOPY-028** (canopy code): the writer acts on a user toggle only; a stale-re-render test; re-drive
   `util/ad-hoc/2026-10-20_item30_fixwave_redrive.py --step f028 --f028-arms early,mid --f028-repeat 3` on the fix
   (a demo leg on dash 4.x). And canopy's `docs/USER_MANUAL.md` Patch Weights sentence (`:493-501` at `571743db`:
   the row idiom for `output_weights`).
4. **Item 27** (the Live Switch allow arm): a demo leg on this host serves it
   (`bash util/ad-hoc/2026-10-20_turing_canopy_leg.bash up 8062 demo http://127.0.0.1:9 ~/.local/state/juniper/turing-e2/venvs/JuniperCanopy1-dash44/bin/python`,
   then `util/ad-hoc/2026-09-23_f055_f025_allow_arm_demo_drive.py` adapted to the chrome channel and the CDN route).
5. **Items 25 and 28** on the Linux host, against the trio (ledger Phase 12). **Item 29**, the Linux host.
6. **Item 26's second step** once the owner rules (O17).
7. Then the parent's items 5 and 7, and the owner batch O1–O17.

**Traps learned:**

- **A leg on dash 3.x drives nothing** (F-CANOPY-069). Check `/dashboard/_dash-dependencies` for duplicate ids and
  the console for `Duplicate callback outputs` before blaming a driver; the launcher prints the dash it found.
- **canopy falls back to demo mode when cascor is unreachable at boot** (`main.py:439-447`): a cascor-down arm is
  cascor up → canopy up → cascor down, never canopy up against nothing.
- **On turing Chrome cannot fetch cdn.jsdelivr.net** (per-app filter; curl can). The drivers abort that one request
  in the browser; pages are unstyled; VIS halves are not scored. Do not fetch it through another binary.
- **Wait for the mount.** An edit before the mount seed lands is overwritten by it (a typed learning rate reverted
  at +2 s); the drivers settle 25 s and poll every transition with a 30 s budget.
- **A later run overwrites a step's key in the record JSON.** Name a new `--out` for every run whose record must
  survive (run 1's F-CANOPY-028 loss is unrecorded: its JSON was overwritten and its transcript shows only a
  store read). `transcripts/*.log` is gitignored: `git add -f` it, or list the files on the landing command.
- **The guard refuses** `for` loops with `gh`/`unzip`, `awk` programs, `$(…)` in command text and env prefixes;
  one plain command per call, interpreters by path, logic in a script.
- **turing has no signing**: land through `util/open_signed_pr.py` (small files) and
  `util/ad-hoc/2026-10-17_push_signed_with_retry.py` (the ledger); build shared files from a fresh `origin/main`
  copy and re-apply with `util/ad-hoc/2026-10-20_phase14_item30_apply.py --root <copy>` plus the round scripts.

## Verification commands

```bash
cd /Users/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/<your worktree>   # or the Linux host's path
git status --short; git log --oneline -3
gh pr list --repo pcalnon/juniper-ml --head docs/canopy-e2e-phase14 --state all --json number,state,mergedAt
python3 -B util/ad-hoc/e2e_finding_triage.py | tail -8   # 80 / 61 / 1 / 2 / 16; P0 1; P1 5; P2 10
python3 -B util/ad-hoc/e2e_finding_triage.py --open-only | grep -c '^OPEN   P1 '   # 5
grep -n '^## Phase 14' notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md
grep -c 'F-CANOPY-069' notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md
python3 -I -c "import json; m=json.load(open('reports/e2e-canopy-2026-09-02/item30-turing/dash_version_matrix.json')); print({k: v['verdict'] for k, v in m.items()})"   # four INERT, one ALIVE
ls ~/.local/state/juniper/turing-e2/venvs/   # on turing: JuniperCanopy1{,-dash304,-dash32,-dash34,-dash44}
lsof -nP -iTCP -sTCP:LISTEN | grep -E ':(8101|8202|8051|8052|8053|806[0-9]|8222) '   # on turing: nothing; on the Linux host: the trio up (never touch it)
```

## Git state

- **juniper-ml:** branch `docs/canopy-e2e-phase14`, landed from turing through the API as signed commits.
  Worktree `serialized-noodling-cray` holds the same files uncommitted (the frozen drafts the consensus rounds
  reviewed are local commits that never leave the host).
- **juniper-canopy, cascor:** no branches from this session; read through the GitHub API and the E2 tree
  (canopy `main` `571743db`; cascor 0.12.0 as rsynced on 2026-10-19).
- **Services:** none left on this host; the legs were torn down (`… down <port>`). The scratch venvs and the
  snapshots under `~/.local/state/juniper/turing-e2/legs/` remain.

## Changed by this session

- **Created:** this file; `util/ad-hoc/2026-10-20_turing_canopy_leg.bash`;
  `util/ad-hoc/2026-10-20_turing_cascor_leg.bash`; `util/ad-hoc/2026-10-20_e2_tree_blob_sha_check.py`;
  `util/ad-hoc/2026-10-20_item30_fixwave_redrive.py`; `util/ad-hoc/2026-10-20_canopy_dash_duplicate_outputs_probe.py`;
  `util/ad-hoc/2026-10-20_cascor_leg_prepare_investigating.py`; `util/ad-hoc/2026-10-20_phase14_item30_apply.py`;
  `util/ad-hoc/2026-10-20_phase14_rebuild_shared_files_for_landing.py` (rebuilds the shared files from `origin/main`
  by replaying the passes, for the API landing); `util/ad-hoc/2026-10-20_push_signed_with_body_retry.py` (the
  large files' signed commits, each with the session's trailer, retried through the link);
  `reports/e2e-canopy-2026-09-02/item30-turing/` (records and transcripts; the 20 screenshots stay on turing under
  the same path, not landed: PNGs are LFS pointers here);
  `reports/e2e-canopy-2026-09-02/drafts/lane14*_phase14_ledger_brief.md`;
  `reports/e2e-canopy-2026-09-02/consensus/2026-10-20_validator_reports_phase14_round*.md`;
  `util/ad-hoc/2026-10-20_phase14_ledger_round*_corrections.py`.
- **Modified:**
  - `notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md`: Phase 14; the headers of F-CANOPY-001,
    -012, -013, -018, -028 and -032 and a dated blockquote in each; the F-CANOPY-069 entry;
  - `notes/JUNIPER_2026-08-08_JUNIPER-CANOPY_E2E-CLICK-BY-CLICK-TEST-MATRIX.md`: eleven status cells;
  - `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-03_canopy-consolidated.md`: the Lane A pointer;
  - `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-03_INDEX_consolidated-development-paths.md`: the P2 row;
  - `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-19_canopy-phase13-manual-sweep-five-p2s-now-p1-item-30-owed.md`:
    the SUPERSEDED banner.
- **Outside the repo**, in auto-memory: `MEMORY.md`, `canopy-e2e-arc-state.md`, `turing-host-profile.md`,
  `turing-little-snitch-per-app-filter.md`.
