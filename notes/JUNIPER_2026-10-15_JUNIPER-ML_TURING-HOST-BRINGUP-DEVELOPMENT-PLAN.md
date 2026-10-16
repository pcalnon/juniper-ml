# Turing host bring-up — development plan

- **Project**: Juniper ecosystem. The plan lives in juniper-ml; it touches juniper-ml, juniper-k8s and juniper-recurrence, plus the host's own configuration.
- **Author**: Paul Calnon (investigation and drafting via a Claude Code session on turing)
- **Date**: 2026-10-15 (round-1 reconciliation 2026-10-16)
- **Version**: 1.0.0 — v0.9 plus every round-1 finding integrated (§15.1)
- **Status**: VALIDATED. Consensus round 1 had 3 reviewers, all ACCEPT-WITH-CHANGES and no BLOCKER; all findings at MAJOR and above were applied; round 2 (§15.2) found 1 MAJOR, which was applied. The plan authorizes the tasks in §6. Tasks marked **OWNER** need the owner at the keyboard.
- **Owner**: Paul Calnon
- **Template**: `notes/templates/TEMPLATE_DEVELOPMENT_ROADMAP.md`, adapted to a single-host bring-up
- **Session prompt**: `prompts/manual/prompt133_2026-10-15.md` (defines the work arc; not versioned)
- **Evidence script**: [`util/ad-hoc/2026-10-15_turing_host_state_probe.bash`](../util/ad-hoc/2026-10-15_turing_host_state_probe.bash) is read-only; Appendix A is its output.

---

## 1. Executive summary

turing is a 15-inch 2018 MacBook Pro: Intel i7-8850H with 6 cores and 12 threads, **16 GiB of soldered RAM**, macOS 15.7.1. The ecosystem documents give it two roles: one Ubuntu **worker VM** in the k8s cluster and, per the session prompt, a **secondary development host** behind yamaguchi. As measured, turing can do neither reliably today.

The five findings that drive the plan, all measured 2026-10-15 and re-measured by reviewers 2026-10-16:

1. **Git auth fails on exactly the two repos whose remotes skip the per-repo SSH alias.**
   - `juniper-k8s` uses `git@github.com:` and `juniper-recurrence` uses `https://`.
   - The other 8 repos use `git@github_juniper-<repo>:`.
   - Rewriting the remotes fixes the client side (§4.1). Deploy-key registration on GitHub is an OWNER step.
2. **Commit signing is not configured on turing.**
   - There is no `user.signingkey` and no `commit.gpgsign`.
   - turing's own commits show `%G?` = `N` (unsigned). Every other commit shows `E` because the signer's public key is not in turing's keyring.
   - The repos carry `required_signatures` (`util/open_signed_pr.py:15-19`: all 9 as of 2026-08-12; juniper-k8s is unverified).
   - **Any local commit on turing makes its branch unmergeable.** That includes the in-flight `feat/adding-new-util-scripts-for-keys` (`651e4793`, `N`). This plan itself lands through `open_signed_pr.py` for the same reason.
3. **The documented VM sizing can't fit.**
   - The primer gives macOS 16 GB and the VM the rest, which on this machine leaves about 0 GB for the VM.
   - Under desktop load, swap was 13.7 of 15.4 GB at probe time (15.7 of 16.4 GB at review).
   - The RAM can't be upgraded. D1 sets a new size.
4. **Security posture fails the primer's hardening line (4 of 5 checks).**
   - SIP is disabled ("Custom Configuration").
   - The application firewall is off.
   - Exported private-key files and GitHub recovery codes sit on disk under `~/.ssh` and `~/.gnupg` (names only; contents were not read).
   - An AWS `.pem` key is readable by everyone (mode 644).
5. **The toolchain is incomplete and stale.**
   - 10 ecosystem tools are missing: `shellcheck`, `markdownlint-cli2`, `yamllint`, `actionlint`, `sops`, `age`, `yq`, `ykman`, `pinentry-mac`, `timeout` (coreutils). `iperf3` is missing too.
   - Docker 20.10.11 and `kubectl` 1.22.4 both date from 2021; the documented cluster is 1.36.x.
   - pre-commit's gitleaks environment fails to bootstrap: the Go module download timed out.
   - `~/.claude/agents` does not exist.
   - The parent `Juniper/AGENTS.md` is absent.

The work runs as **eight orthogonal arcs** (§6):

- **P0, all independent:** A (auth), B (signing), C (security).
- **Next:** D (toolchain) and E (dev parity).
- **Gated:** F (k8s VM) waits on D1 and a measured memory-headroom gate.
- **Alongside:** G (tooling, tests, CI) and H (MCP and agents).

## 2. Current state (measured)

Values come from turing unless the Source column names a document. Where a document and a measurement disagree, the measurement wins, and §3 lists the correction the document needs. Memory and disk figures are volatile, recorded *at probe time*; F3 produces the real baselines.

### 2.1 Hardware and OS

| Item | Documented | Measured | Gap |
|---|---|---|---|
| Model | "16" 2019 i7, ≤ 64 GB" (primer :26); "15 inch" (prompt133:15) | i7-8850H with Radeon Pro 560X, which is the 15-inch 2018 | primer wrong |
| CPU | "6 cores/12 threads" (primer :26) | `hw.physicalcpu`=6, `hw.ncpu`=12; VT-x (`VMX`); `kern.hv_support`=1 | none |
| RAM | "≤ 64 GB", VM "≈ 44 GB" (primer :26, :386) | `hw.memsize`=17179869184 (16 GiB), soldered | **blocks** the documented VM (D1) |
| Memory pressure | — | swap 13.7 / 15.4 GB used; "free" 58% (Firefox ×10 processes, Cursor, 2× claude) | no headroom |
| Disk | — | APFS 500 GB, 76–86 GB free (Data volume ≈ 82% full) | a 60 GB VM disk is tight |
| GPU | prompt133:16 | Radeon Pro 560X 4 GB (Metal 2), UHD 630 (Metal 3) | no use for k8s or PyTorch |
| OS | 15.7.1 (24G231) | `sw_vers` 15.7.1 / 24G231, x86_64 | none |
| Hostname | `turing.midcoip.net` (`juniper-k8s/util/node_scripts/testing/hosts:7`) | `turing.midcoip.net` | none |
| Power | `sleep 0 disksleep 0 standby 0 autorestart 1` (primer :394) | `sleep 0` (held by caffeinate), `disksleep 0`, **`standby 1`**, `powernap 1`, `womp 1`; autorestart unset | apply the primer's `pmset` line (C7) |

### 2.2 Network

| Item | Documented | Measured | Gap |
|---|---|---|---|
| IP | `.222` (testing hosts, handoffs); ".60 or .100 (unresolved)" (primer :63, :72; `juniper-k8s/inventory/hosts.yaml:33`) | Wi-Fi `en0` = **192.168.50.131** | three documented values, none matching |
| Bridge NIC | "USB-C→RJ45 dongle, bridged" (primer :381, :403-406) | **`en7`** "USB 10/100/1000 LAN", Realtek `00:e0:4c:68:06:b1`: **no carrier** (`media: autoselect (none)`, inactive) | no link (F2) |
| `en5` | — | `ac:de:48:00:11:22`, 100baseTX: the **Apple T2 internal iBridge** link, not a network port | ignore |
| `/etc/hosts` | — | only `kubernetes.docker.internal` (a Docker Desktop leftover) | — |

### 2.3 Security posture

| Item | Target (primer :713) | Measured | Gap |
|---|---|---|---|
| FileVault | on | On | none |
| App firewall | on | **disabled** (State = 0) | C2 |
| SIP | (hardened) | **disabled**, "Custom Configuration", all protections off except BaseSystem verification | C1, D5 |
| Remote Login | admin only | not measurable without admin | C5 (OWNER) |
| Updates | automatic security updates | "Automatic checking … on"; install policy not measured | C5 |
| Key material at rest | — | `~/.ssh/priv.asc`, `~/.ssh/pub.asc`, `~/.ssh/github-recovery-codes.txt`, `~/.gnupg/0xCC413455A72974D0.sub_priv.asc`, dirs `~/.gnupg/{gen3,gen3-OLD,gen3a,bla}` (names only; contents never read) | C3, D4 |
| Key perms | ssh rejects keys readable by others | `~/.ssh/id-turing-aws-ec2.pem` **644**; `~/.ssh/config` 644 | C4 |

### 2.4 Git, SSH and signing

| Repo | origin | `%G?` (last 5) | Diagnosis |
|---|---|---|---|
| juniper-canopy | `git@github_juniper-canopy:…` | `NEEEE` | alias OK; local head unsigned |
| juniper-cascor / -cascor-client / -cascor-worker / -data / -data-client / -deploy | `git@github_juniper-<repo>:…` | `EEEEE` | alias OK |
| **juniper-k8s** | **`git@github.com:pcalnon/juniper-k8s.git`** | `EEEEE` | **no alias**: falls to the default identity |
| juniper-ml | `git@github_juniper-ml:…` | `NEEEE` | alias OK (fetch verified in-session); `651e4793` unsigned |
| **juniper-recurrence** | **`https://github.com/pcalnon/juniper-recurrence.git`** | `EEEEE` | **HTTPS**: osxkeychain credential, not the deploy key |
| juniper-legacy | — | — | not a git checkout (archive) |

**SSH**

- `~/.ssh/config` has a `Host github_juniper-<repo>` block for all 10 active repos. Each sets `IdentityFile ~/.ssh/id_ed25519_github_juniper-<repo>`, `IdentitiesOnly yes`, `AddKeysToAgent yes` and `UseKeychain yes`.
- All 10 private keys are mode 600.
- `id_rsa.pub` has no matching private key.
- There is no default `id_ed25519`.

**Git**

- Global git config sets only `user.name`, `user.email=paul.calnon@gmail.com`, `credential.helper=osxkeychain`, `credential.usehttppath=true` and a log alias.
- It does **not** set `user.signingkey`, `commit.gpgsign`, `tag.gpgsign` or `gpg.program`.
- `git log --format='%G? %GK' origin/main` reports `E B5690EEEBB952194`, GitHub's web-flow key, on squash-merged `main` commits.

**GnuPG**

- GnuPG 2.4.8 comes from Homebrew (`/usr/local`, Intel prefix). `/opt/local/bin/gpg` is a MacPorts-path symlink into the Homebrew Cellar, and it comes first on `PATH`.
- `gpg-agent.conf` sets `enable-ssh-support` and `pinentry-program /usr/local/bin/pinentry`. That is the curses pinentry, which can't prompt from a GUI or headless process.
- `SSH_AUTH_SOCK` is the gpg-agent socket. `GPG_TTY` is unset.
- turing's `~/.gnupg/sshcontrol` exists but was **not** inspected (OWNER check, §14.1).

**yamaguchi's target** (`notes/JUNIPER_2026-08-09_JUNIPER-ECOSYSTEM_HEADLESS-SIGNING-AND-SERENA-HARNESS-AUDIT.md`)

- Config (:78-81): `user.signingkey=B5619F58FDA4D94E2D73D8BABA18D1A733B1831A!`, `gpg.program=gpg2`, `commit.gpgsign=true`, `tag.gpgsign=true`.
- Keys (:251-254): master `084FA27B796DABC4`; sign subkey `BA18D1A733B1831A`, which expires 2028-08-06.

### 2.5 Toolchain and environment

| Tool | Measured | Need |
|---|---|---|
| Homebrew | 5.1.10; 139 formulae outdated | single package manager (D6) |
| git / gh | 2.51.0 / 2.88.1 | OK |
| conda / mamba | 25.9.1 / 2.1.1; miniforge `/usr/local/miniforge3`; legacy `~/opt/anaconda3` (dynet, pytorch_cpu, pytorch_cuda) | one distribution (D8) |
| Conda envs | `JuniperPython` only (3.14.3) | AGENTS.md names `JuniperCanopy1`, `JuniperCascor1`, `JuniperData` |
| uv / pre-commit / node | 0.10.7 / 4.3.0 / 25.8.1 | OK; **gitleaks hook env fails to build** (Go proxy timeout) |
| shellcheck, markdownlint-cli2, yamllint, actionlint, sops, age, yq, ykman, pinentry-mac, timeout, iperf3 | **missing** | D0 / D1-tools |
| VirtualBox | 7.2.0r170228; 2 VMs `<inaccessible>` (E_ACCESSDENIED); `~/VirtualBox VMs/{Win10_New,Win10_Old}` | upgrade to latest 7.2.x; clean up (C6) |
| Docker | 20.10.11 client and server (2021) | D7 |
| kubectl / helm | 1.22.4 / 4.1.4 | kubectl within ±1 minor of 1.36 |
| Claude Code | 2.1.301; `~/.claude/agents` **absent**; repo `.claude/agents` has 6 agents | H1 |
| MCP | `~/.claude/mcp-servers/` holds `adaptive-graph-of-thoughts`, `agi-mcp-server`; `claude mcp list` hung > 120 s | H0, §10 |
| Parent `Juniper/AGENTS.md` | **absent** | E4 |

## 3. Documented target and required corrections

The procedure of record is `juniper-k8s/notes/JUNIPER_2026-09-24_JUNIPER-ECOSYSTEM_KUBERNETES-PRIMER.md`. Its header says it is "not yet executed on the hardware" (:4). For turing it specifies:

- turing is never control plane (:47) and gets no Longhorn disk (:621, :628).
- macOS is "only a host and an admin client" (:28, :381).
- One Ubuntu 26.04.1 amd64 VM, `juniper-macvm`, on VirtualBox (chosen over UTM, :387), with a NIC bridged to the dongle (:403-406) and LaunchDaemon autostart (:409).
- Cluster stack: kubeadm, k8s 1.36.x, containerd 2.2.2, Cilium 1.20.x without kube-proxy, Longhorn 1.12.x (:76-89, :116).

Corrections owed (task E5 in juniper-k8s, task E6 in juniper-ml):

| # | Document : line | Says | Should say |
|---|---|---|---|
| X1 | primer :26 | "16" 2019 i7 ≤ 64 GB" | "15-inch 2018, i7-8850H 6C/12T, 16 GiB soldered" |
| X2 | primer :386 | "≈ 8 vCPU and 44 GB" | the D1 sizing (4 vCPU / 6 GiB, gated) |
| X3 | primer :63, :72; `inventory/hosts.yaml:33` | ".60 or .100 (unresolved)" | the address reserved in A6; bridge NIC `en7` |
| X4 | `util/node_scripts/testing/hosts:7` | `192.168.50.222` | same as X3 |
| X5 | `inventory/hosts.yaml:30` | `ansible host:` | `ansible_host:` |
| X6 | handoffs 2026-09-11 → 2026-10-03; `reports/2026-10-04_consolidated-development-plan/extraction-P4-release-P11-k8s.md:65` (P4-27) | "turing down 09-22 (UNVERIFIED)", treated as a Pi-pull runner | turing is an amd64 Intel Mac in active use (`notes/JUNIPER_2026-08-22_JUNIPER-ECOSYSTEM_BYPASS-CANDIDATE-DETERMINATION.md:174`) |
| X7 | `notes/JUNIPER_2026-07-16_JUNIPER-ECOSYSTEM_CODE-SIGNING-KEY-MIGRATION-STATUS.md` | ed448 `93E8591643C507FF` as signing key | superseded by `BA18D1A733B1831A` (audit A1-F1/F2) |
| X8 | primer :184 `juniper_cluster`; `ws-05_make-distribute-ssh-keys.bash:19` `juniper_k8s`; `hosts.yaml:17` `id_ed25519_pi_cluster` | three admin-key names | one name (k8s-side decision; flagged here, not decided) |
| X9 | `juniper-k8s/AGENTS.md:1-7` | juniper-ml's header verbatim | juniper-k8s's own header |
| X10 | AGENTS.md / REFERENCE.md worktree paths | `/home/pcalnon/...` | `$HOME`-relative wording (turing's home is `/Users/pcalnon`) |

## 4. Known issues — root cause

### 4.1 GitHub authentication (juniper-k8s, juniper-recurrence)

**How the alias design works.**

- `IdentitiesOnly yes` plus a per-repo `Host` alias means ssh offers exactly one key: that repo's deploy key.
- A deploy key authenticates for one repository only.

**Why the two repos fail.**

- A `git@github.com:` remote bypasses the alias.
- ssh then falls back to the default identities: the gpg-agent socket (the YubiKey auth subkey, if a card is inserted and its keygrip is in `sshcontrol`), then the default `~/.ssh/id_*` files. turing has no usable default file.
- On **yamaguchi**, `sshcontrol` holds a fingerprint where a keygrip belongs, which makes gpg-agent SSH latent (audit A1-F9, :390-406). turing's `sshcontrol` is not inspected yet (§14.1).
- Either way, auth fails unless a card happens to work. That matches the prompt's "failing for several newer repos while working for others".
- `juniper-recurrence` over HTTPS depends on an osxkeychain token that may be absent or expired.

**Contributing cause: the clone helper.**

- `util/git_clone_with_specified_id.bash:6` (on the in-flight branch) clones with `GIT_SSH_COMMAND="ssh -i …" git clone git@github.com:…`.
- The persisted `origin` is the bare `github.com` URL. That is how juniper-k8s ended up broken for later fetches.
- Without `IdentitiesOnly`, `-i` also offers other identities.

**Possible contributing cause: `AddKeysToAgent yes` with `SSH_AUTH_SOCK` on gpg-agent.**

- ssh hands each key to gpg-agent, and gpg-agent asks via pinentry for a protection passphrase.
- With the curses pinentry this hangs headless sessions. With pinentry-mac it would pop up GUI dialogs.

**GitHub side (not measurable here).**

- The census counts **8** "Deploy Key - Turing" entries dated 2026-05-07 (`notes/JUNIPER_2026-08-20_JUNIPER-ECOSYSTEM_BYPASS-ACTOR-CENSUS.md:166`).
- There are 10 active repos today, and juniper-k8s did not exist when the keys were counted.
- Keys must be write-enabled to push.

**Fix:** A1 (rewrite remotes), A8 (`AddKeysToAgent no`), A2 (verify and register keys; OWNER), A3 (auth matrix gate), A4 (replace the clone helper).

### 4.2 Code signing

**Primary cause.** turing has no signing configuration (§2.4), so every local commit is unsigned and blocks the merge. Squash does not rescue it (`util/open_signed_pr.py:15-19`).

**Secondary causes.**

- turing's keyring lacks the owner's public key.
- The curses pinentry can't prompt for a card PIN.

**Unresolved: are the two YubiKeys clones or two keys?**

- On yamaguchi, gpg ties each card stub to one card serial (audit A1-F4, :256-304), which assumes both cards carry the *same* subkeys.
- But `util/juniper-backup.bash:211-214` lists two **distinct** recipient UIDs (`…Yubikey-3c_2026-08-06`, `…Yubikey-3a_2026-08-11`), which suggests two separate keys.
- B3 resolves this before choosing the stub model (D3).

**Fix:** arc B with D3.

## 5. Decisions

Each decision gives options with strengths, weaknesses, risks and guardrails, then a recommendation. **OWNER** decisions need a ruling before their dependent tasks start. The others take the recommendation by default.

### D1 — k8s role and VM sizing (OWNER)

| Option | Strengths | Weaknesses | Risks | Guardrails |
|---|---|---|---|---|
| a. Admin client only | zero memory cost | loses the documented amd64 worker | docs drift | X2 records it |
| b. **Gated small worker: 4 vCPU / 6 GiB / 60 GB, "node mode" only** | keeps the role at a size that fits; amd64 image tests | fits light pods only; competes with dev use | macOS swap storm; NotReady flaps | G-MEM before start; kubelet `--system-reserved`; taint `turing=constrained:NoSchedule`; autostart **off** |
| c. Documented ≥ 8 vCPU / 44 GB | matches the primer | **physically impossible** | — | — |
| d. Replacement hardware | a proper node | cost; out of scope | — | — |

**Recommendation: b, falling back to a automatically whenever G-MEM fails.** A 6 GiB VM leaves about 10 GiB to macOS, which still swaps under today's load. So the gate requires macOS headroom *before* start: node mode never stacks on a full desktop. The taint keeps only tolerating workloads (smoke tests, amd64 image validation) on the node.

### D2 — GitHub transport authentication

| Option | Strengths | Weaknesses | Risks | Guardrails |
|---|---|---|---|---|
| a. **Per-repo deploy keys via `Host` aliases (current design)** | one repo per key; passwordless; headless; 8/10 in place | one key and alias per repo | each **write** deploy key is also a `DeployKey` **ruleset bypass actor** on `main` (deletion, non-fast-forward), per census §3b, kept by owner ruling (`…BYPASS-CANDIDATE-DETERMINATION.md` §4b). Ten passphrase-less write keys on a laptop that travels and runs agents | mode 600; FileVault; `IdentitiesOnly`; G-ALIAS; fixed title `Deploy Key - Turing`; **lost-device runbook** (§13); keys added via the web UI, not `gh` (below) |
| b. YubiKey auth subkey via gpg-agent SSH | hardware-bound; one key | needs the card plus PIN or touch; useless to agents | agent hangs | interactive fallback only |
| c. HTTPS + `gh` token | simple | account-wide token; expiry | wide blast radius | retired for transport |

**Recommendation: a for all repos, b as the interactive fallback, c retired** (juniper-recurrence moves back to SSH).

- **Add deploy keys through the GitHub web UI, not `gh repo deploy-key add`.** Per `gh repo deploy-key add --help`, keys added by gh are bound to the current token and **deleted when that token is revoked**. A token rotation would silently break every repo.
- New repos get a key and alias through `util/juniper_repo_ssh_setup.bash` (A5), which prints the web-UI step.

### D3 — Commit signing from turing

| Option | Strengths | Weaknesses | Risks | Guardrails |
|---|---|---|---|---|
| a. **YubiKey GPG sign subkey `BA18D1A733B1831A!`** (yamaguchi's) | one identity across hosts; hardware-bound; uploaded to GitHub | card + PIN; stubs per card serial | agent hangs or silent owner-signing with a cached PIN; card contention (`notes/JUNIPER_2026-07-16_JUNIPER-ECOSYSTEM_CODE-SIGNING-KEY-MIGRATION-STATUS.md` §3.3) | pinentry-mac; touch policy `cached`; `no-allow-external-cache`; agents unsigned by construction (D11) |
| b. On-disk SSH signing key (`gpg.format ssh`) | headless | a file on disk can sign as the owner | silent compromise | rejected |
| c. **GitHub-API signing (`util/open_signed_pr.py`, `createCommitOnBranch`)** for agent and headless commits | no key on the host; the ecosystem's headless path (`notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md:1192`) | file-level only; needs a write-capable gh token | token theft = repo write | fine-grained PAT (D11); `--dry-run` first; refuses existing branches and PRs |

**Recommendation: a for interactive owner commits, c for every agent or headless commit, b rejected.**

- If B3 shows the two cards hold the *same* subkeys: learn stubs per card (`gpg-connect-agent "scd serialno" "learn --force" /bye` after each swap).
- If they hold *different* sign subkeys: upload both public keys to GitHub, and set `user.signingkey` per card through a small `git config` switch script. `!`-pinning still applies.
- Record the serial-to-name mapping (3a / 3c) in B6.

### D4 — Private-key material on disk (OWNER)

| Option | Strengths | Weaknesses | Risks | Guardrails |
|---|---|---|---|---|
| a. **Offline, symmetrically encrypted backup, then delete** | removes at-rest exposure; keeps recovery | owner time | deleting the only copy of the master key | see the steps below; never delete before a test decrypt |
| b. Leave in place (FileVault covers it) | none | any local process (agents, packages) can read it | exfiltration | — |

**Recommendation: a.** Do **not** use `util/juniper-backup.bash` for this. It archives repo trees (`APPLICATION_REPOS`, :133) and encrypts to the two YubiKey-backed recipients (`ENCRYPT_KEYS`, :211-214). That is circular if `priv.asc` is the master for those very cards.

Steps:

1. Write the files to offline media, encrypted with `gpg -c` or an age passphrase, and store that media apart from both YubiKeys.
2. Test-decrypt and compare sha256 sums.
3. Delete the originals.
4. Check `tmutil listlocalsnapshots /` and Time Machine destinations for retained copies.
5. **Regenerate** the GitHub recovery codes (Settings › Password and authentication), which invalidates the file. Store the new set in the password manager.
6. Record an **exposure assessment**: the files were readable for months with SIP off and agents running. Decide on master or subkey rotation.

This plan never reads those files.

### D5 — SIP and firewall (OWNER)

- **Recommendation:** run `csrutil enable` from recoveryOS, then check with `csrutil status` and `csrutil authenticated-root status`. Approve the Oracle system extensions in System Settings › Privacy & Security and reboot. VirtualBox 7.2 on Intel needs kext approval, not SIP off. Upgrade VirtualBox from 7.2.0 to the latest 7.2.x at the same time.
- Turn on the application firewall with "allow signed software" and stealth mode. It filters host sockets, not bridged VM traffic, so the VM needs no allow-list entry.
- **Rollback:** if VirtualBox breaks, the fix is kext approval plus a reboot. It is **never** `csrutil disable`.
- **Risk:** legacy osxfuse or ext4fuse stops loading, which is acceptable.
- **Guardrail:** `kmutil showloaded | grep -v com.apple` before and after.

### D6 — Package management

**Recommendation:** Homebrew is the single source.

- Remove the MacPorts `/opt/local/bin` entry from `PATH`.
- Record the toolchain in `conf/hosts/turing/Brewfile` and gate it with `brew bundle check` (G-TOOLS). A Brewfile pins *presence*, not versions, and is **not** a rollback mechanism.
- During the 139-formula upgrade (D2-upg), `brew pin gnupg pinentry-mac ykman`. Re-run the B5 probe afterwards.
- Never hard-code `/usr/local`. Derive paths from `brew --prefix`: Intel is `/usr/local` and arm64 is `/opt/homebrew`. The one exception is `gpg-agent.conf`, which does not expand shell substitutions and so takes the literal Intel path.

### D7 — Docker

| Option | Strengths | Weaknesses |
|---|---|---|
| a. **Upgrade Docker Desktop; cap it at 3 GiB; never run it in node mode** | `juniper-deploy` compose stacks run locally | its VM uses 2–4 GB |
| b. Colima (lima) | lighter | a second hypervisor |
| c. Remove; containers only in `juniper-macvm` | no duplication | no compose when the VM is down |

**Recommendation: a.** A 2021 engine is a security liability whatever else is decided. G-MEM treats a running Docker Desktop as a node-mode blocker.

Docker Desktop installs its own `/usr/local/bin/kubectl` symlink, which collides with Homebrew `kubernetes-cli` under the shared Intel prefix. So task D3 (Docker) runs before task D4 (kubectl), and task D4 checks `which -a kubectl`.

### D8 — Python environments

**Recommendation:**

- Create the per-repo envs named in each repo's AGENTS.md from that repo's own spec (E2).
- Keep `JuniperPython` for juniper-ml.
- Retire `~/opt/anaconda3` after a reference check (E7).

Cost is about 3–5 GB of disk. Guardrail: G-ENV.

### D9 — Parent `Juniper/AGENTS.md`

**Recommendation:** copy yamaguchi's file over and record its sha256 (E4).

- The file is unversioned (`notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_PARENT-AGENTS-GOVERNANCE-AND-WORKTREE-SETTINGS-ASYMMETRY.md:30,56`), and that note, not this plan, governs it.
- Drift guardrail: the host probe warns when the hash changes.

### D10 — MCP servers

Follow `notes/JUNIPER_2026-03-09_JUNIPER-ML_MCP-SERVER-SETUP-PLAN.md`: Serena at project scope and Context7 at user scope. Fix the known gaps: Serena was never bound to a project, and `.mcp.json` is gitignored (audit A2-F1–F4).

Guardrails:

- **Pin Serena** to a released tag or commit (`git+https://github.com/oraios/serena@<sha>`) and record the pin in `conf/hosts/turing/`, because `uvx --from git+…` runs unpinned HEAD with the owner's keys.
- Exclude Serena's shell-execution tool (`excluded_tools`) so it can't bypass Claude Code's Bash permission rules.
- Reference any API key as `${CONTEXT7_API_KEY}`, never as a literal.
- The two unvetted servers in `~/.claude/mcp-servers/` stay disabled until audited (H5). H0 first checks whether they are already *configured*.

### D11 — Agent identity and permissions on turing

The rule is that agents never touch the YubiKey and land changes only through `open_signed_pr.py`. That is enforced by **configuration, not by prompt**:

1. **Unsigned by construction.** turing's `~/.claude/settings.json` sets `env` `GIT_CONFIG_COUNT=2`, `GIT_CONFIG_KEY_0=commit.gpgsign` / `GIT_CONFIG_VALUE_0=false`, and `GIT_CONFIG_KEY_1=tag.gpgsign` / `GIT_CONFIG_VALUE_1=false`.
2. **Touch required.** `ykman openpgp keys set-touch sig cached` on each card, so a signature needs a physical touch. Do not use `fixed`, which can't be undone.
3. **No PIN in the Keychain.** `gpg-agent.conf` gains `no-allow-external-cache`.
4. **Deny list.** turing's user settings deny, or a PreToolUse hook blocks: `Read(~/.ssh/**)`, `Read(~/.gnupg/**)`, `Bash(gpg --card-status*)`, `Bash(gpg -K*)`, `Bash(ssh-add*)`, `Bash(gh api * -X *)`, `Bash(gh api * -f *)`, `Bash(gh api * --method *)`, `Bash(sudo *)`.
   - **Pattern rules alone are not enough.** Read rules don't apply to Bash, and `gh api` flag order varies.
   - Enforcement is therefore one of:
     - (a) an OS-level read-deny of `~/.ssh` and `~/.gnupg` through the Claude Code sandbox filesystem settings (check the key names against the current docs);
     - (b) a PreToolUse Bash hook that rejects any command referencing `.ssh/`, `.gnupg/`, `ssh -T`, `ssh-add`, `defaults write`, `gh repo deploy-key`, `gh pr create|merge`, or `gh api` with any of `-X`, `--method`, `-f`, `-F`, `--field`, `--raw-field`, `--input` in any position.
   - The H3 negative tests include a Bash `cat ~/.ssh/config` attempt and a flag-first `gh api -X POST` attempt.
5. **Scoped token.** Agent sessions use a **fine-grained PAT** limited to the 10 Juniper repos: Contents and Pull requests read/write, Metadata read, no Administration, 90-day expiry. Deploy-key and ruleset administration stays in the owner's own session.

The auto-mode classifier already blocked one credential-enumeration probe in this session (§14), and that block is the behavior this design formalizes.

### D12 — `/home/pcalnon` path literals

`git grep -c /home/pcalnon` gives about 5,200 line hits across about 1,176 files in juniper-ml, mostly docs.

| Option | Strengths | Weaknesses |
|---|---|---|
| a. `/etc/synthetic.conf` / autofs alias | no edits | a host hack that hides the bug |
| b. **Rewrite executable literals to `$HOME`-derived paths; docs say `~/…`** | fixes the source | many files |

**Recommendation: b** for scripts, CI and configs, gated by G-PATH so no *new* literal lands. Docs are fixed opportunistically.

## 6. Work arcs and tasks

**Priority:** P0 blocks committing or merging from turing, or is a live exposure. P1 is needed for the documented roles. P2 is hardening.

**Actor:** AGENT = a session on turing. OWNER = needs an admin password, a YubiKey PIN or touch, recoveryOS, or the GitHub web UI.

**CI wiring rule (applies to every task that adds a test suite):** the same PR must:

- add `python3 -m unittest -v tests/test_<name>.py` to `ci.yml`'s `Run Python regression tests` step;
- add the suite to `docs/REFERENCE.md` § Test Suite Reference and to its "Running every suite" list;
- keep `tests/test_ci_test_wiring_drift.py` green.

There is no separate later wiring task: the drift gate forbids one.

### Arc A — Git transport authentication (P0)

| ID | Task | Pri | Actor | Depends | Acceptance |
|---|---|---|---|---|---|
| A1 | `git -C juniper-k8s remote set-url origin git@github_juniper-k8s:pcalnon/juniper-k8s.git`; same for juniper-recurrence | P0 | AGENT | — | all 10 `origin` URLs match `^git@github_juniper-<repo>:pcalnon/<repo>\.git$` |
| A8 | Set `AddKeysToAgent no` on every `github_juniper-*` block (deploy keys are passphrase-less) | P0 | AGENT | — | G2 reports no `AddKeysToAgent yes` in those blocks |
| A2 | `gh repo deploy-key list -R pcalnon/<repo> --json title,readOnly,key` for all 10. Add missing turing keys **via the web UI**, titled `Deploy Key - Turing`, write-enabled. Delete any turing-titled key whose fingerprint matches no local `.pub` | P0 | OWNER | — | each repo has exactly one turing key, `readOnly == false`, fingerprint equal to the local `.pub` |
| A3 | Auth matrix (§14.1): `ssh -T`, `git ls-remote origin HEAD` and `git push --dry-run origin HEAD:refs/heads/probe-turing-auth` per repo | P0 | OWNER | A1, A2, A8 | 10/10 on all three (G-AUTH) |
| A4 | Replace `util/git_clone_with_specified_id.bash` with `util/juniper_clone.bash <repo>`, which clones from the alias | P1 | AGENT | — | `tests/test_juniper_clone.py` passes; the clone's `origin` is in alias form |
| A5 | `util/juniper_repo_ssh_setup.bash <repo>`: create the key if absent, append the `Host` block idempotently, print the web-UI deploy-key step | P1 | AGENT | — | `tests/test_juniper_repo_ssh_setup.py`; a second run is a no-op |
| A6 | DHCP reservation for turing (Wi-Fi + `en7` MAC `00:e0:4c:68:06:b1`); record the address | P1 | OWNER | — | address recorded in `conf/hosts/turing/HOST.md`; unblocks X3, X4 |
| A7 | Fix the `~/.ssh/config` comment block (lists `-ml` twice, omits `-recurrence`) | P2 | AGENT | — | comment equals the Host list |

### Arc B — Commit signing (P0)

| ID | Task | Pri | Actor | Depends | Acceptance |
|---|---|---|---|---|---|
| B1 | `brew install pinentry-mac ykman`. In `gpg-agent.conf`, write the literal `pinentry-program /usr/local/bin/pinentry-mac` and add `no-allow-external-cache`. Run `gpgconf --kill gpg-agent` | P0 | AGENT (install) / OWNER (verify) | — | `gpgconf --list-options gpg-agent` shows pinentry-mac; B7 passes |
| B2 | Import the public key from yamaguchi's export or `https://github.com/pcalnon.gpg`. Compare the full 40-hex fingerprint out-of-band, then set ultimate trust. Optionally import the GitHub web-flow key `B5690EEEBB952194` | P0 | OWNER | — | `gpg --list-keys 084FA27B796DABC4` shows `[ultimate]`; a yamaguchi-signed commit shows `G BA18D1A733B1831A` |
| B3 | Per card (3a, then 3c): run `gpg --card-status` and record the serial and the sign-slot fingerprint. Decide same-vs-different subkeys (§4.2). `learn --force` | P0 | OWNER | B1, B2 | per card: the serial shows, and `echo t \| gpg --clearsign -u 'BA18D1A733B1831A!'` succeeds with that card inserted (or with the per-card key if they differ) |
| B4 | `git config --global user.signingkey 'BA18D1A733B1831A!'`; `commit.gpgsign true`; `tag.gpgsign true`; `gpg.program "$(brew --prefix)/bin/gpg"`. Confirm the key's UIDs include the commit email. `ykman openpgp keys set-touch sig cached` per card | P0 | OWNER | B3 | config equals yamaguchi's except `gpg.program` (host-local path); touch policy `Cached` on both cards |
| B5 | Probe: one signed empty commit on a throwaway juniper-ml branch, push, then `gh api repos/pcalnon/juniper-ml/commits/<sha> --jq .commit.verification`. Delete the branch | P0 | OWNER | A3, B4 | `verified: true`, `reason: valid` (G-SIGN) |
| B6 | Record the serial-to-name mapping (3a / 3c) and the stub model in `conf/hosts/turing/HOST.md` | P1 | OWNER | B3 | both serials named |
| B7 | `util/headless_signing_preflight.bash`, the name designed in `notes/JUNIPER_2026-08-09_JUNIPER-ECOSYSTEM_STANDING-ITEMS-CLOSEOUT-AND-HARNESS-REMEDIATION-PLAN.md:1013`. It runs **non-credential checks only**: `signingkey` pinned with `!`, pinentry is a GUI build, agent socket present, `no-allow-external-cache` set, `%G?` of HEAD. The designed `--card-timeout` card checks are dropped here (D11) and remain an owner-run option | P1 | AGENT | — | `tests/test_headless_signing_preflight.py` (U and R); exits 0 / 1 / 2 |
| B8 | Per the closeout plan (:1627), **delete** `util/test_gpg_signing.bash` (stale ed448 id, `:4`). Mark the 2026-07-16 note superseded (X7) | P1 | AGENT | B7 | `git grep 93E8591643C507FF -- util scripts` returns nothing |
| B9 | Re-land the in-flight branch via `open_signed_pr.py`. A4 replaces its clone helper. Rewrite `util/find_encryption_readme_notes.bash` **without `eval`** (it currently runs `eval "ls -Fla ${i}"` on `find` output, an injection vector) as `find … -print0`, `$HOME`-relative and shellcheck-clean | P1 | AGENT | A4 | a PR with verified commits; the old branch closed; `tests/test_find_encryption_readme_notes.py` covers a filename containing `$(…)` |

### Arc C — Security posture (P0)

| ID | Task | Pri | Actor | Depends | Acceptance |
|---|---|---|---|---|---|
| C0 | **Encrypted Time Machine backup before any owner block** (it will hold the C3 files; delete that backup set after C3 verifies) | P0 | OWNER | — | backup completed timestamp recorded |
| C1 | Kext inventory; recoveryOS `csrutil enable`; approve the VirtualBox extensions; reboot; upgrade VirtualBox to the latest 7.2.x | P0 | OWNER | C0 | `csrutil status` = enabled; `csrutil authenticated-root status` = enabled; `kmutil showloaded \| grep -i -E 'vbox\|virtualbox'` lists the loaded kexts |
| C2 | Application firewall on + stealth mode; allow signed software | P0 | OWNER | — | `socketfilterfw --getglobalstate` = enabled; `--getstealthmode` = on |
| C3 | Execute D4 steps 1–6 | P0 | OWNER | C0 | probe lists no `*.asc` or recovery file under `~/.ssh` / `~/.gnupg`; no local snapshot predates the deletion; new recovery codes issued; exposure assessment recorded in `HOST.md` |
| C8 | Apply D11 items 1 and 4 (git env, deny list or hook) to turing's `~/.claude/settings.json` **before Session 1** | P0 | OWNER | — | a test agent's `git config commit.gpgsign` prints `false`; `cat ~/.ssh/config` and `gh api -X POST …` are denied |
| C4 | `chmod 600 ~/.ssh/id-turing-aws-ec2.pem ~/.ssh/config` | P0 | AGENT | — | `stat -f %Sp` shows `-rw-------` |
| C5 | Remote Login limited to the admin user; automatic security updates set to install | P1 | OWNER | — | `AllowUsers <admin>` in `/etc/ssh/sshd_config.d/*.conf`; `defaults read /Library/Preferences/com.apple.SoftwareUpdate CriticalUpdateInstall` = 1 |
| C6 | `VBoxManage unregistervm <uuid>` (**without** `--delete`) for the two inaccessible VMs, once the owner confirms they're disposable | P2 | OWNER | — | `VBoxManage list vms` shows no inaccessible entries |
| C7 | `sudo pmset -c sleep 0 disksleep 0 standby 0 autorestart 1` (primer :394) | P2 | OWNER | — | `pmset -g` shows `standby 0`, `autorestart 1` |

### Arc D — Toolchain (P0 for D0, otherwise P1)

| ID | Task | Pri | Actor | Depends | Acceptance |
|---|---|---|---|---|---|
| D0 | `brew install coreutils` (`timeout` is needed by the H4 probe and ecosystem scripts) | P0 | AGENT | — | `command -v timeout` (gtimeout is linked as `timeout` via the gnubin `PATH` entry) |
| D1-tools | `brew install shellcheck markdownlint-cli2 yamllint actionlint sops age yq iperf3`; write `conf/hosts/turing/Brewfile` | P1 | AGENT | D0 | `brew bundle check --file conf/hosts/turing/Brewfile` returns 0 (G-TOOLS) |
| D2-upg | `brew pin gnupg pinentry-mac ykman`; `brew upgrade`; unpin; upgrade those three deliberately; re-run B5 | P1 | AGENT + OWNER (B5) | B5, D1-tools | pre-commit suite passes; B5 still `verified: true` |
| D3 | Docker Desktop upgrade to the current stable (record the version), memory cap 3 GiB | P1 | OWNER | — | `docker version` equals the recorded version; settings show 3 GiB |
| D4 | kubectl 1.36.x (Homebrew `kubernetes-cli`); remove the 1.22 binary | P1 | AGENT | D3 | `which -a kubectl` lists the 1.36 binary first; `kubectl version --client` = v1.36.x |
| D5 | Drop `/opt/local/bin` from the shell profile | P2 | AGENT | — | `which -a gpg` shows Homebrew only |
| D6 | Make pre-commit's gitleaks env build (Go proxy reachability, or `GOFLAGS=-mod=mod` / `GOPROXY` per network) | P1 | AGENT | — | `pre-commit run gitleaks --all-files` runs |

### Arc E — Secondary dev-environment parity (P1)

| ID | Task | Pri | Actor | Depends | Acceptance |
|---|---|---|---|---|---|
| E1 | `pre-commit install` in every repo; `pre-commit run --all-files` on a freshly fetched `main` per repo | P1 | AGENT | A3, D1-tools, D6 | all hooks pass; baseline recorded |
| E2 | Per-repo conda envs (D8) | P1 | AGENT | — | `conda env list` ⊇ the AGENTS.md names (G-ENV) |
| E3 | Run juniper-ml's CI regression list locally | P1 | AGENT | E1 | same pass count as CI on the same commit, or each delta explained |
| E4 | Copy the parent `Juniper/AGENTS.md` from yamaguchi; record its sha256 (D9) | P1 | OWNER | — | present; hash in `HOST.md` |
| E5 | juniper-k8s errata X1–X5 and X9, X8 flagged, via `open_signed_pr.py --repo juniper-k8s` | P1 | AGENT | A6 | PR merged |
| E6 | juniper-ml errata X6, X7, X10 via `open_signed_pr.py` | P2 | AGENT | — | PR merged |
| E7 | Retire `~/opt/anaconda3` after a reference check | P2 | OWNER | E2 | removed; reclaimed GB recorded |

### Arc F — k8s worker VM `juniper-macvm` (P1, gated)

| ID | Task | Pri | Actor | Depends | Acceptance |
|---|---|---|---|---|---|
| F1 | Owner ruling on D1 | P1 | OWNER | — | recorded under D1 |
| F2 | Get a 1000baseT link on `en7` (cable, switch port or dongle) | P1 | OWNER | — | `ifconfig en7` media shows `1000baseT`, status active; `iperf3` to yamaguchi ≥ 800 Mb/s (G-NET) |
| F3 | Headroom baseline: ≥ 480 samples per mode at 60 s intervals (`vm_stat`, `sysctl vm.swapusage`), in dev mode and node mode. Node mode means desktop apps and Docker Desktop quit, with no VM running; the owner sets the state | P1 | AGENT | D0 | `reports/<run-date>_turing-headroom/` with p50/p95 free memory and swap |
| F5a | `util/macvm_ctl.bash {start,stop,status}`: G-MEM check before `start`, refuse on failure | P1 | AGENT | — | `tests/test_macvm_ctl.py` (R-F5) with stubbed `VBoxManage` / `vm_stat` |
| F4 | Create the VM per primer §4 at the D1 size; Ubuntu 26.04.1; bridged on `en7` | P1 | OWNER | C1, F1, F2, F3, A6 | boots; gets the reserved IP |
| F5b | Integration: `macvm_ctl stop/start` 3× on the real VM | P1 | OWNER | F4, F5a | I-F4 passes |
| F6 | Node join (an nd-* macvm variant); taint plus `--system-reserved` | P1 | OWNER | F4, task D4 (kubectl), juniper-k8s control-plane bring-up (primer §2, owned by the juniper-k8s plan) | `kubectl get node juniper-macvm` Ready ≥ 24 h with no flaps; taint present |
| F7 | LaunchDaemon plist that runs `util/macvm_ctl.bash start` (so G-MEM applies) with `UserName pcalnon` (root's VBoxManage has a different registry); installed **disabled** | P2 | AGENT | F5a | `launchctl print system/local.juniper-macvm` shows disabled; `plutil -lint` OK |

### Arc G — Scripts, checks, CI (P1, parallel)

| ID | Task | Pri | Actor | Depends | Acceptance |
|---|---|---|---|---|---|
| G1 | Graduate the ad-hoc probe to `util/host_state_probe.bash` (collection) plus `util/host_state_check.py` (evaluates `conf/hosts/<host>/expected.yaml`; Python, so no `yq` dependency). Flags: `--json`, `--check`, `--section` | P1 | AGENT | — | `tests/test_host_state_probe.py`, `tests/test_host_state_check.py`; JSON schema documented |
| G2 | `util/git_remote_alias_check.py [--fix]`: alias-form origin, key present at 600, `Host` block present, `AddKeysToAgent no` | P1 | AGENT | — | `tests/test_git_remote_alias_check.py` (R-G2a/b/c) |
| G4 | Job `host-tooling-macos` **in `ci.yml`**: no `on.paths` filter; a change-detection step sets an output, and later steps are `if:`-gated on it, so the job reports success when nothing relevant changed; fires on `merge_group` too. Runs the host-tooling suites with `/bin/bash` (3.2) explicitly, plus a `brew --prefix` portability assertion. Advisory first; required after 10 green runs by adding it to the Quality Gate's `required-checks.needs`, never as a separate ruleset context | P1 | AGENT | G2 | job green on `macos-latest` |
| G5 | `util/home_path_literal_check.py`: fails on a *new* `/home/pcalnon` literal in `*.bash`, `*.sh`, `*.py`, `*.yml` under `util/`, `scripts/`, `.github/` (baseline file) | P2 | AGENT | — | `tests/test_home_path_literal_check.py`; pre-commit `local` hook + CI step (G-PATH) |
| G6 | pre-commit `local` hook `git-remote-alias` (G2 `--check`, `stages: [pre-push]`, `pass_filenames: false`); **exits 0 when `~/.ssh/config` has no `github_juniper-*` alias**, so other hosts aren't blocked | P2 | AGENT | G2 | `pre-commit run --hook-stage pre-push` passes on turing and in CI |

### Arc H — MCP servers and custom SME agents (P1)

| ID | Task | Pri | Actor | Depends | Acceptance |
|---|---|---|---|---|---|
| H0 | List the **keys only** of `mcpServers` in `~/.claude.json` and any `.mcp.json`. If an unvetted server is configured, remove it | P0 | AGENT | — | key list recorded; no unvetted server configured |
| H1 | `bash util/install_agents.bash` from a **clean `main` checkout** (not a feature worktree, since symlinks follow the checkout's branch) | P1 | AGENT | — | `~/.claude/agents/*.md` symlinks to every `.claude/agents/*.md` on main (9 after H2) |
| H2 | Author the 3 SME agents in §11 | P1 | AGENT | H1 | `tests/test_agents_frontmatter.py` green; a new `tests/test_<agent>_contract.py` per agent (pattern: `tests/test_fleet_supervisor_contract.py`) pins its tool set and asserts every "Must never" item appears in the body. After the H2 PR merges, re-run `util/install_agents.bash` from a clean `main`: 9 symlinks |
| H3 | Live validation: each agent runs one scripted task on turing. Compare against a `util/host_state_probe.bash --json` run taken within ±10 min (`k8s-node-sme`: against errata X1–X5). Plus one **negative test** per agent: a forbidden command is attempted and denied by D11's deny list | P1 | AGENT | H2, G1, C8 | 3/3 with zero contradictions on covered gates; 3/3 denials. The H3 task prompts pass `prompts/agent_templates/RUBRIC.md` via `prompt-validator` |
| H4 | `util/mcp_setup.bash [checkout]`: write `.mcp.json` with Serena pinned and bound to the checkout, shell tool excluded (D10) | P1 | AGENT | D0 | `timeout 30 claude mcp list` shows serena connected; `tests/test_mcp_setup.py` |
| H5 | `auditor` agent audits the two unvetted `~/.claude/mcp-servers/` entries (provenance, permissions, egress) | P2 | AGENT | H0 | audit note in `notes/`; enable or remove |

## 7. Dependency graph, orthogonality and sessions

```text
Arc A   A1, A8, A2 ─> A3 ─> B5            A4 ─> B9      A5, A6, A7 independent
Arc B   B1, B2 ─> B3 ─> B4 ─> B5 ─> D2-upg   B3 ─> B6    B7 ─> B8
Arc C   C0 ─> C1 ─> F4 ; C0 ─> C3          C2, C4, C5, C6, C7 independent
Arc D   D0 ─> D1-tools ─> E1 ; D3 ─> D4 ─> F6 ; D6 ─> E1
Arc E   A3 ─> E1 ─> E3 ; E2 ─> E7 ; A6 ─> E5 ; E4, E6 independent
Arc F   F1 + F2 + F3 + C1 + A6 ─> F4 ─> F5b ; F5a ─> F5b, F7 ; F4 + D4 + k8s control plane ─> F6
Arc G   G2 ─> G4, G6 ; G1, G5 independent
Arc H   H0 ─> H5 ; H1 ─> H2 ─> H3 (needs G1, B4) ; D0 ─> H4
```

- **Start together:** arcs A, C, D, G and H can all start at once. B needs nothing from D.
- **Joins:** B5 (A+B), E1 (A+D), H3 (H+G+C), and F4/F6 (multi-arc).
- **Shared files:** every PR that adds a suite edits `ci.yml`'s regression step and `docs/REFERENCE.md`, so merge those PRs serially, rebasing each onto the last.
- **Critical path to "turing can land work":** `(A1 ∥ A8 ∥ A2) → A3` and `(B1 ∥ B2) → B3 → B4 → B5`. The two meet at B5.
- **Critical path to "turing is a node":** `C0 → C1`, `F1`, `F2`, `F3` (≈ 16 h of sampling: 8 h per mode), `A6`, then `F4 → F5b`. F6 also waits on juniper-k8s's control plane, which doesn't exist yet (primer :4).

**Sessions.** Every task appears exactly once below (B1 is split by actor). Each session ends with a handoff prompt archived to `prompts/thread-handoff_automated-prompts/` (AGENTS.md § Thread Handoff).

0. **Owner block 0:** C8 (agent guardrails), before any agent session.
1. **Session 1 (AGENT):** A1, A8, C4, D0, H0, B1-install, G2, B7, B8, A4, A5, A7, F5a, F3 (starts sampling).
2. **Owner block 1:** C0, then A2, A3, B1-verify, B2–B6, C1–C3, C5, C7, E4, A6, F1, F2.
3. **Session 2 (AGENT):** D1-tools, D6, D5, D2-upg (with an owner B5 re-check), D3 (OWNER), D4, E1–E3, G1, G4, G5, G6, B9.
4. **Session 3 (AGENT):** H1–H5, E5, E6.
5. **Session 4 (OWNER + AGENT):** F4, F5b, F7, C6, E7, then F6 once the cluster exists.

## 8. Scripts and automation inventory

| Script / file | Status | Purpose | Test file |
|---|---|---|---|
| `util/ad-hoc/2026-10-15_turing_host_state_probe.bash` | **new (this PR)** | read-only evidence capture | — (its output is Appendix A) |
| `util/host_state_probe.bash`, `util/host_state_check.py` | new (G1) | probe + gate evaluator | `tests/test_host_state_probe.py`, `tests/test_host_state_check.py` |
| `conf/hosts/turing/{expected.yaml,Brewfile,HOST.md}` | new (G1, D1-tools, A6, B6) | host target state and record | consumed by G1 |
| `util/git_remote_alias_check.py` | new (G2) | remote/key invariant | `tests/test_git_remote_alias_check.py` |
| `util/juniper_clone.bash` | new (A4); replaces `git_clone_with_specified_id.bash` | alias-form clone | `tests/test_juniper_clone.py` |
| `util/juniper_repo_ssh_setup.bash` | new (A5) | key + alias provisioning | `tests/test_juniper_repo_ssh_setup.py` |
| `util/headless_signing_preflight.bash` | new (B7) | non-credential signing readiness | `tests/test_headless_signing_preflight.py` |
| `util/test_gpg_signing.bash` | **deleted** (B8) | — | grep-based R-B8 inside the B7 suite |
| `util/find_encryption_readme_notes.bash` | rewritten (B9) | no-`eval` search | `tests/test_find_encryption_readme_notes.py` |
| `util/macvm_ctl.bash` | new (F5a) | gated VM lifecycle | `tests/test_macvm_ctl.py` |
| `util/mcp_setup.bash` | new (H4) | per-checkout `.mcp.json` | `tests/test_mcp_setup.py` |
| `util/home_path_literal_check.py` | new (G5) | path-literal ratchet | `tests/test_home_path_literal_check.py` |
| `.claude/agents/{macos-host-sme,signing-auth-sme,k8s-node-sme}.md` | new (H2) | SME agents | `tests/test_<agent>_contract.py` ×3 |
| `.github/workflows/ci.yml`, `.pre-commit-config.yaml`, `docs/REFERENCE.md` | changed (every suite-adding PR, G4, G5, G6) | wiring | `tests/test_ci_test_wiring_drift.py` |

**Conventions for every script:**

- `#!/usr/bin/env bash` and `set -euo pipefail`.
- Bash 3.2-safe, or an explicit `BASH_VERSINFO` check.
- shellcheck clean.
- Exit codes: 0 = OK, 1 = gate failed, 2 = usage/environment.
- `--help`; `--dry-run` for any script that writes.
- Every external macOS tool is called through an overridable variable, e.g. `SOCKETFILTERFW="${SOCKETFILTERFW:-/usr/libexec/ApplicationFirewall/socketfilterfw}"`. Tests can't PATH-stub absolute paths.
- File-mode checks use Python `os.stat` or `find -perm`, not `stat -f` / `stat -c`.
- Scripts check paths and modes only. **They never read private-key contents.**

## 9. Testing requirements, gates and metrics

### 9.1 Test classes (mandatory for every code change in this work arc)

**Unit.** Hermetic `unittest` suites (the file names in §8).

- External commands (`git`, `gh`, `ssh`, `gpg`, `sysctl`, `vm_stat`, `VBoxManage`, `ifconfig`) are PATH stubs or tool-variable overrides that print recorded fixtures (the pattern of `tests/test_open_signed_pr.py`).
- Each suite covers:
  - the happy path;
  - every exit code;
  - that `--dry-run` writes nothing;
  - idempotency for writers.
- Suites run on Linux CI and on `host-tooling-macos`.

**Regression.** One test per defect this plan found:

| ID | Defect pinned |
|---|---|
| R-G2a | an origin of the form `git@github.com:` (juniper-k8s) |
| R-G2b | an `https://` origin (juniper-recurrence) |
| R-G2c | an alias with no `Host` block, or with `AddKeysToAgent yes` |
| R-A4 | the clone helper must persist the alias origin |
| R-B7a | a `signingkey` without the `!` pin (the 2026-07-16 ambiguity class) |
| R-B7b | a curses pinentry (unusable headless) |
| R-B8 | the stale key id appearing in executable files |
| R-B9 | a filename containing `$(…)` is never executed |
| R-F5 | `start` refuses when stubbed swap is over the gate |
| R-G1 | `expected.yaml` asks for more VM memory than `hw.memsize` minus the reserve (the X2 class) |

**Integration.** Operator-run on turing, recorded under `reports/<run-date>_turing-bringup/`:

| ID | Pass condition |
|---|---|
| I-A3 | auth matrix 10/10 on all three checks |
| I-B5 | `verification.verified == true` |
| I-G1 | `--check` all-green |
| I-F4 | VM boots and gets the reserved IP, then survives `stop`/`start` 3× |
| I-F6 | node Ready ≥ 24 h |
| I-H3 | agent reports agree with the probe; denials hold |

### 9.2 Gate placement

| Layer | Gate | Scope |
|---|---|---|
| pre-commit | the existing hooks (shellcheck, markdownlint, yamllint, flake8, bandit, gitleaks, doc-links) + G5 | every commit |
| pre-push | G6 | every push from a host with aliases |
| CI regression step | every new suite (wired in the PR that adds it) | every PR |
| CI `host-tooling-macos` | the same suites under BSD userland and `/bin/bash` 3.2 | every PR (in-job change detection) |
| Operator | `host_state_check.py --check` + I-\* | after each owner block; before F4 |

### 9.3 Host gates (evaluated by `host_state_check.py --check`, except G-AUTH, G-PATH and G-AGENT as noted)

| Gate | Pass condition | Today |
|---|---|---|
| G-ALIAS | 10/10 alias-form origins; keys 600; `AddKeysToAgent no` | **fail** (8/10; `yes` everywhere) |
| G-AUTH | 10/10 `ssh -T` + `ls-remote` + `push --dry-run` (operator) | not measured (§14) |
| G-SIGN | `commit.gpgsign=true`; `signingkey` ends in `!`; GUI pinentry; `no-allow-external-cache`; I-B5 verified | **fail** (unconfigured) |
| G-SEC | SIP and authenticated-root enabled; firewall on; FileVault on; no `*.asc`/recovery files in `~/.ssh` or `~/.gnupg`; no key more permissive than 600 | **fail** (4 of 5) |
| G-TOOLS | `brew bundle check` returns 0; kubectl within ±1 minor of the cluster | **fail** (11 missing; kubectl 14 minors behind) |
| G-ENV | conda envs ⊇ the AGENTS.md list; parent AGENTS.md hash matches | **fail** |
| G-NET | `en7` at 1000baseT with the reserved IP; ≥ 800 Mb/s to yamaguchi | **fail** (no carrier) |
| G-MEM | before VM start: free + inactive ≥ VM size + 4 GiB, swap used ≤ 2 GiB, Docker Desktop not running | **fail** (swap 13.7 GB) |
| G-PATH | no new `/home/pcalnon` literal in executable files (G5) | n/a until G5 |
| G-AGENT | frontmatter test + per-agent contract test green; H3 denials hold | n/a |

### 9.4 Metrics (per run, in `reports/`)

- **Readiness:** host gates passing, out of 10. This is the headline.
- **Memory:** p50/p95 free and swap per mode (F3); VM boot-to-Ready seconds.
- **Network:** link speed; `iperf3` throughput.
- **Auth and signing:** auth-matrix success (target: 10/10 on 3 consecutive runs); verified rate of turing-origin commits (target: 100%).
- **CI:** suites added (count); `host-tooling-macos` green streak (≥ 10 before it becomes required).

**macOS runner tradeoff.** `macos-latest` is arm64.

- **What it tests:** BSD userland, `/bin/bash` 3.2, and launchd/plist tooling.
- **What it doesn't test:** Intel `sysctl` keys (all stubbed anyway), the `/usr/local` prefix (covered by the `brew --prefix` assertion), and VirtualBox. Real hardware is covered by I-G1.
- **Optional Intel leg:** a non-required leg on an Intel macOS label, but verify that label's retirement date first.
- **Cost:** confirm juniper-ml's visibility before adding the job. macOS minutes carry a 10× multiplier on private repos.

## 10. MCP servers

| Server | Scope | Install / activate | Validation |
|---|---|---|---|
| Serena | project (per checkout / worktree) | `util/mcp_setup.bash` writes `.mcp.json`: `uvx --from git+https://github.com/oraios/serena@<pinned-sha> serena start-mcp-server --context claude-code --project <checkout>` (base command: `notes/JUNIPER_2026-03-09_JUNIPER-ML_MCP-SERVER-SETUP-PLAN.md:108-110`; `--project` fixes A2-F1; pin per D10); shell tool excluded | `timeout 30 claude mcp list` shows connected; one symbol query succeeds |
| Context7 | **user** | HTTP transport per the MCP plan :121-123; key as `${CONTEXT7_API_KEY}` | connected; one library-doc query succeeds |
| GitHub | — | not added: `gh` already covers it, and the server would hold the same broad token | — |
| `adaptive-graph-of-thoughts`, `agi-mcp-server` | — | unvetted; H0 checks whether configured, H5 audits | — |

## 11. Custom role-based SME agents

**Required frontmatter** (`tests/test_agents_frontmatter.py`): `name` equal to the file stem, `description` ≥ 60 characters, `tools`, `model: opus`, `effort: max`, and a body > 200 characters. This matches `.claude/agents/auditor.md:2-6`.

**Validation:**

- that frontmatter test;
- a per-agent contract test (H2);
- the live run and negative test (H3).

RUBRIC/`prompt-validator` applies to the H3 task *prompts*, not to the agent files.

| Agent | Role | Tools | Writes | Must never (enforced by D11's deny list, pinned by the contract test) |
|---|---|---|---|---|
| `macos-host-sme` | Measures a macOS host against `conf/hosts/<host>/expected.yaml`; explains each gate failure with its fix | Read, Grep, Glob, Bash, Write | one `reports/` file | `sudo`; read `~/.ssh/**` or `~/.gnupg/**`; `defaults write`; change settings |
| `signing-auth-sme` | Diagnoses git transport and signing (aliases, deploy keys, gpg config, rulesets via read-only `gh api` GETs); emits the OWNER command list | Read, Grep, Glob, Bash, Write | one `reports/` file | `gpg --card-status`, `gpg -K`, `ssh-add`, `ssh -T`; PIN-bearing commands; `gh api` with `-X` / `-f` / `--method`; any `gh` write |
| `k8s-node-sme` | Reviews VM sizing, kubelet reservations, taints and node-join steps against the primer; reconciles errata | Read, Grep, Glob, WebFetch, Write (**no Bash**: WebFetch + Bash is a prompt-injection-to-exfiltration path) | one `notes/` audit | anything outside its write target |

## 12. AGENTS.md / CLAUDE.md and memory updates

**This PR.** AGENTS.md (CLAUDE.md is a symlink to it) gains one Hazards bullet: an unsigned local commit makes its branch permanently unmergeable, so a host without signing (turing, today) lands work through `util/open_signed_pr.py`.

- Budget measured with `util/memory_budget_check.py`: 28,274 of 38,000 characters before the change.
- The bullet adds about 450 characters.

**Later (E6).**

- X10 path wording.
- A Key Files pointer to `conf/hosts/` once G1 lands.

**Session memory (Claude Code's per-project memory on turing).** Recorded for future sessions:

- turing's measured profile and gate status;
- the auth root cause (alias bypass);
- agents must not probe live credentials, so those checks go in operator lists;
- `timeout` is missing until D0;
- turing commits are unsigned, so land through `open_signed_pr.py`.

## 13. Risk register

| Risk | L | I | Mitigation |
|---|---|---|---|
| Deleting key exports before an offline backup verifies (C3) | M | **Critical** | D4 steps; C0 first; OWNER-only; never `juniper-backup.bash` (circular) |
| **turing lost or compromised** (10 write deploy keys = ruleset bypass actors, plus a gh token) | L | **H** | **Runbook:** (1) from another host, for each of the 10 repos, `gh repo deploy-key list -R pcalnon/<repo> --json id,title` then `gh repo deploy-key delete <id>` for every `Deploy Key - Turing`; (2) revoke turing's gh token and the agent PAT; (3) revoke the card subkeys only if a card went missing too. Fixed key titles (A2/A5) make step 1 scriptable |
| Token rotation silently removes gh-added deploy keys | M | M | add keys via the web UI (D2) |
| SIP re-enable breaks a needed kext (C1) | M | M | kext inventory; approval + reboot; never `csrutil disable` |
| VM starves macOS (F) | H without the gate | H | G-MEM in `macvm_ctl start`; autostart off; taint |
| An agent signs as the owner (cached PIN) or hangs on pinentry | M | M | D11 items 1–4; touch `cached` |
| Unpinned Serena HEAD runs with the owner's credentials | M | H | pin (D10); shell tool excluded |
| A card stub is bound to the wrong serial after a swap | H | L | `learn --force` in B3; `HOST.md` |
| A deploy key is read-only | M | M | A2 `readOnly == false`; A3 `push --dry-run` |
| The mass brew upgrade breaks signing | M | M | `brew pin` in D2-upg; B5 re-run |
| Errata drift again | M | L | `expected.yaml` is machine-checked; docs cite it |
| Parent AGENTS.md copies diverge | M | L | hash check in G-ENV |

## 14. Investigation and validation log

**2026-10-15, on turing:**

1. **Read the work-arc prompt.** The given path `prompts/prompt133_2026-10-15.md` doesn't exist; the file is at `prompts/manual/prompt133_2026-10-15.md`.
2. **Measured hardware, OS, disk, GPU, memory, network, power and uptime** with `sysctl`, `sw_vers`, `df`, `diskutil`, `system_profiler SPDisplaysDataType`, `vm_stat`, `ifconfig`, `networksetup` and `pmset` (§2.1–2.2).
3. **Measured the toolchain and hypervisors:** a `command -v` / `--version` sweep, `VBoxManage list`, `docker version`, `kubectl version --client` and `conda env list` (§2.5).
4. **Read git and SSH config:**
   - global config;
   - per-repo remote, signing settings and `%G?`;
   - `~/.ssh` names and modes;
   - the Host blocks.

   A `git fetch` through `github_juniper-ml` succeeded (§2.4).
5. **Read the GPG config files and binary locations.** No keys were listed.
6. **Blocked:** a combined probe was **denied by the Claude Code auto-mode classifier** as credential exploration. It would have run `ssh -T` per alias, `ssh-add -l`, `gh auth status`, `gpg --card-status`, `gpg -K` and USB YubiKey detection.
   - It was not retried or worked around.
   - Those checks became OWNER tasks A3, B3 and B5 and §14.1. The block is also the basis for D11.
   - Separately, the probe would have failed anyway because `timeout` is missing, which became D0.
7. **Measured security posture:** `fdesetup`, `socketfilterfw` and `csrutil`. `systemsetup -getremotelogin` requires admin, so it became C5.
8. **Ran a read-only documentation-survey sub-agent (Explore)** across all ecosystem repos, with file:line citations. Its findings feed §2–§5.
9. **Read** `notes/JUNIPER_2026-07-16_JUNIPER-ECOSYSTEM_CODE-SIGNING-KEY-MIGRATION-STATUS.md` in full and the outline of `notes/JUNIPER_2026-08-03_JUNIPER-ECOSYSTEM_YUBIKEY-GPG-ED448-KEYTOCARD-PROCEDURE.md`.
10. **Checked CI shape, pre-commit and budgets:**
    - `.github/workflows/*.yml`: 62 of 62 jobs are `runs-on: ubuntu-latest`;
    - the pre-commit hook set;
    - the `util/open_signed_pr.py` contract;
    - the memory budget.
11. **Wrote and ran `util/ad-hoc/2026-10-15_turing_host_state_probe.bash`** (rc 0). Its output is Appendix A.
12. **`pre-commit run` on this PR's files.** The gitleaks env failed to build (Go proxy i/o timeout), which became D6. With `SKIP=gitleaks`, every other applicable hook passed.

**2026-10-16, consensus round 1:** three reviewers (§15) independently re-measured about 25 host facts and opened 30+ citations. Their corrections are in v1.0.0: `en7`/`en5`, `standby 1`, the 4-of-5 G-SEC count, the D12 counts, the yamaguchi-only provenance of A1-F4/A1-F9, and the web-flow `E` key.

### 14.1 Operator checklist (credential-bearing; owner-run in a terminal or with `! <cmd>`)

```bash
J=~/Development/python/Juniper
REPOS="canopy cascor cascor-client cascor-worker data data-client deploy k8s ml recurrence"
# A2 — deploy keys: exactly one "Deploy Key - Turing", readOnly=false, fingerprint = local .pub
for r in $REPOS; do echo "== $r"; gh repo deploy-key list -R "pcalnon/juniper-$r" --json title,readOnly,key; ssh-keygen -lf ~/.ssh/id_ed25519_github_juniper-$r.pub; done
# A3 — auth matrix (after A1, A2, A8)
for r in $REPOS; do
  printf '%-16s ' "$r"; ssh -o BatchMode=yes -T "github_juniper-$r" 2>&1 | head -1
  git -C "$J/juniper-$r" ls-remote origin HEAD >/dev/null && echo "  ls-remote ok"
  git -C "$J/juniper-$r" push --dry-run origin HEAD:refs/heads/probe-turing-auth >/dev/null 2>&1 && echo "  push-dry-run ok"
done
# §4.1 — turing's sshcontrol must hold keygrips (40 hex), not fingerprints
grep -v '^#' ~/.gnupg/sshcontrol; gpg -K --with-keygrip
# B3 — per card (insert 3a, then 3c)
gpg --card-status; gpg-connect-agent "scd serialno" "learn --force" /bye; echo t | gpg --clearsign -u 'BA18D1A733B1831A!'
# B4 — touch policy per card
ykman openpgp keys set-touch sig cached; ykman openpgp info
# B5 — verification probe
gh api repos/pcalnon/juniper-ml/commits/<sha> --jq .commit.verification
# juniper-k8s ruleset check (§1 item 2)
gh api repos/pcalnon/juniper-k8s/rulesets --jq '.[].name'
# C5
sudo systemsetup -getremotelogin
```

## 15. Consensus validation record

**Method.** Three independent reviewer sub-agents reviewed v0.9, each with its own lens. All were read-only and barred from credential-bearing commands.

| Reviewer | Lens |
|---|---|
| R1 | evidence and correctness: re-measured host facts and opened citations |
| R2 | security and operational risk: checked commands against `--help` and vendor docs |
| R3 | feasibility, dependencies and testability: checked against the repo's CI, tests and agent conventions |

**Rule.** Every finding at MAJOR or above is applied before merge. Each MINOR or NIT is either applied or declined with a reason.

### 15.1 Round 1 (2026-10-16): 3 × ACCEPT-WITH-CHANGES, 0 BLOCKER

| Reviewer | MAJOR | MINOR | NIT | Disposition |
|---|---|---|---|---|
| R1 evidence | 4 | 9 | 3 | all applied |
| R2 security | 9 | 11 | 3 | all applied |
| R3 feasibility | 10 | 8 | 1 | all applied, except the item declined below |

**Main changes integrated:**

- **R1:**
  - Bridge NIC corrected to `en7` (no carrier); `en5` identified as the T2 iBridge.
  - Session order now matches the task dependencies.
  - F5 removed from CI wiring.
  - A1-F4/A1-F9 labeled yamaguchi-only, and a turing `sshcontrol` check added.
  - Counts corrected: `standby 1`, G-SEC 4/5, D12 ≈ 5,200/1,176, "9 repos as of 2026-08-12".
  - B7/B8 aligned with the closeout plan's design.
  - `iperf3` added.
  - Status, §12 and the X6 wording made accurate; `credential.usehttppath` added; volatile figures marked.
- **R2:**
  - Deploy keys documented as bypass actors, with a lost-device runbook.
  - Keys added via the web UI (gh-added keys die with the token).
  - Fine-grained PAT for agents.
  - Agents unsigned by construction (`GIT_CONFIG_*` env), touch `cached`, `no-allow-external-cache`.
  - Offline symmetric backup instead of `juniper-backup.bash`; recovery-code regeneration; snapshot check; exposure assessment.
  - `AddKeysToAgent no`.
  - Serena pinned with its shell tool excluded; the MCP config check (H0).
  - Deny-list enforcement plus negative tests; Bash removed from `k8s-node-sme`.
  - Per-card B3 acceptance; literal pinentry path; fingerprint-verified import; `readOnly == false` check; `brew pin`; C0 backup; `unregistervm` without `--delete`.
  - `authenticated-root` check, VirtualBox upgrade, rollback rule; plist `UserName`; D3 before D4; B9's `eval` injection fix; firewall wording; Context7 scope; agent symlinks pointed at `main`.
- **R3:**
  - G3 dissolved into the per-PR CI wiring rule.
  - B2 acceptance fixed (`main` is web-flow-signed).
  - Missing dependencies added (F4 → A6, E1 → A3, F6 → D4 + the control plane, H4 → D0, G1 written in Python).
  - F5 split into a/b.
  - Agent validation moved to `tests/test_agents_frontmatter.py` plus contract tests (`model: opus`, `effort: max`); `Write` added to the agents' tools.
  - G4 designed against orphaned required checks (no paths filter, `merge_group`, Quality Gate `needs`).
  - Overridable tool variables and `/bin/bash` 3.2 runs.
  - H3 compared against a fresh probe.
  - Objective acceptance criteria (C1, C5, D3, F3, H1); G-PATH defined.
  - D2-upg after B5; G6 skips on hosts without aliases.
  - Test file names given; a handoff at each session boundary; this PR lands through `open_signed_pr.py`.

**Declined, with reason:**

- R3 #19 (NIT): the `reports/` date placeholder was replaced with `<run-date>` rather than a fixed date, because these runs happen later.
- R1 #16 (volatile memory figures): the values stay as captured, labeled "at probe time", because F3 produces the baseline.

### 15.2 Round 2 (2026-10-16): ACCEPT-WITH-CHANGES, 0 BLOCKER, 1 MAJOR, 7 MINOR, 4 NIT, all applied

One reviewer checked v1.0.0 against every round-1 MAJOR and found all of them reflected except one: deny-list enforcement. It also checked for regressions (session coverage, dependency edges, gate counts) and spot-checked 5 new citations, all accurate.

**Applied:**

- **MAJOR.** D11 item 4 now says pattern rules don't bind Bash, and requires sandbox read-deny or a PreToolUse hook. Negative tests were added for `cat ~/.ssh/config` and flag-first `gh api -X`.
- **MINOR:**
  - The new task C8 applies the agent guardrails before Session 1 (Owner block 0), and H3 now depends on C8.
  - `tag.gpgsign` is now neutralized too (`GIT_CONFIG_COUNT=2`).
  - The §7 joins and shared-file statements are now accurate.
  - Task-versus-decision D-numbers are qualified.
  - Node mode is defined, and F3 is ≈ 16 h.
  - B4 uses `$(brew --prefix)` for `gpg.program`.
  - D0's text matches H0.
  - H2 re-runs the agent installer.
- **NIT:** the §9.3 heading scope, the undefined U-F5 ID, the G4 step-gating wording, and the B1 split note.

Rounds 1 and 2 leave no open BLOCKER or MAJOR. The plan is VALIDATED.

## Appendix A — probe output excerpts (2026-10-15)

```text
== hardware
Intel(R) Core(TM) i7-8850H CPU @ 2.60GHz
12            (hw.ncpu)
6             (hw.physicalcpu)
17179869184   (hw.memsize)
1             (kern.hv_support)
ProductVersion: 15.7.1   BuildVersion: 24G231   x86_64
== disk
/dev/disk1s1  466Gi  355Gi  80Gi  82%  /System/Volumes/Data
Container Total Space: 500.0 GB   Container Free Space: 86.2 GB   Solid State: Yes
== memory (at probe time)
vm.swapusage: total = 15360.00M  used = 13684.00M  free = 1676.00M  (encrypted)
System-wide memory free percentage: 58%
== network
en0 ip=192.168.50.131  status: active                                   [Wi-Fi]
en5 ip=  media: autoselect (100baseTX <full-duplex>)  status: active    [ac:de:48:00:11:22 = T2 iBridge, not a port]
en7 ip=  media: autoselect (none)  status: inactive                     [USB 10/100/1000 LAN, 00:e0:4c:68:06:b1 = the dongle]
== power
sleep 0 (sleep prevented by caffeinate)  disksleep 0  standby 1  powernap 1  womp 1
== security
FileVault is On.
Firewall is disabled. (State = 0)
System Integrity Protection status: unknown (Custom Configuration).  [all protections disabled except BaseSystem Verification]
== toolchain (missing)
ykman pinentry-mac shellcheck markdownlint-cli2 yamllint sops age yq actionlint timeout iperf3
== toolchain (stale)
docker 20.10.11   kubectl v1.22.4   VirtualBox 7.2.0r170228 (2 VMs <inaccessible>)
== git
juniper-k8s         url=git@github.com:pcalnon/juniper-k8s.git              gpgsign=  signingkey=unset last5sig=EEEEE
juniper-recurrence  url=https://github.com/pcalnon/juniper-recurrence.git   gpgsign=  signingkey=unset last5sig=EEEEE
juniper-ml          url=git@github_juniper-ml:pcalnon/juniper-ml.git        gpgsign=  signingkey=unset last5sig=NEEEE
(7 other repos: alias form, EEEEE or NEEEE)
```
