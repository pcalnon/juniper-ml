# Handoff — turing Session 1: owner rulings made, all six code tasks staged and verified, landing blocked by turing's Wi-Fi link

- **From:** the 2026-10-17/18 session on turing, named "turing dev env". It continues `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-17_turing-prs-landed-session-1-partial-owner-c8-a1-d6-next.md`.
- **Plan of record:** `notes/JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md` v1.0.0. Task and gate IDs below refer to it.

## Owner rulings this session

- **D6, how packages reach Intel turing:** conda-forge plus vendor binaries.
  - A dedicated conda env, `JuniperHostTools`, holds the tools; only the named binaries are symlinked into `~/.local/bin`, which is already first on PATH.
  - sops comes from its release binary.
  - ykman comes from pip under Python 3.13.
  - pinentry-mac is the single Homebrew exception. It was poured bottle-only with `--ignore-dependencies`, with gnupg and pinentry pinned and owner sign-off. The bottle's recorded runtime deps (libgpg-error 1.51, libassuan 3.0.1, gettext 0.23.1, libunistring 1.3) are all older than turing's installed versions.
- **C8:** apply D11 item 1 (the env block) now; deliver item 4 as a tested PreToolUse hook PR that the owner installs.
- **Merge approval** is granted for every PR in this work arc. Merge serially with `util/safe_merge.py --pr N --execute`.
- **Root cause:** the owner rejected "ExpressVPN is the cause", since yamaguchi uses the same VPN. Diagnosis and remediation focus on the local network. See finding 1.

## Done on the host

- **C8 item 1.** `~/.claude/settings.json` `env` carries `GIT_CONFIG_COUNT=2`, `commit.gpgsign=false` and `tag.gpgsign=false`. `git config --show-origin` reports both as `command line: false`, live in-session. Backup: `~/.claude/settings.json.bak-2026-10-17-pre-C8`.
- **H0.** `~/.claude.json` has no MCP servers: the user scope and both project scopes are empty. There is no `.mcp.json` under Juniper. A 23-entry `mcpServers` block in `~/.claude/settings.json` is **inert**: per the debug-your-config docs, settings.json never reads that key. It still holds both plan-named unvetted servers; the owner may delete the block.
- **D0 and D1-tools (D6 form).** `JuniperHostTools` holds:
  - python 3.13.16 and nodejs 26.10.0;
  - coreutils 9.12, shellcheck 0.11.0, yamllint 1.38.0, actionlint 1.7.12;
  - age 1.3.2, go-yq 4.54.1, iperf 3.20, markdownlint-cli2 0.23.3.

  Links:
  - The `~/.local/bin` symlinks are `timeout`, `shellcheck`, `yamllint`, `actionlint`, `age`, `age-keygen`, `yq` and `iperf3`.
  - `markdownlint-cli2` is a 2-line wrapper that runs the env's node, because the first solve picked nodejs 12.4.0.
  - sops 3.13.3 is at `~/.local/opt/sops/v3.13.3/`, with its sha256 checked against the release's checksums.txt; cosign was unavailable to check the signature.
  - **ykman 5.9.2 is installed** in a venv at `~/.local/opt/ykman` (the env's Python 3.13) and linked into `~/.local/bin`. cryptography is pinned to `48.0.1`, the last release with an Intel macOS (universal2) wheel; 50.x ships only an sdist that needs Rust. pipx had hung in its own pip bootstrap. With pinentry-mac and ykman both in, B1's agent part is complete.

  The env spec draft is `~/.local/state/juniper/turing-session1/hosttools-environment.yml`. It should land as `conf/hosts/turing/hosttools-environment.yml`.
- **B1, agent part.** pinentry-mac 1.3.1.1 is installed. `gpg-agent.conf` now reads `pinentry-program /usr/local/bin/pinentry-mac`, the agent was restarted, `gpgconf --check-options gpg-agent` passes, and `GETINFO flavor` answers `mac`. Backup: `~/.gnupg/gpg-agent.conf.bak-2026-10-17-pre-B1-pinentry`. B1-verify, a real PIN prompt, stays owner-run with B3.
- **F3, dev mode.** Sampling started 2026-10-17T23:19Z as pid 1848, detached under launchd, and **died silently after 307 samples**, at 2026-10-18T04:27Z. There was no reboot, sleep or kill on record, so `set -e`/pipefail is the likely cause. The sampler is now hardened (no `-e`/pipefail, plus an EXIT trap that logs rc and sample count), and it **restarted at 17:29Z as pid 29538 with `--samples 180`**, appending to the same file for a total of 487.
  - **Partial result (309 samples):**
    - available memory p5 1856 / p50 3124 / p95 5420 MiB;
    - swap used p50 17784 MiB;
    - Docker Desktop running in 309 of 309 samples;
    - **G-MEM pass rate 0%** at the D1 6 GiB VM.

    In dev mode turing cannot host the VM; D1's admin-only fallback applies.
  - Data goes to `~/.local/state/juniper/turing-headroom/dev.tsv`, written by a copy of `util/ad-hoc/2026-10-17_turing_headroom_sampler.bash`.
  - Summarize with `python3 util/ad-hoc/2026-10-17_turing_headroom_summarize.py ~/.local/state/juniper/turing-headroom/dev.tsv --out reports/2026-10-17_turing-headroom/summary.md`.
  - Node mode is still to do: the owner quits desktop apps and Docker Desktop, then starts the sampler with `--mode node`.
- **Network diagnosis.** It was done with `util/ad-hoc/2026-10-17_turing_network_probe.bash`. A Wi-Fi power cycle was agent-run with owner approval, but macOS re-joined the same weak radio.

## Code: staged and verified, not landed

| Task | Files | Suite | Mutants |
|---|---|---|---|
| F5a | `util/macvm_ctl.bash`, `tests/test_macvm_ctl.py`, `util/ad-hoc/2026-10-17_turing_f5a_mutation_check.py`, `util/ad-hoc/2026-10-17_turing_wire_suite.py` | 54 | 22/22 |
| C8 | `util/claude_agent_guard.py`, `util/install_claude_agent_guard.bash`, `tests/test_claude_agent_guard.py`, `util/ad-hoc/2026-10-17_turing_c8_guard_mutation_check.py`, `util/ad-hoc/2026-10-17_turing_c8_guard_review_probe.py` | 37 (321 rows) | 18/18, plus 71/71 in the lead's black-box review |
| G2 | `util/git_remote_alias_check.py`, `tests/test_git_remote_alias_check.py`, `util/ad-hoc/2026-10-17_turing_g2_mutation_check.py` | 82 | 16/16 |
| B7 | `util/headless_signing_preflight.bash`, `tests/test_headless_signing_preflight.py`, `util/ad-hoc/2026-10-17_turing_b7_mutation_check.py` | 51 | 18/18 |
| B8 | delete `util/test_gpg_signing.bash`; add `StaleKeyIdTest` (`wire/b8-rb8-test.py.txt`) to the B7 suite; put `b8-note-banner.md` on `notes/JUNIPER_2026-07-16_JUNIPER-ECOSYSTEM_CODE-SIGNING-KEY-MIGRATION-STATUS.md` and set its Status to SUPERSEDED; extend the B7 REFERENCE bullet with R-B8 | (B7 suite) | — |
| A5 | `util/juniper_repo_ssh_setup.bash`, `tests/test_juniper_repo_ssh_setup.py`, `util/ad-hoc/2026-10-17_turing_a5_mutation_check.py` | 54, 1 skip | 16/16 |

- All six suites pass locally on turing; 292 tests ran.
- `SKIP=gitleaks pre-commit run --files ...` passes for F5a, and the agents ran it for the others.
- **Copies:**
  - the untracked files in worktree `.claude/worktrees/gleaming-sauteeing-lamport`;
  - the agent worktrees `agent-a8faa550d94047746` (F5a), `agent-add4944f3d586c0ca` (C8), `agent-a8b5627df8b3e0893` (G2), `agent-a1620477d243877a9` (B7) and `agent-ab433a392310ffec0` (A5);
  - a durable snapshot in `~/.local/state/juniper/turing-session1/`: `staged-code.tar` with 25 files, plus `wire/<task>/{ci,test,util*,changelog}.txt` and `body.md` (the PR body) for each task.
- **F5a: PR juniper-ml#2237 is open, with auto-merge (squash) armed.**
  - `REFERENCE.md` failed 10 of 10 attempts on the ch 3 radio. It landed first try (`fb36761f`, all 8 blobs verified against local) once turing was briefly on 5 GHz ch 153, where the 1.33 MB upload test took 1.77 s.
  - `safe_merge` refreshed the base server-side. That made head `1e6fee4f`, a GitHub-signed merge with `main` `2719f7f3` (`verified=true`). It then armed auto-merge before the link dropped and `gh` lost api.github.com.
  - GitHub completes the merge when the required checks go green. Check with `gh pr view 2237 --json state,mergeCommit`.
  - **18:5xZ:** all 22 checks passed, but the PR went `BEHIND` again, because `main` moved to #2238 and the branch rules require an up-to-date branch. A second server-side `update-branch` made head `d89d889f`, signed (`verified=true`), with auto-merge still armed. If `main` moves again before CI re-passes, repeat with `gh api -X PUT repos/pcalnon/juniper-ml/pulls/2237/update-branch -f expected_head_sha=<full head sha>`, or run `util/safe_merge.py`, which loops up to 3 refreshes.
  - **Claude Code reaped this session's background PR-wait** because the system was critically low on memory (swap 19.3 of 20.5 GB). It is not to be restarted without the owner's say-so. The same reaper may explain the first F3 sampler's silent death. `CLAUDE_CODE_DISABLE_BG_SHELL_PRESSURE_REAP=1`, set at Claude Code startup, turns it off.
  - `main` had moved by #2232 (AGENTS, CHANGELOG, REFERENCE), but in other hunks, so the merge is a clean three-way merge.

## Findings

1. **The 499s are caused by turing's Wi-Fi link, not ExpressVPN.**
   - **Sticky client.** turing sticks to the weakest radio of its own network: 2.4 GHz ch 3, the only 802.11ax unit, at about −72 dBm with an SNR of 4-10 dB. The same network name is available on ch 1 at −42 dBm, ch 10 at −44 dBm and 5 GHz ch 153 at −48 dBm.
   - **Overlapping channels.** The 2.4 GHz radios sit on channels 1, 3, 5 and 10, and 1/3/5 overlap.
   - **Measured on that link:**
     - networkQuality: 31 Mbps up (16 flows) but **36 Kbps down**, with 2.3-3.9 s of loaded latency;
     - pinging the gateway one hop away: 0-27% loss, with RTTs up to 2.3 s;
     - a single TCP flow up through the tunnel: 150-250 KB/s, so a 1.33 MB body (REFERENCE.md as base64) takes **8.97 s**, while 180 KB takes 0.73 s.
   - **Why it fails.** GitHub's GraphQL frontend drops a request that runs past about 7-10 s.
   - **Remediation is physical**, and the owner chose "move turing / fix roaming": a roaming assistant around −70 dBm, band steering, and a 1/6/11 channel plan. Ethernet on `en7` (task F2) is the robust alternative.
   - **Gate before landing:** the probe shows SNR ≥ 20 dB and clean pings, or the 1.33 MB upload test finishes in under 5 s:
     ```bash
     curl -s -o /dev/null -w '%{time_total}\n' --data-binary @<1.33MB random file> https://speed.cloudflare.com/__up
     ```
2. **⚠ A radio on ch 10 broadcasts the owner's network name with `Security: None`.** It is either a misconfigured extender or guest network, or an evil twin. The owner should identify it.
3. **ExpressVPN's network lock is on**: traffic bound outside the tunnel gets "No route to host". The ISP path cannot be measured separately unless the lock is lifted.
4. **`~/.condarc` sets `ssl_verify: false`** and lists five third-party channels. Installs this session overrode both (`CONDA_SSL_VERIFY=true`, `--override-channels -c conda-forge`). The owner should fix the file.
5. **MacPorts is dead.** It was built for darwin 18, every `port` command errors, and its 2019 binaries are early on PATH. This supports D5 (drop `/opt/local/bin`).
6. **G-MEM fails on all three conditions today**: 4405 MiB available against 10240 needed, 17 GB of swap, and Docker Desktop running. `bash util/macvm_ctl.bash status` (once F5a lands) is the reading.
7. **Once the C8 guard is installed**, it denies `gh api` with `-X`/`-f`/`--input`, `gh pr create` and `gh pr merge`, and any reference to `.ssh` or `.gnupg`. So:
   - land with `util/open_signed_pr.py`, which opens the PR immediately with the first commit, then `util/ad-hoc/2026-10-17_push_signed_with_retry.py`, then `util/safe_merge.py`;
   - the previous handoff's checks (`grep ~/.ssh/config`, `stat ~/.ssh/...`) become owner-run, and `util/git_remote_alias_check.py` replaces most of them.

   The guard's self-protection also means the owner installs it from a terminal, not through an agent.
8. **Plan updates owed (E6):**
   - C4, A8, A7 and B1's config edits become OWNER once C8 is installed; all are done today.
   - D6 is now conda-forge, and §2.2 needs the network facts.
   - The plan header still says prompt133 is "not versioned", which is stale since #2228.
9. **A pre-push hook in a linked worktree inherits `GIT_DIR`.** G2 scrubs git's local env vars for this, and a real-hook test pins it.
10. **shellcheck 0.11.0** (the conda env) raises a false-positive SC2218 that the repo's v0.10.0.1 pin does not. Treat the pre-commit hook as the gate.
11. **Correction:** the `mcpServers` block has 23 entries, not the 25 stated mid-session.

## Next

**Owner:**

- Fix the link (finding 1), and say when it's done. The agent re-probes.
- **A1** (still pending):
  ```bash
  ! git -C ~/Development/python/Juniper/juniper-k8s remote set-url origin git@github_juniper-k8s:pcalnon/juniper-k8s.git && git -C ~/Development/python/Juniper/juniper-recurrence remote set-url origin git@github_juniper-recurrence:pcalnon/juniper-recurrence.git
  ```
  Then `python3 util/git_remote_alias_check.py` should exit 0.
- After the C8 PR merges, run from a terminal on a clean `main` checkout:
  ```bash
  bash util/install_claude_agent_guard.bash          # prints the entry
  bash util/install_claude_agent_guard.bash --apply  # installs it
  ```
- The rest of Owner block 1: C0, A2, A3, B2-B6, C1-C3, C5, C7, E4, A6, F1 and F2.

**Agent, once the link passes the gate:**

1. **F5a.** Re-read the head, then push `docs/REFERENCE.md`. It must be byte-identical to the F5a staging (`staged-code.tar`), and only if `origin/main` is still `909da222` or no later commit touched the four wired files. Otherwise rebuild the F5a wiring on the new `main` with the helper and re-push all four. Then:
   ```bash
   gh pr create --base main --head feat/turing-f5a-macvm-ctl --title "<as in body.md>" --body-file ~/.local/state/juniper/turing-session1/wire/f5a/body.md
   python3 util/safe_merge.py --pr N --execute
   ```
2. **Then C8, G2, B7, B8 and A5, one PR each, serially.** Recommended order: C8 first, so the owner can install the guard early. For each one:
   - `git checkout -B land/<task> origin/main`;
   - copy in the task's files;
   - run `python3 util/ad-hoc/2026-10-17_turing_wire_suite.py --suite tests/test_<x>.py --ci-block wire/<t>/ci.txt --test-bullet wire/<t>/test.txt --util-bullet wire/<t>/util*.txt --changelog wire/<t>/changelog.txt`;
   - run the suite and `tests/test_ci_test_wiring_drift.py`;
   - `SKIP=gitleaks pre-commit run --files ...`;
   - create the branch, push one file per commit, open the PR, then `safe_merge`.

   B8 has no new suite, so wire it by hand.
3. **After F3's dev run ends:** summarize it into `reports/2026-10-17_turing-headroom/`. Ask the owner to set node mode, then run `--mode node`.
4. **Host-record PR:**
   - `conf/hosts/turing/hosttools-environment.yml`;
   - `util/ad-hoc/2026-10-17_turing_network_probe.bash`;
   - the F3 sampler and summarizer;
   - this handoff;
   - the E6 plan errata.
5. **ykman** in a venv (see above).

## Rules carried forward

- **Never commit and push from turing.** Land everything as API-signed commits.
- **After any API error, re-read the ref.** Whole-file uploads must start from the head being committed onto.
- **No agent credential probes.**
- **On turing:** use `SKIP=gitleaks`. No `brew install` without a dry run and owner sign-off. Never run a brew upgrade.
- **Before landing, check the link** (finding 1). A 499 at about 7 s on a large file means the link, not the code.
- **Local test baseline:** 26 suites fail on turing exactly as they do on clean `main` (Linux-only tools). Compare against `main`.

## Verify the starting state

```bash
git fetch origin && git log -1 --oneline origin/main                    # 909da222 or later
gh api "repos/pcalnon/juniper-ml/compare/main...feat/turing-f5a-macvm-ctl" --jq .ahead_by   # 7 (until REFERENCE.md lands)
gh search prs --owner pcalnon --state open --json repository,number,title
printenv GIT_CONFIG_COUNT                                               # 2 (C8 item 1)
command -v timeout shellcheck yamllint actionlint sops markdownlint-cli2   # all under ~/.local/bin
ls ~/.local/state/juniper/turing-session1/                              # staged-code.tar, wire/, probe outputs
ps -p 1848 -o etime,command                                             # F3 dev sampler (gone once 480 samples are done)
bash util/ad-hoc/2026-10-17_turing_network_probe.bash --no-load         # the link gate
```

## Git state at handoff

- **Worktree:** `.claude/worktrees/gleaming-sauteeing-lamport` is on the local-only branch `land/f5a-macvm-ctl`, based on `origin/main` `909da222`.
  - The four F5a-wired files are modified: `ci.yml`, `docs/REFERENCE.md`, `CHANGELOG.md`, `AGENTS.md`.
  - All six tasks' new files are untracked. Never push this branch; it is a staging area.
- **Remote:** `feat/turing-f5a-macvm-ctl` holds 7 verified commits and has no PR.
- **This file:** it lands through the host-record PR in Next, item 4.
