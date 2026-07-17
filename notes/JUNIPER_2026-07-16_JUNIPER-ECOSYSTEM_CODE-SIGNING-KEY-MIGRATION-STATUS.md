# Code-Signing Key Migration — Findings & Deferred Work

**Project**: Juniper — Cascade Correlation Neural Network Research Platform
**Scope**: Ecosystem-wide (git commit signing on the development host + GitHub account keys + per-repo rulesets)
**Author**: Paul Calnon (investigation and edits driven via Claude Code session)
**Date**: 2026-07-16
**Status**: PARTIALLY MIGRATED — remaining steps DEFERRED (see §5)

---

## 1. How this surfaced

During the PyPI release-train wave-2 fan-out (2026-07-14), task-executor agents committing in the
juniper-data / juniper-data-client / juniper-cascor-client repos hit intermittent GPG failures
(`KEYEXPIRED`, `Bad PIN`) and fell back to `git commit --no-gpg-sign`. A push to juniper-cascor-client
additionally printed **ruleset bypass warnings** ("Commits must have verified signatures" — bypassed by
the owner token). That prompted a full diagnosis of the signing setup on 2026-07-16.

## 2. Key inventory (as diagnosed 2026-07-16)

| Key | Algo / created | Expiry | Where | UID email | Role |
|---|---|---|---|---|---|
| `EDA873F7371DA4C7` | rsa4096, 2019-01-10 | **expired 2021-01-09** | offline stub (`sec#`) | paul.calnon@gmail.com | 2019 certify master; its a/s/e subkeys expired 2021-01-08 |
| `B5AFCD0686585249` | rsa4096, 2019-01-10 | one resolution path expired, one never-expires (see §3) | YubiKey (card `0006 09258397`), `sec>` | paul.calnon@gmail.com | **was** git `user.signingkey` |
| `93E8591643C507FF` | ed448, 2025-08-29 | never | YubiKey "yubikey-3" | overtoad.research@gmail.com | intended replacement; **now** git `user.signingkey` |

## 3. Diagnosis

1. **Git pointed at the 2019 key.** `user.signingkey` was `0xB5AFCD0686585249`. The replacement ed448
   key (`93E8591643C507FF`, created 2025-08-29, uid comment "yubikey-3") existed with ultimate trust
   but git was never repointed — a repoint, not a renewal, was the actual fix.
2. **Ambiguous key-ID resolution explains `KEYEXPIRED`.** The id `B5AFCD0686585249` resolves along two
   paths in the keyring: via the expired 2019 chain (master `EDA873F7` + expired s/a/e subkeys) and via
   a never-expiring standalone `[SC]` entry. Depending on resolution, gpg either signed fine or failed
   `KEYEXPIRED`. Pinning with a trailing `!` (exact-key suffix) eliminates this class.
3. **`Bad PIN` was YubiKey contention, not a wrong PIN.** Multiple parallel agents signing at once
   serialize on a single card; concurrent access produced card errors. Card-resident keys are
   inherently unusable for parallel headless automation.
4. **Verification email mismatch (latent).** The ed448 key's only uid is `overtoad.research@gmail.com`
   while git `user.email` is `paul.calnon@gmail.com`. GitHub marks a commit Verified only when the
   committer email matches a verified account email that appears in the signing key's uids — as-is,
   signed commits would show **Unverified (email mismatch)** even after the key is uploaded.

## 4. What was done (2026-07-16)

- `git config --global user.signingkey '93E8591643C507FF!'` — repointed to the ed448 yubikey-3 key,
  **exact-pinned** with the `!` suffix (kills the §3.2 ambiguity class). `commit.gpgsign` remains `true`.
- Verified the ed448 key signs (interactive PIN entry; headless signing works only while the PIN is
  cached in gpg-agent — a later probe commit popped pinentry on the desktop and was cancelled, which is
  the expected behavior for a card key without a cached PIN).
- Established the **operational rule for automation** (agents / headless sessions): always commit with
  `git -c commit.gpgsign=false commit …`. A card-resident key cannot sign without a human; attempting
  it pops a pinentry dialog on the owner's display and then fails the commit.

## 5. Deferred work (re-entry checklist)

1. **UID/email alignment** (pick one):
   - `gpg --quick-add-uid 93E8591643C507FF 'Paul Calnon <paul.calnon@gmail.com>'` (recommended —
     keeps the long-standing commit identity), or
   - switch `git config --global user.email` to `overtoad.research@gmail.com` (changes commit identity
     everywhere).
2. **Upload the public key to GitHub**: `gpg --armor --export 93E8591643C507FF` → paste at
   `github.com/settings/gpg/new`. (The session token lacks `admin:gpg_key` scope, so this is a
   console action.)
3. **Empirical ed448 verification probe** — REQUIRED before trusting the setup: one signed empty
   commit on a throwaway branch, push, inspect `.commit.verification` via
   `gh api repos/<owner>/<repo>/commits/<sha>`. GitHub's documented EdDSA support has historically
   meant **Ed25519; ed448 acceptance is unconfirmed**. If the probe shows `unverified`
   with a valid local signature: fall back to an **ed25519 signing subkey** on the same card, or to
   **SSH commit signing** (`gpg.format ssh` with the existing YubiKey SSH key).
4. **Bot-commit policy decision.** Headless automation cannot sign (see §4). Current practice:
   unsigned bot commits; on repos whose rulesets require verified signatures (observed:
   juniper-cascor-client, which also restricts branch create/delete), owner-token pushes bypass with
   warnings. Decide: relax those rulesets for `ci/*`+`fix/*` lanes, scope them to `main` only, or
   accept the recurring bypass warnings.
5. **Old-key disposition.** After the probe verifies: leave the old RSA public key uploaded on GitHub
   (keeps historical commits Verified); locally mark the 2019 chain retired (optionally revoke the
   expired master). Do not delete it from GitHub.

## 6. References

- Release-train wave-2 context: `notes/JUNIPER_2026-07-11_JUNIPER-ECOSYSTEM_PYPI-RELEASE-TRAIN-WORKFLOW-PLAN.md`
  (the work during which this surfaced).
- GitHub docs: "About commit signature verification" (email-match + supported-algorithm rules).
- gpg specifics preserved above (fingerprints, card serial, uid strings) were read from the live
  keyring on 2026-07-16; re-verify with `gpg --list-secret-keys --keyid-format long` on re-entry.
