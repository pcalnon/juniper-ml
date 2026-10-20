# Commit signing for the terminal and the IDEs (Cursor, VS Code) — plan

- **Project**: Juniper ecosystem. The plan and its tooling live in juniper-ml. The configuration it installs covers every git checkout under `~/Development/python/Juniper/` on a developer host: the 10 active repos, their linked worktrees, and the three legacy repos under `juniper-legacy/`.
- **Author**: Paul Calnon (investigation and drafting via a Claude Code session on turing)
- **Date**: 2026-10-19
- **Version**: 1.1.0. Version 1.0.0 applied consensus round 1 (§14.2), and 1.1.0 applies round 2 (§14.3).
- **Status**: VALIDATED.
  - Round 1 returned 3 × ACCEPT-WITH-CHANGES and no BLOCKER. All 10 MAJOR findings were applied, and every MINOR or NIT was either applied or declined with a reason.
  - Round 2 returned ACCEPT-WITH-CHANGES and no BLOCKER. All 18 findings were applied, including its one new MAJOR (N1).
  - Tasks marked **OWNER** need the owner at the keyboard, at a YubiKey, or in an IDE.
- **Owner**: Paul Calnon
- **Extends**: `notes/JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md` (the bring-up plan), arc B: decisions D3 and D11, tasks B2–B5.
  - This plan replaces the git-config half of task B4 and adds the IDE half, which the bring-up plan does not cover.
  - Where the two disagree on B4 or B5, this plan wins. Everything else stays with the bring-up plan.
- **Template**: `notes/templates/TEMPLATE_DEVELOPMENT_ROADMAP.md`, adapted to a host-configuration change.

---

## 1. Executive summary

**Goal.** Every commit the owner makes in a Juniper checkout is signed with the YubiKey signing subkey. That holds whether the commit starts in a terminal, in the Source Control view of Cursor or VS Code, or in either IDE's integrated terminal.

No existing check or test is weakened. **Claude Code agents still cannot sign.** An IDE agent signs only after a per-command owner approval and a physical touch (S7, S11).

**What turing has today** (measured 2026-10-19, §3):

1. **No signing configuration at any scope.** The global config holds only `user.name`, `user.email`, the credential helper and an alias. The system config holds only `credential.helper`. None of the 10 checkouts has a local signing or identity key, and there is no XDG config file.
2. **The GUI half is in place.** Bring-up task B1 set `pinentry-program /usr/local/bin/pinentry-mac` and `no-allow-external-cache`.
3. **turing cannot sign or verify yet.** The owner's public key is not in turing's keyring. Commit `be9f1319`, signed on yamaguchi, reads `E BA18D1A733B1831A`. So B2 (import and trust) and B3 (card stubs) are still open.
4. **Both IDEs defer to git's own configuration.**
   - Cursor 3.25.9 and VS Code 1.108.2 each bundle a `vscode.git` extension. It adds `-S` to its `git commit` only when `git.enableCommitSigning` is true, and neither copy contains `--no-gpg-sign`.
   - Cursor's fork also appends its own `GIT_CONFIG_*` keys to every git spawn and keeps any it inherits. None of those keys touches signing, but an inherited D11 environment would (§7.3).
5. **`gpg` on PATH depends on context.**
   - This session resolves `/opt/local/bin/gpg` first, while login shells resolve Homebrew's after D5.
   - `gpg2` exists only under the demoted MacPorts path.
   - An IDE launched from the Dock takes its PATH from a login-shell probe.

   So `gpg.program` must be an absolute path.
6. **The card signs without a touch once its PIN is in.** As recorded on yamaguchi: `UIF Sign=off`, `Signature PIN: not forced`, retry counters `3 0 3`, no reset code.
7. **IDE agents need little or no approval.**
   - **VS Code.** `chat.tools.terminal.autoApprove` holds `"/.*/": true`. VS Code's default rules deny only commands such as `rm`, `curl`, `chmod`, `eval` and `sed -i`, so Copilot agent mode runs `git commit --no-gpg-sign` unprompted.
   - **Amp.** `amp.permissions` contains two unconditional `Bash allow` rules.
   - **Cursor.** Its default run mode since 3.6 is Auto-review, in which a classifier can allow a call that bypasses the sandbox.
8. **The sandbox and D11 both leave gaps.**
   - **Cursor's sandbox cannot sign.** In the sandbox the agent socket is unreachable, and agents have answered that with `--no-gpg-sign`.
   - **D11 does not stop explicit signing.** An explicit `-S`, `-c include.path=` or `--config-env=commit.gpgsign=…` still signs under D11's environment (measured, §10.1). Only the C8 guard and K12 close those paths.

Items 6 to 8 together lead to **the sequencing rule: no card goes into turing until C8 is installed, K12 (the guard rules) is merged and re-installed, and K13 (IDE agent approvals) is ruled** (round 2, N1).

- Any `gpg --card-status` makes gpg-agent `LEARN` the card, which writes a stub for each card key.
- Once the public key is imported (K6), those stubs make signing live, whichever step inserts the card first.
- Until then every signing attempt fails, closed.
- The touch policy (S11) is set with the first insertion (K8), before K6.

**The design** (§7):

- **The configuration.** `~/.gitconfig` gains one conditional include, `[includeIf "gitdir/i:~/Development/python/Juniper/"]`, pointing at `~/.config/git/juniper-signing.gitconfig`. That file holds yamaguchi's four signing values, except that `gpg.program` is an absolute path to a known GnuPG install.
- **No IDE setting changes.** The new check fails any IDE setting that would defeat the git configuration.
- **A tested tool.** `util/configure_commit_signing.py` installs the configuration (`--apply`), undoes it exactly (`--remove`), and verifies it without credentials (`--check`). The check covers:
  - the include's integrity;
  - planted repository-local keys;
  - IDE settings;
  - whether IDE agents can commit or bypass signing unprompted.
- **The owner's steps.** The YubiKey and approval steps stay with the owner, in a safe order (§13).
- **The AGENTS.md hazard.** It gains one sentence: an IDE agent must never "fix" a signing failure with `--no-gpg-sign`.

## 2. Scope

**In scope**

- Owner commits on a developer host in any checkout under the Juniper root, including linked worktrees, from:
  - a terminal;
  - the Source Control views of Cursor and VS Code: commit, amend, and the merge, rebase and cherry-pick commands that create commits;
  - both IDEs' integrated terminals.
- How IDE AI agents (the Cursor agent, Copilot agent mode, Amp) are allowed to commit (S7).
- turing, where it is applied first. The tool derives every path from `$HOME`, so it is host-agnostic; on yamaguchi it reports, by design, that `gpg.program=gpg2` is not absolute.

**Out of scope**

- **Claude Code agent sessions.** D11 keeps them unsigned by construction, and they land through `util/open_signed_pr.py`. This plan changes none of that (R4), and K12 tightens it.
- **Cloud and background agents** (Cursor Background Agents, Codespaces, CI runners). They have no access to the YubiKey.
- **Dev Containers.** A container would inherit `gpg.program` with a host-only path, which is a known failure mode. No Juniper repo uses one today.
- **JetBrains IDEs.** PyCharm CE is installed. It reads the same git config, so the include covers it. Its "configure GPG agent" helper can rewrite `gpg-agent.conf`, which the B7 preflight detects.
- **GitHub-side rulesets.** `required_signatures` stays exactly as it is.
- **Signed pushes** (`push.gpgSign`). GitHub does not use push certificates.
- **yamaguchi's own layout.** It keeps its global configuration. `--check` reports on it, but this plan does not run `--apply` there.

## 3. Current state (measured on turing, 2026-10-19)

| Item | Measured | Source |
|---|---|---|
| Host | turing, macOS 15.7.1, x86_64 | `sw_vers`, `uname -m` |
| git | `/usr/local/bin/git` 2.51.0 (Homebrew), first on PATH; `/usr/bin/git` 2.50.1 (Apple Git-155) | `which -a git`, `--version` |
| GnuPG | 2.4.8 from Homebrew. `/usr/local/bin/gpg` → `../Cellar/gnupg/2.4.8/bin/gpg`; `/opt/local/bin/gpg` and `/opt/local/bin/gpg2` link into the same Cellar. There is **no `/usr/local/bin/gpg2`**. `/usr/local/bin` and the Cellar are `drwxrwxr-x pcalnon admin` | `ls -la`, `which -a gpg gpg2` |
| pinentry | `/usr/local/bin/pinentry-mac` (1.3.1.1) | `ls -la`; bring-up plan §16.2, B1 row |
| Global config | `user.name=pcalnon`, `user.email=paul.calnon@gmail.com`, `alias.lgb`, `credential.usehttppath`, `credential.helper=osxkeychain`. No `user.signingkey`, `commit.gpgsign`, `tag.gpgsign`, `gpg.*` or `include*` | `git config --global --list --show-origin` |
| System config | `/usr/local/etc/gitconfig`: `credential.helper=osxkeychain` only | `git config --system --list --show-origin` |
| XDG config | `~/.config/git` does not exist; `XDG_CONFIG_HOME` is unset | `ls`, `env` |
| Repo-local config | no signing or identity keys in any of the 10 `.git/config` files. juniper-ml's `core.hooksPath` is the only `[core]` extra, and it names juniper-ml's own `.git/hooks` | `grep` |
| This session | `GIT_CONFIG_COUNT=2`: `commit.gpgsign=false` and `tag.gpgsign=false` in the `command` scope (D11 item 1) | `git config --show-scope --get-regexp` |
| Scoped reads ignore D11 | `git config --global --get commit.gpgsign` exits 1 (unset); plain `--get` prints `false`; `--show-scope` prints `command false` | measured |
| Public keyring | the owner's key is absent: `be9f1319` → `E BA18D1A733B1831A`. Web-flow commits on `origin/main` → `E B5690EEEBB952194` | `git log --format='%h %G? %GK'` |
| Card state (yamaguchi, 2026-08-09) | `Signature PIN: not forced`, `UIF Sign=off`, PIN retry counter `3 0 3`, no reset code. Cards `24955323` (the stubs' serial) and `24955114` (backup) hold the same subkeys | audit :279-283, A1-F4 (:256-304), A1-F11 (:419-423) |
| UIDs | the 3c key's UID ends `<paul.calnon@gmail.com>` (audit :169, as of 2026-08-09). `util/juniper-backup.bash:211-214` lists a second, 3a UID (`…Yubikey-3a_2026-08-11`), also with that email | audit; script |
| Shell profile | `~/.bash_profile:63-75` starts gpg-agent, runs `updatestartuptty` and points `SSH_AUTH_SOCK` at gpg-agent's ssh socket. `GPG_TTY` is set nowhere, and `~/.bashrc` is empty | `grep`, Read |
| IDEs | `/Applications/Cursor.app` 3.25.9; `/Applications/Visual Studio Code.app` 1.108.2; PyCharm CE | `defaults read …/Info.plist CFBundleShortVersionString` |
| IDE user settings | **Cursor:** 4 keys, strict JSON, no signing, terminal-env or agent keys. **VS Code:** 67 keys, strict JSON: `git.autofetch`, `git.enableSmartCommit`, `git.confirmSync`, `terminal.integrated.inheritEnv: false`; no `git.enableCommitSigning`, `terminal.integrated.env.*` or `git.path` | `~/Library/Application Support/{Cursor,Code}/User/settings.json` |
| Workspace and folder settings | `~/Development/python/Juniper/Juniper.code-workspace` (12 folders; `"settings": {}`). `<root>/.vscode/settings.json` holds `cSpell` words only. `juniper-cascor/.vscode/settings.json` holds formatter, linting, analysis, `editor.*` and `files.*` keys. None of them is signing-relevant | Read |
| IDE git extension | Both bundles' `extensions/git/package.json` define `git.enableCommitSigning` ("Enables commit signing with GPG, X.509, or SSH.", default `false`, scope `resource`), and `git.path` is `machine`-scoped. `dist/main.js` builds `["commit","--quiet"]`, adds `--allow-empty-message --file -`, adds `-S` only when the setting is true, and prefixes `-c user.useConfigOnly=true`. Neither bundle contains `no-gpg-sign` | the installed bundles |
| Cursor's fork | its extension builds git's environment from `process.env` and keeps inherited `GIT_CONFIG_KEY_n`. On every spawn it appends `safe.bareRepository=explicit`, `core.fsmonitor=false` and `core.attributesFile=/dev/null`. It also appends `core.hooksPath=/dev/null`, except for commit, merge, rebase, cherry-pick, pull and push | R1 (round 1), Cursor's `extensions/git/dist/main.js` |
| GitLens (VS Code) | builds some commits with `commit-tree` and adds `-S` from its own read of `commit.gpgsign`, so it follows the include. Its `createEmptyInitialCommit` never signs | R1 (round 1) |
| VS Code agent approvals | **`chat.tools.terminal.autoApprove`:** 15 entries, including `"/.*/": true`, `"xargs": true` and accidental fragment keys (`output_size`, `history`, `def.*run\`). **`chat.tools.terminal.enableAutoApprove`:** unset (default `true`). **`amp.permissions` (Sourcegraph Amp):** 58 rules; counting from 1, rule 2 asks for `*git*push*`, and rules 28 and 39 are unconditional `Bash allow` in mid-list | VS Code user settings |
| VS Code approval order | the 1.108.2 workbench checks every `false` (deny) entry before any allow entry, and denies a command that carries inline environment assignments. Rule keys are parsed with `^\/(?<pattern>.+)\/(?<flags>[dgimsuvy]*)$` (`g` dropped); plain keys become `^<key>\b`, case-sensitive except for PowerShell. The legacy `chat.agent.terminal.autoApprove` is merged in. Session auto-approval and `chat.tools.global.autoApprove` approve before the rules are consulted. The built-in defaults allow `git status`, `log`, `show`, `diff`, `ls-files`, `grep` and `branch`, and allow no commit-creating command | `…/out/vs/workbench/workbench.desktop.main.js` |
| Cursor agent | no `~/.cursor/sandbox.json` and no `<repo>/.cursor/sandbox.json`. The run mode and allowlist live in Cursor's own state store, not in `settings.json` | `ls` |
| Other git work on the host | `~/Development` also holds `Boost`, `c++`, `Dash`, `data`, `Docker`, `googletest`, `rust`, `PythonBook`, `Router_work` and `python/{dynamic_nn,yamaguchi}` | `ls` |
| Local commits by owner tools | `util/worktree_cleanup.bash:372` runs `git merge` in the primary checkout. No `util/` script creates a tag; release tags come from GitHub Releases (AGENTS.md § Publishing) | `grep`, Read |

**yamaguchi's target** (`notes/JUNIPER_2026-08-09_JUNIPER-ECOSYSTEM_HEADLESS-SIGNING-AND-SERENA-HARNESS-AUDIT.md`, the audit)

- §3.1 (:76-87): global `user.signingkey=B5619F58FDA4D94E2D73D8BABA18D1A733B1831A!`, `gpg.program=gpg2`, `commit.gpgsign=true`, `tag.gpgsign=true`.
- §3.3 (:241-254): signing subkey `BA18D1A733B1831A` (ed25519) of master `084FA27B796DABC4`, expiring 2028-08-06.
- The master's full fingerprint `06DBAC384131E0380D89923F084FA27B796DABC4` is recorded at audit :399 and at `notes/JUNIPER_2026-08-09_JUNIPER-ECOSYSTEM_STANDING-ITEMS-CLOSEOUT-AND-HARNESS-REMEDIATION-PLAN.md:952`. Both are repo text, so K6 checks it against an independent source.

## 4. Requirements

| ID | Requirement |
|---|---|
| R1 | **Signed by default.** In any checkout under the Juniper root, the owner's commit-creating git commands sign with the pinned subkey. Those commands are commit (and `--amend`), merge, rebase, cherry-pick, revert, `am`, `pull` (merge or rebase), and annotated tags. This holds from a terminal, from the IDE Source Control view and from the IDE's integrated terminal. **Not covered**, because git ignores `commit.gpgSign` for them: `commit-tree` (GitLens adds `-S` itself), stash, notes and fast-import. |
| R2 | **Scoped.** Repositories outside the Juniper root gain no signing requirement. |
| R3 | **GUI-safe.** Signing needs neither a TTY nor the shell's PATH: `gpg.program` is absolute and the pinentry is a GUI build. |
| R4 | **No new agent signing.** Claude Code sessions stay unsigned by construction (D11). Nothing here edits `~/.claude/settings.json` or weakens the C8 guard, and no Claude Code agent reads `~/.gnupg` or `~/.ssh` or runs a card or secret-key command. An IDE agent's commit signs only after a per-command owner approval and a touch (S7, S11, an owner ruling). IDE agents can read the filesystem, which includes the exported key files on disk; bring-up task C3 removes those. |
| R5 | **No check removed.** No test, pre-commit hook, CI job or ruleset is disabled, skipped or removed, and `required_signatures` is untouched. |
| R6 | **Fail closed.** Inside the Juniper tree a commit that cannot be signed fails rather than landing unsigned. The exception is a *missing* include file, which git skips silently. `--check` fails that case. |
| R7 | **Verifiable without credentials.** An agent can verify the configuration without signing, without touching the card and without reading key material. Signature verification (`%G?`) uses public keys only. |
| R8 | **Reversible.** `--remove` undoes exactly what `--apply` added and keeps everything else, and every host write is backed up first. |
| R9 | **Parity.** Inside the Juniper tree the effective signing values equal yamaguchi's (§3), except `gpg.program`, which is host-local. This is the bring-up plan's B4 acceptance. |

## 5. Best-practice basis

These are primary sources. WebFetch timed out on turing (§14.1), so each statement below was confirmed from search excerpts of the same page or from the installed software.

| Source | What it says | Applied as |
|---|---|---|
| GitHub Docs, [Telling Git about your signing key](https://docs.github.com/en/authentication/managing-commit-signature-verification/telling-git-about-your-signing-key) (macOS, GPG) | set `user.signingkey`; append `!` to a subkey; export `GPG_TTY=$(tty)` from the shell startup file; optionally install pinentry-mac | S2; S6; B1 (done) |
| GitHub Docs, [Signing commits](https://docs.github.com/en/authentication/managing-commit-signature-verification/signing-commits) | `commit.gpgsign true` signs every commit by default | S1 (the same key, through an include) |
| GitHub Docs, [About commit signature verification](https://docs.github.com/en/authentication/managing-commit-signature-verification/about-commit-signature-verification) | the committer email must be verified on the account and must match a UID on the key; verification records persist | K8 (UID check) |
| git-config(1): "Conditional includes", `gpg.program`, `user.signingKey`, `commit.gpgSign`, `tag.gpgSign` | `gitdir/i:` matches the `.git` location without regard to case; a trailing `/` matches everything below it; `~/` expands to `$HOME`. `gpg.program` replaces "gpg found on `$PATH`". `user.signingKey` is passed unchanged to `gpg --local-user` | S1–S4 |
| gpg(1), key specification | an exclamation mark after a key ID or fingerprint forces exactly that (sub)key | S2 |
| gpg-agent(1) | `--pinentry-program`; `--no-allow-external-cache`; "you should always add `GPG_TTY=$(tty)`" | B1 (done), D11 item 3, S6 |
| Yubico, [`ykman openpgp keys set-touch`](https://docs.yubico.com/software/yubikey/tools/ykman/OpenPGP_Commands.html); installed ykman 5.9.2 (`ykman/_cli/openpgp.py:452`) | policies `on`, `off`, `fixed`, `cached`, `cached-fixed`. `cached` caches a touch for 15 s; `fixed` "can't be disabled without deleting the private key" | S11, K8 |
| The installed IDEs' `vscode.git` extension (§3) | `git.enableCommitSigning` only adds `-S`; the extension never disables signing; `git.path` is machine-scoped | S5 |
| The installed VS Code workbench (§3) | deny-before-allow, the key grammar, merged legacy rules, the session and global auto-approve paths, and the default rules | S7, K13, `--check` INFO |
| Cursor: [run modes](https://cursor.com/docs/agent/security/run-modes), [3.6 changelog (Auto-review)](https://cursor.com/changelog/auto-review), [`sandbox.json`](https://cursor.com/docs/reference/sandbox), [Agent Sandboxing announcement](https://forum.cursor.com/t/agent-sandboxing-available-in-cursor-2-0/139449) | the Seatbelt sandbox reads the filesystem but writes only the workspace and `/tmp`, with no network. Auto-review (the default since 3.6) sends an unsandboxed call to a classifier that may allow it; the Allowlist mode asks | S7 |
| Cursor forum, [Agent Sandbox no access to ssh agent](https://forum.cursor.com/t/agent-sandbox-no-access-to-ssh-agent/141389) | Bitwarden SSH-agent signing: the sandbox cannot reach the agent socket, and the agent then committed with `--no-gpg-sign` | S7; the AGENTS.md hazard |
| Amp, [legacy permissions rules](https://ampcode.com/manual/appendix/legacy-permissions-rules.txt) | `amp.permissions` rules are checked in order, and the first match decides (`allow`, `ask`, `reject`, `delegate`) | S7, `--check` INFO |

## 6. Decisions

The S1–S12 numbers avoid colliding with the bring-up plan's D-numbers. Each decision takes its recommendation unless it is marked as an owner ruling.

### S1 — Where the signing configuration lives

| Option | Strengths | Weaknesses |
|---|---|---|
| a. Global `~/.gitconfig` (B4 as written; yamaguchi's layout) | simplest; signs everything | every repo on the host needs the card. `~/Development` holds other projects (§3). Applying it before B2/B3 breaks commits everywhere, and a temp repo a test or helper creates would try to sign |
| **b. Conditional include on the Juniper root** | the requested scope (R2). Temp repos under `$TMPDIR` are untouched. Fail-closed is confined to repos where unsigned commits are unmergeable anyway. The effective values equal yamaguchi's (R9) | a Juniper repo cloned *outside* the root does not sign; `util/juniper_clone.bash` clones into the root |
| c. `git config --local` in each checkout | — | 10 copies; a new clone misses them; drift |
| d. Include on the remote URL (`hasconfig:remote.*.url:`) | follows a clone anywhere | also matches temp test repos whose remotes look like GitHub URLs |

**Recommendation: b, using `gitdir/i:`, since APFS is case-insensitive by default.**

- **Rendering.** The pattern and the include path are rendered from realpaths: under `realpath($HOME)` they are written `~/` plus the relative path, and elsewhere as the realpath. git realpaths `$HOME` when it expands `~` and compares against the physical `.git` location, so a root spelled through a symlink still matches (R-S15).
- **Refusals.** The tool exits 2 for a root that is `$HOME` or an ancestor of it (that would sign everything), for a root containing a glob character, and for an include file under the root or inside any git work tree. Any branch could rewrite an include that lives in a work tree.
- **Worktrees.** A linked worktree's git directory is `<main>/.git/worktrees/<name>`, so it matches wherever it is checked out (R-S11).
- **Position is not the guarantee.** An owner section with the same pattern, or a later global `commit.gpgsign=false`, can still win. The guarantee is that `--check` judges the deciding value in every checkout (R-S3).

### S2 — The signing-key spec

**Recommendation: the full fingerprint, pinned: `B5619F58FDA4D94E2D73D8BABA18D1A733B1831A!`.**

- It is yamaguchi's exact value (R9) and B4's own acceptance.
- A fingerprint cannot collide the way a 16-hex ID can, and the `!` forces that subkey (gpg(1); R-B7a).
- The grammar is B7's: an optional `0x`, 16, 40 or 64 hex digits, then `!`. It is normalised to upper case without `0x`.
- B4's text gives the long ID for the same subkey; that is erratum E-B4-KEY.
- If B3 finds a card with a *different* sign subkey, `--signing-key` sets it. B6 records each card by serial and its 3a/3c name.

### S3 — `gpg.program`

**Recommendation: an absolute path to a known GnuPG install.**

- **Which path.** On Intel Homebrew it is `/usr/local/bin/gpg`, a stable link into `Cellar/gnupg/<version>/bin/gpg`. The tool's candidates are `/opt/homebrew/bin/gpg`, `/usr/local/bin/gpg` and `/usr/bin/gpg`.
- **Not `gpg` or `gpg2` found on PATH.** An IDE's PATH comes from a login-shell probe that can fail. `gpg2` exists on turing only under MacPorts.
- **Soundness, judged by `--check`:**
  - absolute, executable, and owned by the user or root;
  - no link on the way to it owned by another user;
  - not writable by group or others;
  - resolving to a known install: Homebrew's `…/Cellar/gnupg/<version>/bin/gpg`, `/usr/local/MacGPG2/bin/gpg[2]` or `/usr/bin/gpg[2]`.

  `--gpg-program` vouches for one other program.
- **Known installs** (round 2, N4) are `gnupg/<version>/bin/gpg` in Homebrew's own Cellar directories (`/usr/local/Cellar`, `/opt/homebrew/Cellar`, `/home/linuxbrew/.linuxbrew/Cellar`), `/usr/local/MacGPG2/bin/gpg[2]` and `/usr/bin/gpg[2]`. A Cellar-shaped path under `/tmp` or `~/.cache` does not count. `COMMIT_SIGNING_GNUPG_CELLARS` replaces the Cellar list, for the hermetic tests.
- **What this does not stop.** It catches another user's tampering, mode drift, and a program planted outside those installs. It **cannot** stop an agent running as the owner, who owns the Homebrew prefix (`/usr/local/bin` and the Cellar are writable by the owner and by `admin`). Directory writability is therefore not judged, because the real layout would fail. The controls for that threat are C8 and K12 (S9) plus the touch policy (S11).

### S4 — `tag.gpgsign`

**Recommendation: true (R9).**

- Inside the Juniper tree, `git tag <name>` then makes a signed annotated tag. Without a message it fails ("no tag message?"), and an IDE's "Create Tag" with an empty message does the same.
- No `util/` script tags locally. Release tags come from GitHub Releases, which GitHub signs.

### S5 — The IDE setting `git.enableCommitSigning`

| Option | Effect |
|---|---|
| **a. Leave it unset (`false`)** | the IDE runs plain `git commit`, and git's config decides |
| b. `true` in user settings | `-S` in **every** repo the IDE opens. Outside the tree no key is set, so git passes the committer identity to `gpg -u` and the signature fails |
| c. `true` in `Juniper.code-workspace` | applies only when the multi-root workspace is open; a second source of truth in an unversioned file |

**Recommendation: a.** `--check` reports the setting, and FAILs settings that would defeat the git config:

- an integrated-terminal environment that injects `GIT_CONFIG_COUNT`, `GIT_CONFIG_PARAMETERS`, `GIT_CONFIG_GLOBAL`, `GNUPGHOME` or `HOME`. That covers `terminal.integrated.env.*` and the `env` of `terminal.integrated.profiles.*`, `terminal.integrated.automationProfile.*` and `chat.tools.terminal.terminalProfile.*`. A `null` value unsets and is fine;
- a user-level `git.path` that names no executable. `git.path` is machine-scoped, so the IDE ignores it in workspace files;
- `chat.tools.global.autoApprove`, which approves every agent action (S7).

### S6 — `GPG_TTY`

**Recommendation: an optional owner step, neither automated nor a gate.**

- GitHub's macOS steps and gpg-agent(1) recommend it.
- With pinentry-mac it has no effect on prompting. GnuPG falls back to the TTY of stdin, and pinentry-mac ignores the TTY.
- If wanted, place this above `~/.bash_profile:63`:

  ```bash
  if [ -t 0 ]; then GPG_TTY="$(tty)"; export GPG_TTY; fi
  ```

### S7 — IDE AI agents (OWNER ruling: an exception to D11)

| Option | Strengths | Weaknesses |
|---|---|---|
| a. Widen Cursor's sandbox (`sandbox.json` adds `~/.gnupg`) | agent commits sign unattended | every sandboxed command gains read and write access to the keyring directory, against D11. The socket may still be blocked |
| **b. An IDE agent's history-writing git command needs the owner's per-command approval; the touch is the second factor** | owner-mediated, the same as committing agent-written changes from the Source Control view | one approval per commit |
| c. IDE agents land only through `util/open_signed_pr.py` | no card | no IDE can make its agent unsigned by construction |

**Recommendation: b, in four layers.**

0. **Built in.** Both IDEs' agents already carry "NEVER skip hooks (--no-verify, --no-gpg-sign, etc) unless the user explicitly requests it". Cursor has it in `extensions/cursor-agent-exec/dist/main.js`, and Copilot Chat in `dist/cli.js`.
1. **Instruction.** The AGENTS.md hazard gains: never answer a signing failure with `--no-gpg-sign` or `-c commit.gpgsign=false`. This reaches **juniper-ml only**, 1 of the 10 repos. The other nine repos' AGENTS.md carry no such hazard, so K14 is the optional follow-up, and layer 2 is primary.
2. **Approval (K13, OWNER).** This layer is primary.
   - **VS Code, required:** delete `"/.*/": true`, the accidental fragment keys and `"xargs": true`. **K13 is met only then** (round 2, N2).
   - **VS Code, a dated interim only:** while `/.*/` stays, add this deny pair. Deny entries are evaluated first, so it holds even beside `/.*/`. It stops `/usr/local/bin/git`, `GIT`, `env`, `command`, `sh -c`, `xargs`, `-c commit.gpgsign=`, `--config-env` and `include.path`, and it does not prompt for `git merge-base` or `git log --format=%am`.

     It is **not** sufficient. Five of `--check`'s 17 probes still get through (R-S14):
     - a `-c alias.*` with an abbreviated `--no-gpg`;
     - a misspelt subcommand that `help.autocorrect` runs as `commit`;
     - writes to `gpg.<format>.program`, `core.hooksPath` or `core.fsmonitor`.

     ```json
     "/\\bgit\\b.*\\s(commit|merge|rebase|cherry-pick|revert|am|pull|tag)(?![\\w-])/i": false,
     "/--no-gpg-sign|gpgsign|gpg\\.program|--config-env|include(if)?\\b[^\\s=]*\\.path|GIT_CONFIG_|GNUPGHOME/i": false
     ```

     Never add a deny pattern that matches the empty string (a stray `|`). VS Code turns such a rule into one that never matches (round 2, N3).
   - **VS Code, always:** never turn on session auto-approval or `chat.tools.global.autoApprove`; both approve before any rule is consulted.
   - **Amp:** remove the unconditional `Bash allow` rules 28 and 39 (required). In the interim, put the same two patterns first in `amp.permissions` as `ask` entries.
   - **Cursor:** set Approvals & Execution to **Allowlist** with the sandbox on, and keep history-writing git commands off the allowlist. `--check` cannot read Cursor's state store, so the owner records this attestation **at K13** (round 2, N11).
3. **Touch (S11).** A signature needs the owner's physical touch.

**Residual risk.** Until K13, VS Code and Amp agents can commit, or bypass signing, with no prompt. That is why no card goes into turing before K13 (§1). A bypassed commit fails at merge; `main` is never silently unsigned.

### S8 — When to activate

**Recommendation: now, failing closed (R6).**

- Until B2/B3 are done, an owner commit in the tree fails with "gpg failed to sign the data". It would otherwise land unsigned, and so be unmergeable.
- Agent sessions are unaffected (D11).
- **Recovery:**
  - a commit fails with no change to HEAD;
  - a merge, rebase or cherry-pick stops mid-operation. Use `git <op> --abort`, or for a deliberately local-only result, `git -c commit.gpgsign=false <op> --continue`;
  - a deliberate local-only commit takes `--no-gpg-sign`;
  - `util/worktree_cleanup.bash`'s merge (:372) now needs the card;
  - the commit message survives in `.git/COMMIT_EDITMSG`.

### S9 — Who writes the host configuration

- **This session runs `--apply` once (K5)**, because the owner asked for the change to be implemented. That moves B4's git half from OWNER to AGENT, and K4 records the actor change. The dry-run plan is recorded verbatim in the PR, and `--remove` undoes the change exactly.
- **The C8 guard covers neither file today.** As written, it does not cover `~/.gitconfig` or `~/.config/git/`. A Claude Code agent able to write them could set `gpg.program`, `core.sshCommand`, `core.fsmonitor` or `core.hooksPath` to a program that later runs in owner sessions.
- **The same agent can outrank the include.** It can write repo-local config or `.git/hooks/` directly. A `post-commit` hook runs right after the owner's touched signature, inside a `cached` touch window.
- **D11's environment can be overridden** with `git -c include.path=<file>` or `git --config-env=commit.gpgsign=…`. The guard checks only `-c *gpgsign*` (`util/claude_agent_guard.py:1105-1111`).
- **K12 (AGENT) extends the guard to deny the following.** It is a follow-up PR, and it must be merged and re-installed before any card goes into turing (§1).
  - `git -c include.path=…`, `-c includeIf.*…` and `-c gpg.*program=…`;
  - `--config-env` with any key, in both forms: `--config-env=<key>=<var>`, and `--config-env <key>=<var>`, which git 2.51.0 also accepts (round 2, N12);
  - `git config` writes, at any scope, of `gpg.*`, `user.signingkey`, `commit.gpgsign`, `tag.gpgsign`, `include*`, `core.hooksPath`, `core.fsmonitor` and `core.sshCommand`, plus `--edit` and removing or renaming those sections;
  - file-tool writes to these files, and any Bash command that names them (Bash cannot tell a read from a write): `.git/hooks/`, a repository's `.git/config` or `config.worktree`, `~/.gitconfig`, `~/.config/git/**`, and the system gitconfigs `/usr/local/etc/gitconfig`, `/opt/homebrew/etc/gitconfig` and `/etc/gitconfig` (round 2, N13);
  - `util/configure_commit_signing.py --apply` or `--remove` without `--dry-run`.

  It binds Claude Code only. IDE agents are bounded by K13 and S11.
- **`--check` now fails the planted-key cases** (local or worktree `gpg.*`, `include*` and `core.sshCommand`, a foreign `core.hooksPath`, a program-valued `core.fsmonitor`). It also lists executable hooks with sha256, so tampering is visible.

### S10 — Detecting unsigned commits before push

**Deferred.**

- A per-repo `pre-push` hook that refuses commits without a `gpgsig` header would catch a bypass before it reaches GitHub.
- It needs a hook in each of 10 pre-commit configs, and an inventory of the flows that legitimately push unsigned commits first.
- The planted-key and hook checks in `--check` cover the tampering half now.

### S11 — Touch policy for the signing slot (OWNER ruling)

| Option | Effect |
|---|---|
| **a. `on`** | every signature needs its own touch. A rebase of N commits needs N touches |
| b. `cached` (bring-up D11 item 2) | a touch covers 15 s. A `post-commit` hook or a second agent command inside that window signs with no touch (S9) |
| c. `forcesig` (PIN per signature) | the strongest; a PIN per commit |
| d. `fixed` / `cached-fixed` | never: "can't be disabled without deleting the private key" |

**Recommendation: a**, given IDE agents with broad approval and the hook window. `cached` is acceptable only once K12 and K13 are in place. The policy is a property of the card, so it changes yamaguchi too (S12). Set it at the first card insertion (K8), before K6 and K7, one card at a time (§13).

### S12 — yamaguchi under a touch policy (OWNER ruling)

**Recommendation: rule this before K8.**

- yamaguchi's agents commit signed today ("Commit normally (signed)", `prompts/thread-handoff_automated-prompts/HANDOFF_2026-08/HANDOFF_2026-08-07_pr-backlog-processing-fleet-merge-waves.md:13`), with touch off (audit :282).
- Under any touch policy those commits block on the card and then time out. Either yamaguchi's agents go unsigned by construction and land through the API (D11 there), or the owner accepts touching for them.

## 7. Design

### 7.1 The two host writes

At the end of `~/.gitconfig`:

```ini
[includeIf "gitdir/i:~/Development/python/Juniper/"]
	path = ~/.config/git/juniper-signing.gitconfig
```

`~/.config/git/juniper-signing.gitconfig`, with the directory created at mode 0700 and the file at 0644:

```ini
# Managed by util/configure_commit_signing.py (juniper-ml): the owner's commit signing for the Juniper tree.
# The global git config includes this file through an includeIf on the Juniper root.
# Plan: notes/JUNIPER_2026-10-19_JUNIPER-ECOSYSTEM_COMMIT-SIGNING-TERMINAL-AND-IDE-PLAN.md
[user]
	signingkey = B5619F58FDA4D94E2D73D8BABA18D1A733B1831A!
[commit]
	gpgsign = true
[tag]
	gpgsign = true
[gpg]
	program = /usr/local/bin/gpg
```

**Precedence** runs system < global (with the include at its position) < local < worktree < command. So:

- a repo-local or later-global `false` wins over the include, and `--check` fails it;
- D11's command-scope `false` wins in agent sessions.

### 7.2 What happens on a commit

| Origin | Path |
|---|---|
| Terminal | `git commit` applies the include, because the git dir is under the root. It runs `/usr/local/bin/gpg --status-fd=2 -bsau B5619…!`, which reaches gpg-agent through its standard socket, then scdaemon and the card. pinentry-mac prompts for the PIN when it is not cached; the card asks for a touch under S11 |
| IDE Source Control view | runs `git -c user.useConfigOnly=true commit --quiet --allow-empty-message --file -` with no `-S`. The same config applies, and gpg is reached by absolute path whatever the IDE's PATH. `user.useConfigOnly` needs `user.email`, which is set |
| IDE integrated terminal | the same as a terminal. On macOS the IDE starts a login shell (`bash -l`) |
| IDE agent | after K13: an approval prompt, then the terminal path, then a touch. In Cursor's sandbox, signing **fails** (R6): the agent must ask for an unsandboxed run, never bypass |
| Claude Code session | the command scope sets `commit.gpgsign=false` (D11), so a plain commit never calls gpg. An explicit `-S`, `-c include.path=` or `--config-env` would still sign: C8's GPG-SIGN rule blocks `-S`, and K12 blocks the others. That is why no card goes in before both (§1) |

### 7.3 Failure modes

| Condition | Symptom | Fix |
|---|---|---|
| B2 not done (no public key) | `gpg: skipped "B5619…!": No secret key`, then `error: gpg failed to sign the data` | owner K6 |
| B3 not done (no card stub) | the same | owner K7 |
| Card absent | pinentry-mac asks for the card by serial | insert it |
| No touch in time | the signature fails with a card error or timeout | retry, then touch |
| Cursor sandbox | `gpg: signing failed`, or an agent-socket error | an unsandboxed run, with approval |
| Include file **missing** | commits land **unsigned**: git skips a missing include silently | `--check` FAILs it; re-run `--apply` |
| Include unreadable (mode 000) | every git command in the tree fails (`fatal: unable to access`), agents and IDE autofetch included | `--check` FAILs it; fix the mode |
| Merge, rebase or cherry-pick interrupted | stops mid-operation, changes staged | `git <op> --abort` (S8) |
| Lightweight tag | `fatal: no tag message?` | `git tag -m …` |
| IDE launched from a Claude Code shell (`code .`, `cursor .`) | it inherits D11's `GIT_CONFIG_*` (Cursor appends its own), so its commits are silently unsigned; `--check` cannot see an IDE process's environment | launch IDEs from the Dock or `open -a`, never from a Claude Code session |
| Repo cloned outside the root | unsigned (`%G?` = `N`) | clone into the root (`util/juniper_clone.bash`) |

## 8. Tooling — `util/configure_commit_signing.py`

```text
python3 util/configure_commit_signing.py [--check | --apply [--dry-run] | --remove [--dry-run]] [--json]
    [--root DIR] [--signing-key KEYSPEC] [--gpg-program PATH] [--include-file PATH] [--ide-settings FILE]...
```

The conventions follow bring-up plan §8: exit 0 / 1 / 2, `--help`, `--dry-run` for the writers, overridable tools (`GIT`), and **no key material read**. The tool is Python 3.9-compatible, because turing's `/usr/bin/python3` is 3.9.6 (bring-up §17.3 E-C8). Its docstring is the full contract; the essentials follow.

**Modes**

- **`--check`** (the default) only reads.
- **`--apply`** writes:
  - the include directory (0700) and the include file (`O_EXCL`, 0644, header written by Python);
  - each signing key, via `git config --file`, only when it differs;
  - one `includeIf.<pattern>.path` via `git config --global --add`, only when it is absent.

  Before a file's first change, `--apply` backs it up to `<file>.bak-<YYYY-MM-DD>-pre-commit-signing`. The date is local and pinned by `COMMIT_SIGNING_TODAY`, and a backup is never overwritten. `--apply` then runs the checks and prints the rollback, in undo order.

  An existing include, or its directory, that fails the `include` check stops `--apply` with exit 2 **before** any write (round 2, N6). git's `--file` writer follows a symlink, so a planted link would otherwise send the keys to the link's target.
- **`--remove`** works in this order:
  1. it unsets exactly the `path` values it wrote, with `--fixed-value`;
  2. it drops the section if that leaves it empty;
  3. it deletes the include file only when it is byte for byte what `--apply` writes, comments included (round 2, N18), and no other global include still points at it (round 2, N5). Deleting it then would make that other include fail open;
  4. it removes the directory if that leaves it empty.

  It never restores a backup, which would discard later edits, and it exits 1 when it refuses to delete an edited include.
- **`--dry-run`** with either writer prints the plan and writes nothing. With `--apply` it also runs the checks, so it exits 1 while anything still fails, as `util/git_remote_alias_check.py --fix --dry-run` does.

**Defaults**

| Option | Default |
|---|---|
| `--root` | `$JUNIPER_ROOT`, then `$HOME/Development/python/Juniper` |
| `--signing-key` | `B5619F58FDA4D94E2D73D8BABA18D1A733B1831A!` |
| `--gpg-program` | `--check` accepts any sound program (S3). `--apply` keeps the include's existing sound value, else the first sound candidate. `COMMIT_SIGNING_GPG_CANDIDATES` overrides the list, and the soundness rule still applies to every candidate |
| `--include-file` | `~/.config/git/juniper-signing.gitconfig`; must not be under the root or inside a git work tree |
| IDE settings | **user level:** `User/settings.json` and `User/profiles/*/settings.json` of Code, Cursor, Code - Insiders and VSCodium, under both `~/Library/Application Support` and `$XDG_CONFIG_HOME` (`~/.config`) on every platform. `--ide-settings` replaces this set. **Always:** `<root>/*.code-workspace`, `<root>/.vscode/settings.json` and each checkout's `.vscode/settings.json` |

**Checks**

`git` runs without the variables that `git rev-parse --local-env-vars` lists, which include D11's `GIT_CONFIG_COUNT`. So an agent session judges the owner's configuration.

| Check | FAIL when |
|---|---|
| `include` | the file is wired but missing (it fails open, §7.3); it is a symlink, not a regular file, not the user's, unreadable, or writable by group or others; its directory is not the user's or is writable by group or others; or it holds any key beyond the four managed ones |
| `repo:<name>` | the owner-effective `commit.gpgsign` or `tag.gpgsign` is not true; `user.signingkey` is not the expected spec; `gpg.format` is not `openpgp`; the deciding `gpg.program` or `gpg.openpgp.program` is not sound (S3); `user.email` is unset; a local or worktree `gpg.program`, `gpg.openpgp.program`, `include.*`, `includeIf.*` or `core.sshCommand` is set; `core.fsmonitor` names a program; or `core.hooksPath` is not the checkout's own hooks directory. The planted-key test also runs on **every linked worktree's** `config.worktree`, since agents work there (round 2, N13). The message names the scope and file that decided each value |
| `ide:<label>` | the file cannot be parsed, even as JSONC (a string-aware tokenizer: BOM, `//`, `/* */`, trailing commas); an injected terminal variable (S5); a dead user-level `git.path`; or `chat.tools.global.autoApprove` is on |
| INFO | the include layout; executable hooks per checkout, with sha256 (a hooks path inside a credential directory is never listed or read); hook, monitor, ssh and include settings at **global or system** scope, which apply to every repository (round 2, N13); the D11 override; environment variables that redirect git's config (`GIT_CONFIG_GLOBAL`, `GIT_CONFIG_SYSTEM`, `GIT_CONFIG_NOSYSTEM`, `XDG_CONFIG_HOME`); the agent verdicts below; Cursor's attestation reminder; missing checkouts |

**Agent verdicts (INFO)**

- **The probes.** The question is whether an agent's plain `git commit`, or any of 17 bypass spellings, runs without a prompt. The spellings are:
  - `--no-gpg-sign`;
  - `-c commit.gpgsign=false`;
  - `--config-env`;
  - `-c include.path=`;
  - `/usr/local/bin/git`;
  - `GIT`;
  - `env`;
  - `command`;
  - `sh -c`;
  - `xargs`;
  - `git config --local gpg.program`;
  - the abbreviation `--no-gpg`;
  - `-c alias.c=commit c --no-gpg`;
  - `git config gpg.openpgp.program`;
  - `git config core.hooksPath`;
  - `git -c help.autocorrect=immediate comit --no-gpg`, which git runs as `commit` (measured, git 2.51.0);
  - `git config core.fsmonitor` (the last six from round 2, N2).
- **VS Code** is evaluated as 1.108.2 does it:
  - `enableAutoApprove: false` means every command needs approval;
  - the legacy key is merged in;
  - deny entries are evaluated first;
  - keys use VS Code's grammar, `g` is dropped, and named groups are translated;
  - a rule that matches the empty string becomes a never-match, except `.*` and the bare anchors (round 2, N3);
  - matching is case-sensitive unless the regex carries `i`.

  The line also **names any catch-all allow rule**: one that approves unrelated commands such as `rm -rf`, `curl` and `git push --force`. A regex Python cannot read (flags `d`, `u`, `v` or `y`, or failed syntax) reports **cannot evaluate**; it never yields a guessed verdict. The built-in default rules are not modelled. They allow only read-only git commands, so leaving them out can only over-report.
- **Amp's** `amp.permissions` is first-match, and the line names any unconditional `Bash allow`. A command no rule matches reports "Amp's bundled defaults decide".

**JSON** carries `{schema, mode, root, include_file, global_config, expected, writes[], rollback[], checks[], ok, exit_code, summary}`.

## 9. Tasks

**Actor.** AGENT means a session on the host. OWNER means the YubiKey, its PIN or touch, an IDE's settings, a trust decision, or a ruling.

| ID | Task | Actor | Depends | Acceptance |
|---|---|---|---|---|
| K1 | This plan, with consensus rounds 1 and 2 | AGENT | — | §14 records both; every MAJOR applied |
| K2 | The tool and `tests/test_configure_commit_signing.py`; `ci.yml`'s regression step; `main-verify.yml`'s battery (its SYNC NOTE asks for it); `docs/REFERENCE.md` (Test Suite Reference, "Running every suite", Utility Script Reference); `CHANGELOG.md`; mutation evidence (`util/ad-hoc/2026-10-19_commit_signing_mutation_check.py`) | AGENT | K1 | the suite is green in CI and locally under JuniperPython and `/usr/bin/python3` 3.9.6; flake8, bandit and the CodeQL pre-screen are clean; every mutant is killed by its own pin; the wiring drift gates are green |
| K3 | AGENTS.md: one sentence in the unsigned-commit hazard plus the tool's name; the suite count at :79, recomputed from `main` at upload (217 → 218 on 2026-10-20); `Last Updated` set to the **UTC** date at upload | AGENT | K1 | the memory budget, header schema and version-drift gates are green |
| K4 | Bring-up plan §19 (v1.4.0). It builds on the Session 3 record's §18 (v1.3.0), which the bring-up session claimed on 2026-10-20, and adds: B4 split into B4a (this tool, AGENT, at the owner's request) and B4b (OWNER); errata E-B4-KEY, E-B4-SCOPE, E-B4-GPG, E-G-SIGN, E-ACTIVE, E-D11-S and E-D5-LINE; B5 widened | AGENT | K1, the Session 3 record merged | merged with K2 and K3; the apply script refuses to write §19 until §18 is on `main` |
| K5 | `--apply` on turing, then `--check` | AGENT | K2 | every `repo:*` check and the `include` check pass. B2/B3 are not a precondition (S8). The dry-run plan is recorded in the PR |
| C8 | Install the agent guard: `bash util/install_claude_agent_guard.bash --apply` (bring-up §16.2) | OWNER | — | the guard's `--self-test` passes; `git commit -S` is denied to an agent |
| K12 | Guard rules (S9), in a follow-up PR | AGENT | K5 | merged; the owner re-runs the C8 line from an up-to-date `main` (§13), and the installed guard's `--self-test` passes; the guard's suite pins each new denial, including both `--config-env` forms (`--config-env=K=V` and `--config-env K=V`) |
| K13 | IDE agent approvals (S7): VS Code, Amp, Cursor | OWNER | — | VS Code's `"/.*/": true`, `"xargs": true` and the fragment keys are deleted; Amp's rules 28 and 39 are removed; `--check` INFO reports "needs approval" for every probe in VS Code and Amp and names no catch-all; the owner records the Cursor attestation (Allowlist, sandbox on, no history-writing git command allowlisted) **at K13**, and K11 files it |
| K8 | Rulings S11 and S12, then the touch policy, card by card (§13) | OWNER | S12 ruled; C8, K12, K13 (the first card insertion, §1) | `ykman openpgp info` shows the ruled policy on the sign slot of each card |
| K6 (= B2) | Import the public key and verify it against an independent source; ultimate trust gated on that check; the web-flow key imported with no trust | OWNER | C8, K12, K13 (the card's own fingerprint line is one of the sources, §1) | `be9f1319` shows `G` |
| K7 (= B3) | Per card: `--card-status`, `learn --force`, and a test clearsign with the pinned spec. Signing is live from the first step that has both the public key and a card stub (§1), which may be K6 | OWNER | K6, K8, C8, K12, K13 | the clearsign succeeds on each card |
| K9 | `bash util/headless_signing_preflight.bash` and `--check`, from a **real owner terminal**, never `! <cmd>`. The session's D11 environment fails the preflight by design; `--check` strips it, so it reports the same either way | OWNER | K5, K7 | both exit 0 |
| K10 (= B5) | The I-SIGN matrix (§10.2) | OWNER | K9, bring-up A3 (at least juniper-ml's A2/A3 rows) | T1–T5 `verified: true, reason: valid`; T7 reads `command false`, and its commit is `N`; T8–T10 each showed an approval prompt |
| K11 | Record the results in `reports/<run-date>_turing-signing-probe/`, with the K13 Cursor attestation. Change the AGENTS.md hazard's "turing, as of 2026-10-15" to the verified date. Claude Code agents keep landing through the API (D11) | AGENT | K10 | merged |
| K14 | The hazard sentence in the other nine repos' AGENTS.md | AGENT | K3 | optional follow-up |

## 10. Testing, gates and errata

### 10.1 Unit and regression (hermetic: `tests/test_configure_commit_signing.py`)

**Fixtures**

- A temp `HOME` with the Juniper root under it, holding real `git init` checkouts of the 10 active names.
- A scrubbed environment:
  - `GIT_CONFIG_NOSYSTEM=1`;
  - every `GIT_*` variable scrubbed, except where a case sets D11's on purpose;
  - `XDG_CONFIG_HOME`, `GNUPGHOME`, `JUNIPER_ROOT` and the tool's variables scrubbed;
  - `RedactedEnv` throughout (`tests/redacted_env.py`; `tests/test_env_repr_safety.py` enforces it).
- A recording fake gpg installed the way Homebrew would install it (`opt/Cellar/gnupg/<v>/bin/gpg`, reached through `bin/gpg`). It answers like a successful detached signature. Every `--apply` passes it explicitly or through the candidates variable, and each end-to-end case asserts that the include names it before committing. For the tool's own runs the fake is a tripwire.

| ID | Pins |
|---|---|
| R-S1 | an unpinned or malformed key spec exits 2 with nothing written; an unpinned key in the include fails; normalisation |
| R-S2 | a relative, missing, non-executable or group-writable `--gpg-program` exits 2 with nothing written; those values in the config fail; a later `gpg.openpgp.program` decides and is judged |
| R-S3 | a repo-local `commit.gpgsign=false` fails that repo, naming its scope; a later global `false` fails every repo, even when an owner section with the same pattern exists |
| R-S4 | D11 keeps a plain agent commit and tag from calling gpg, and `--check` still judges the owner-effective values. **The boundary:** `-S`, `-c include.path=` and `--config-env` under D11 *do* call gpg; that gap is K12's |
| R-S5 | IDE settings: an injected variable fails (in `env` and in profile `env`); `null` unsets; JSONC parses (`//` and `/*` inside strings survive); an unparseable file, a dead user-level `git.path` and global auto-approve fail; a workspace-level `git.path` is not judged; workspace, root, folder and profile files are scanned, on both platforms' paths |
| R-S6 | `--apply --dry-run` writes nothing and exits 1 while anything fails, 0 when nothing is left to do |
| R-S7 | a second `--apply` writes nothing and changes no byte |
| R-S8 | backups are made once and never overwritten; an existing include is backed up before it is edited; an owner include with the same pattern survives |
| R-S9 | an audit hook proves the tool opens nothing under `~/.gnupg` or `~/.ssh`, never executes the gpg program, and writes only the include and the backups (nothing at all under `--check` or `--dry-run`). git's own writes are outside the hook, so a snapshot of the temp `HOME` before and after `--apply` must differ only in those files. A hooks path planted inside `~/.ssh` fails as planted and is never listed or read (round 2, N6 and N18) |
| R-S10 | **end to end:** a terminal commit, the IDE's exact argv with and without `-S`, Cursor's injected keys, a merge, a cherry-pick and an annotated tag all produce a signature from the pinned key; a lightweight tag fails (S4); an IDE that inherited D11's env commits unsigned |
| R-S11 | a linked worktree checked out outside the root signs |
| R-S12 | a repository outside the root is untouched |
| R-S13 | exit 2: no checkout, missing git, bad arguments, a bad `COMMIT_SIGNING_TODAY`, a root that is `$HOME` or above, a glob in the root, an include under the root or in a work tree |
| R-S14 | the agent verdicts for VS Code: `/.*/`, the S7 deny pair in either order (5 of 17 probes still unprompted), `enableAutoApprove: false`, the legacy key, object values, plain prefixes, named groups, the `v` flag (cannot evaluate), case sensitivity, and a deny rule that matches the empty string, which protects nothing (round 2, N3). A catch-all allow rule is named. For Amp: first match wins, and an unconditional `Bash allow` is named (round 2, N2) |
| R-S15 | `$HOME` and the root spelled through symlinks still sign; a root outside `$HOME` is written as its realpath |
| R-S16 | planted local `gpg.program`, `include.path`, `core.sshCommand`, a foreign `core.hooksPath` and a program-valued `core.fsmonitor` fail; the checkout's own `hooksPath` and a boolean `fsmonitor` pass. A key planted in a linked worktree's `config.worktree` fails, and global `core.hooksPath` and `include.path` settings are reported, but not the tool's own include (round 2, N13) |
| R-S17 | a missing (wired) include fails, and a commit then lands unsigned; a symlinked or writable include, or a writable directory, fails. `--apply` refuses to write through a symlinked include, or into a group-writable directory, with exit 2 and no write; the link's target is unchanged (round 2, N6) |
| R-S18 | a program outside a known GnuPG install fails unless `--gpg-program` vouches for it; `--apply` replaces such a value. A Cellar-shaped path outside Homebrew's own Cellars is not a known install (round 2, N4) |
| R-S19 | an unmanaged key in the include fails |

**Also pinned:**

- `--remove` restores `~/.gitconfig` byte for byte and keeps an owner include;
- it refuses to delete an edited include, including one where only a comment was added (round 2, N18);
- it keeps an include that another root's wiring still uses, and that root still signs (round 2, N5);
- `--help` and `--check` run under `/usr/bin/python3`;
- the source parses as Python 3.9;
- flake8 is clean;
- executable hooks are listed with sha256.

**Mutation evidence.** `util/ad-hoc/2026-10-19_commit_signing_mutation_check.py` re-introduces each defect class: 40 mutants from round 1, plus 10 for the classes round 2 found. Every mutant is killed by the suite, and by its own pin test alone (§14.4).

### 10.2 Integration (owner-run: the I-SIGN matrix)

**Procedure.**

- Run on a throwaway branch `probe/signing-<date>` in juniper-ml.
- Launch both IDEs **from the Dock** or with `open -a`, never with `code` or `cursor` from a Claude Code shell.
- Each row makes one empty commit. In the IDE Source Control view use the command palette's **Git: Commit Empty** (`git.commitEmpty`); the Commit button cannot make an empty commit.
- Push the branch. For each SHA run `gh api repos/pcalnon/juniper-ml/commits/<sha> --jq .commit.verification`, then delete the branch.

| Row | Origin | Required |
|---|---|---|
| T1 | a real owner terminal: `git commit --allow-empty -m "probe T1"` | yes |
| T2 | Cursor Source Control view (Git: Commit Empty) | yes |
| T3 | VS Code Source Control view (Git: Commit Empty) | yes |
| T4 | Cursor integrated terminal | yes |
| T5 | VS Code integrated terminal | yes |
| T6 | Cursor agent, after an approved unsandboxed run | optional |
| T7 | negative control. In a Claude Code session, in a linked worktree **under the root**: `git config --show-scope --get commit.gpgsign` prints `command false`, and an empty commit there is `%G?` = `N`. It is never pushed | yes, local only |
| T8–T10 | ask the Cursor agent, Copilot agent mode and Amp each to run `git commit --allow-empty -m probe`; each must show an approval prompt (decline it) | yes, after K13 |

**Pass:** T1–T5 report `"verified": true` and `"reason": "valid"`, and locally `%G?` = `G` with key `BA18D1A733B1831A`. T7 is as stated, and T8–T10 each prompted.

### 10.3 Gates and errata against the bring-up plan

**G-SIGN** (bring-up plan §9.3) is now evaluated inside the checkouts by `util/configure_commit_signing.py --check`, which exits 0, together with I-SIGN T1–T5. `git config --global --get` outside a checkout cannot see an include, so it is not the gate.

**Errata** (applied in K4)

- **E-B4-KEY.** B4's `'BA18D1A733B1831A!'` becomes the fingerprint (S2).
- **E-B4-SCOPE.** `git config --global` becomes the S1 include.
- **E-B4-GPG.** `$(brew --prefix)/bin/gpg` stands, as the literal `/usr/local/bin/gpg`.
- **E-G-SIGN.** As above.
- **E-ACTIVE.** Owner commits in the tree fail closed until B2 and B3 (S8).
- **E-D11-S.** D11's environment does not stop an explicit `-S`, `-c include.path=` or `--config-env`. So no card goes into turing until C8 and K12 are in place, which holds B2 and B3 (K6, K7) back too, and B4's touch policy follows the S11 ruling.
- **E-D5-LINE.** The D5 row's `~/.bash_profile:87` is now `:92`.

## 11. Rollout, landing and rollback

**Order.** K1 runs first. K2–K4 go in one PR (this one), then K5. C8, K12 and K13 follow, then K8, K6, K7, K9 and K10 (§13), then K11. K14 is optional.

**Landing from turing.** turing cannot sign, so the PR lands through the GitHub API.

1. Run `util/ad-hoc/2026-10-18_turing_link_gate.py` first.
2. Open the PR with `util/open_signed_pr.py` and the small files. The commit body carries the attribution trailers through `--commit-body-file`.
3. Push the shared files one per commit with `util/ad-hoc/2026-10-17_push_signed_with_retry.py`:
   - `docs/REFERENCE.md`, about 1 MB;
   - `CHANGELOG.md`;
   - `.github/workflows/ci.yml` and `main-verify.yml`, which need the token's `workflow` scope;
   - `AGENTS.md`.
4. Build each shared file from a fresh `origin/main` copy, using the idempotent apply script `util/ad-hoc/2026-10-19_commit_signing_shared_file_edits.py`.
5. Re-check `origin/main` for the edits after the merge.

No `Allow-*` trailer is needed: every shared-file edit is additive.

**Rollback** restores today's state exactly, keeping any owner edits:

```bash
python3 util/configure_commit_signing.py --remove     # --dry-run first to see the plan
# by hand, the same (--fixed-value needs git 2.30 or later):
git config --global --fixed-value --unset-all 'includeIf.gitdir/i:~/Development/python/Juniper/.path' '~/.config/git/juniper-signing.gitconfig'
# git 2.50.1 and 2.51.0 drop the emptied [includeIf] header themselves (measured). An older git can leave
# it behind: remove it, but only once nothing is left under it.
git config --global --get-regexp '^includeif\.gitdir/i:~/Development/python/Juniper/\.' >/dev/null \
  || git config --global --remove-section 'includeIf.gitdir/i:~/Development/python/Juniper/' 2>/dev/null
rm ~/.config/git/juniper-signing.gitconfig && rmdir ~/.config/git
```

Delete the include by hand only when no other include still points at it. `--remove` checks this for you (round 2, N5).

## 12. Risks

| Risk | L | I | Mitigation |
|---|---|---|---|
| The owner's Juniper commits fail until B2/B3 | H | L | intended (S8); recovery steps; `--remove` |
| An IDE agent commits (owner-signed) or bypasses signing with no prompt | H until K13 | M | no card before K13 (§1); S11 touch; the AGENTS.md sentence (1 of 10 repos) and the IDEs' built-in rule; a bypass fails at merge, loudly |
| A Claude Code agent signs through `-S`, `-c include.path=`, `--config-env`, a planted local `gpg.program` or a `post-commit` hook | L | **H** | no card before C8 and K12 (§1); `--check` fails planted keys and lists hooks; S11 `on` |
| A same-user process replaces `/usr/local/bin/gpg` or the Cellar binary | L | H | not detectable by file checks (S3); C8, K12 and S11 |
| The include goes missing, and commits land unsigned | L | M | `--check` FAILs it (R6 exception) |
| A wrong Admin PIN locks the card during `set-touch` (retry `3 0 3`, no reset code) | L | **H** | §13: read the counters first, one card at a time, never retry a failed Admin PIN; offline backup (C3/D4) |
| The touch policy breaks yamaguchi's signed agent commits | M | M | S12 ruling before K8 |
| A clone outside the root lands unsigned commits | L | M | clone into the root; the hazard's `%G?` check |
| A concurrent session's whole-file upload reverts the shared-file edits | M | M | build from fresh `origin/main`; an idempotent apply script; re-check after merge |

## 13. Owner checklist (credential-bearing)

**Run every line in a real terminal**, not as `! <cmd>`. The Claude Code session carries D11's environment, which disables signing and fails K9's preflight by design. Run the steps in this order.

**No card goes into turing until C8 is installed, K12 is merged and re-installed, and K13 is done** (§1; round 2, N1). Any `gpg --card-status` writes the card's stubs, and signing is live from the moment the public key is there too.

```bash
# K13 -- IDE agent approvals (S7). VS Code: delete "/.*/", "xargs" and the fragment keys from
#        chat.tools.terminal.autoApprove. Amp: delete amp.permissions rules 28 and 39. Cursor: set
#        Approvals & Execution to Allowlist with the sandbox on, and write that attestation down now.
#        Then every "agents:" line must read "needs approval" and name no catch-all:
cd ~/Development/python/Juniper/juniper-ml && python3 util/configure_commit_signing.py --check | grep 'agents:'

# C8  -- install the agent guard from an up-to-date main (bring-up §16.2 and E-C8). The installer
#        self-tests the installed copy and exits 0 only when that passes:
cd ~/Development/python/Juniper/juniper-ml && git switch main && git pull --ff-only
bash util/install_claude_agent_guard.bash --apply
# K12 -- once the guard-rules PR has merged, re-run both C8 lines: the guard is installed as a copy.

# K8 -- rule S11 and S12 first. Per card, ONE CARD INSERTED AT A TIME (Admin PIN; never retry a failed one).
#       ykman reads the card without gpg, so no stub is written here:
gpgconf --kill scdaemon                        # scdaemon may still hold the card, and ykman then cannot connect
ykman openpgp info | tee "$TMPDIR/k8-card.txt"
awk -F': *' '$1 == "PIN tries remaining" {p = $2} $1 == "Admin PIN tries remaining" {a = $2} END {exit !(p == 3 && a == 3)}' "$TMPDIR/k8-card.txt" \
  && ykman openpgp keys set-touch sig on \
  || echo 'STOP: a PIN counter is below 3, or set-touch failed. Do not retry the Admin PIN.'
ykman openpgp info                             # "Touch policies" shows the ruled policy (never 'fixed') on the signature key

# K6 (B2) -- import from a file, then gate the trust on a fingerprint the owner reads from an
#            INDEPENDENT source: yamaguchi's `gpg --fingerprint 084FA27B796DABC4` (the primary), or the
#            "Signature key" line of `gpg --card-status` on turing (the signing subkey; the card may go in now).
curl -fsSL https://github.com/pcalnon.gpg -o "$TMPDIR/pcalnon.gpg"
gpg --show-keys --with-subkey-fingerprints "$TMPDIR/pcalnon.gpg"
gpg --import "$TMPDIR/pcalnon.gpg"
read -r -p 'Fingerprint as read from the independent source: ' FPR; FPR=$(printf '%s' "$FPR" | tr -d ' ' | tr 'a-f' 'A-F')
KEYS=$(gpg --with-colons --with-subkey-fingerprints --fingerprint 084FA27B796DABC4)
case "$FPR" in 06DBAC384131E0380D89923F084FA27B796DABC4|B5619F58FDA4D94E2D73D8BABA18D1A733B1831A) ;; *) FPR=no-match ;; esac
printf '%s\n' "$KEYS" | grep -q "^fpr:::::::::$FPR:" \
  && printf '%s\n' "$KEYS" | grep -q '^fpr:::::::::06DBAC384131E0380D89923F084FA27B796DABC4:' \
  && echo '06DBAC384131E0380D89923F084FA27B796DABC4:6:' | gpg --import-ownertrust \
  || echo 'STOP: the fingerprints disagree. Trust was NOT set.'
curl -fsSL https://github.com/web-flow.gpg | gpg --import         # no trust: main's squash commits then show U

# K7 (B3) -- per card, one at a time:
gpg --card-status
gpg-connect-agent "scd serialno" "learn --force" /bye
echo t | gpg --clearsign -u 'B5619F58FDA4D94E2D73D8BABA18D1A733B1831A!' >/dev/null && echo SIGN-OK
gpg --list-keys --with-colons 084FA27B796DABC4 | grep '^uid' | grep -c '<paul.calnon@gmail.com>'   # UID check (B4b)

# K9 -- from this real terminal, on an up-to-date main:
cd ~/Development/python/Juniper/juniper-ml && git switch main && git pull --ff-only
python3 util/configure_commit_signing.py --check
bash util/headless_signing_preflight.bash --repo .
# K10 -- the I-SIGN matrix (§10.2), then per SHA:
gh api repos/pcalnon/juniper-ml/commits/<sha> --jq .commit.verification
```

The trust gate needs three values to agree: the owner's reading from the independent source, a fingerprint in the imported key, and the repo text (§3). An agent that edited the repo text still could not get trust set. `gpg --card-status` prints the signing subkey's fingerprint, not the primary's, so the gate accepts either.

## 14. Validation record

### 14.1 Investigation log (2026-10-19, turing)

1. Read the bring-up plan in full (arc B, D3, D11, §16, §17) and the audit's signing sections.
2. Read the configuration at every scope (global, system, XDG, the 10 repo-local files) and the session environment. No key material was read, and no credential probe was run.
3. Verified a yamaguchi-signed commit with `%G?`, which needs public keys only. It read `E`, so B2 is open.
4. Read the IDE bundles' git extension (`package.json`, `package.nls.json` and the commit argv in `dist/main.js`), the VS Code workbench's auto-approve code, and the IDE, workspace and folder settings.
5. WebFetch timed out (300 s) on every documentation URL. That fits turing's per-application outbound filter (bring-up §17.3, E-NET-2), and it was not worked around. The §5 sources were confirmed through WebSearch excerpts and the installed software.

### 14.2 Consensus round 1 (2026-10-19): 3 × ACCEPT-WITH-CHANGES, 0 BLOCKER

**Method.** Three independent, read-only reviewers worked on v0.9.0, each with its own lens. None was allowed to run credential probes. Each re-measured host facts and ran hermetic git experiments in its own scratch directory.

| Reviewer | Lens | MAJOR | MINOR | NIT |
|---|---|---|---|---|
| R1 | evidence and correctness | 3 | 12 | 8 |
| R2 | security and operational risk | 3 | 10 | 4 |
| R3 | feasibility, dependencies, testability | 4 | 17 | 3 |

**MAJOR findings, all applied:**

- **R1:**
  - `! <cmd>` carries D11's environment, so K9 and K10 must run in a real terminal or IDE (§13);
  - the AGENTS.md sentence reaches 1 of 10 repos, so the built-in IDE rule becomes layer 0, K13 becomes primary, and K14 is added (S7);
  - the integrity check cannot stop a same-user agent, so the plan now has the known-install rule, the include-key and planted-key checks, and K7 waiting for K12 (S3, S9).
- **R2:**
  - after K7, every IDE agent would sign silently, so K7 now waits for K8, K13, C8 and K12, the touch policy has its own ruling, and "agents cannot sign" is scoped (§1, S7, S11);
  - the VS Code deny regex was easy to get around, so the robust pair replaces it, plus the primary clean-up and the `--check` evaluator inputs (S7, §8);
  - the hijack vectors (local config, hooks, `-c include.path=`, `--config-env`) are now covered by `--check`'s planted-key and hook checks, K12's list and the risk re-rating (S9, §12).
- **R3:**
  - the pattern is now rendered from realpaths, with exit-2 refusals and R-S15 (S1);
  - the auto-approve evaluation got its real inputs, Cursor became an attestation, and K13's acceptance changed (§8, K13);
  - K10 depends on A3 (§9);
  - D11 does not stop `-S`, so K7 waits for C8 and R-S4 pins the boundary (§7.2, §9).

**MINOR and NIT findings applied:**

- **Facts.** Cursor's fork differs from VS Code's, and a D11-inherited IDE is a new failure mode (§3, §7.3). Corrected or added: the default-deny wording, the Amp numbering, the root `.vscode`, profile environments, the machine scope of `git.path`, R1's command list, G-SIGN's evaluation, the citations, and the card naming by serial.
- **The tool:**
  - environment-redirect INFO; the scrub list; the Python 3.9 interpreter test; the in-suite flake8 gate;
  - mkdir 0700 and a Python-written header; R-S8 with the same-pattern layout; an exact rollback (`--remove`, `--fixed-value`);
  - the global-file rule; the dry-run exit; the key grammar; `--include-file` refusals;
  - platform-independent IDE paths and profiles; JSONC cases; an injectable date; the YOLO FAIL.
- **Owner steps:**
  - landing via the retry pusher; the `:75` count; the `main-verify.yml` mirror;
  - I-SIGN with Commit Empty, Dock launches, T7 under the root, and agent prompt rows;
  - K12's command forms; the K6 verification and gated trust; the PIN-lockout guard; the yamaguchi ruling; S8 recovery;
  - R4 scoped; S4's tag behaviour pinned; the `fixed` wording; the gpg default-key wording; the D5 line erratum.

**Declined, with reasons:**

- **R1:** adding the hazard to all 10 AGENTS.md now. Declined because that is nine more PRs over turing's link; K14 is the follow-up, and K13 is the primary layer.
- **R2: three items:**
  - **Evaluating VS Code's default rules.** They allow only read-only git commands, so leaving them out can only over-report.
  - **Ignoring `COMMIT_SIGNING_GPG_CANDIDATES` without `--gpg-program`.** Candidates still pass the soundness rule, the chosen program is printed, and the hermetic tests need the variable.
  - **Failing a group-writable directory on the path.** turing's real `/usr/local/bin` and Cellar are `admin`-writable, and so would fail. That is recorded as a residual risk (S3), as R3 advised.
- **R2, modified:** the owner reviews `--apply --dry-run` before K5. K5 runs at the owner's explicit request instead. It fails closed, and nothing can sign before the owner's K7. The plan is recorded in the PR, and `--remove` undoes it.
- **R3:**
  - **Running K5 after merge from an up-to-date checkout.** It runs from this PR's worktree, the identical code, so the PR's record is true; re-running is idempotent.
  - **Amp's evaluation spec.** Implemented best-effort from Amp's first-match rule, which its legacy permissions page states.

### 14.3 Consensus round 2 (2026-10-19): ACCEPT-WITH-CHANGES, 0 BLOCKER

**Method.** One independent, read-only reviewer checked v1.0.0 against every round-1 MAJOR, and the implementation against §8 and §10.1. It ran no credential probe. It ran:

- the suite: 50 of 50 at the time, under JuniperPython 3.14.3, including the `/usr/bin/python3` and flake8 tests;
- a read-only `--check` on the real host, which showed the pre-K5 state that §3 describes;
- hermetic git experiments in its own scratch directory.

**The round-1 MAJORs.** All ten were applied, and nine were resolved. #5, the deny regex, was only partly resolved. The listed spellings and both false positives were fixed, but the pair was still not robust, and K13 could be accepted with `/.*/` still in place (N2).

**New findings, all applied (1 MAJOR, 12 MINOR, 5 NIT):**

| ID | Class | Finding | Applied as |
|---|---|---|---|
| N1 | MAJOR | any `gpg --card-status` makes gpg-agent `LEARN` the card, which writes the stubs. So signing goes live at K6, not K7, and §9 gave K6 and K8 no guard dependency | §1's rule: no card goes into turing until C8 is installed, K12 is merged and re-installed, and K13 is done. K6 and K8 depend on C8, K12 and K13, and K7 no longer claims to make signing live. S7, S11, §7.2, §10.3 and §12 are reworded. K8 reads the card with ykman, which writes no stub |
| N2 | MINOR | "covers every bypass spelling" held only for §8's list. An abbreviated option, `help.autocorrect`, `-c alias.*`, and writes to `gpg.<format>.program`, `core.hooksPath` and `core.fsmonitor` all passed the pair | six probes added, 17 in all, each measured. K13 is accepted only once `/.*/`, `xargs` and the fragment keys are gone; the pair is a dated interim. `--check` names any catch-all allow rule in VS Code and any unconditional `Bash allow` in Amp |
| N3 | MINOR | VS Code turns a rule that matches the empty string into a never-match. The tool did not, so a stray `\|` in a deny rule under-reported | modelled (`.*` and the bare anchors excepted), with an R-S14 case |
| N4 | MINOR | any `…/Cellar/gnupg/<v>/bin/gpg` counted as a known install, even under `/tmp` | only Homebrew's own Cellar directories count; `COMMIT_SIGNING_GNUPG_CELLARS` replaces them, for the tests (S3, R-S18) |
| N5 | MINOR | `--remove` for one root deleted an include another root still used, which then failed open | the file is kept while any global include still resolves to it (§8, `--remove` step 3) |
| N6 | MINOR | `--apply` wrote through a pre-existing symlinked include into the link's target | an unsafe include or directory stops `--apply` with exit 2 before any write, and R-S9 snapshots the temp `HOME` (§8, R-S17) |
| N7 | MINOR | the PIN-counter guard fired on the reset code's `0`, and it was only a comment | a conditional on the PIN and Admin PIN counters, which skips `set-touch` (§13). Tested on canned `ykman openpgp info` text under `/bin/bash` 3.2.57 |
| N8 | MINOR | scdaemon may still hold the card after `--card-status`, so ykman cannot connect | `gpgconf --kill scdaemon` first (§13) |
| N9 | MINOR | no fast-forward before C8 and K9, and the primary checkout lacked the tool | `git switch main && git pull --ff-only` before both (§13) |
| N10 | MINOR | the trust gate compared against repo text, and the independent check was only a comment | the gate needs three values to agree: the owner's reading from an independent source, the imported key and the repo text. It also accepts the card's subkey line (§13). Tested on canned key listings |
| N11 | MINOR | K13 deferred the Cursor attestation to K11, which runs after K7 | recorded at K13; K11 files it (§9, S7) |
| N12 | MINOR | K12's acceptance was "merged", but the guard is installed as a copy | merged; re-installed by re-running C8, whose installer self-tests the copy; both `--config-env` forms denied (§9, S9) |
| N13 | MINOR | planted keys were judged only in the 10 primary checkouts, at local or worktree scope, and K12 lacked direct file writes | each linked worktree's `config.worktree` is judged. Global and system hook, monitor, ssh and include settings are an INFO. K12 covers `.git/config`, `config.worktree` and the system gitconfigs (§8, S9) |
| N14 | NIT | K9 said D11 fails both commands, but `--check` passes under D11; and the `session` line named only C8 | K9 reworded; the line names C8 and K12 |
| N15 | NIT | §10.1 asserted the mutation result while §14.4 said "Pending". On the 21:14 suite S24 survived | recorded in §14.4 and re-run on the final suite |
| N16 | NIT | stale `:75 (213 → 214)` and `AGENTS.md:47-52` | K3 cites :79 and a count recomputed at upload; §15 cites :47-56 |
| N17 | NIT | the by-hand rollback had no `--remove-section` | added, guarded to run only on an empty section; git 2.50.1 and 2.51.0 drop the header themselves (measured, §11) |
| N18 | NIT | "managed" ignored values and comments, and a hooks path under `~/.ssh` was listed | the include must be byte for byte what `--apply` writes; a hooks path in a credential directory is never listed or read |

**Citations.** The reviewer's spot-check found every reference accurate except the two N16 lines.

### 14.4 Mutation evidence

Pending (K2).

## 15. References

- `notes/JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md`: D3 (:250-262), D11 (:341-356), arc B (:396-408), G-SIGN (:596), §16.2 B1 row (:851), §17.2 D5 row (:903), §17.3 E-C8 (:918)
- `notes/JUNIPER_2026-08-09_JUNIPER-ECOSYSTEM_HEADLESS-SIGNING-AND-SERENA-HARNESS-AUDIT.md` (the audit): §3.1 (:76-87), A1-F2 (:169), §3.3 (:241-254), A1-F4 (:256-304) including the card status (:276-286), A1-F5 (:308-329), A1-F9 (:390-406), A1-F11 (:419-423)
- `notes/JUNIPER_2026-08-09_JUNIPER-ECOSYSTEM_STANDING-ITEMS-CLOSEOUT-AND-HARNESS-REMEDIATION-PLAN.md:952`: the master fingerprint
- `util/headless_signing_preflight.bash` (B7): the D11 override detection (:253-273) and the commit-gpgsign check (:288-299)
- `util/claude_agent_guard.py`: CRED-PATH-BASH (:152), GPG-SIGN (:157), the `-c`/`--config-env` handling (:1105-1111)
- `util/git_remote_alias_check.py`: the repository-local environment scrub this tool copies (:193-211, :386-395)
- `util/worktree_cleanup.bash:372`: the owner tool's `git merge`
- `util/juniper-backup.bash:211-214`: the 3c and 3a recipient UIDs
- `prompts/thread-handoff_automated-prompts/HANDOFF_2026-08/HANDOFF_2026-08-07_pr-backlog-processing-fleet-merge-waves.md:13`: yamaguchi's signed agent commits
- `AGENTS.md:47-56`: the unsigned-commit hazard, with this plan's sentence (K3)
