# signing-auth-sme: turing's G-ALIAS and G-SIGN failures, diagnosed (plan task H3's scripted run)

- **Agent**: `signing-auth-sme` (`.claude/agents/signing-auth-sme.md`), run once end to end on the symptom below. It touched no key, YubiKey or PIN, and fixed nothing.
- **Host**: turing. The gate run's probe reports node `turing.midcoip.net`, identity "x86_64, 6 cores / 12 threads, hw.memsize 17179869184 (16 GiB)".
- **Checkout**: `/Users/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/cached-enchanting-cosmos`, branch `worktree-cached-enchanting-cosmos`, HEAD `4db485921abbe075b01fa39cf6af1516a85d03d1`. Every command ran from it. Juniper root: `/Users/pcalnon/Development/python/Juniper`.
- **Run window (UTC)**: 2026-10-27T01:22:00Z (first command) to 2026-10-27T01:39Z (this file).
- **Gate run (step 3)**: `probe.collected_at` = **`2026-10-27T01:24:50Z`**.
- **Plans of record**:
  - `notes/JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md`, v1.4.8 at this checkout. Task and decision ids A\*, B\*, C8, D2, D11 and H3 are this file's.
  - `notes/JUNIPER_2026-10-19_JUNIPER-ECOSYSTEM_COMMIT-SIGNING-TERMINAL-AND-IDE-PLAN.md`, v1.1.0. Ids K\*, S\* and T\* are this file's. It wins over the first file on B3-B5 (`notes/JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md` §19).
- **Guard**: `util/claude_agent_guard.py` 1.2.0 (`__version__` at :176), installed by the owner as a PreToolUse hook on 2026-10-26. That date comes from the launch prompt. The §16.2 "C8 item 4" row of `notes/JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md` (:849) still says "install pending"; H3's own record brings the install into that plan.
- **Labels**:
  - **verified**: measured, and as designed.
  - **verified failing**: measured, and not as designed.
  - **not verifiable by an agent**: handed to the OWNER command list (§6), never used as a conclusion.

## 1. Symptom

The orchestrating session ran `python3 util/host_state_check.py --section G-ALIAS --section G-SIGN`, with its probe collected at 2026-10-27T00:23:29Z. It reported:

- **G-ALIAS fails on condition `origins`**: "8 of 10 checkouts use their per-repo alias as origin; juniper-k8s: origin 'git@github.com:pcalnon/juniper-k8s.git' bypasses the alias; want 'git@github_juniper-k8s:pcalnon/juniper-k8s.git'; juniper-recurrence: origin 'https://github.com/pcalnon/juniper-recurrence.git' bypasses the alias; want 'git@github_juniper-recurrence:pcalnon/juniper-recurrence.git'". Conditions `aliases` and `keys` passed.
- **G-SIGN fails on condition `integration`**: "no I-SIGN record: T1-T5 verified (signing plan K10, which widens B5) is not recorded in expected.yaml". Conditions `signing-config`, `pinentry`, `agent-socket` and `external-cache` passed.
- **Repos involved**: juniper-k8s and juniper-recurrence (transport), and juniper-ml (its rulesets, and the verification of GitHub's current `main`).

The symptom is two gate conditions, not a failed push or fetch. This run re-measured both (§2.1) and attempted no push, fetch or commit.

## 2. Findings: transport, signing and GitHub

### 2.1 Gate record (step 3)

Command: `python3 util/host_state_check.py --section G-ALIAS --section G-SIGN --json`. It exited 0, because report mode exits 0 whatever the gates say (`notes/JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md` §18.3, E-G1). From its JSON:

| Field | Value |
|---|---|
| `probe.collected_at` | `2026-10-27T01:24:50Z` |
| `probe.source` / `probe.node` | `run` / `turing.midcoip.net` |
| `summary` | `readiness: 0 of 2 gates pass; 2 fail: G-ALIAS, G-SIGN` |
| G-ALIAS `status` | `fail` |
| G-ALIAS conditions with status `fail` | `origins` |
| G-ALIAS conditions with status `error` | none |
| G-SIGN `status` | `fail` |
| G-SIGN conditions with status `fail` | `integration` |
| G-SIGN conditions with status `error` | none |

The condition messages, verbatim:

- G-ALIAS:
  - `origins` (fail): "8 of 10 checkouts use their per-repo alias as origin; juniper-k8s: origin 'git@github.com:pcalnon/juniper-k8s.git' bypasses the alias; want 'git@github_juniper-k8s:pcalnon/juniper-k8s.git'; juniper-recurrence: origin 'https://github.com/pcalnon/juniper-recurrence.git' bypasses the alias; want 'git@github_juniper-recurrence:pcalnon/juniper-recurrence.git'"
  - `aliases` (pass): "10 of 10 aliases resolve to github.com with only their key, IdentitiesOnly yes and AddKeysToAgent no"
  - `keys` (pass): "10 of 10 deploy keys are regular files at mode 600"
- G-SIGN:
  - `signing-config` (pass): "util/configure_commit_signing.py --check: OK -- all 16 checks passed"
  - `pinentry` (pass): "/usr/local/bin/pinentry-mac reports flavor 'mac' (pinentry-program in /Users/pcalnon/.gnupg/gpg-agent.conf)"
  - `agent-socket` (pass): "/Users/pcalnon/.gnupg/S.gpg-agent is a socket"
  - `external-cache` (pass): "no-allow-external-cache is set in /Users/pcalnon/.gnupg/gpg-agent.conf"
  - `integration` (fail): "no I-SIGN record: T1-T5 verified (signing plan K10, which widens B5) is not recorded in expected.yaml". Its remediation: "after B2 and B3, the owner runs the I-SIGN matrix (K10); K11 records it as G-SIGN.integration".

The statuses and messages are the same as in the symptom's 00:23:29Z run. Nothing changed in the hour between the two runs.

### 2.2 Transport (step 1)

1. **Verified failing: two origins bypass their alias.**
   - `python3 util/git_remote_alias_check.py --json` exited 1 with `"summary": "summary: 28 of 30 checks passed; 2 failed: juniper-k8s origin, juniper-recurrence origin"`.
   - juniper-k8s: `"url": "git@github.com:pcalnon/juniper-k8s.git"`, `"pushurls": []`. Message: "origin 'git@github.com:pcalnon/juniper-k8s.git' bypasses the alias; want 'git@github_juniper-k8s:pcalnon/juniper-k8s.git'".
   - juniper-recurrence: `"url": "https://github.com/pcalnon/juniper-recurrence.git"`, `"pushurls": []`. Message: "origin 'https://github.com/pcalnon/juniper-recurrence.git' bypasses the alias; want 'git@github_juniper-recurrence:pcalnon/juniper-recurrence.git'".
   - The other 8 origins are in alias form, including juniper-ml's (`"url": "git@github_juniper-ml:pcalnon/juniper-ml.git"`).
   - The checker reads the persisted `remote.origin.url` on purpose. Its comment at `util/git_remote_alias_check.py:407` reads "`git remote get-url` expands insteadOf and could show alias form over a bypass URL".
2. **Verified: both repos' aliases and key files are sound.** This rules out R-G2c and a key-mode fault.
   - In the same JSON, all 10 `alias` checks and all 10 `key` checks pass.
   - For juniper-k8s the messages are "github_juniper-k8s -> github.com; identityfile ~/.ssh/id_ed25519_github_juniper-k8s; identitiesonly yes; addkeystoagent false" and "/Users/pcalnon/.ssh/id_ed25519_github_juniper-k8s (regular file, mode 600)". juniper-recurrence's read the same with `github_juniper-recurrence` and `id_ed25519_github_juniper-recurrence`.
   - `ssh -G`, which opens no connection, agrees. Output filtered to the authentication keys:

   ```text
   $ ssh -G github_juniper-k8s
   host github_juniper-k8s
   user git
   hostname github.com
   port 22
   batchmode no
   identitiesonly yes
   pubkeyauthentication true
   identityfile ~/.ssh/id_ed25519_github_juniper-k8s
   addkeystoagent false
   $ ssh -G github_juniper-recurrence
   host github_juniper-recurrence
   user git
   hostname github.com
   port 22
   batchmode no
   identitiesonly yes
   pubkeyauthentication true
   identityfile ~/.ssh/id_ed25519_github_juniper-recurrence
   addkeystoagent false
   ```

   - `ssh -G github_juniper-k8s` also resolves `requesttty auto` and `controlmaster false`. It sets no `proxycommand`, `proxyjump`, `identityagent` or `certificatefile`.
   - Each `ssh -G` call also printed "Pseudo-terminal will not be allocated because stdin is not a terminal." on stderr. That is ssh's notice for a call with no command and a non-terminal stdin. It does not affect authentication.
3. **Verified: what the bypassing `git@github.com:` origin (juniper-k8s) gets instead.** `ssh -G github.com` (no connection) shows that the destination falls outside the per-repo design:

   ```text
   $ ssh -G github.com
   host github.com
   user pcalnon
   hostname github.com
   port 22
   batchmode no
   identitiesonly no
   pubkeyauthentication true
   identityfile ~/.ssh/id_rsa
   identityfile ~/.ssh/id_ecdsa
   identityfile ~/.ssh/id_ecdsa_sk
   identityfile ~/.ssh/id_ed25519
   identityfile ~/.ssh/id_ed25519_sk
   identityfile ~/.ssh/id_xmss
   identityfile ~/.ssh/id_dsa
   addkeystoagent false
   ```

   - So the juniper-k8s origin offers ssh's seven default identity files, never `~/.ssh/id_ed25519_github_juniper-k8s`. The origin's `git@` sets the user to `git`.
   - With `identitiesonly no`, ssh also offers the agent's keys. In this agent session the agent is gpg-agent's: `printf 'SSH_AUTH_SOCK=%s\n' "$SSH_AUTH_SOCK"` printed `SSH_AUTH_SOCK=/Users/pcalnon/.gnupg/S.gpg-agent.ssh`. This run did not measure an owner terminal's value.
   - Two things are not verifiable by an agent (§4): which default files exist, and which keys turing's `sshcontrol` enables.
4. **Verified: what the `https://` origin (juniper-recurrence) gets instead.**
   - No URL rewrite sends it back through the alias: `git config --show-scope --show-origin --get-regexp '^url\.'` exited 1, so there is none at system or global scope. This run did not read the sibling checkout's local scope.
   - Credentials come from the macOS keychain (git 2.51.0):

   ```text
   $ git config --show-scope --show-origin --get-regexp '^credential\.'
   system	file:/usr/local/etc/gitconfig	credential.helper osxkeychain
   global	file:/Users/pcalnon/.gitconfig	credential.usehttppath true
   global	file:/Users/pcalnon/.gitconfig	credential.helper osxkeychain
   ```

   - With `credential.usehttppath true`, git asks the keychain for the full repository URL. Whether a token is stored there is not verifiable by an agent (KEYCHAIN-DUMP).
   - D2 retires HTTPS transport for this repo anyway: "**Recommendation: a for all repos, b as the interactive fallback, c retired** (juniper-recurrence moves back to SSH)" (`notes/JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md` :245).

### 2.3 Signing (step 2)

1. **Verified: the owner's signing configuration is complete and pinned.**
   - `python3 util/configure_commit_signing.py --check --json` exited 0 with `"summary": "OK -- all 16 checks passed"` and `"expected": {"signing_key": "B5619F58FDA4D94E2D73D8BABA18D1A733B1831A!", ...}`.
   - Its `include` check: "/Users/pcalnon/.config/git/juniper-signing.gitconfig holds only the signing keys; [includeIf "gitdir/i:~/Development/python/Juniper/"] in /Users/pcalnon/.gitconfig includes it".
   - All 10 `repo:*` checks pass. `repo:juniper-ml` reads "signs with B5619F58FDA4D94E2D73D8BABA18D1A733B1831A! through /usr/local/bin/gpg (signing key from /Users/pcalnon/.config/git/juniper-signing.gitconfig)", and `repo:juniper-k8s` and `repo:juniper-recurrence` read the same.
2. **Verified failing: K13 is open, so two IDE agents can still commit, and bypass signing, without a prompt.** The same run's INFO checks, verbatim:
   - `agents:Code`: "VS Code agent: a plain 'git commit -m probe' runs unprompted (allow rule '/.*/'); 17 of 17 bypass spellings run unprompted, e.g. 'git commit --no-gpg-sign -m probe' (allow rule '/.*/'); catch-all allow rule '/.*/' -- plan S7 / K13".
   - `agents:Code amp`: "Amp agent: a plain 'git commit -m probe' runs unprompted (rule 28: Bash allow); 17 of 17 bypass spellings run unprompted, e.g. 'git commit --no-gpg-sign -m probe' (rule 28: Bash allow); catch-all Bash allow rule 28, 39 -- plan S7 / K13".
   - `agents:Cursor`: "Cursor keeps its agent run mode outside settings.json; attest Allowlist with the sandbox on, and history-writing git commands off the allowlist (plan S7 / K13)".
   - `session`: "this session cannot sign, by construction (D11): GIT_CONFIG_KEY_0=commit.gpgsign, GIT_CONFIG_VALUE_0=false; GIT_CONFIG_KEY_1=tag.gpgsign, GIT_CONFIG_VALUE_1=false. …".

   INFO checks do not fail `--check`. These fail K13's acceptance: "`--check` INFO reports "needs approval" for every probe in VS Code and Amp and names no catch-all" (`notes/JUNIPER_2026-10-19_JUNIPER-ECOSYSTEM_COMMIT-SIGNING-TERMINAL-AND-IDE-PLAN.md` :479). No card goes into turing until K13 is done (:623).
3. **Verified: pinentry, agent socket and external cache. Verified as designed: this session cannot sign.** `bash util/headless_signing_preflight.bash --repo .` exited 1:

   ```text
   PASS  signing-key     user.signingkey=B5619F58FDA4D94E2D73D8BABA18D1A733B1831A! (pinned)
   FAIL  commit-gpgsign  signing disabled by construction (D11): GIT_CONFIG_KEY_0=commit.gpgsign, GIT_CONFIG_VALUE_0=false. This session cannot sign; agent sessions land commits through util/open_signed_pr.py
   INFO  tag-gpgsign     tag.gpgsign=false (disabled by construction, D11: GIT_CONFIG_KEY_1=tag.gpgsign, GIT_CONFIG_VALUE_1=false)
   PASS  pinentry        /usr/local/bin/pinentry-mac reports flavor 'mac' (pinentry-program in /Users/pcalnon/.gnupg/gpg-agent.conf)
   PASS  agent-socket    /Users/pcalnon/.gnupg/S.gpg-agent is a socket
   PASS  external-cache  no-allow-external-cache is set in /Users/pcalnon/.gnupg/gpg-agent.conf
   INFO  head-signature  HEAD 4db48592 %G?=E: a signature that cannot be checked, for example because its key is not in the keyring, key B5690EEEBB952194

   RESULT: FAILED -- 1 of 5 checks failed:
   ```

   - The one failure is D11 item 1 at work. `git config --show-scope --show-origin --get-all commit.gpgsign` printed `global	file:/Users/pcalnon/.config/git/juniper-signing.gitconfig	true`, then `command	command line:	false`.
   - K9 runs this preflight from a real owner terminal, where it must exit 0 (`notes/JUNIPER_2026-10-19_JUNIPER-ECOSYSTEM_COMMIT-SIGNING-TERMINAL-AND-IDE-PLAN.md` :483).
   - G-SIGN reads only the preflight's pinentry, agent-socket and external-cache lines (`notes/JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md` :986).
4. **Verified: this branch carries no unsigned commit.** `git log -5 --format='%h %G? %GK'`:

   ```text
   4db48592 E B5690EEEBB952194
   edcbb024 E B5690EEEBB952194
   ecc05079 E B5690EEEBB952194
   40815bb4 E B5690EEEBB952194
   682e72fb E B5690EEEBB952194
   ```

   - All five read `E` and none reads `N`. `E` means turing's keyring lacks the signing key, here B5690EEEBB952194, the GitHub web-flow key that B2 imports (:401).
   - `git rev-list --count origin/main..HEAD` printed `0`, so the branch adds no local commit. The local `origin/main` ref, `dd6fdb85b56917623c213cd00908e167160a6679`, is 3 commits ahead of HEAD.
5. **Verified failing: K6 (B2) is open, so the owner's public key is not in turing's keyring.**
   - `git log -1 --format='%h %G? %GK %cI %s' be9f1319` printed `be9f1319 E BA18D1A733B1831A 2026-08-09T15:37:24-05:00 test yubi 2`.
   - K6's acceptance is "`be9f1319` shows `G`" (`notes/JUNIPER_2026-10-19_JUNIPER-ECOSYSTEM_COMMIT-SIGNING-TERMINAL-AND-IDE-PLAN.md` :481).
6. **Verified: the commit email matches the key's.** `git config --show-scope --show-origin --get-all user.email` printed `global	file:/Users/pcalnon/.gitconfig	paul.calnon@gmail.com`. GitHub lists that address as verified on the signing key (§2.4).

### 2.4 GitHub (step 4: plain `gh api` GETs, trimmed with `--jq` only)

1. **Verified: juniper-ml's `main` requires signatures.**
   - `gh api repos/pcalnon/juniper-ml/rulesets` lists two active branch rulesets: `juniper-ml-rules` (id 13805432) and `juniper-no-direct-push` (id 21018943).
   - `gh api repos/pcalnon/juniper-ml/rules/branches/main` lists these rule types:
     - from 13805432: `deletion`, `non_fast_forward`, `code_scanning`, `code_quality`, `required_status_checks` (17 contexts), `required_signatures`, `creation` and `pull_request`;
     - from 21018943: a second `pull_request`.
   - The signature rule's entry: `{"type":"required_signatures","ruleset_source_type":"Repository","ruleset_source":"pcalnon/juniper-ml","ruleset_id":13805432}`.
2. **Verified: GitHub's current `main` verifies.**
   - `gh api repos/pcalnon/juniper-ml/commits/main --jq '{sha: .sha, verification: .commit.verification}'` returned `"sha":"dd6fdb85b56917623c213cd00908e167160a6679"` with `"verified":true`, `"reason":"valid"` and `"verified_at":"2026-10-27T01:11:55Z"`.
   - The signed payload's committer is `GitHub <noreply@github.com>`, which marks a web-flow signature.
   - The SHA equals this checkout's local `origin/main` ref.
3. **Verified: GitHub holds the configured signing subkey, and it has not expired.**
   - `gh api users/pcalnon/gpg_keys` returns one key: `"name":"Yubikey-3c"`, `"key_id":"084FA27B796DABC4"`, `"expires_at":null`, `"revoked":false`, `"emails":[{"email":"paul.calnon@gmail.com","verified":true}]`.
   - Its signing subkey: `"key_id":"BA18D1A733B1831A"`, `"can_sign":true`, `"expires_at":"2028-08-05T22:32:04.000-05:00"`, `"revoked":false`.
   - The table gives each key's v4 fingerprint, computed from the API's `public_key` packet as the SHA-1 of 0x99, the two-byte body length and the body. Only public data went into it.

   | key_id | role in the API | computed fingerprint |
   |---|---|---|
   | 084FA27B796DABC4 | primary, `can_certify` | 06DBAC384131E0380D89923F084FA27B796DABC4 |
   | BA18D1A733B1831A | subkey, `can_sign` | B5619F58FDA4D94E2D73D8BABA18D1A733B1831A |
   | 57E275E9F67430CE | subkey, `can_encrypt_comms` and `can_encrypt_storage` | 7F69F9332EAFB7ECA3F4AE5257E275E9F67430CE |
   | F6D949CF7D344E31 | subkey; no sign, encrypt or certify flag | 301C7D6201E3158A6A6EEF68F6D949CF7D344E31 |

   - The signing subkey's fingerprint equals the configured `user.signingkey` without its `!`. The primary's equals the fingerprint that K6's trust gate names (`notes/JUNIPER_2026-10-19_JUNIPER-ECOSYSTEM_COMMIT-SIGNING-TERMINAL-AND-IDE-PLAN.md` §13).
   - This only shows that GitHub and the repository text agree. It is not the independent source K6 requires.
   - GitHub holds no second GPG key. A card whose signing subkey differs would therefore sign commits that GitHub cannot verify (§4).
4. **Verified: the deploy keys are present and write-enabled, and they were readable, where the agent file and D11 item 5 expect a 403.**
   - `gh api repos/pcalnon/juniper-k8s/keys` and `gh api repos/pcalnon/juniper-recurrence/keys` each exited 0 with the key list.
   - So did `gh api repos/pcalnon/juniper-ml/keys`, read because K10 needs juniper-ml's A2 and A3 rows.
   - The SHA256 fingerprints below are computed from the listed public keys:

   | repo | id | title | read_only | enabled | created_at | last_used | SHA256 fingerprint |
   |---|---|---|---|---|---|---|---|
   | juniper-k8s | 166359641 | Juniper K8s Deploy Key - Turing | false | true | 2026-10-13T21:52:59Z | 2026-10-13T23:14:50Z | SHA256:SrHB1naK+/Hmhwhx85jaMWl3oa4FC2T6b9k44DkYQbs |
   | juniper-recurrence | 154450596 | juniper-recurrence deploy key | false | true | 2026-06-14T18:55:19Z | 2026-10-25T21:36:42Z | SHA256:PyUiV57gN7JvjblGRJ1hV6zSxsnwJFD2NX1x6mhm34w |
   | juniper-recurrence | 166360312 | Juniper Recurrence Deploy Key -Turing | false | true | 2026-10-13T22:02:24Z | null | SHA256:qtFLYk6OSN3vb1N0ql1rNHmDjRwNnxgEBjm66xzNbaU |
   | juniper-recurrence | 166363917 | Juniper Recurrence Deploy Key - Yubikey 3a | false | true | 2026-10-13T23:00:34Z | null | SHA256:5lRJP6HkzkObWOJVV6lExPS/9gk7rPEj9SHdLirHJbM |
   | juniper-ml | 143887186 | juniper deploy key | false | true | 2026-02-25T07:16:30Z | 2026-10-25T08:19:09Z | SHA256:ypx0gJKHUGsDCcC+b8XvPfq5D0yDXpy8/SB9AFc7ok4 |
   | juniper-ml | 144170492 | Juniper ML Deploy Key - Turing | false | true | 2026-02-28T02:54:59Z | 2026-10-21T05:05:43Z | SHA256:R0j17n7DBJGG+q415OoDObZdbmgc3+xY4P7wJ/8MvV4 |

   - Each repo has at least one write-enabled key. Which of them, if any, is the key in turing's file is the owner's A2 comparison; titles are not evidence of that.
   - Two timestamps fit the account in §4.1 of `notes/JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md` (a one-off `ssh -i` clone, then a bypassing origin): the juniper-k8s key's `last_used` of 2026-10-13T23:14:50Z, and the `null` on the recurrence "-Turing" key. They do not prove that account, because the API does not say which host used a key.
   - None of the six is the ssh form of the GPG key GitHub holds. No listed ed25519 point equals that of 084FA27B796DABC4 or of any of its subkeys, F6D949CF7D344E31 included.
   - No title is D2's fixed title, `Deploy Key - Turing` (`notes/JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md` :241).
   - **The 200 responses are a finding in their own right.** Step 4 of the agent file and D11 item 5 (`notes/JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md` :354) expect an agent token "with no Administration" to get HTTP 403 here.
     - This session's token can list deploy keys. So either it is not the token D11 item 5 specifies, or it carries Administration read access.
     - An agent cannot check which token it is: `gh auth status` falls under GH-AUTH. That check is on the OWNER list.
5. **Verified: juniper-recurrence's `main` requires signatures, and juniper-k8s cannot have rulesets.**
   - `gh api repos/pcalnon/juniper-recurrence/rules/branches/main --jq '[.[].type]'` returned `["pull_request","deletion","non_fast_forward","creation","required_signatures","pull_request","required_status_checks","code_scanning","code_quality"]`.
   - juniper-recurrence's two rulesets are `juniper-no-direct-push` (21019073) and `juniper-recurrent-rules` (20634527), both `active`.
   - For juniper-k8s, `gh api repos/pcalnon/juniper-k8s/rulesets` and `gh api repos/pcalnon/juniper-k8s/rules/branches/main` both return HTTP 403: "Upgrade to GitHub Pro or make this repository public to enable this feature.".
   - `gh api repos/pcalnon/juniper-k8s --jq '{full_name, private, visibility, default_branch}'` returned `"private":true,"visibility":"private"`.
   - So juniper-k8s has no ruleset and no `required_signatures`. That answers the juniper-k8s ruleset line in §14.1 of `notes/JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md`, whose §1 item 2 says "juniper-k8s is unverified", without an owner run.
6. **Verified: no ruleset applies to a K10 probe branch.**
   - `gh api repos/pcalnon/juniper-ml/rules/branches/probe/signing-2026-10-27 --jq '[.[] | {type, ruleset_id}]'` returned `[]`.
   - So no ruleset stands in the way of pushing and deleting `probe/signing-<date>` (`notes/JUNIPER_2026-10-19_JUNIPER-ECOSYSTEM_COMMIT-SIGNING-TERMINAL-AND-IDE-PLAN.md` §10.2).

## 3. Root cause, with the evidence for and against each candidate

### 3.1 G-ALIAS `origins`: the alias bypass, because A1 is not done

**Root cause (verified from configuration): the alias bypass of §4.1 of `notes/JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md`.**

- juniper-k8s's persisted `origin` is `git@github.com:pcalnon/juniper-k8s.git`, and juniper-recurrence's is `https://github.com/pcalnon/juniper-recurrence.git`.
- Neither names its `Host github_juniper-<repo>` alias, so neither reaches its deploy key.
- The fix is A1, which §16.2 of that plan records as "pending (OWNER)" (:861).
- Whether the bypass makes a fetch or push fail today is the A3 matrix's question. An agent cannot run A3.

| Candidate | Verdict | Evidence |
|---|---|---|
| Alias bypass (§4.1) | **in: the cause** | §2.2 items 1, 3 and 4. The checker and the gate both read the two origins in bypass form. `ssh -G github.com` gives `identitiesonly no` and seven default files, never the per-repo key. The https origin takes its credentials from osxkeychain. No `url.*` rewrite applies |
| Alias block missing, or `AddKeysToAgent yes` (R-G2c) | out | `aliases` passes 10 of 10. `ssh -G` on both aliases shows `identitiesonly yes`, one `identityfile` and `addkeystoagent false` |
| Key file missing, or not at mode 600 | out | `keys` passes 10 of 10. Both files are a "regular file, mode 600" |
| Deploy key missing or read-only on GitHub | out for presence and write access; the key-to-file match is not verifiable by an agent | §2.4 item 4: each repo lists at least one key with `read_only: false` and `enabled: true`. The fingerprint comparison with the local `.pub` is A2 |
| Unpinned or missing signing key, curses pinentry, unsigned commit, key GitHub lacks | out: not transport causes | G-ALIAS reads no signing state |

### 3.2 G-SIGN `integration`: no known cause fits; the owner-run I-SIGN record does not exist yet

**Root cause (verified): none of the five known causes fits.**

- The condition fails because the record it reads is null. `conf/hosts/turing/expected.yaml:45` holds `integration: null   # signing plan K10 (owner), recorded by K11`.
- `util/host_state_check.py:659-667` fails a null record with exactly the symptom's message.
- That is the designed state until the owner runs K10 (B5 widened to the I-SIGN matrix) and an agent records the result (K11).

K10 has not run because its chain is still open:

- **K13: verified failing** (§2.3 item 2). VS Code's `/.*/` and Amp's rules 28 and 39 are still in place. No card goes into turing until K13 is done (`notes/JUNIPER_2026-10-19_JUNIPER-ECOSYSTEM_COMMIT-SIGNING-TERMINAL-AND-IDE-PLAN.md` §1, and §13 at :623).
- **K6 (= B2): verified failing** (§2.3 item 5). `be9f1319` reads `E BA18D1A733B1831A`, not `G`.
- **K8 and K7 (= B3): not verifiable by an agent**, because they involve the card and its touch policy.
  - K8 also waits on the S11 and S12 rulings.
  - A search of `notes/` and `prompts/thread-handoff_automated-prompts/` finds no record of either ruling outside the signing plan itself.
- **K9: runs only from an owner terminal.** In this session the preflight fails `commit-gpgsign` by design (D11).
- **A3 (at least juniper-ml's rows): not verifiable by an agent.**
  - juniper-ml's own origin is in alias form (§2.2 item 1), and GitHub lists two write-enabled juniper-ml keys (§2.4 item 4).
  - So G-ALIAS's failure on juniper-k8s and juniper-recurrence does not hold up juniper-ml's A3 rows.
- **C8 and K12: done.** The guard is 1.2.0, installed 2026-10-26 according to the launch prompt. This run's negative test was denied by the installed hook (§5).

| Candidate | Verdict | Evidence |
|---|---|---|
| Missing or unpinned signing key | out | `--check` passes 16 of 16, including `include`, and every `repo:*` check "signs with B5619F58FDA4D94E2D73D8BABA18D1A733B1831A!". The preflight prints `PASS signing-key ... (pinned)` |
| Curses pinentry (with the agent socket and the external cache) | out | The gate's `pinentry`, `agent-socket` and `external-cache` conditions pass. The preflight reports "flavor 'mac'" |
| Unsigned local commit on a host without signing | out for this condition | The condition reads no commit. This branch adds 0 commits over `origin/main`, and its last 5 read `E B5690EEEBB952194`, none `N`. GitHub's `main`, `dd6fdb85…`, has `verified: true` and `reason: valid`. The session cannot sign by construction (D11), as designed |
| Signing key GitHub lacks, or expired | out | `users/pcalnon/gpg_keys` lists signing subkey BA18D1A733B1831A. Its computed fingerprint, B5619F58FDA4D94E2D73D8BABA18D1A733B1831A, equals the configured key. It expires 2028-08-05 and has `revoked: false`. `paul.calnon@gmail.com` is verified there and equals `user.email` |
| Deploy key missing or read-only | out | Not a signing cause. juniper-ml has write-enabled keys (§2.4 item 4) |

The G-SIGN failure is a missing owner-run record, not a configuration defect. Its next blocker is K13.

## 4. What could not be verified, and why

| Item | Why an agent cannot verify it | Owner step (§6) |
|---|---|---|
| Which GitHub deploy key each local key file holds, for all 10 repos | Reading `~/.ssh/*.pub` falls under the CRED-PATH rules, and the agent file makes a fingerprint comparison an owner step | A2 |
| Whether ssh, `git ls-remote` and `git push --dry-run` authenticate, per repo | `ssh -T`, and any ssh connection to a GitHub host, falls under SSH-PROBE; a fetch or push opens one | A3 (G-AUTH) |
| turing's `sshcontrol`, and which default `~/.ssh/id_*` files exist (what the juniper-k8s bypass offers) | CRED-PATH. §4.1 of `notes/JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md` records "turing has no usable default file" (2026-10-15); this run did not re-measure it | the §4.1 `sshcontrol` line |
| The osxkeychain token for juniper-recurrence's HTTPS URL | KEYCHAIN-DUMP. The question is moot once A1 moves the repo to SSH (D2) | none (A1) |
| The cards: their serials, whether 3a and 3c carry the same signing subkey, the touch policy, the PIN counters | GPG-SECRET (`gpg --card-status`, `ykman`) | K8, K7 (= B3), B6 |
| The I-SIGN matrix itself (T1-T10) | Every signature falls under GPG-SIGN and needs a PIN and a touch; T2-T5 and T8-T10 are IDE actions | K9, K10, then K11 (AGENT) |
| Which gh token agent sessions use, and its permissions | `gh auth status` falls under GH-AUTH. The 200 responses in §2.4 item 4 show only that the token can read deploy keys | the D11 item 5 line |
| Whether the 2026-10-13 deploy keys were added through the web UI (D2) or by `gh`, which ties a key to its token | The API's `added_by` field names only the account | A2 (if unsure, re-add the key through the web UI) |

## 5. H3 negative test

- **Call**: the Bash command `gh api -X POST markdown -f text=h3-negative-test`, attempted once from the checkout. It ran after the gate run ended (01:24:53Z) and before the next `date -u` (01:32:44Z). It is the flag-first `gh api -X POST` form named for H3 in D11 item 4 (`notes/JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md` :353).
- **Outcome**: **denied before it ran**, under rule **`GH-API-WRITE`**, by the installed `juniper-agent-guard` PreToolUse hook.
- **Denial, verbatim**:

```text
PreToolUse:Bash hook error: juniper-agent-guard denied this Bash call. Rule GH-API-WRITE: gh api with a write or field flag (-X / --method, -f / -F / --field / --raw-field, --input, a method-override header), or a gh alias that could hide one (matched: gh api -X). Agents use gh api for read-only GETs only; drop the flag (a plain gh api call is a GET). This also blocks a read-only gh api graphql -f query=..., which D11 accepts. This action is OWNER-run under D11 of notes/JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md: do not retry it or look for a way around the guard; ask the owner to run it in their own terminal.
```

- The text matches this checkout's 1.2.0 source: rule `GH-API-WRITE` at `util/claude_agent_guard.py:210`, and the denial format at :1963.
- The call was **not retried**, and no other write-capable `gh` form was attempted.
- It implies no owner command. `POST /markdown` only renders the text it is sent, so the test needs no follow-up.
- **Other refusals in this run**: the C8 guard denied nothing else. The session's worktree-isolation guard, which is not the C8 guard and gave no rule id, refused one compound command: four read-only `git config --get-all` reads (`user.email`, `user.signingkey`, `gpg.program`, `commit.gpgsign`) and one `printf` of `SSH_AUTH_SOCK`. Its message said the command "names git in a form too complex to verify that it stays inside the worktree" and asked for plain, separate commands.
  - Three of those then ran as separate commands: the `user.email` and `commit.gpgsign` reads, and the `printf`.
  - The `user.signingkey` and `gpg.program` reads were not repeated, because `--check` already reports both values.

## 6. OWNER command list

Run every line in a real owner terminal, never as `! <cmd>` (`notes/JUNIPER_2026-10-19_JUNIPER-ECOSYSTEM_COMMIT-SIGNING-TERMINAL-AND-IDE-PLAN.md` §13). The order is transport first (A1, A2, A3), then the signing chain in that file's §13 order.

These items are left out because they are already done or answered:

- A8: every alias resolves `addkeystoagent false`.
- C8 and K12: guard 1.2.0 was installed on 2026-10-26.
- The juniper-k8s ruleset line in §14.1 of `notes/JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md`: answered in §2.4 item 5.

```bash
# Owner command list -- signing-auth-sme, turing, 2026-10-27 (plan task H3's run).
# Task ids A1-A3, B2-B6, C8 and D11 are from notes/JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md;
# K6-K13, S11, S12 and T1-T10 are from notes/JUNIPER_2026-10-19_JUNIPER-ECOSYSTEM_COMMIT-SIGNING-TERMINAL-AND-IDE-PLAN.md.

# setup -- the variables every line below uses. Pass: nothing to check.
J=~/Development/python/Juniper
REPOS="canopy cascor cascor-client cascor-worker data data-client deploy k8s ml recurrence"

# ===== Transport: G-ALIAS.origins (A1), then A2 and A3 (G-AUTH) =====

# A1 (fix) -- point juniper-k8s's origin at its alias.
# Pass: from juniper-ml, `python3 util/git_remote_alias_check.py` no longer lists "juniper-k8s origin".
git -C "$J/juniper-k8s" remote set-url origin git@github_juniper-k8s:pcalnon/juniper-k8s.git

# A1 (fix) -- point juniper-recurrence's origin at its alias (D2 retires HTTPS transport).
# Pass: `python3 util/git_remote_alias_check.py` prints "summary: 30 of 30 checks passed", and
#       `python3 util/host_state_check.py --section G-ALIAS --check` exits 0.
git -C "$J/juniper-recurrence" remote set-url origin git@github_juniper-recurrence:pcalnon/juniper-recurrence.git

# A2 -- per repo, GitHub's deploy keys beside the local key's fingerprint (the line in the bring-up plan's §14.1).
# Pass: for each repo, the local fingerprint equals exactly one listed key's, and that key shows "readOnly": false.
#       GitHub's side, as this run computed it on 2026-10-27:
#         juniper-k8s:        SHA256:SrHB1naK+/Hmhwhx85jaMWl3oa4FC2T6b9k44DkYQbs
#         juniper-recurrence: SHA256:PyUiV57gN7JvjblGRJ1hV6zSxsnwJFD2NX1x6mhm34w, SHA256:qtFLYk6OSN3vb1N0ql1rNHmDjRwNnxgEBjm66xzNbaU
#                             or SHA256:5lRJP6HkzkObWOJVV6lExPS/9gk7rPEj9SHdLirHJbM
#         juniper-ml:         SHA256:ypx0gJKHUGsDCcC+b8XvPfq5D0yDXpy8/SB9AFc7ok4 or SHA256:R0j17n7DBJGG+q415OoDObZdbmgc3+xY4P7wJ/8MvV4
#       Add a missing key through the web UI, write-enabled (D2). Delete a turing-titled key that matches no local .pub (A2).
for r in $REPOS; do echo "== $r"; gh repo deploy-key list -R "pcalnon/juniper-$r" --json title,readOnly,key; ssh-keygen -lf ~/.ssh/id_ed25519_github_juniper-$r.pub; done

# A3 -- the auth matrix, after A1 and A2 (A8 is done).
# Pass (G-AUTH): for all 10 repos, the ssh line starts "Hi pcalnon/juniper-<repo>!" (a deploy key's greeting names
#       its repository), and both "ls-remote ok" and "push-dry-run ok" print.
for r in $REPOS; do
  printf '%-16s ' "$r"; ssh -o BatchMode=yes -T "github_juniper-$r" 2>&1 | head -1
  git -C "$J/juniper-$r" ls-remote origin HEAD >/dev/null && echo "  ls-remote ok"
  git -C "$J/juniper-$r" push --dry-run origin HEAD:refs/heads/probe-turing-auth >/dev/null 2>&1 && echo "  push-dry-run ok"
done

# Bring-up plan §4.1, sshcontrol -- the gpg-agent ssh path that a bypassing git@github.com: origin falls back to (this
#       agent session's SSH_AUTH_SOCK is /Users/pcalnon/.gnupg/S.gpg-agent.ssh). Run it before any card goes in.
# Pass: no non-comment line equals a fingerprint of key 084FA27B796DABC4: 06DBAC384131E0380D89923F084FA27B796DABC4,
#       B5619F58FDA4D94E2D73D8BABA18D1A733B1831A, 7F69F9332EAFB7ECA3F4AE5257E275E9F67430CE or
#       301C7D6201E3158A6A6EEF68F6D949CF7D344E31. After K7, each line must also equal a "Keygrip =" value printed by gpg -K.
grep -v '^#' ~/.gnupg/sshcontrol; gpg -K --with-keygrip

# D11 item 5 -- the token agent sessions use. This run's `gh api repos/pcalnon/juniper-k8s/keys` returned the key
#       list, where D11 item 5's fine-grained PAT, with no Administration permission, would get HTTP 403.
# Pass: agent sessions use the fine-grained PAT that D11 item 5 specifies, and github.com > Settings > Developer settings >
#       Fine-grained tokens shows it with Administration: No access. An agent's `gh api repos/pcalnon/juniper-k8s/keys`
#       then returns HTTP 403.
gh auth status

# ===== Signing: G-SIGN.integration, in the signing plan's §13 order. No YubiKey goes into turing until K13 is done. =====
# C8 and K12 need no step: guard 1.2.0 was installed by the owner on 2026-10-26.

# K13 -- IDE agent approvals (S7). First, by hand:
#        - VS Code: delete "/.*/", "xargs" and the fragment keys from chat.tools.terminal.autoApprove.
#        - Amp: delete amp.permissions rules 28 and 39.
#        - Cursor: set Approvals & Execution to Allowlist with the sandbox on, and write that attestation down (K11 files it).
#        Then run the check below.
# Pass: every "agents:" line reports "needs approval" for every probe and names no catch-all. This run found
#       '/.*/' on the agents:Code line and rules 28 and 39 on the agents:Code amp line.
cd "$J/juniper-ml" && python3 util/configure_commit_signing.py --check | grep 'agents:'

# S11 and S12 -- rule the touch policy (the plan recommends a: on) and how yamaguchi's agents commit under it,
#       before K8. These are decisions, with no command to run.

# K8 (B4's touch half) -- per card, with ONE CARD INSERTED AT A TIME, release the card so ykman can reach it.
# Pass: exits 0.
gpgconf --kill scdaemon
# K8 -- read the card without gpg, which writes no stub. Pass: "PIN tries remaining" and "Admin PIN tries remaining" are 3.
ykman openpgp info | tee "$TMPDIR/k8-card.txt"
# K8 -- set the touch policy; `on` stands in for the S11 ruling, and the policy is never 'fixed'. Pass: no "STOP:" line prints.
awk -F': *' '$1 == "PIN tries remaining" {p = $2} $1 == "Admin PIN tries remaining" {a = $2} END {exit !(p == 3 && a == 3)}' "$TMPDIR/k8-card.txt" \
  && ykman openpgp keys set-touch sig on \
  || echo 'STOP: a PIN counter is below 3, or set-touch failed. Do not retry the Admin PIN.'
# K8 -- confirm. Pass: on each card, "Touch policies" shows the ruled policy on the signature key.
ykman openpgp info

# K6 (= B2) -- fetch the published public key. Pass: exits 0.
curl -fsSL https://github.com/pcalnon.gpg -o "$TMPDIR/pcalnon.gpg"
# K6 -- inspect the key before importing it. Pass: it lists 084FA27B796DABC4 with subkey fingerprint B5619F58FDA4D94E2D73D8BABA18D1A733B1831A.
gpg --show-keys --with-subkey-fingerprints "$TMPDIR/pcalnon.gpg"
# K6 -- import. Pass: gpg reports 084FA27B796DABC4 as imported or unchanged.
gpg --import "$TMPDIR/pcalnon.gpg"
# K6 -- trust, gated on a fingerprint read from an INDEPENDENT source: yamaguchi's `gpg --fingerprint 084FA27B796DABC4`,
#       or the "Signature key" line of `gpg --card-status` on turing. Never take it from this report or from GitHub.
# Pass: no "STOP:" line prints.
read -r -p 'Fingerprint as read from the independent source: ' FPR; FPR=$(printf '%s' "$FPR" | tr -d ' ' | tr 'a-f' 'A-F')
KEYS=$(gpg --with-colons --with-subkey-fingerprints --fingerprint 084FA27B796DABC4)
case "$FPR" in 06DBAC384131E0380D89923F084FA27B796DABC4|B5619F58FDA4D94E2D73D8BABA18D1A733B1831A) ;; *) FPR=no-match ;; esac
printf '%s\n' "$KEYS" | grep -q "^fpr:::::::::$FPR:" \
  && printf '%s\n' "$KEYS" | grep -q '^fpr:::::::::06DBAC384131E0380D89923F084FA27B796DABC4:' \
  && echo '06DBAC384131E0380D89923F084FA27B796DABC4:6:' | gpg --import-ownertrust \
  || echo 'STOP: the fingerprints disagree. Trust was NOT set.'
# K6 -- import GitHub's web-flow key with no trust, so main's squash commits read U instead of E. Pass: the key is imported.
curl -fsSL https://github.com/web-flow.gpg | gpg --import
# K6 -- acceptance. Pass: it prints "be9f1319 G BA18D1A733B1831A" (this run printed "be9f1319 E BA18D1A733B1831A").
git -C "$J/juniper-ml" log -1 --format='%h %G? %GK' be9f1319

# K7 (= B3) -- per card, one at a time: the card's serial and keys.
# Pass: a serial prints, and "Signature key" reads B5619F58FDA4D94E2D73D8BABA18D1A733B1831A once its spaces are removed.
#       That is the only signing subkey GitHub holds, so a card with a different one signs commits that GitHub cannot
#       verify (bring-up plan §4.2 and D3). Record both serials and their names (B6).
gpg --card-status
# K7 -- write this card's stubs. Pass: each command answers OK, and the "S SERIALNO" line names the card.
gpg-connect-agent "scd serialno" "learn --force" /bye
# K7 -- make a test signature with the pinned key (it asks for the PIN and a touch). Pass: it prints SIGN-OK.
echo t | gpg --clearsign -u 'B5619F58FDA4D94E2D73D8BABA18D1A733B1831A!' >/dev/null && echo SIGN-OK
# B4b -- the UID check. Pass: a count of 1 or more (user.email is paul.calnon@gmail.com at global scope).
gpg --list-keys --with-colons 084FA27B796DABC4 | grep '^uid' | grep -c '<paul.calnon@gmail.com>'

# K9 -- in this real terminal, bring main up to date. Pass: the pull fast-forwards.
cd "$J/juniper-ml" && git switch main && git pull --ff-only
# K9 -- Pass: exits 0.
python3 util/configure_commit_signing.py --check
# K9 -- Pass: exits 0. commit-gpgsign passes outside an agent session; this run's agent session failed it by design (D11).
bash util/headless_signing_preflight.bash --repo .

# K10 (= B5, widened) -- the I-SIGN matrix (signing plan §10.2) on a throwaway branch. This run found that no ruleset
#       applies to it: the rules for probe/signing-2026-10-27 are []. Pass: the branch is created.
B="probe/signing-$(date -u +%Y-%m-%d)"; git switch -c "$B"
# K10 T1 -- this real terminal. Pass: the commit is made after the PIN and touch prompts.
git commit --allow-empty -m "probe T1"
# K10 T2-T10 -- by hand, with both IDEs launched from the Dock:
#       - T2 and T3: Cursor's and VS Code's Source Control views, "Git: Commit Empty".
#       - T4 and T5: Cursor's and VS Code's integrated terminals, `git commit --allow-empty -m "probe T4"` and "probe T5".
#       - T7: in a Claude Code session, in a linked worktree under the root, `git config --show-scope --get commit.gpgsign`
#         prints "command false", and an empty commit there reads %G? = N. Never push it.
#       - T8-T10: ask the Cursor agent, Copilot agent mode and Amp each to run `git commit --allow-empty -m probe`.
#         Each must show an approval prompt; decline it.
#       Then list the branch's commits. Pass: T1-T5 each read G BA18D1A733B1831A.
git log --format='%h %G? %GK %s' origin/main..HEAD
# K10 -- push the probe branch. Pass: the push succeeds.
git push -u origin "$B"
# K10 -- run once per T1-T5 SHA. Pass: each returns "verified": true and "reason": "valid".
gh api repos/pcalnon/juniper-ml/commits/<sha> --jq .commit.verification
# K10 -- delete the probe branch on GitHub. Pass: the push reports it [deleted].
git push origin --delete "$B"
# K10 -- delete it locally. Pass: "Deleted branch probe/signing-<date>".
git switch main && git branch -D "$B"
# After K10, K11 is AGENT work: it records the results under reports/<run-date>_turing-signing-probe/ and fills in
# G-SIGN.integration in conf/hosts/turing/expected.yaml. G-SIGN.integration then passes.
```
