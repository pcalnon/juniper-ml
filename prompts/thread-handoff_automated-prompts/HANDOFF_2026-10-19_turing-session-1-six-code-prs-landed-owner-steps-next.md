# Handoff — turing Session 1: all six code PRs landed; owner steps next (C8 install, A1, Wi-Fi, F3 node mode)

- **From:** the 2026-10-17 to 2026-10-19 session on turing, named "turing dev env". It continues
  `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-18_turing-session-1-code-staged-landing-blocked-by-wifi.md`.
  That handoff was written before a context compaction, when landing was blocked by the Wi-Fi link. The same thread then
  landed everything once turing was on a 5 GHz radio.
- **Plan of record:** `notes/JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md` v1.1.0. Its §16, added
  in the PR that carries this file, holds the Session 1 record, the task status table and the errata. Task IDs below refer
  to the plan.

## Landed (all squash-merged to `main` after green)

| Task | PR | Merge | Notes |
|---|---|---|---|
| F5a | juniper-ml#2237 | `0364e05f` | `util/macvm_ctl.bash` gates the VM start on G-MEM |
| C8 item 4 | juniper-ml#2242 | `4d9c5c44` | the agent guard plus its owner-run installer. A CodeQL note (`py/import-and-import-from`) blocked the merge until it was fixed |
| G2 | juniper-ml#2245 | `8412ce3e` | the advisory "Verify AGENTS.md Last Updated" check was **red** at merge: UTC rolled over to 2026-10-19 mid-cycle, and auto-merge (which ignores advisory checks) beat the fix. #2247 carries the bump |
| B7 | juniper-ml#2247 | `6b3c53dc` | the signing preflight; also bumps AGENTS.md `**Last Updated**` to 2026-10-19 |
| B8 | juniper-ml#2249 | `0ca9d165` | erratum X7: the ed448 validator is deleted, R-B8 is pinned, and the 2026-07-16 note is SUPERSEDED |
| A5 | juniper-ml#2250 | `c263d346` | per-repo deploy-key and alias setup |

Every branch was checked before its PR opened with `util/ad-hoc/2026-10-18_turing_verify_landed_branch.py`: exact file
set, every blob equal to local, every commit `verified=true`.

## Owner steps

1. **Install the C8 guard**, from a terminal on a clean `main` checkout:
   ```bash
   bash util/install_claude_agent_guard.bash          # prints the entry
   bash util/install_claude_agent_guard.bash --apply  # installs it
   ```
   Once it is installed, agents can no longer use `gh api -X`/`-f` or `gh pr create`, so they land through
   `util/open_signed_pr.py`, `util/ad-hoc/2026-10-17_push_signed_with_retry.py` and `util/safe_merge.py`.
2. **A1**, then check with `python3 util/git_remote_alias_check.py`, which should exit 0:
   ```bash
   ! git -C ~/Development/python/Juniper/juniper-k8s remote set-url origin git@github_juniper-k8s:pcalnon/juniper-k8s.git && git -C ~/Development/python/Juniper/juniper-recurrence remote set-url origin git@github_juniper-recurrence:pcalnon/juniper-recurrence.git
   ```
3. **The network** (plan §16.3 E-NET):
   - ⚠ identify the radio broadcasting your network name with `Security: None` (2.4 GHz ch 10, the strongest signal on 2026-10-19);
   - fix roaming, move turing, or use Ethernet on `en7` (F2);
   - reserve turing's address (A6): `en0` moved from `.131` to `.180`.
4. **`~/.condarc`** sets `ssl_verify: false` and lists five third-party channels. Fix the file.
5. **F3 node mode:** quit the desktop apps and Docker Desktop, with no VM running, then say so. The agent runs the sampler
   with `--mode node` for at least 480 samples.
6. The rest of Owner block 1: C0, A2, A3, B2-B6, C1-C3, C5, C7, E4, A6, F1 and F2.

## Agent next

1. **E6 remainder:** errata X6 (stale "turing down" statements) and X10 (`/home/pcalnon` path literals in AGENTS.md and
   REFERENCE.md). Both are in plan §3. X10 edits AGENTS.md, so set `**Last Updated**` to today's UTC date.
2. **F3 node mode**, once the owner has set the state. Append its summary to `reports/2026-10-17_turing-headroom/`.
3. **Follow-up:** fold CodeQL `py/import-and-import-from` into `util/ad-hoc/2026-10-05_codeql_python_prescreen.py`. The
   one-off screen is `util/ad-hoc/2026-10-18_codeql_import_and_import_from_screen.py`.

## Landing notes (measured this session)

- **Gate each upload on the link.** Run `python3 -I util/ad-hoc/2026-10-18_turing_link_gate.py --upload <random 1.33 MB file>`,
  and land only when the upload takes under 5 s. SNR alone misleads: at SNR 9-12 dB on 5 GHz, uploads still took 1.2-2.2 s.
- **`main` moves every 10-20 minutes** while other sessions land. Each refresh (`update-branch` with `expected_head_sha`)
  costs about 9 minutes of CI.
- **`util/safe_merge.py --timeout N` disarms its auto-merge net** when it exits on that timeout. To arm and leave, use
  `gh pr merge N --auto --squash --match-head-commit <full sha>`, printing the full sha first.
- **Wait in the foreground.** The session's background PR-wait was reaped under memory pressure (swap about 18 GB), and is
  not restarted without the owner's say-so. Waits here used `gh run watch <run-id> --exit-status`.

## Verify the starting state

```bash
git fetch origin && git log -1 --oneline origin/main
gh pr view 2250 --repo pcalnon/juniper-ml --json state,mergeCommit
gh search prs --owner pcalnon --state open --json repository,number,title
python3 util/git_remote_alias_check.py                  # exit 1 until A1, on juniper-k8s and juniper-recurrence
printenv GIT_CONFIG_COUNT                               # 2 (C8 item 1)
python3 -I util/ad-hoc/2026-10-18_turing_link_gate.py   # the link
```

## Git state at handoff

- **Worktree:** `.claude/worktrees/gleaming-sauteeing-lamport` is a staging area; nothing in it was committed locally.
  Its branch is the local-only one used to stage the host-record PR.
- **Durable copies:** `~/.local/state/juniper/turing-session1/` holds `staged-code.tar`, the wiring inputs and PR bodies
  (`wire/<task>/`), and the network probe outputs.
