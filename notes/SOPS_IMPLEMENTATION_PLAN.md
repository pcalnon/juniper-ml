# Plan: Implement SOPS with age Encryption Across the Juniper Ecosystem

**Date**: 2026-02-26
**Status**: Approved, pending execution
**Prerequisite**: `juniper-ml/notes/SECRETS_MANAGEMENT_ANALYSIS.md`

---

## Context

The Juniper ecosystem has no encrypted secrets management. The primary risk is `juniper-cascor/.env` containing 15 real API keys/tokens in plaintext on disk. While `.env` is in `.gitignore` across all repos, there is no mechanism to safely store, share, or version secrets. This plan implements SOPS with `age` encryption as recommended in `juniper-ml/notes/SECRETS_MANAGEMENT_ANALYSIS.md`.

## Approach

Single `age` key pair shared across all Juniper repos. The private key lives at the SOPS default location (`~/.config/sops/age/keys.txt`) and will be stored as a GitHub Secret (`SOPS_AGE_KEY`) for CI/CD decryption. Each repo gets a `.sops.yaml` config pointing to the same `age` public key.

## Implementation Steps

### Step 1: Install SOPS and age

Install both CLI tools via system package manager or direct download.

```bash
# age
sudo apt install age  # or: brew install age

# sops
# Download latest from https://github.com/getsops/sops/releases
```

### Step 2: Generate age key pair

```bash
mkdir -p ~/.config/sops/age
age-keygen -o ~/.config/sops/age/keys.txt
# Output will show the public key (age1...)
```

Save the public key for `.sops.yaml` files. The private key at `~/.config/sops/age/keys.txt` is auto-discovered by SOPS.

### Step 3: Create `.sops.yaml` in each repo

**Repos to configure** (all 7 active repos):

Each repo gets a `.sops.yaml` at its root:

```yaml
creation_rules:
  - path_regex: \.env\.enc$
    age: "age1<PUBLIC_KEY_HERE>"
```

This tells SOPS to use the `age` public key when encrypting any file matching `*.env.enc`.

**Files to create/modify per repo:**

| Repo | `.sops.yaml` | `.env.example` | `.env.enc` | `.gitignore` update |
|------|-------------|---------------|-----------|-------------------|
| juniper-cascor | Create | Create (from existing .env keys) | Encrypt existing .env | No change needed (`.env` already ignored; `.env.enc` is not matched) |
| juniper-deploy | Create | Already exists | Create (for secret vars) | Add `!.env.enc` exception |
| juniper-data | Create | Create | No (no secrets currently) | No change needed |
| juniper-data-client | Create | Create | No | No change needed |
| juniper-cascor-client | Create | Create | No | No change needed |
| juniper-cascor-worker | Create | Create | No | No change needed |
| juniper-ml | Create | No (meta-package, no app secrets) | No | No change needed |

### Step 4: juniper-cascor — Primary target

1. Create `.sops.yaml` with age public key
2. Create `.env.example` with all 15 variable names (no values):
   ```
   # Third-party API keys
   HF_TOKEN=
   ALPHA_VANTAGE_TOKEN=
   SCOUT_TOKEN=
   EXA_API_KEY=
   KAGGLE_API_TOKEN=
   ANTHROPIC_API_KEY=
   SENTRY_SDK_DSN=

   # PyPI publishing (manual)
   JUNIPER_ML_PYPI=
   JUNIPER_ML_TEST_PYPI=
   JUNIPER_ML_USERNAME=
   JUNIPER_ML_TEST_USERNAME=
   TWINE_PASSWORD=
   TWINE_USERNAME=
   TEST_TWINE_PASSWORD=
   TEST_TWINE_USERNAME=
   ```
3. Encrypt `.env` → `.env.enc`: `sops -e .env > .env.enc`
4. Commit `.sops.yaml`, `.env.example`, `.env.enc`

### Step 5: juniper-deploy — Docker Compose secrets

1. Create `.sops.yaml` with age public key
2. Create `.env.secrets.example` listing the secret-only vars (API keys):
   ```
   # API Security — copy to .env.secrets, fill in, then encrypt:
   #   sops -e .env.secrets > .env.secrets.enc
   JUNIPER_DATA_API_KEYS=
   JUNIPER_CASCOR_API_KEYS=
   CANOPY_API_KEY=
   ```
3. Update `.gitignore` to add `!.env.enc` and `!.env.secrets.enc` exceptions
4. No encrypted file created yet (no real secrets to encrypt in this repo currently)

### Step 6: Remaining repos — `.sops.yaml` + `.env.example`

For juniper-data, juniper-data-client, juniper-cascor-client, juniper-cascor-worker:
- Create `.sops.yaml` (future-proofing)
- Create `.env.example` with documented env vars from their settings/config

For juniper-ml:
- Create `.sops.yaml` only (meta-package, no app env vars)

### Step 7: Add SOPS pre-commit hook to repos with `.pre-commit-config.yaml`

Add a local hook that prevents committing unencrypted `.env` files:

```yaml
  - repo: local
    hooks:
      - id: no-unencrypted-env
        name: Block unencrypted .env files
        entry: bash -c 'echo "ERROR: Unencrypted .env file detected. Use sops to encrypt." && exit 1'
        language: system
        files: ^\.env$
        types: [file]
```

**Repos with pre-commit configs**: juniper-cascor, juniper-data, juniper-data-client, juniper-cascor-client, juniper-cascor-worker (5 repos). juniper-ml and juniper-deploy do not have pre-commit configs.

### Step 8: Documentation

Create `Juniper/juniper-ml/notes/SOPS_USAGE_GUIDE.md` with:
- Setup instructions (install SOPS + age, get private key)
- Daily workflow (decrypt, edit, re-encrypt)
- CI/CD integration pattern
- Key rotation procedure
- Troubleshooting

## Files Created/Modified Summary

| File | Action | Repo |
|------|--------|------|
| `~/.config/sops/age/keys.txt` | Create (age key pair) | Local system |
| `.sops.yaml` | Create | All 7 repos |
| `.env.example` | Create | juniper-cascor, juniper-data, juniper-data-client, juniper-cascor-client, juniper-cascor-worker |
| `.env.enc` | Create (encrypted) | juniper-cascor |
| `.env.secrets.example` | Create | juniper-deploy |
| `.gitignore` | Modify (add exceptions) | juniper-deploy |
| `.pre-commit-config.yaml` | Modify (add hook) | juniper-cascor, juniper-data, juniper-data-client, juniper-cascor-client, juniper-cascor-worker |
| `notes/SOPS_USAGE_GUIDE.md` | Create | juniper-ml |

## Verification

1. `sops -d .env.enc` in juniper-cascor should decrypt to plaintext matching original `.env`
2. `sops -e .env` should produce valid encrypted output
3. `git status` in each repo should show `.env.enc` as trackable, `.env` as ignored
4. Pre-commit hook should block `git add .env` attempts
5. Age key at `~/.config/sops/age/keys.txt` is auto-discovered (no env var needed locally)

## Out of Scope

- Revoking/rotating the exposed credentials (separate task, should be done urgently)
- Removing secrets from git history (requires `git-filter-repo`, separate task)
- GitHub Actions workflow modifications for SOPS decryption (depends on which workflows need secrets at runtime -- currently none do since OIDC handles publishing)
- Storing `SOPS_AGE_KEY` in GitHub Secrets (manual step -- documented in usage guide)
