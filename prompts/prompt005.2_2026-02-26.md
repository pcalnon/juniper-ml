# Install and config SOPS

## Execute the SOPS with age encryption implementation plan for the Juniper ecosystem

The full plan is at: juniper-ml/notes/SOPS_IMPLEMENTATION_PLAN.md
The analysis that led to this plan is at: juniper-ml/notes/SECRETS_MANAGEMENT_ANALYSIS.md

## Completed so far

- Researched 10 secrets management solutions and wrote analysis (committed + pushed to origin/main)
- Explored all 7 Juniper repos: audited .env files, .gitignore rules, pre-commit configs, GitHub Actions workflows
- Identified juniper-cascor/.env as the primary target (15 real secrets, not git-tracked but on disk)
- Confirmed SOPS and age are NOT yet installed on this system
- Wrote implementation plan to juniper-ml/notes/SOPS_IMPLEMENTATION_PLAN.md (untracked, needs commit)
- User decisions: single encrypted .env per repo, add pre-commit hooks, GitHub Secrets for age key backup

## Remaining work (execute steps 1-8 from the plan)

1. Install SOPS and age CLI tools (sudo apt install age; download sops binary)
2. Generate age key pair at ~/.config/sops/age/keys.txt
3. Create .sops.yaml in all 7 repos with the age public key
4. juniper-cascor: create .env.example, encrypt .env → .env.enc, commit
5. juniper-deploy: create .sops.yaml, .env.secrets.example, update .gitignore
6. Remaining repos: create .sops.yaml + .env.example files
7. Add no-unencrypted-env pre-commit hook to 5 repos (juniper-cascor, juniper-data, juniper-data-client, juniper-cascor-client, juniper-cascor-worker)
8. Write SOPS_USAGE_GUIDE.md documentation in juniper-ml/notes/
9. Commit changes in each repo

## Next Steps

- Perform an audit of the code base and configuration for all repos against the Juniper/juniper-ml/notes/SOPS_IMPLEMENTATION_PLAN.md
  - Also consider the SECRETS_MANAGEMENT_ANALYSIS.md file and the SOPS_USAGE_GUIDE.md
- identify and document any remaining tasks or issues identified during audit
- complete any remaining tasks and remediate any issues identified during audit
- fully implement the SOPS sulution and integrate it with all active juniper repos.
- update all documentation to relfect the status of SOPS install, configuration, implementation, and integration.

## Key context

- All repos are at /home/pcalnon/Development/python/Juniper/\<repo-name>/
- .env is already in .gitignore across all repos; .env.enc will NOT be matched (safe to commit)
- juniper-deploy .gitignore needs !.env.enc and !.env.secrets.enc exceptions added
- Only juniper-cascor has a real .env file with secrets to encrypt
- juniper-ml .env contains only CLAUDE_AUTOCOMPACT_PCT_OVERRIDE (non-secret, ignore it)
- Pre-commit configs exist in 5 repos (not juniper-ml, not juniper-deploy)
- juniper-deploy already has .env.example (non-secret config vars) — don't overwrite it
- Follow Juniper file header conventions for new files
- Worktree procedure: each repo change should be committed on its own branch per the worktree procedure, OR committed directly to main if the change is small (adding config files qualifies)

## Verification

- sops --version && age --version (tools installed)
- sops -d juniper-cascor/.env.enc (decrypts correctly)
- git status in each repo (new files trackable, .env still ignored)

## Git status

on branch main in juniper-ml, notes/SOPS_IMPLEMENTATION_PLAN.md is untracked (commit it first)
Pre-existing untracked/modified files (not related to this task): .claude/, prompts/, notes/MICROSERVICES_ARCHITECTURE_ANALYSIS.md, notes/PYPI_MANUAL_SETUP_STEPS.md

---

## Launch Command

```bash
claude --dangerously-skip-permissions --rename "P5.2: Install and config SOPS"
```

---
