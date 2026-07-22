# Recurrence Secret Provision — JUNIPER_RECURRENCE_API_KEYS in .env.secrets.enc — Execution Plan

**Project**: Juniper
**Repository**: pcalnon/juniper-ml (plan document); execution in pcalnon/juniper-deploy
**Author**: Paul Calnon
**Date**: 2026-07-22
**Status**: APPROVED as written (owner, 2026-07-22) — implementation in flight in the authoring session

---

## 1. Context

juniper-deploy#160 (merged 2026-07-22) provisions the `juniper_recurrence_api_keys` secret surface and sets `JUNIPER_RECURRENCE_REQUIRE_AUTH=true` for the composed stack, completing SEC-F01 parity for juniper-recurrence. However `.env.secrets.enc` — the SOPS-encrypted canonical secrets bundle — carries no `JUNIPER_RECURRENCE_API_KEYS` entry: `scripts/prepare_secrets.bash` reports populated=7, placeholder/empty=1 (the new recurrence file), so the next recurrence bring-up refuses to boot (CRITICAL + AuthPostureError — the intended fail-closed behavior) until a real token exists. The owner directed populating the constant now. A small remnant of the ml#695 cleanup (worktree prune + primary sync) is folded into step 1.

## 2. Verified facts

- `.env.secrets.enc` and `.sops.yaml` are git-tracked in juniper-deploy, so the change ships as a branch + owner-merge PR whose diff is an opaque re-encrypted blob.
- sops 3.12.1 is installed; the age private key exists at `~/.config/sops/age/keys.txt` (mode 0600). A bare `sops -d .env.secrets.enc` FAILS ("invalid character '#'") because the `.enc` suffix defeats format sniffing — the working house invocation, taken from `scripts/prepare_secrets.bash:88`, is `sops --input-type dotenv --output-type dotenv -d`.
- The `.sops.yaml` creation rule is `path_regex: \.env(\.secrets)?$` with `encrypted_regex: "^.+$"` and a single age recipient — so the plaintext intermediate must be named `.env.secrets` (worktree root) for re-encryption to select the right rule, and is deleted immediately after. The `no-unencrypted-env` pre-commit hook blocks any accidental commit of the plaintext.
- Token format rule (from the prepare-secrets #91/#92 incident): a **raw single-line token, never JSON** — the recurrence service parses the accept-list as CSV; canopy sends the same value verbatim as `X-API-Key`.
- One token serves all consumers (symmetric mount, single source of truth): recurrence inbound accept-list, canopy and canopy-demo outbound key.

## 3. Security discipline (hard rules)

- The token value is NEVER echoed, printed, logged, or included in any PR/commit text. All verification is by key-name grep counts and byte lengths only.
- Token generation and every write that uses it happen inside a single shell invocation (`TOKEN=$(openssl rand -hex 32)`), since shell env does not persist across tool calls.
- The plaintext `.env.secrets` exists only for the seconds between decrypt and re-encrypt inside the worktree, then is removed; `git status` is re-checked afterward to prove no plaintext is staged or lingering.

## 4. Steps

1. Finish the ml#695 cleanup remnant: `git worktree prune` + ff-sync the juniper-ml primary (the remote branch had been auto-deleted by GitHub on merge — first observed auto-delete on this repo; cleanup tooling now tolerates it).
2. juniper-deploy worktree on branch `chore/populate-recurrence-secret` from origin/main (central `worktrees/` naming).
3. Single-shot token flow (one Bash invocation, no value output):
   a. `TOKEN=$(openssl rand -hex 32)` — 64-char hex, the same shape class as the sibling keys.
   b. `sops --input-type dotenv --output-type dotenv -d .env.secrets.enc > .env.secrets`
   c. Guard: abort if `JUNIPER_RECURRENCE_API_KEYS` already exists in the decrypted bundle (a concurrent session may have acted); otherwise append `JUNIPER_RECURRENCE_API_KEYS=$TOKEN`.
   d. `sops --input-type dotenv --output-type dotenv -e .env.secrets > .env.secrets.enc` then `rm .env.secrets`.
   e. Write the same token to the PRIMARY deploy checkout's live `secrets/juniper_recurrence_api_keys.txt` (chmod 600, matching siblings) so the running host is bring-up-ready immediately, independent of merge/pull timing. `prepare_secrets.bash` never clobbers an existing non-empty file for a key absent from its bundle, and after the PR merges the bundle and the file agree.
4. Verification (names/counts only): decrypted-stream `grep -c '^JUNIPER_RECURRENCE_API_KEYS='` equals 1; `bash scripts/prepare_secrets.bash` in the worktree reports populated=8 placeholder/empty=0; `wc -c` of the generated secrets file exceeds 32; `git status --porcelain` shows ONLY `.env.secrets.enc` modified; pre-commit passes on the changed file.
5. Commit + push + owner-merge PR (`-c commit.gpgsign=false`): the body explains the opaque encrypted diff, the raw-token format rule, that the live host's `secrets/` file already carries the same value, and that other checkouts obtain it via `make prepare-secrets` after pulling.
6. On the owner's merge signal: standard worktree/branch cleanup + deploy primary sync.

## 5. End-state verification

- Worktree `prepare_secrets.bash` run: populated=8, placeholder/empty=0.
- Primary checkout: `secrets/juniper_recurrence_api_keys.txt` present, mode 600, non-trivial length.
- After merge and the next `make up` (owner smoke): recurrence boots with the posture INFO log (not CRITICAL), keyless requests to protected recurrence routes return 401, and the canopy-to-recurrence A1 flow authenticates with the shared token.

## 6. Validation record

Facts probed read-only in the authoring session on 2026-07-22 (sops version/behavior, `.sops.yaml` creation rule, age-key presence, tracked-file status, prepare-secrets decrypt invocation and populate counts). Owner approved the plan as written on 2026-07-22 and directed archival of this document ahead of implementation.
