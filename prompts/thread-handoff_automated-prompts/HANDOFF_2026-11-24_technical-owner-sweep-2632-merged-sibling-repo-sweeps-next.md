# Handoff: technical-owner sweep -- ml#2632 MERGED; the sibling repos' sweeps next

**Date**: 2026-11-24 (written about 13:40Z)
**From**: session eb0525 ("overtoad-rename-2606-merged-technical-owner-sweep-next"), worktree
`juniper-ml/.claude/worktrees/wondrous-conjuring-lamport`
**Predecessor**: `prompts/thread-handoff_automated-prompts/HANDOFF_2026-11-24_overtoad-rename-2606-merged-technical-owner-sweep-next.md`
(archived by ml#2632)
**Memory**: `project_overtoad_rename_pr_repair_2026-11-23.md` (the SWEEP MERGED paragraph), `reference_ci_merge_mechanics_hub.md`
(the fail-open `unresolved_threads()` line)

---

## Goal

The 8 sibling repos' rename PRs were repaired with the same `classify` (`util/ad-hoc/2026-11-23_overtoad_rename_repair.py`)
that missed 340 technical owners in juniper-ml. Sweep each sibling repo the way ml#2632 swept juniper-ml: one signed PR per
repo. Merge approval does not carry over from a handoff, so ask the owner for it in the new session.

## Completed this session

- **ml#2632 MERGED** 2026-11-24 13:20:45Z as `c93914a7`:
  - 340 tokens in 112 files; built on `d7709ef7`, uploaded as 5 signed commits on `8e754305`; update-branch over ml#2631;
    `safe_merge` run from the PR's branch.
  - By kind: CODE 40, UNIX 84, GITHUB 21, FIELD 81, ROLE 108, GPG+TECH 6.
  - Main's post-merge runs on `c93914a7` all succeeded: CI/CD Pipeline, CodeQL Analysis, Post-Merge Main Verification.
- **The worst defect, now fixed**: `util/safe_merge.py:599` `unresolved_threads()` queried `repository(Overtoad: ...)`.
  GitHub answers "Field 'repository' is missing required arguments: owner" and the probe returns `[]`, so from
  `5a049144` to `c93914a7` main's safe_merge could not see review threads. A real query confirmed it both ways.
  - Also restored: 17 GraphQL queries in 10 ad-hoc scripts, and an `owner-email` key that a probe matches against
    lowercased text.
- **Peers**:
  - the backup lane (`2abfbf`) reviewed its 26 files and found 6 of the 13 late additions: the test needle, two
    mutant labels, and three tokens in other files;
  - flood-4 (`17d26a`), one-artifact (`ffffd3`) and R-OBS-SC-2 (`007878`) held merges for the window, which is closed.
- **One sibling finding, handed off**: recurrence `publish-recurrence-{app,model,client}.yml:22` reads
  "Overtoad = pcalnon" (the trusted publisher's owner). The one-artifact lane took it as a recurrence-port item. Do not
  duplicate it.
- **MEMORY.md** went from 24,236 to 22,401 bytes: two reference clusters moved verbatim into
  `reference_process_runtime_traps_hub.md` and `reference_worktree_precommit_traps_hub.md`. The link set was proven
  complete (166 links before, none lost).

## Remaining work

1. **Sibling sweeps.** For each repo, the rename merge commit (base = its parent):

   | Repo | Merge (PR) |
   |---|---|
   | juniper-cascor | `e9c86f83` (#772) |
   | juniper-data | `2ad7b7b5` (#547) |
   | juniper-data-client | `246b3a4d` (#267) |
   | juniper-cascor-client | `a17109c2` (#201) |
   | juniper-cascor-worker | `dcd2c2a9` (#234) |
   | juniper-canopy | `1e504572` (#830) |
   | juniper-harcot | `dd3b0bd3` (#28) |
   | juniper-deploy | `552756a1` (#281); repair #285 merged later, so use main as head |
   | juniper-recurrence | `93a28202` (#237); repair #238 merged later, so use main as head |

   Steps for each repo:
   - Run `python3 <juniper-ml>/util/ad-hoc/2026-11-24_technical_owner_candidates.py --repo <checkout> --base <merge>^
     --head <merge> --out ...` in a checkout of that repo. Its `ARC_TOOLS` set is juniper-ml's and is harmless elsewhere.
   - Review the same slices ml#2632 did. `2026-11-24_technical_owner_decisions.py`'s docstring lists them.
   - Read the repo's tests for needles that pair with a restored message.
   - Then decisions, restore (`--avoid` that repo's open high/error CodeQL alert paths), verify, and the repo's full tests.
   - Ask the session that owns the touched files to review its hunks.
   - Check main of each repo first: a checkout can be stale. The local primaries showed `{Overtoad}` API paths that main
     had already restored.
2. **Owner decisions to surface**, none of them ours:
   - R14 and R15, the sentry-sdk<3 caps (rows R14/R15 of
     `notes/JUNIPER_2026-11-23_JUNIPER-ECOSYSTEM_R-OBS-SC-2-FOLLOW-UPS-REMAINING-TASKS.md`);
   - canopy#831, the Dependabot claude-code-action bump, open with merge state UNKNOWN;
   - CodeQL #1059/#1060 (high, `py/clear-text-storage-sensitive-data`) at `util/ad-hoc/2026-10-05_gate_regression.py:415/:417`:
     fix or dismiss.
3. **MEMORY.md** is 22.4 KB against the 20 KB target. The next cut means retiring a closed arc's line into
   `project_closed_arcs_hub.md`. The largest line is the Canopy E2E arc's (2.1 KB), but that lane is active, so ask
   first.
4. **Archive this handoff.** It is untracked in this worktree.

## Key context and traps

- **`classify`'s blind spots, all seen in juniper-ml**:
  - possessives ("the env file's owner");
  - lists ("mode, owner");
  - verbs ("change owner");
  - "its/their/whose owner" followed by a verb;
  - field labels ("Owner: juniper-ml", "Owner repo", "Owner-class");
  - arguments and keys inside code strings (GraphQL `repository(owner:`, JS `{owner: ...}`, `"owner-email"`).
- **High-recall review lanes still missed code-string tokens.** The full test run caught a test needle (`owner root`) for
  a restored message, and the file-owning session found two mutant labels.
- **Use the blobs API, not contents, for files over 1 MB.** The contents API returns no inline content for them, so use
  `git/blobs/<sha>`.
- **The command guard** refuses a `.github/` path, `xargs` feeding git, or a complex git form in a Bash command. Put such
  steps in a script file.
- **Evidence to keep** (retention rule): `tmp/tech-owner-sweep/` in this worktree. It holds the 7,741-row candidate TSV,
  the four lanes' flags, the review slices, the run logs and the merge checks.

## Verify the starting state

```bash
gh pr view 2632 -R pcalnon/juniper-ml --json state,mergeCommit   # MERGED c93914a7
git -C <a juniper-ml checkout> show origin/main:util/safe_merge.py | grep -n 'repository(owner:'   # line 599
gh pr list -R pcalnon/juniper-ml --state open    # nothing of this arc open
```

## Git status

Worktree `wondrous-conjuring-lamport`, branch `worktree-wondrous-conjuring-lamport`, HEAD `8e754305` (main is now
`c93914a7` or later). Its 113 tracked edits are uncommitted, and all of them are on main through ml#2632. Do not commit
from it. The untracked files are the sweep's files, already on main (8 under `util/ad-hoc/`, plus the predecessor
handoff), and this handoff. Nothing is staged.
