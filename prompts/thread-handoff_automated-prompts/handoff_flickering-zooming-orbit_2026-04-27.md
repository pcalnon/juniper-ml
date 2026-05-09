# Implementation Roadmap

The previous session's working directory (/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/flickering-zooming-orbit) was removed.
The shell couldn't resolve its CWD, so every Bash call errored before reaching the command.

Claude Code has been restarted from an existing directory and needs to resume with this checkpoint:

Resume goal: Continue Track 5 — start CI-03 + 5C in juniper-deploy.

State at restart:

- juniper-deploy#34 (Track 5A) — MERGED
- juniper-cascor-client#27 (Track 5B partial: CI-04/05) — MERGED
- Two worktrees from this session need removal:
  - worktrees/juniper-deploy--infra--track-5a-deploy-01-02-03--20260427-0503--783713f6 + branch infra/track-5a-deploy-01-02-03
  - worktrees/juniper-cascor-client--ci--track-5b-ci-01-04-05--20260427-0511--74c08a68 + branch ci/track-5b-ci-01-04-05

Cleanup recipe per repo:

```bash
cd /home/pcalnon/Development/python/Juniper/<repo>
git fetch origin
git checkout main
git pull origin main
git worktree remove <worktree path>
git branch -D <branch name>
git worktree prune
```

Then resume the new work:

1. Create new worktree in juniper-deploy on a branch like infra/track-5b-5c-ci-03-deploy-05-16.
2. Read CI-03 + DEPLOY-05..DEPLOY-16 details from juniper-ml/notes/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V7_IMPLEMENTATION_ROADMAP.md.
3. Decide bundling — 13 items may want a split into "CI-03 + critical deploy fixes" vs "deploy hardening batch".
4. Implement, test (docker compose config, pytest, pre-commit), commit, push, open PR.
