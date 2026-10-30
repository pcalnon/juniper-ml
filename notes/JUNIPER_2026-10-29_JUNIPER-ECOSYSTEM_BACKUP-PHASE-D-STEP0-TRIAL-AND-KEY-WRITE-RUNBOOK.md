# Phase D runbook: step 0's confinement trial, Procedure A's key write, and A0's command lines

**Author**: Paul Calnon (drafted by Claude Code, session `backup-ac11-passed-transcript-count-zero-then-phase-d`)
**Date**: 2026-10-29
**Status**: validated in four rounds (seven lanes). §3 records the owner's rulings of 2026-10-30 and the departures not
yet put to the owner, which the sitting asks about before step 0. To be run by the owner in Phase D's sitting.
**Related**: `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-29_backup-ac11-passed-transcript-count-zero-then-phase-d.md`
(juniper-ml#2387); `notes/JUNIPER_2026-10-03_JUNIPER-ECOSYSTEM_BACKUP-SYSTEM-STATE-ASSESSMENT-AND-RECOVERY-PLAN.md` §6.4;
`notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-INFRASTRUCTURE-INTEGRATED-DESIGN.md` §7.3.2 and §8

This is the design the sitting follows for the commands no earlier document gave. Everything else in Phase D is the
assessment's §6.4, with the handoff's deltas. What actually runs is recorded at the end of Phase D, in the assessment's
running record (the handoff's "Continue", item 6), not here.

Rounds 1 to 4 are folded in, and §6 maps each finding to where it landed. Round 1 had three lanes (A re-probe, B
adversarial code, C consequence and omission); round 2 had two (R2-A code delta, R2-B runbook delta); round 3 had one,
on round 2's delta (R3); round 4 had one, on round 3's delta and the 10-30 handoff to the sitting (R4; §6).

Session continuing `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-29_backup-ac11-passed-transcript-count-zero-then-phase-d.md`
("the handoff"; juniper-ml#2387). The phase plan is
`notes/JUNIPER_2026-10-03_JUNIPER-ECOSYSTEM_BACKUP-SYSTEM-STATE-ASSESSMENT-AND-RECOVERY-PLAN.md` ("the assessment"); its §6.4 is
Phase D. The design of record is `notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-INFRASTRUCTURE-INTEGRATED-DESIGN.md` ("D").

Artifacts this design adds or changes (one signed PR, to merge before step 0 is run):

| Path | What |
| --- | --- |
| `util/ad-hoc/2026-10-29_duplicati-trial-override.conf` | NEW. Step 0(b)'s drop-in. |
| `util/ad-hoc/2026-10-29_write_matched_settings_key.py` | NEW, 1.3.1. Procedure A's key write: dry run at step 7, the write at step 9. |
| `tests/test_write_matched_settings_key.py` | NEW, 26 tests; wired into `.github/workflows/ci.yml` and `docs/REFERENCE.md` (`AGENTS.md`'s count 226 to 227). |
| `util/ad-hoc/2026-10-29_write_matched_settings_key_mutation_check.py` | NEW. 34 mutants of the tool, each to be killed by the suite. |
| `util/ad-hoc/2026-10-29_password_init_env_mutation_check.py` | NEW. 5 mutants of the helper's 1.4.0 environment. |
| `util/ad-hoc/2026-10-03_rekey_settings_key.bash` | 1.3.0 to 1.4.0: step 9's VACUUM under `PRAGMA temp_store=MEMORY`. |
| `util/ad-hoc/2026-10-03_password_init_hand_start.bash` | 1.3.0 to 1.4.0: the server runs under the unit's three `Environment=` values and `TMPDIR=<data folder>`. |
| `tests/test_backup_rekey_real_path.py`, `tests/test_duplicati_wrapper_contract.py` | Pins for the two 1.4.0 changes, including the helper's root branch. |

## 0. Shells, checkout and temporary space

- **If a tool, path or flag is not where this document, the handoff, the assessment or D says, stop and report it;
  never substitute one** (the handoff's Continue item 1). Where this document departs from them on purpose (§3), it
  wins, once the owner has ruled on that departure.
- **Root shell** for every command below except where it says "pcalnon shell". In it, `~` is `/root`; write `~pcalnon`.
  **Never type `sudo` inside the root shell**: `sudo` resets the environment, which drops the `TMPDIR` set below.
- **Checkout**: the primary, `~pcalnon/Development/python/Juniper/juniper-ml`, at `origin/main` **including this design's PR**.
  In the pcalnon shell: `git -C ~/Development/python/Juniper/juniper-ml pull --ff-only`, then
  `git -C ~/Development/python/Juniper/juniper-ml log -1 --format='%h %s'` (the design PR's merge). Never run git as root
  in pcalnon's checkout. The root shell then works from `cd ~pcalnon/Development/python/Juniper/juniper-ml`.
- **Temp space** (the handoff's Key context): root's tools use `/root/phase-d-tmp` (0700 root), which the real unit masks
  (`InaccessiblePaths=-/root`). The root shell exports `TMPDIR=/root/phase-d-tmp` as soon as the directory exists (§1.2),
  so the installer's `mktemp -d` and A0's `duplicati-cli` put their files there. **Before step 9's installer and before
  A0's scripts**, run `test "$TMPDIR" = /root/phase-d-tmp && echo "TMPDIR ok"`: a reopened root shell has lost the export.
  Anything run as `duplicati` uses `/home/duplicati/phase-d-tmp` (0700 duplicati), which the unit can read, so **no
  cleartext key material goes there**, and A0's restore goes under `/root/phase-d-tmp` (§2.4). Nothing under `/tmp`,
  `/var/tmp` or `/home/pcalnon`.
- **Pasting back**: counts, `stat` lines, exit codes and the tools' own summary lines. Never a raw journal from a server
  start. Never the text of a `query error` line or of a wrapper `FATAL:` line beyond its first clause; say that it
  appeared.
- **Step 0 never creates, reads or touches `/etc/credstore/duplicati-settings-key`.**
- **The no-reboot window is already open** (the assessment's §6.3.1 finding 17, widened 2026-10-29). There is no reboot
  from now until step 10's start has been checked, and on Procedure A until step 12's re-key is done. Step 0 changes
  nothing about that.

## 1. Step 0: the rehearsal on a throwaway folder (the assessment's §6.4 step 0)

The handoff's Remaining §1 "Step 0" sets three things:

- the target: step 0(a)'s scratch folder and throwaway key, never the freeze;
- the location: the data folder goes under `/home/duplicati`, because the unit masks `/root`;
- the six overrides.

What follows is the command list. D's O-2 aside in §6.4 step 0 (token minting without `--password`) is moot: the B2 API
clients (ml#2115, ml#2134) log in with the web credential and obtain the single-operation token themselves.

### 1.1 Preconditions (root shell)

```bash
cd ~pcalnon/Development/python/Juniper/juniper-ml
ss -ltn | grep -c ':8398 '            # 0 -- the trial's port
ss -ltn | grep -c ':8399 '            # 0 -- the helper's port (inert on the 102 path, but its gate checks it)
ls -la /etc/credstore                  # the "before" listing, names only: duplicati-settings-key must NOT exist yet
systemctl is-active duplicati.service  # active -- pid 1397393 keeps running through step 0; nothing here touches it
systemctl show duplicati.service -p NeedDaemonReload   # NeedDaemonReload=no (re-read before each daemon-reload)
```

### 1.2 The temporary directories and the throwaway secrets (root shell)

```bash
install -d -m 0700 /root/phase-d-tmp
export TMPDIR=/root/phase-d-tmp
install -d -m 0700 -o duplicati -g duplicati /home/duplicati/phase-d-tmp
install -d -m 0700 -o duplicati -g duplicati /home/duplicati/phase-d-tmp/step0
install -d -m 0700 -o duplicati -g duplicati /home/duplicati/phase-d-tmp/step0/data
test ! -e /etc/credstore/phase-d-trial-key && ( umask 077; openssl rand -base64 48 | tr -d '\n' > /etc/credstore/phase-d-trial-key )
( umask 077; openssl rand -base64 24 | tr -d '\n' > /root/phase-d-tmp/trial-ui-password )
stat -c '%U:%G %a %s %n' /root/phase-d-tmp /home/duplicati/phase-d-tmp /home/duplicati/phase-d-tmp/step0 /home/duplicati/phase-d-tmp/step0/data /etc/credstore/phase-d-trial-key /root/phase-d-tmp/trial-ui-password
#   root:root 700 ... /root/phase-d-tmp
#   duplicati:duplicati 700 ... (three directories)
#   root:root 600 64 /etc/credstore/phase-d-trial-key
#   root:root 600 32 /root/phase-d-tmp/trial-ui-password
```

Both secrets are random, never typed and never printed. Exposing either would not matter: they guard only a scratch
database that §1.5 shreds. The key sits under `/etc/credstore`, which the unit masks, so the trial's credential count
confirms D §7.3.2's claim that the mask does not break `LoadCredential=`. Lane A re-derived it from systemd's source:
`exec_setup_credentials` runs before the unit's mount namespace exists.

### 1.3 Step 0(a): the password-init helper (root shell)

```bash
bash util/ad-hoc/2026-10-03_password_init_hand_start.bash --data-folder /home/duplicati/phase-d-tmp/step0/data --settings-key-file /etc/credstore/phase-d-trial-key --ui-password-file /root/phase-d-tmp/trial-ui-password --port 8399 --dry-run
#   "dry run: gates passed; ..." and the command it would run, starting "env DO_NOT_TRACK=1 ..."
bash util/ad-hoc/2026-10-03_password_init_hand_start.bash --data-folder /home/duplicati/phase-d-tmp/step0/data --settings-key-file /etc/credstore/phase-d-trial-key --ui-password-file /root/phase-d-tmp/trial-ui-password --port 8399; echo "helper exit=$?"
#   "exit 102: UI password set. ..." then "parameters file shredded" and helper exit=0
```

On 103, 200 or anything else, stop: paste the helper's own line. The helper is 1.4.0. Its server runs under
`env DO_NOT_TRACK=1 USAGEREPORTER_Duplicati_LEVEL=none AUTOUPDATER_Duplicati_SKIP_UPDATE=1 TMPDIR=<data folder>`, because:

- `sudo -u` drops the unit's three `Environment=` lines;
- the server starts its usage reporter before the 102 return (`Program.cs` 284, then 286), with no `IPAddressDeny=` behind it;
- the .NET runtime's diagnostic socket goes to `$TMPDIR`, else to `/tmp`.

Check it on a copy taken with its `-wal`/`-shm` (the 102 run does not close its connection):

```bash
install -d -m 0700 /root/phase-d-tmp/step0-copy
cp -p /home/duplicati/phase-d-tmp/step0/data/Duplicati-server.sqlite* /root/phase-d-tmp/step0-copy/
sqlite3 /root/phase-d-tmp/step0-copy/Duplicati-server.sqlite "SELECT Name, Value FROM Option WHERE BackupID = -2 AND Name IN ('autogenerated-passphrase', 'encrypted-fields');"
#   autogenerated-passphrase|False       (encrypted-fields absent, or False: only the unit's first start sets it)
sqlite3 /root/phase-d-tmp/step0-copy/Duplicati-server.sqlite "SELECT count(*) FROM Option WHERE BackupID = -2 AND Name = 'pbkdf-config' AND Value LIKE 'enc-v1:%';"
#   1
find /root/phase-d-tmp/step0-copy -type f -exec shred -u {} +
rmdir /root/phase-d-tmp/step0-copy
```

The session then lists `find /tmp -maxdepth 1 -user duplicati` (read-only). It expects only the live server's own
`dotnet-diagnostic-1397393-…-socket`, which was there before step 0.

### 1.4 Step 0(b): the confinement trial (root shell)

**Design.** The trial unit is `util/systemd/duplicati.service` copied **byte for byte** to
`/run/systemd/system/duplicati-trial.service`, plus one drop-in, `util/ad-hoc/2026-10-29_duplicati-trial-override.conf`.

The drop-in resets and re-sets four directives:

- `ExecStart=`;
- `EnvironmentFile=`;
- `LoadCredential=`;
- `SystemCallErrorNumber=`, empty, which means kill.

The copied defaults file it names carries the port and the data folder, which makes the handoff's six. It adds four
settings, none a confinement directive:

- `Restart=no`;
- `Environment=DUPLICATI_ENV_FILE=` (the contract copy);
- console logging at `Warning`, through the `DUPLICATI__LOG_CONSOLE` and `DUPLICATI__LOG_LEVEL` environment options;
- a cosmetic `Description=`.

`ExecStart=` also plants one unknown option, `--phase-d-trial-unknown-option-marker`, as console logging's positive
control. So the trial runs every confinement directive step 9 installs, parsed by the same unit-file parser, with
production's `DAEMON_OPTS` words except the port and the folder, plus the marker. This departs from the documents'
"`systemd-run`" (§3).

**Where the trial's files live.** The three files the trial executes or reads as configuration (the wrapper, the
defaults copy and the env-contract copy) go in `/usr/local/lib/duplicati-trial/`, root-owned 0755. They do not go in the
duplicati-owned scratch folder, because a file the `duplicati` uid can replace is a code-injection path into a process
holding `CAP_DAC_READ_SEARCH` (round 2, R2B-7). They do not go under `/run` either: this host mounts `/run` `noexec`,
so a wrapper there would fail every start with `203/EXEC` before any directive is tried (round 3, R3-1). `/` is ext4
without `noexec`, and `ProtectSystem=strict` only makes it read-only. Only the data folder, which the server must own,
stays under `/home/duplicati`.

**Console logging.** 2.4.0.0 writes its own log messages to the console only under `--log-console`. That covers
`Unknown option supplied` and every `Log.Write*` warning or error (`Program.cs` `ConfigureLogging`;
`CommandLineArgumentValidator.cs` logs, never prints). The planted option proves the logging reaches the journal:
exactly one `Unknown option supplied` line, naming it.

```bash
install -d -m 0755 -o root -g root /usr/local/lib/duplicati-trial
install -m 0755 -o root -g root scripts/duplicati-wrapper.bash /usr/local/lib/duplicati-trial/duplicati-wrapper.bash
install -m 0640 -o root -g duplicati util/systemd/duplicati-env.contract /usr/local/lib/duplicati-trial/env
sed -e 's#--webservice-port=8300 #--webservice-port=8398 #' -e 's#--server-datafolder=/home/duplicati/.config/Duplicati #--server-datafolder=/home/duplicati/phase-d-tmp/step0/data #' util/systemd/duplicati.default > /usr/local/lib/duplicati-trial/duplicati.default
chmod 0644 /usr/local/lib/duplicati-trial/duplicati.default
diff util/systemd/duplicati.default /usr/local/lib/duplicati-trial/duplicati.default
#   exactly one changed line, DAEMON_OPTS, differing only in --webservice-port=8398 and
#   --server-datafolder=/home/duplicati/phase-d-tmp/step0/data
install -m 0644 -o root -g root util/systemd/duplicati.service /run/systemd/system/duplicati-trial.service
install -d -m 0755 /run/systemd/system/duplicati-trial.service.d
install -m 0644 -o root -g root util/ad-hoc/2026-10-29_duplicati-trial-override.conf /run/systemd/system/duplicati-trial.service.d/override.conf
cmp scripts/duplicati-wrapper.bash /usr/local/lib/duplicati-trial/duplicati-wrapper.bash && cmp util/systemd/duplicati-env.contract /usr/local/lib/duplicati-trial/env && cmp util/systemd/duplicati.service /run/systemd/system/duplicati-trial.service && cmp util/ad-hoc/2026-10-29_duplicati-trial-override.conf /run/systemd/system/duplicati-trial.service.d/override.conf && echo "trial files: SAME as the repository"
systemctl show duplicati.service -p NeedDaemonReload       # NeedDaemonReload=no -- otherwise stop and say so
systemctl daemon-reload
```

**Gate before the start (the session, read-only):**

```bash
systemctl show duplicati-trial.service -p LoadState -p FragmentPath -p DropInPaths -p ExecStart -p EnvironmentFiles -p SystemCallErrorNumber -p Restart -p User -p UMask --no-pager
#   LoadState=loaded; FragmentPath=/run/systemd/system/duplicati-trial.service;
#   DropInPaths=/run/systemd/system/duplicati-trial.service.d/override.conf;
#   ExecStart path=/usr/local/lib/duplicati-trial/duplicati-wrapper.bash (one entry, argv ... $DAEMON_OPTS --phase-d-trial-unknown-option-marker);
#   EnvironmentFiles=/usr/local/lib/duplicati-trial/duplicati.default (ignore_errors=no) -- one entry;
#   SystemCallErrorNumber=2147483646 (kill); Restart=no; User=duplicati; UMask=0027
systemctl show duplicati-trial.service -p Environment --no-pager
#   the unit's own configured Environment= values (repository text, no secret): AUTOUPDATER_Duplicati_SKIP_UPDATE=1,
#   USAGEREPORTER_Duplicati_LEVEL=none, DO_NOT_TRACK=1, DUPLICATI_ENV_FILE=/usr/local/lib/duplicati-trial/env,
#   DUPLICATI__LOG_CONSOLE=true, DUPLICATI__LOG_LEVEL=Warning
busctl get-property org.freedesktop.systemd1 /org/freedesktop/systemd1/unit/duplicati_2dtrial_2eservice org.freedesktop.systemd1.Service LoadCredential
#   a(ss) 1 "settings-key" "/etc/credstore/phase-d-trial-key"
#   (systemctl show prints LoadCredential as [unprintable]; busctl reads it unprivileged, measured 2026-10-29)
findmnt -no TARGET,OPTIONS -T /usr/local/lib/duplicati-trial
#   / with rw,relatime and no noexec (the wrapper must be executable there)
ls -la /home/duplicati/.config/Duplicati/preload.json /usr/lib/duplicati/preload.json 2>&1
#   both "No such file or directory": the server reads a preload.json from the default data folder (world-writable
#   until step 6) and from its install directory (PreloadSettingsLoader.cs); both were absent on 2026-10-29
systemctl show duplicati.service -p NeedDaemonReload -p MainPID -p ActiveState
#   NeedDaemonReload=no MainPID=1397393 ActiveState=active -- the reload changed nothing for the live unit
systemd-analyze security duplicati-trial.service --no-pager | tail -1
#   an early read of AC-12's exposure figure, not AC-12 itself (lane A: 1.7 offline on this drop-in and unit)
```

If any line differs, do not start; the next action is §1.5's cleanup and a decision.

**The start and the counts (root shell):**

```bash
T0="$(date '+%Y-%m-%d %H:%M:%S')"; echo "T0=$T0"; systemctl start duplicati-trial.service; echo "start exit=$?"
for i in $(seq 1 60); do [ "$(journalctl -u duplicati-trial.service --since "$T0" -o cat --no-pager | grep -c 'Server has started')" -ge 1 ] && break; [ "$(systemctl is-active duplicati-trial.service)" = active ] || break; sleep 2; done; echo "rounds=$i"
sleep 20
systemctl show duplicati-trial.service -p ActiveState -p SubState -p Result -p ExecMainCode -p ExecMainStatus -p NRestarts --no-pager
#   ActiveState=active SubState=running Result=success ExecMainCode=0 ExecMainStatus=0 NRestarts=0
ss -ltn | grep -c ':8398 '                                        # 2 -- 127.0.0.1 and [::1] (loopback binds both, as 8300 does)
J() { journalctl -u duplicati-trial.service --since "$T0" -o cat --no-pager; }
J | grep -c 'Server has started'                                  # 1
J | grep -c 'systemd credential settings-key (64 chars)'          # 1 -- the key came through the masked /etc/credstore
J | grep -c 'Unknown option supplied'                             # 1 -- the planted marker, and nothing else (AC-14)
J | grep 'Unknown option supplied' | grep -c 'phase-d-trial-unknown-option-marker'    # 1 -- that one line is the marker
J | grep -c 'signin.html'                                         # 0 -- the password is set, so no sign-in URL
J | grep -c -e 'No database encryption key was found' -e 'but no key was specified' -e 'encryption key is blacklisted' -e 'Database encryption key is required'    # 0
J | grep -v 'phase-d-trial-unknown-option-marker' | grep -c -i -e 'exception' -e 'error'    # 0 expected; if not, the owner reads those lines and says what they are, no values
journalctl -k --since "$T0" --no-pager | grep 'type=1326' | grep 'sig=31' | grep -c " uid=$(id -u duplicati) "    # 0 -- no seccomp KILL of a duplicati process
```

The four encryption strings are 2.4.0.0's own (`Duplicati/Library/RestAPI/Strings.cs`): `NoEncryptionKeySpecified`,
`EncryptionKeyMissing`, `BlacklistedEncryptionKey` and `DatabaseEncryptionKeyRequired`, from the
`v2.4.0.0_stable_2026-09-03` tag. The same count settles step 10's "no encryption warning", which the assessment's §6.4
step 10 leaves without a string.

The `uid=` filter keeps another process's seccomp kill on this host from reading as the trial's. This boot already
holds snap ERRNO records (`sig=0`), which the `sig=31` filter excludes.

**A PASS means the server starts, listens and idles under the set.** It is not AC-12. The trial runs no request and no
backup. A silent `ENOENT` under `ProcSubset=pid` or an `EAFNOSUPPORT` for AF_NETLINK under `RestrictAddressFamilies=` (D
§7.3.2 names both) shows only if the server throws. AC-12's full backup at step 14 is the real test. On a pass, the real
unit keeps `SystemCallErrorNumber=EPERM`, and the record states that switch, as D §7.3.2 asks.

**Then rehearse step 13's gate on a copy** (the trial's first start encrypted the scratch database under the throwaway key):

```bash
time systemctl stop duplicati-trial.service                      # how long a stop takes (steps 10 and 12 stop and start)
systemctl show duplicati-trial.service -p ActiveState -p Result --no-pager
install -d -m 0700 /root/phase-d-tmp/step0-gate
cp -p /home/duplicati/phase-d-tmp/step0/data/Duplicati-server.sqlite* /root/phase-d-tmp/step0-gate/
python3 util/ad-hoc/2026-10-03_rekey_gate.py /root/phase-d-tmp/step0-gate/Duplicati-server.sqlite /etc/credstore/phase-d-trial-key; echo "gate exit=$?"
#   counts, then gate exit=0 (encrypted-fields True, every enc-v1 blob under the trial key)
```

A non-zero gate exit is not a confinement finding, but stop and report it: step 13 runs the same gate on the real database.

**Reading a failure.** The first matching row wins, so a SIGSYS in any duplicati process outranks the symptom it caused.
Before any re-run, run `systemctl reset-failed duplicati-trial.service`: the copied unit carries `StartLimitBurst=5`.

| What `systemctl show`, the counts and the files say | What it is | Next |
| --- | --- | --- |
| the `sig=31` count with the `uid=` filter is ≥ 1, or `ExecMainStatus=31` (`ExecMainCode` 2, or 3 if a core was dumped) | a system call `@system-service` blocks, in the server or in a tool the wrapper runs (a SIGSYS-killed `mountpoint` surfaces as a false wrapper FATAL) | Paste `journalctl -k --since "$T0" --no-pager \| grep 'type=1326' \| grep 'sig=31' \| grep " uid=$(id -u duplicati) " \| grep -o 'exe="[^"]*" sig=31 arch=[0-9a-f]* syscall=[0-9]*' \| sort \| uniq -c`. **Pause Phase D at step 0.** |
| `ExecMainStatus=243` (CREDENTIALS) with `/etc/credstore/phase-d-trial-key` present (§1.2's `stat`) | a credential-setup failure (the credentials filesystem or workspace). It is not the `/etc/credstore` mask: systemd reads the credential before the namespace exists (lane R2-B, `exec-credential.c`) | Paste only the errno after the last colon of the `Failed to set up credentials:` line. **Pause Phase D at step 0**: step 10's real start would fail the same way. |
| `ExecMainStatus=226` (NAMESPACE) | a namespace directive: every path the unit's namespace names exists or carries `-` | Confirm `ls -ld /home/duplicati /mnt/Backups/Ubuntu/Dropbox/Backups/Yamaguchi`. **Pause Phase D at step 0.** |
| `ExecMainStatus=203` (EXEC) | harness: the wrapper copy, or a `noexec` mount under it | `ls -la /usr/local/lib/duplicati-trial/`, re-run the `cmp`, and `findmnt -no OPTIONS -T /usr/local/lib/duplicati-trial`; fix, `reset-failed`, re-run. |
| `start exit` ≠ 0 with nothing started, or a dependency failed | harness: `RequiresMountsFor=` or a unit dependency | `systemctl status duplicati-trial.service --no-pager \| head -5` names it. Fix, `reset-failed`, re-run. |
| `ExecMainStatus=78` | the wrapper refused | Paste the wrapper's `FATAL:` line's first clause; it names an option or a path, never a value. A copy problem is harness: fix and re-run. Anything else, decide together. |
| exit 100 with "address already in use" | harness: the port | Re-check `ss -ltn`; pick another port in the `sed`, and re-run from the install lines. |
| the marker count is not exactly 1 | console logging did not reach the journal, so the AC-14 and error counts are void | Decide together; it is not by itself a directive finding. |
| no SIGSYS and no `Server has started` (an exception), or counts off after a start (`Unknown option supplied` above 1, `signin.html` above 0, the credential line 0, a non-zero error count, a death in the `sleep 20`) | possibly a directive (`ProcSubset=pid`, AF_NETLINK), possibly a wrong option word | The owner reads the lines and says the exception's type and message, or the option name, no values. Decide together whether a directive is the cause; if so, **pause Phase D at step 0**. |

**"Pause Phase D at step 0" means:**

1. Run §1.5's cleanup now, and stop.
2. The fix changes the repository unit, D §7.3.2's tagged block (so the stage gate), and the record of the AC-12 row's
   "removed **and recorded**". It goes through a validated PR.
3. After that PR merges, pull the checkout and re-run step 0, then step 1. Step 3's stage gate must then read `0 staged`
   against the new `main`.
4. Steps 6 onward, starting with the stop of pid 1397393, wait for that. The no-reboot window is already open (§0) and
   stays open through the pause. Pid 1397393 keeps running meanwhile.

### 1.5 Cleanup, at the end of step 0 (root shell)

```bash
systemctl stop duplicati-trial.service; systemctl reset-failed duplicati-trial.service 2>/dev/null
rm /run/systemd/system/duplicati-trial.service.d/override.conf
rmdir /run/systemd/system/duplicati-trial.service.d
rm /run/systemd/system/duplicati-trial.service
rm /usr/local/lib/duplicati-trial/duplicati-wrapper.bash /usr/local/lib/duplicati-trial/duplicati.default /usr/local/lib/duplicati-trial/env
rmdir /usr/local/lib/duplicati-trial
systemctl show duplicati.service -p NeedDaemonReload       # NeedDaemonReload=no
systemctl daemon-reload
systemctl list-units --all --no-legend 'duplicati-trial*' | wc -l          # 0
shred -u /etc/credstore/phase-d-trial-key /root/phase-d-tmp/trial-ui-password
find /root/phase-d-tmp/step0-gate /home/duplicati/phase-d-tmp/step0 -type f -exec shred -u {} + 2>/dev/null
rm -r /root/phase-d-tmp/step0-gate /home/duplicati/phase-d-tmp/step0 2>/dev/null
ls -la /etc/credstore /root/phase-d-tmp /home/duplicati/phase-d-tmp   # /etc/credstore as in 1.1; both temp dirs empty
```

The session then checks, read-only, that systemd removed the trial's private temporary directories at the stop:
`ls -d /tmp/systemd-private-*duplicati-trial* /var/tmp/systemd-private-*duplicati-trial* 2>/dev/null | wc -l` = 0.

`/root/phase-d-tmp` and `/home/duplicati/phase-d-tmp` stay for the later steps. The handoff's Key context shreds them at
the end of Phase D.

## 2. Step 7, Procedure A's key write, and A0's command lines

### 2.1 The probe (step 7; the handoff's Remaining §1 step 7, with two changes)

```bash
ls -la --time-style=full-iso /home/duplicati/.cache/root-data-folder-<date>/
install -d -m 0700 /root/phase-d-tmp/probe
cp -p /home/duplicati/.cache/root-data-folder-<date>/Duplicati-server.sqlite* /root/phase-d-tmp/probe/
ls -la /root/phase-d-tmp/probe/        # the same Duplicati-server.sqlite* names as the freeze (Phase C found no -wal/-shm/-journal)
python3 util/ad-hoc/2026-09-21_duplicati_settings_key_hash_probe.py scripts/duplicati-wrapper.bash ~pcalnon/.config/duplicati-backup/env frozen-copy=/root/phase-d-tmp/probe/Duplicati-server.sqlite < /home/duplicati/.config/Duplicati.empty-2026-09-20/.env
sqlite3 /root/phase-d-tmp/probe/Duplicati-server.sqlite 'SELECT "ID", "Name", "DBPath" FROM "Backup";'
#   the jobs and their index paths (cleartext columns): record which, if any, names OVFDREJHJT.sqlite
#   (the handoff's step-7 item; the assessment's §6.3.1 finding 4)
```

`<date>` is step 5's freeze date. The two changes:

- **The copy takes `Duplicati-server.sqlite*`.** Phase C's listing (the assessment's §6.3.1 Line 5) found no side file,
  so today the glob copies the main file alone. It still copies a `-wal` if one exists, because a main file without its
  WAL can match the wrong key (D's line on the old confirmation probe).
- **The `.env` goes in by redirect, not `cat … |`.** A mistyped path then fails in the shell before the probe runs. A
  mistyped `cat` would instead feed an empty pipe, which loads no `.env` candidate and reads "no match" (the handoff's
  second fake no-match).

The handoff's trust conditions stand, plus two:

1. `candidates loaded:` lists `ENV_ACTIVE_KEY`;
2. there is no `query error` line (if one appears, do not paste its text: it can quote a column);
3. `encrypted blobs=` is at least 1, and equals `content-hash-verified=`;
4. **new**: `distinct-key-hashes=1`;
5. **new**: a "match" counts for Procedure A **only if it names an `ENV_ACTIVE_KEY/<variant>` label**. A match on any
   other candidate (`ENV_C_KEY_n`, `ENV_C_PASSPHRASE*`, `PASSPHRASE*`, `L`) is outside the O-1/O-2 ruling: **stop**, and
   the owner rules. Those candidates were excluded on 09-21 (D §5.4), so such a match is a surprise.

### 2.2 On an `ENV_ACTIVE_KEY` match: decide the route at step 7, before anything is placed (root shell)

```bash
python3 util/ad-hoc/2026-10-29_write_matched_settings_key.py --dry-run --env /home/duplicati/.config/Duplicati.empty-2026-09-20/.env --db /root/phase-d-tmp/probe/Duplicati-server.sqlite --out /etc/credstore/duplicati-settings-key; echo "dry run exit=$?"
#   key-hash match: [the ENV_ACTIVE_KEY labels the probe printed]; the gate's five columns: ... under-another-key=0;
#   deliverable ...; dry run: would write ...; exit 0
python3 util/ad-hoc/2026-10-03_rekey_gate.py --unrewritten /root/phase-d-tmp/probe/Duplicati-server.sqlite; echo "unrewritten exit=$?"
#   "never-rewritten enc-v1 blobs: ..." and exit 0 -- step 12's re-key would refuse on anything else
```

- **Both exit 0: Procedure A.** Steps 8 onward follow it, and the write happens at step 9.
- **The dry run refuses: stop, and the owner rules.** Its refusals are: the form cannot be delivered, a blob under
  another key, a missing column, or "NONE" after the probe matched (the two disagree: check `--env` and `--db` are the
  probe's own paths). A0 is the fallback, but never on the dry run's word alone, and the `.env` is kept. Nothing was
  written.
- **`--unrewritten` exits non-zero.** The re-key will refuse at step 12 until the owner's remedy (the assessment's note
  6a: delete saved connection strings in the UI, or orphaned rows with `sqlite3`). Decide now between that and A0.
- **Read `--unrewritten`'s line even at exit 0.** A column reading `absent` is a table the frozen 09-18 schema lacks,
  or a read failure, since the gate reports any `OperationalError` as absent: say which columns. Step 12's own
  pre-flight runs the same count again on the upgraded database.

### 2.3 Step 9 on Procedure A: the key write (after the installer, before the `.env` is shredded; root shell)

Run `test "$TMPDIR" = /root/phase-d-tmp && echo "TMPDIR ok"` **before step 9's installer** (§0), which runs first. Then:

```bash
python3 util/ad-hoc/2026-10-29_write_matched_settings_key.py --env /home/duplicati/.config/Duplicati.empty-2026-09-20/.env --db /root/phase-d-tmp/probe/Duplicati-server.sqlite --out /etc/credstore/duplicati-settings-key; echo "key write exit=$?"
#   wrote /etc/credstore/duplicati-settings-key: mode 0600, uid 0, gid 0, N bytes; read back ... both match ...; exit 0
test ! -e /etc/credstore/duplicati-settings-key.new && ( umask 077; openssl rand -base64 48 | tr -d '\n' > /etc/credstore/duplicati-settings-key.new )
stat -c '%U:%G %a %s %n' /etc/credstore/duplicati-settings-key /etc/credstore/duplicati-settings-key.new
cmp -s /etc/credstore/duplicati-settings-key /etc/credstore/duplicati-settings-key.new; case $? in 0) echo "SAME -- stop";; 1) echo "different (expected)";; *) echo "cmp failed -- stop";; esac
```

**Trust the tool's last decision line, whatever the exit status after it.** The tool defers SIGINT, SIGTERM, SIGHUP and
SIGQUIT from just before the create until it has decided. So:

- `wrote … both match …` means written and verified;
- `removed …` means nothing is left;
- a run **ended by a signal** (exit status 128 or more) with neither line printed was killed before a decision: by a
  SIGKILL inside the window (the one signal that cannot wait), by a deferred signal that arrived before the window, or
  by a signal the tool does not defer. Any file left is unverified: `ls -la /etc/credstore`, shred any
  `duplicati-settings-key` there, and re-run. A `REFUSED: … already exists` is not this case: that file predates the run, so look at it first.

**On any non-zero exit, run `ls -la /etc/credstore` and say what is there**: a failed removal prints a WARNING and still
exits 1. The `.env` is kept, and nothing further runs until the owner rules.

Then step 9's tail, as the assessment's §6.4 step 9 and the handoff's Remaining §1 step 9 give it:

1. **Escrow the new key** (`…-key.new`, the key the database will be under after step 12's re-key) on the printed sheet,
   in the password manager and on the `sda1` sibling, and verify it by hash (I-40).
2. **After printing the escrow sheet**, run `ls -la /var/spool/cups`. `lpr` keeps its own `d…` copy (the assessment's
   §6.3.1 finding 11). Shred that copy.
3. Confirm `/etc/duplicati/env` has **no key line and no commented assignment** (names only, never values).
4. `shred -u` the moved-aside `.env`.

Step 12's re-key needs both files: it refuses unless `…-key` and `…-key.new` are present, `0600` root, and different.

### 2.4 A0's two command lines (step 7's other branch; the handoff's, with `TMPDIR` and three more variables)

```bash
test "$TMPDIR" = /root/phase-d-tmp && echo "TMPDIR ok"     # before A0's scripts (§0)
env YAMAGUCHI_ENV_FILE=/home/pcalnon/.config/duplicati-backup/env YAMAGUCHI_JOB_DB=/home/duplicati/.cache/root-data-folder-<date>/BMXWPAOGLP.sqlite YAMAGUCHI_WORKDIR=/root/phase-d-tmp/a0-work TMPDIR=/root/phase-d-tmp DO_NOT_TRACK=1 USAGEREPORTER_Duplicati_LEVEL=none AUTOUPDATER_Duplicati_SKIP_UPDATE=1 bash util/ad-hoc/2026-09-22_confirm_a0_premise.bash
env YAMAGUCHI_ENV_FILE=/home/pcalnon/.config/duplicati-backup/env YAMAGUCHI_JOB_DB=/home/duplicati/.cache/root-data-folder-<date>/BMXWPAOGLP.sqlite YAMAGUCHI_WORKDIR=/root/phase-d-tmp/a0-work TMPDIR=/root/phase-d-tmp DO_NOT_TRACK=1 USAGEREPORTER_Duplicati_LEVEL=none AUTOUPDATER_Duplicati_SKIP_UPDATE=1 bash util/ad-hoc/2026-09-22_restore_server_db_from_fileset.bash /root/phase-d-tmp/a0-restore
```

- In the root shell no `sudo` is needed, and none is typed (§0).
- The work directory and the restore directory are under `/root/phase-d-tmp`: ext4 (`/`), outside `/home/pcalnon`, and
  masked from the real unit. The restore is a cleartext database carrying the passphrase.
- The three extra variables are the unit's own. They cost nothing if `duplicati-cli` ignores them. Whether it reads them
  is unverified, so they are passed rather than assumed unneeded.

### 2.5 The re-key's VACUUM (step 12)

`util/ad-hoc/2026-10-03_rekey_settings_key.bash` 1.4.0 runs its step 9 under `PRAGMA temp_store=MEMORY`. Its
`sudo -u duplicati` carries no `TMPDIR`. So SQLite's temporary copy of the database goes to `/var/tmp` once it outgrows
the page cache, about 2 MB (lane B, under strace and inotify). The server database was 240 KiB on 09-21, so today the copy
stays in the cache and the pragma is a guard. This host's SQLite is 3.46.1 through `/usr/bin/python3`, built with
`TEMP_STORE=1`, so the pragma is honoured; lane B measured 0 temporary files in 18 runs with it. The re-key's own copies
already go to `/root/.cache/duplicati-rekey` (root's home on `/`).

## 3. Departures from the documents, for the owner to approve

1. **Step 0(b) is a runtime unit plus a drop-in, not `systemd-run -p …`.** The assessment's §6.4 step 0, D §7.3.2, the
   AC-12 row and D's O-12 all say `systemd-run`.
   - Why:
     - the file is byte-identical to what step 9 installs, so every directive is present and parsed by the unit-file
       parser, with no hand transcription of about forty `-p` assignments;
     - the drop-in is the whole difference, and `cmp` checks it;
     - `busctl` and `systemctl show` verify the effective properties before the start, and `systemd-analyze security`
       reads the loaded unit.
   - Cost:
     - **two** `daemon-reload`s, one before the start and one in the cleanup, while pid 1397393 runs. Each comes after a
       check that `duplicati.service` reads `NeedDaemonReload=no`, and lane A found 0 of 937 loaded units needing a
       reload;
     - two files under `/run/systemd/system` (tmpfs) and three under `/usr/local/lib/duplicati-trial/`, all removed
       by §1.5.
2. **The drop-in's four extra settings, the planted marker, and the trial inputs under `/usr/local/lib/duplicati-trial/`** (§1.4).
   The console logging makes the trial's journal show warnings that production's journal does not (§5).
3. **The throwaway key sits under `/etc/credstore`**, not in the scratch folder, so the trial also confirms the mask claim.
4. **Step 7's probe**: the glob copy, the redirect, the `Backup` listing, and two added trust conditions (§2.1).
5. **The key write's dry run and `rekey_gate.py --unrewritten` move to step 7** (§2.2), so the route is known before
   anything is placed.
6. **The password-init helper 1.4.0** and **A0's command lines** carry the unit's three `Environment=` values and a
   `TMPDIR` (§1.3, §2.4).
7. **The root shell exports `TMPDIR=/root/phase-d-tmp`**, and `sudo` is never typed in it (§0). This replaces the
   handoff's "pass `TMPDIR` inside every root `sudo env`", which assumed `sudo` from the pcalnon shell.
8. **A failed trial pauses Phase D at step 0** (§1.4). The documents carry no such branch. The fix PR, then a re-run of
   step 0, step 1 and step 3's stage gate, all come before step 6.

**Owner rulings, 2026-10-30** (asked by the designing session at 2026-10-29 23:19 CDT, before round 3 reported; answered
2026-10-30 03:18 CDT):

- **The trial's form (item 1):** approved as the question put it: the runtime copy plus one drop-in carrying the
  handoff's six overrides, `Restart=no`, console logging and the planted marker.
- **Items 5 to 8, and item 4's redirect:** approved. These are the five departures the question listed.
- **The no-`/tmp` directive:** `PrivateTmp=yes` is accepted for Phase D and recorded (§4).
- **The sitting** (steps 0 to 14) runs in a fresh thread, from this document and the handoff this design's PR lands.

**Not yet put to the owner** (lane R4, R4-1). The sitting asks about all three before step 0:

- item 2's later parts: the trial's inputs under `/usr/local/lib/duplicati-trial/` (added by round 3, R3-1, after the
  question was written), and the drop-in's `DUPLICATI_ENV_FILE` and `Description=`;
- item 3: the throwaway key under `/etc/credstore`;
- item 4's other parts: the glob copy, the `Backup` listing and the two added trust conditions.

A ruling against one of them changes this document first: a fix PR, then step 0, as for a failed trial (item 8).

**Still open:** AC-14's Phase E ruling (§5).

## 4. Temporary files: the observations for an owner ruling (the 2026-10-26 no-`/tmp` directive)

- **(a) The .NET runtime's diagnostic socket goes to `$TMPDIR`, else `/tmp`.** The live server has
  `/tmp/dotnet-diagnostic-1397393-110564528-socket` open now (2026-10-29). Phase D's own runs no longer add any: the
  hand start's goes into its data folder (helper 1.4.0), and A0's into `/root/phase-d-tmp`.
- **(b) The real unit's `PrivateTmp=yes`, like the trial's, gives the service two systemd-private directories**,
  `/tmp/systemd-private-<boot>-<unit>-*` and its `/var/tmp` twin. `/usr/lib/tmpfiles.d/systemd-tmp.conf` excludes both
  from aging (`x` lines) and clears them at boot (`R!` lines). systemd removes the trial's at its stop (§1.5).
- **Ruled 2026-10-30: (b) is accepted for Phase D and recorded.** The directive's reasons are aging and reboot loss,
  and neither bites a namespace systemd manages.
- **Phase E options:**
  - `PrivateTmp=disconnected` (systemd 259 has it) moves the private directories off `/tmp` and `/var/tmp`; it is a
    blessed-unit change;
  - a `TMPDIR=` line in the env contract (the wrapper's `ENV_EXPORT_ALLOW` admits `TMPDIR`) moves the .NET socket, but
    not the private directories.

## 5. A finding for the record: AC-14 cannot fail on production's journal

- **The gap.** D's AC-14 counts `Unknown option supplied` in `journalctl -u duplicati.service`. 2.4.0.0 sends that line
  only to its log destinations, and the console is one only under `--log-console`, which production's `DAEMON_OPTS` does
  not set (lane A, re-derived from `CommandLineArgumentValidator.cs:64` and `Program.cs` `ConfigureLogging`). So step
  10's count reads 0 whatever the options say.
- **Where it is measured instead.** The trial runs production's option words with console logging on, and the planted
  marker shows the logging reached the journal. So §1.4's count of exactly 1, the marker, is the measurement. Step 10
  keeps its count, but its 0 is not evidence.
- **Owner ruling, Phase E:**
  - add `--log-console --log-level=Warning` to `DAEMON_OPTS` (a blessed change), or
  - re-point AC-14 at the server's own log.
- **Adding `--log-console` needs an AC-8 check first.** Job runs log in non-isolating scopes, so every job warning would
  reach the journal. That includes `SendHttpMessage`'s printed report URL on a failed report, which S-8 calls a bearer
  credential and O-13 expects a warning from on every run (lane R2-B).
- **The same blindness covers `Log.Write*` errors in general**, so a production start's journal shows only console
  writes and ASP.NET's own warnings.

Step 2's AC-8 count uses `grep -c 'Settings Encryption Key:'` **case-sensitively**. After step 0, the journal holds the
trial wrapper's lower-case `settings encryption key: systemd credential …` line, which `-i` would count.

## 6. Rounds 1 to 4: each finding and where it landed

| Lane finding | Where |
| --- | --- |
| A-1 AC-14 blind | drop-in item 9 and the planted marker; §1.4; §5 |
| A-2 `type=1326` unfiltered | §1.4 (`sig=31`, and R2B-5's `uid=`) |
| A-3 `LoadCredential` replaces; `ExecStart=` cited to `systemd.service(5)` | drop-in header |
| A-4 what a PASS means; listener check | §1.4 (R2B-1: the count is 2) |
| A-5 failure-table gaps | §1.4 table |
| A-6 two reloads, `NeedDaemonReload` | §1.1, §1.4, §1.5, §3 item 1 |
| A-7 string member names | §1.4 |
| A-8 the hand start's usage report and `/tmp` socket | helper 1.4.0 (R2A-3's root-branch test); §1.3; §2.4 |
| B-1 the probe copy without side files | §2.1 (glob; on this host none exists) |
| B-2 a decode error quotes the column | tool 1.1.0; §0; §2.1 |
| B-3 the `O_EXCL` mutant | the race test; both mutation checks |
| B-4, R2A-2 interruption after the create | tool 1.2.0 (signals deferred); §2.3 (trust the last decision line) |
| B-5 the VACUUM temp file above ~2 MB | re-key 1.4.0 comments; §2.5 |
| B-6 to B-10, B-13 | tool 1.1.0; §2.3 (`cmp` case) |
| B-11 a non-UTF-8 `.env` | kept strict (the tool refuses where the probe crashes) |
| B-12, C-2 routing | tool message; §2.1 item 5; §2.2; §2.3 |
| C-1, R2B-3 the 243 and 226 rows | §1.4 table (243: a credential-setup failure, not the mask) |
| C-3 step 9's dropped items | §2.3 |
| C-4, R2B-2 next actions; the no-reboot window | §0; §1.4 "pause" |
| C-5 the dry run too late | §2.2 |
| C-6 `/tmp` observations | §4 |
| C-7, R2B-9 `TMPDIR`; the `.pyc`; A0's directory | §0; §2.3; §2.4; tool 1.1.0 |
| C-8 citations; counts; AC-8's case | §1.4; §3; §5 |
| R2A-1 the index held an older tool | re-staged; the PR uploads working-tree files |
| R2A-4, R2A-5, R2A-6 the dry run's refusals; five columns; DQS | tool 1.2.0 (DQS off); tests (all five columns, dry-run variants, a missing column) |
| R2A-7, R2A-8, R2A-9 messages; removal; "no socket" | tool 1.2.0; helper 1.4.0 comments |
| R2B-4 "Duplicate option" is DEBUG-only; no positive control | drop-in; §1.4 (the planted marker; `-p Environment`) |
| R2B-6 rows 3 and 4; 203; `StartLimitBurst` | §1.4 table; `reset-failed` before a re-run |
| R2B-7 duplicati-writable trial inputs; `preload.json` | §1.4 (`/usr/local/lib/duplicati-trial/`; the `preload.json` check) |
| R2B-8 `--log-console` in production | §5 |
| R2B-10 `--unrewritten`'s `absent`; any non-zero exit; the pause; OVFDREJHJT; O-2 | §2.2; §2.3; §3 item 8; §2.1; §1 |
| R3-1 `/run` is `noexec` here | drop-in; §1.4 (`/usr/local/lib/duplicati-trial/`, the `findmnt` check, the 203 row); §1.5; §3 item 1 |
| R3-2 only SIGTERM was tested | the deferral test runs SIGTERM, SIGINT, SIGHUP and SIGQUIT; two mutants |
| R3-3, R3-4, R3-5 the "last line" wording; "neither line"; the `TMPDIR` check's place | tool 1.3.0 docstring; §2.3 |
| R3-6 a SIGQUIT core with the key in memory | tool 1.3.0 (`RLIMIT_CORE` 0); the deferral test's two `(0, 0)` checks (R4-3) |
| R4-1 §3 and the 10-30 handoff (`prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-30_backup-phase-d-design-merged-then-sitting.md`) overstated the rulings: three departures were never put to the owner, and the date was 10-29 | §3 (the rulings as asked and answered, 2026-10-30; the rest pending, asked before step 0); the 10-30 handoff |
| R4-2 the 10-30 handoff dropped the handoff's stop-and-report rule, its snap-mount verify line and its Remaining §2 | the 10-30 handoff; §0 (the rule) |
| R4-3 two probe mutants survived: the block after the create; the core limit after the key is read | the deferral test also signals inside the write (from the first `fsync`) and records the core limit as `active_key` is entered; three mutants added (33) |
| R4-4 the signal test fails under `nohup` or in a background job, which inherit ignored signals | the test's driver restores the four signals' defaults and unblocks them |
| R4-5 "a SIGKILL inside the window" claimed more than "neither line" shows | tool 1.3.1 docstring; §2.3 ("killed before a decision") |
| R4-6 the status, the body and this heading lagged round 3; no round-4 rows | the status line; the body; this table |
| R4-7 the 10-30 handoff's "changed nothing on the host" left out the memory edits and the primary checkout's `tmp/claude-1000/` files | the 10-30 handoff |
| R4-8 bare "§6.4", "§6.7" and "#2387" in the 10-30 handoff | the 10-30 handoff |
| CodeQL `py/catch-base-exception` on the read-back's cleanup (a review thread on juniper-ml#2389, the first design PR): the `except BaseException` re-raised, but the outer handlers let it reach a normal exit | tool 1.3.1 (a flag and a `finally`; every exception still removes the file); one mutant added (34); the design re-landed as one commit in a fresh PR |
