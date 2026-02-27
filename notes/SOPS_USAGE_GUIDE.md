# SOPS Usage Guide — Juniper Ecosystem

**Date**: 2026-02-27
**Prerequisite**: `juniper-ml/notes/SOPS_IMPLEMENTATION_PLAN.md`

---

## Overview

The Juniper ecosystem uses [SOPS](https://github.com/getsops/sops) with [age](https://github.com/FiloSottile/age) encryption to manage secrets. Secrets are stored as encrypted `.env.enc` files that can be safely committed to git. The plaintext `.env` files remain gitignored.

**Encryption**: age (X25519)
**Key location**: `~/.config/sops/age/keys.txt` (auto-discovered by SOPS)
**Config**: `.sops.yaml` in each repo root

---

## Initial Setup (New Developer)

### 1. Install Tools

```bash
# age (via conda, apt, or brew)
conda install -c conda-forge age     # conda
sudo apt install age                  # Debian/Ubuntu
brew install age                      # macOS

# SOPS
# Download from https://github.com/getsops/sops/releases
# Or: brew install sops
```

### 2. Obtain the Private Key

Get the age private key from a team member or from the `SOPS_AGE_KEY` GitHub Secret:

```bash
mkdir -p ~/.config/sops/age
# Paste the private key into this file:
nano ~/.config/sops/age/keys.txt
chmod 600 ~/.config/sops/age/keys.txt
```

The file should look like:
```
# created: 2026-02-26T22:55:34-06:00
# public key: age1qmmfhude4xlpdx3wvqv994ahqayke04sgkt5r3ruclu9wmyt04xsdl2kkv
AGE-SECRET-KEY-1<REDACTED>
```

### 3. Verify

```bash
cd juniper-cascor
sops -d --input-type dotenv --output-type dotenv .env.enc > .env
# Should produce a valid .env file with all secrets in plaintext
```

---

## Daily Workflow

### Decrypt secrets (start of session)

```bash
cd <repo>
sops -d --input-type dotenv --output-type dotenv .env.enc > .env
```

### Edit secrets

Option A — Edit in plaintext, then re-encrypt:
```bash
# Edit .env directly
nano .env

# Re-encrypt
sops -e --input-type dotenv --output-type dotenv .env > .env.enc

# Commit the encrypted file
git add .env.enc && git commit -m "chore: update encrypted secrets"
```

Option B — Edit through SOPS (opens $EDITOR with decrypted content):
```bash
sops --input-type dotenv --output-type dotenv .env.enc
# Saves re-encrypted on exit
git add .env.enc && git commit -m "chore: update encrypted secrets"
```

### Add a new secret

1. Add the variable name to `.env.example` (no value)
2. Add the variable with its value to `.env`
3. Re-encrypt: `sops -e --input-type dotenv --output-type dotenv .env > .env.enc`
4. Commit both `.env.example` and `.env.enc`

---

## Per-Repo Reference

| Repo | Encrypted File | Example File | Has Secrets? |
|------|---------------|-------------|-------------|
| juniper-cascor | `.env.enc` | `.env.example` | Yes (15 keys) |
| juniper-deploy | (none yet) | `.env.secrets.example` | No (future) |
| juniper-data | (none yet) | `.env.example` | No (future) |
| juniper-data-client | (none yet) | `.env.example` | No (future) |
| juniper-cascor-client | (none yet) | `.env.example` | No (future) |
| juniper-cascor-worker | (none yet) | `.env.example` | No (future) |
| juniper-ml | (none) | (none) | No (meta-package) |

When a repo starts needing secrets:
```bash
cp .env.example .env
# Fill in values
sops -e --input-type dotenv --output-type dotenv .env > .env.enc
git add .env.enc
```

---

## CI/CD Integration

### GitHub Actions

Store the full contents of `~/.config/sops/age/keys.txt` as a GitHub repository secret named `SOPS_AGE_KEY`.

```yaml
# In a workflow step:
- name: Decrypt secrets
  env:
    SOPS_AGE_KEY: ${{ secrets.SOPS_AGE_KEY }}
  run: |
    sops -d --input-type dotenv --output-type dotenv .env.enc > .env
```

**Note**: Currently no Juniper workflows need runtime secrets (PyPI publishing uses OIDC trusted publishing). Add this pattern when workflows require API keys.

---

## Key Rotation

### When to Rotate

- Team member leaves the project
- Key is suspected compromised
- Periodic rotation (annual recommended)

### Rotation Procedure

```bash
# 1. Generate a new age key
age-keygen -o /tmp/new-age-key.txt

# 2. Note the new public key from the output

# 3. Update .sops.yaml in ALL 7 repos with the new public key

# 4. Re-encrypt each .env.enc with the new key
#    For each repo that has a .env.enc:
sops -d --input-type dotenv --output-type dotenv .env.enc > .env
#    (update .sops.yaml with new public key first)
sops -e --input-type dotenv --output-type dotenv .env > .env.enc

# 5. Replace the old key file
mv /tmp/new-age-key.txt ~/.config/sops/age/keys.txt
chmod 600 ~/.config/sops/age/keys.txt

# 6. Update SOPS_AGE_KEY GitHub Secret with new private key

# 7. Commit updated .sops.yaml and .env.enc in all affected repos
```

---

## Troubleshooting

### "no matching creation rules found"

The `.sops.yaml` `path_regex` doesn't match the file you're encrypting. The regex matches the **input** file path. Use `--input-type dotenv --output-type dotenv` flags and ensure you're encrypting `.env` (not `.env.enc`).

### "failed to decrypt"

- Verify your private key is at `~/.config/sops/age/keys.txt`
- Check file permissions: `chmod 600 ~/.config/sops/age/keys.txt`
- Ensure the key matches the public key in `.sops.yaml`

### "could not find common decryption key"

The `.env.enc` file was encrypted with a different age key than what's in your `keys.txt`. Get the correct private key from a team member.

### Pre-commit hook blocks `git add .env`

This is intentional. The `no-unencrypted-env` hook prevents committing plaintext secrets. Encrypt first: `sops -e --input-type dotenv --output-type dotenv .env > .env.enc`, then commit `.env.enc` instead.

### Blank lines differ after decrypt

SOPS may strip consecutive blank lines from dotenv files. This is cosmetic and does not affect functionality.

---

## Security Notes

- **Never commit** `~/.config/sops/age/keys.txt` or the private key to any repository
- **Never share** the private key over unencrypted channels
- The `.env` file is gitignored but exists on disk in plaintext — treat your workstation as a trusted environment
- `.env.enc` is safe to commit — it contains only AES-256-GCM encrypted values
- The age public key in `.sops.yaml` is not secret (it's the encryption key, not the decryption key)
