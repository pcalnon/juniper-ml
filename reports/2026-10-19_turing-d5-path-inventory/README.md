# turing PATH inventory for task D5 (2026-10-19)

Plan: `notes/JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md`, task D5 (§17 records the outcome).

D5 said to drop MacPorts' `/opt/local/bin` from the shell profile, because MacPorts is dead on turing: it was built for darwin 18, and every `port` command errors. The plan assumed that was a no-op cleanup. `2026-10-19_before-demote.txt`, from `util/ad-hoc/2026-10-19_turing_d5_path_inventory.py` run with the pre-D5 PATH, shows it is not:

| What happens to the 327 commands in `/opt/local/{bin,sbin}` if both entries are dropped | Count |
|---|---|
| An earlier PATH entry already wins, so nothing changes | 95 |
| Resolves to a Homebrew (`/usr/local/bin`) or system copy instead | 104 |
| **Exists only in `/opt/local`, so it disappears from PATH** | **128** |

The 128 include `python3.7`, `perl5.28`, `maxima`, `sbcl`, `rlwrap`, `recode`, the texinfo tools and the giflib tools. They also include `gpg2`, `gnupg` and `gnupg2`: the owner's hand-made links into Homebrew's `gnupg` Cellar, which Homebrew does not link into `/usr/local/bin`.

**Owner ruling (2026-10-19): demote, don't remove.** `~/.bash_profile:87` (the MacPorts installer's 2019 line) changed as follows:

- before: `export PATH="${HOME}/.local/bin:/opt/local/bin:/opt/local/sbin:${PATH}"`
- after: `export PATH="${HOME}/.local/bin:${PATH}:/opt/local/bin:/opt/local/sbin"`

A comment above the line records the ruling. The backup is `~/.bash_profile.bak-2026-10-19-pre-D5`.

Verified in a clean login shell (`env -i TERM=xterm-256color /usr/local/bin/bash -l`):

- `/opt/local/bin` and `/opt/local/sbin` are the last two PATH entries;
- `gpg` → `/usr/local/bin/gpg` (Homebrew), `sqlite3` → `/usr/bin/sqlite3`, `xz` → `/usr/local/bin/xz`;
- the MacPorts-only `gpg2` and `rlwrap` still resolve to `/opt/local/bin`.

Running sessions keep their old PATH until a new login shell starts.
