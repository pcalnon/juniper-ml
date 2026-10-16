# Handoff — turing bring-up: the plan has landed, Session 1 is next

**From:** the 2026-10-15/16 planning session on turing (work arc `prompts/manual/prompt133_2026-10-15.md`)
**Plan of record:** `notes/JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md` v1.0.0. It was validated by consensus rounds 1 and 2.

## Done

- **Measured turing's state.** The read-only probe is `util/ad-hoc/2026-10-15_turing_host_state_probe.bash`.
- **Wrote the plan.** It has 12 decisions, 8 arcs, gates and tests. Three reviewers validated it in round 1 and one in round 2; all findings were applied.
- **Added an AGENTS.md hazard.** An unsigned commit makes a branch unmergeable, so turing lands work through `util/open_signed_pr.py`.
- **Saved four session memories** covering the turing profile, the auth root cause, landing via the API, and the no-credential-probes rule.

## Next: Owner block 0, then Session 1 (plan §7)

0. **OWNER C8**, before any agent session. Put the git env (`GIT_CONFIG_COUNT=2`, which turns off commit and tag signing) and the deny list or PreToolUse hook in turing's `~/.claude/settings.json` (plan D11).
1. **AGENT Session 1:**
   - A1: rewrite the juniper-k8s and juniper-recurrence remotes to the alias form.
   - A8: set `AddKeysToAgent no`.
   - C4: `chmod 600` the `.pem` and `~/.ssh/config`.
   - D0: `brew install coreutils`.
   - H0: list the `mcpServers` keys only.
   - B1-install.
   - G2, B7, B8, A4, A5, A7, F5a: each with its test suite **wired into `ci.yml` and `docs/REFERENCE.md` in the same PR**.
   - F3: start sampling.

## Rules

- **Don't commit and push for merge from turing.** Land every change with `python util/open_signed_pr.py … --dry-run` first, then without `--dry-run`.
- **Don't run credential probes from an agent.** That means `ssh -T`, `ssh-add`, `gh auth status`, `gpg --card-status` and `gpg -K`. The owner runs them, and they are listed in plan §14.1.
- **pre-commit on turing:** use `SKIP=gitleaks` until task D6 lands.

## Verify the starting state

```bash
cd ~/Development/python/Juniper/juniper-ml && git fetch origin && git log -1 --oneline origin/main
test -f notes/JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md && echo plan-present
for r in k8s recurrence; do git -C ../juniper-$r remote get-url origin; done   # expect non-alias until A1
command -v timeout || echo "timeout missing (D0 pending)"
```

## Git state at handoff

- The plan PR lands on `main` through `open_signed_pr.py`, on branch `docs/turing-host-bringup-plan`.
- The planning worktree `worktrees/juniper-ml--docs--turing-host-bringup-plan--20261015-2203--6f5de915` can be removed after merge with `util/worktree_cleanup.bash`.
- The pre-existing branch `feat/adding-new-util-scripts-for-keys` (unsigned `651e4793`) is untouched. Plan task B9 re-lands it.
- `prompts/manual/prompt133_2026-10-15.md` is still untracked in the main checkout.
