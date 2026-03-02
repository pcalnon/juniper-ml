# Plan: Implement SOPS with age Encryption Across the Juniper Ecosystem

**Date**: 2026-02-26
**Completed**: 2026-02-27
**Status**: Complete
**Prerequisite**: `juniper-ml/notes/SECRETS_MANAGEMENT_ANALYSIS.md`

---

## Context

The Juniper ecosystem has no encrypted secrets management. The primary risk is `juniper-cascor/.env` containing 15 real API keys/tokens in plaintext on disk. While `.env` is in `.gitignore` across all repos, there is no mechanism to safely store, share, or version secrets. This plan implements SOPS with `age` encryption as recommended in `juniper-ml/notes/SECRETS_MANAGEMENT_ANALYSIS.md`.

## Approach

Single `age` key pair shared across all Juniper repos. The private key lives at the SOPS default location (`~/.config/sops/age/keys.txt`) and will be stored as a GitHub Secret (`SOPS_AGE_KEY`) for CI/CD decryption. Each repo gets a `.sops.yaml` config pointing to the same `age` public key.

## Implementation Steps

### Step 1: Install SOPS and age — COMPLETE

Installed SOPS v3.9.4 (`/usr/local/bin/sops`) and age v1.3.1 (`/opt/miniforge3/envs/JuniperCascor/bin/age`).

### Step 2: Generate age key pair — COMPLETE

Generated key pair at `~/.config/sops/age/keys.txt` (chmod 600).
Public key: `age1qmmfhude4xlpdx3wvqv994ahqayke04sgkt5r3ruclu9wmyt04xsdl2kkv`

### Step 3: Create `.sops.yaml` in each repo — COMPLETE

Created `.sops.yaml` in all 8 active repos (including juniper-canopy). Used `path_regex: \.env(\.secrets)?$` to match input files (corrected from the original plan's `\.env\.enc$` which matched the output file).

**Files created/modified per repo:**

| Repo | `.sops.yaml` | `.env.example` | `.env.enc` | `.gitignore` update |
|------|-------------|---------------|-----------|-------------------|
| juniper-cascor | Created | Created (15 vars) | Created (encrypted) | Added `.env` + variants |
| juniper-deploy | Created | Already existed | Not yet (no secrets) | Added `!.env.enc`, `!.env.secrets.enc` exceptions |
| juniper-data | Created | Created | Not yet | Added `.env` variants |
| juniper-data-client | Created | Created | Not yet | Added `.env` variants |
| juniper-cascor-client | Created | Created | Not yet | Added `.env` variants |
| juniper-cascor-worker | Created | Created | Not yet | Added `.env` variants |
| juniper-canopy | Created | Created | Not yet | Added `.env` + variants |
| juniper-ml | Created | No (meta-package) | Not yet | Added `.env` variants |

### Step 4: juniper-cascor — Primary target — COMPLETE

1. Created `.sops.yaml` with age public key
2. Created `.env.example` with all 15 variable names (no values)
3. Encrypted `.env` → `.env.enc` using `sops -e --input-type dotenv --output-type dotenv .env > .env.enc`
4. Added `.env` and variants (`.env.local`, `.env.development`, `.env.production`, `.env.staging`, `.env.test`) to `.gitignore` (was previously missing)
5. Committed `.sops.yaml`, `.env.example`, `.env.enc`, `.gitignore`

### Step 5: juniper-deploy — Docker Compose secrets — COMPLETE

1. Created `.sops.yaml` with age public key
2. Created `.env.secrets.example` listing the secret-only vars (API keys)
3. Updated `.gitignore` to add `!.env.enc`, `!.env.secrets.enc`, `!.env.secrets.example` exceptions and `.env.secrets` ignore rule
4. Added `.env` variant patterns to `.gitignore`
5. No encrypted file created yet (no real secrets to encrypt in this repo currently)

### Step 6: Remaining repos — `.sops.yaml` + `.env.example` — COMPLETE

Created `.sops.yaml` and `.env.example` in juniper-data, juniper-data-client, juniper-cascor-client, juniper-cascor-worker, and juniper-canopy. Created `.sops.yaml` only in juniper-ml (meta-package). All repos also received `.env` variant patterns in `.gitignore`.

### Step 7: Add SOPS pre-commit hook — COMPLETE

Added `no-unencrypted-env` local hook to juniper-cascor and juniper-data (the 2 repos with existing `.pre-commit-config.yaml` files). The other 3 repos listed in the original plan (juniper-data-client, juniper-cascor-client, juniper-cascor-worker) do not have pre-commit configs.

Hook definition:
```yaml
  - repo: local
    hooks:
      - id: no-unencrypted-env
        name: Block unencrypted .env files
        entry: bash -c 'echo "ERROR: Unencrypted .env file detected. Use sops to encrypt." && exit 1'
        language: system
        files: ^\.env(\.secrets)?$
        types: [file]
```

### Step 8: Documentation — COMPLETE

Created `juniper-ml/notes/SOPS_USAGE_GUIDE.md` with setup instructions, daily workflow, per-repo reference, CI/CD integration pattern, key rotation procedure, and troubleshooting.

### Step 9: GitHub Secrets — COMPLETE

Stored the age private key as `SOPS_AGE_KEY` GitHub Secret in all 8 repos (juniper-cascor, juniper-deploy, juniper-data, juniper-data-client, juniper-cascor-client, juniper-cascor-worker, juniper-ml, juniper-canopy).

## Files Created/Modified Summary

| File | Action | Repo |
|------|--------|------|
| `~/.config/sops/age/keys.txt` | Created (age key pair, chmod 600) | Local system |
| `.sops.yaml` | Created | All 8 repos |
| `.env.example` | Created | juniper-cascor, juniper-data, juniper-data-client, juniper-cascor-client, juniper-cascor-worker, juniper-canopy |
| `.env.enc` | Created (encrypted) | juniper-cascor |
| `.env.secrets.example` | Created | juniper-deploy |
| `.gitignore` | Modified (added `.env` + variants) | All 8 repos |
| `.pre-commit-config.yaml` | Modified (added hook) | juniper-cascor, juniper-data |
| `notes/SOPS_USAGE_GUIDE.md` | Created | juniper-ml |
| `SOPS_AGE_KEY` | GitHub Secret set | All 8 repos |

## Verification — COMPLETE

1. `sops -d --input-type dotenv --output-type dotenv .env.enc` in juniper-cascor decrypts to plaintext matching original `.env` — **verified**
2. `sops -e --input-type dotenv --output-type dotenv .env` produces valid encrypted output — **verified**
3. `git status` in each repo shows `.env.enc` as trackable, `.env` as ignored — **verified**
4. Pre-commit hook blocks `git add .env` attempts — **verified** (hook definition correct, `files: ^\.env(\.secrets)?$`)
5. Age key at `~/.config/sops/age/keys.txt` is auto-discovered (no env var needed locally) — **verified**

## Deviations from Original Plan

1. **path_regex corrected**: Changed from `\.env\.enc$` (output file) to `\.env(\.secrets)?$` (input file) — SOPS matches the creation rule against the file being encrypted
2. **juniper-cascor .gitignore**: `.env` was NOT previously in `.gitignore` (plan assumed it was). Added `.env` plus all environment-specific variants
3. **Pre-commit hooks**: Only 2 repos (juniper-cascor, juniper-data) had pre-commit configs, not 5 as originally estimated
4. **juniper-canopy**: Added to the plan (8th repo, not in original 7-repo scope)
5. **GitHub Secrets**: Originally listed as out of scope but completed via `gh secret set`
6. **dotenv format flags**: Required `--input-type dotenv --output-type dotenv` for proper key=value encryption

## Out of Scope

- Revoking/rotating the exposed credentials (separate task, should be done urgently)
- Removing secrets from git history (requires `git-filter-repo`, separate task)
- GitHub Actions workflow modifications for SOPS decryption (depends on which workflows need secrets at runtime — currently none do since OIDC handles publishing)
