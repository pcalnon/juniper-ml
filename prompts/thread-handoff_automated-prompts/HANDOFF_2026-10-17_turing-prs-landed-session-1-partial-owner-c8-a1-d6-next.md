# Handoff — turing: the open PRs are landed, Session 1 is partly done, and the owner is up next (C8, A1, D6)

- **From:** the 2026-10-16/17 session on turing. Its work arc was `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-16_turing-bringup-plan-landed-session-1-next.md`.
- **Plan of record:** `notes/JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md` v1.0.0. Section and task IDs below refer to it.

## Done

**PR sweep.** The owner asked for every Juniper PR to be merged and granted merge approval.

- **juniper-ml#2222 was re-landed with signed commits as juniper-ml#2228**, merged as `fc90ae89`. #2222 is closed.
  - #2228 carries tasks A4 and B9, plus regressions R-A4 and R-B9.
  - `util/juniper_clone.bash` replaces the alias-bypassing clone helper, which was never landed.
  - `util/find_encryption_readme_notes.bash` is rewritten without the `eval` injection.
  - Two new suites are wired into `ci.yml` and `docs/REFERENCE.md`: `tests/test_juniper_clone.py` (22 tests) and `tests/test_find_encryption_readme_notes.py` (26 tests).
  - `util/ad-hoc/2026-10-16_turing_a4_b9_mutation_check.py` kills 17 of 17 mutants.
  - `prompts/manual/prompt133_2026-10-15.md` is now versioned.
- **juniper-canopy#749 is closed, per the owner.** It had no file changes, and its unsigned commits could never merge.
- **juniper-deploy#249 is deliberately left open.** The concurrent W1.13 session opened it at 20:04Z. It pins canopy 0.9.0 and recurrence 0.6.0, and neither was on PyPI at 20:15Z. Merging it before those publish would break deploy installs. Its session owns the merge.

**Host tasks, done before C8 as the owner chose ("Agent does ~/.ssh first").**

- **C4:** `~/.ssh/config` and `~/.ssh/id-turing-aws-ec2.pem` are mode 600.
- **A8:** `AddKeysToAgent no` in all 10 `github_juniper-*` blocks. `ssh -G` reports `addkeystoagent false`.
- **A7:** the Contents comment now matches the Host list. The Notes example that recommended `GIT_SSH_COMMAND="ssh -i …" git clone git@github.com:…` (the §4.1 root cause) now shows the alias form instead.
- **B1, partly:**
  - `no-allow-external-cache` was added to `~/.gnupg/gpg-agent.conf`, and the agent was reloaded.
  - **pinentry-mac and ykman are not installed** (see finding 1). `pinentry-program` is unchanged.
- **Backups:** `~/.ssh/config.bak-2026-10-17-pre-A8-A7` and `~/.gnupg/gpg-agent.conf.bak-2026-10-17-pre-B1`.

**Token.** The owner added the `workflow` scope to turing's `gh` token (`gh auth refresh -s workflow`).

**Memory.** New: `homebrew-intel-no-bottles`, `turing-api-landing-pitfalls`. Updated: `turing-host-profile`.

## Findings that need owner decisions (they change the plan)

1. **Homebrew dropped Intel macOS in September 2026.** It builds no bottles for Intel and recommends MacPorts.
   - `brew install pinentry-mac ykman` planned source builds of python@3.14 and @3.15, openssl@4, cmake and gettext, plus **19 dependency upgrades**. It was stopped before anything changed.
   - D0 (`coreutils`) also needs texinfo. `pinentry-mac` alone upgrades cmake, libunistring, gettext and libgpg-error.
   - This blocks D0, B1, D1-tools, D2-upg and D4, and contradicts D6 (Homebrew as the single source) and D5 (drop `/opt/local/bin`).
   - Options: MacPorts binaries; Yubico's pkg or `pipx install yubikey-manager` for ykman; conda-forge (osx-64) for the CLI tools; or approved source builds of small C and Go tools only.
2. **D11's fine-grained agent PAT must include Workflows: read/write.** Every suite-adding PR edits `ci.yml` (the §6 CI wiring rule), and without the scope `createCommitOnBranch` is refused.
3. **ExpressVPN breaks large API commits.** Through the tunnel, every `createCommitOnBranch` of 180 KB or more returned 499 or EOF, while about 105 KB landed.
   - `docs/REFERENCE.md` (about 1 MB) has to be re-uploaded by every suite-adding PR.
   - Use `util/ad-hoc/2026-10-17_push_signed_with_retry.py`: one file per commit, a head re-read before every attempt, and backoff.
   - Keep `brew` and other downloads off the link while landing; one saturated it.
4. **The C8 design and the agent tasks conflict.**
   - D11's deny list and hook would block agent edits under `~/.ssh` and `~/.gnupg` (A8, A7, C4, and B1's config). The owner resolved that for this session by ordering those tasks first.
   - D11 option (a), an OS-level read-deny of `~/.ssh`, would also break agent `git fetch` and push over ssh. Prefer hook option (b).
5. **Worktree-isolated sessions can't run `git -C` on sibling repos**, so A1 is owner-run in this setup.
6. **Errata for E6:** the plan's header says prompt133 is "not versioned", but #2228 versioned it.

## Next

**Owner first:**

- **A1:**

  ```bash
  J=~/Development/python/Juniper
  git -C "$J/juniper-k8s" remote set-url origin git@github_juniper-k8s:pcalnon/juniper-k8s.git
  git -C "$J/juniper-recurrence" remote set-url origin git@github_juniper-recurrence:pcalnon/juniper-recurrence.git
  ```

- **C8:** the D11 items 1 and 4, weighed against findings 2 and 4.
- **D6:** rule on how packages get onto Intel turing (finding 1).

**Then AGENT, the rest of Session 1, under C8:**

- H0.
- D0, in whatever form the D6 ruling allows.
- B1, completed: install pinentry-mac and ykman per D6, write `pinentry-program <brew-or-port prefix>/bin/pinentry-mac`, then `gpgconf --kill gpg-agent`.
- G2, B7, B8, A5 and F5a. Each is its own PR, with its suite wired into `ci.yml` and `docs/REFERENCE.md` in the same PR. Merge them serially through `util/safe_merge.py --pr N --execute`.
- F3, which needs D0's `timeout`.

## Rules carried forward

- **Never commit and push for merge from turing.** Land with `util/open_signed_pr.py`, and for large files use `util/push_signed_commit.py` with the retry driver.
- **After any API error, re-read the ref before retrying.** A 499 can land a commit or land nothing. `open_signed_pr.py` creates the branch first, so a failure can leave an empty branch sitting at `main`.
- **Every whole-file upload must start from the head being committed onto.** Check `git log <base>..origin/main` before uploading.
- **No agent credential probes:** `ssh -T`, `ssh-add`, `gh auth status`, `gpg --card-status`, `gpg -K`.
- **On turing:** use `SKIP=gitleaks` (D6), and never run `brew install` or `brew upgrade` without `--dry-run` and owner sign-off.
- **Local test baseline:** 26 suites fail on turing, identically on clean `main`. They need Linux-only tools (`flock`, `/proc`, GNU `realpath` and `stat`, `libgomp`). Compare against `main`, not against zero.

## Verify the starting state

```bash
cd ~/Development/python/Juniper/juniper-ml && git fetch origin && git log -1 --oneline origin/main   # at or after fc90ae89
gh search prs --owner pcalnon --state open --json repository,number,title   # expect only W1.13's deploy pin, or nothing
grep -c 'AddKeysToAgent no' ~/.ssh/config                                   # 10
stat -f '%Sp %N' ~/.ssh/config ~/.ssh/id-turing-aws-ec2.pem                # both -rw-------
grep -c '^no-allow-external-cache' ~/.gnupg/gpg-agent.conf                 # 1
for r in k8s recurrence; do git -C ../juniper-$r remote get-url origin; done   # alias form once A1 is done
jq '.env // {} | keys' ~/.claude/settings.json                             # GIT_CONFIG_* present once C8 is done
command -v timeout || echo "timeout missing (D0 pending, blocked on D6)"
```

## Git state at handoff

- Worktree `.claude/worktrees/mutable-finding-crescent` is clean at `fc90ae89`.
- `fix/turing-a4-b9-reland-2222` was merged, and its remote branch was auto-deleted (`delete_branch_on_merge=true`).
- The closed PRs' branches remain on the remotes: `feat/adding-new-util-scripts-for-keys` (juniper-ml) and `feat/juniper-canopy-changes` (juniper-canopy). The owner may delete them.
- This handoff file lands on `main` through `util/open_signed_pr.py`.
