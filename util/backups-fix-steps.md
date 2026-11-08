# Backup Restoration

## Step 10

Step 10, part 1: check the existing web-credential file

Step 10 writes ~/.config/duplicati-backup/web-credential with the root-era S-5 password, the one the restored database holds. But that file already exists: 1372 B, 0600, written 10-05, when the watchdog deploy used it. A single DUPLICATI_WEB_CREDENTIAL=… line would be far shorter, so the file holds more than one line, and I won't have you overwrite it blind. The command below lists its line names and lengths only, never values.

In the pcalnon shell:
awk '{ if ($0 ~ /^[[:space:]]*#/) printf "%d: comment (%d chars)\n", NR, length($0);
       else if (index($0,"=")) printf "%d: %s=<elided> (%d chars)\n", NR, substr($0,1,index($0,"=")-1), length($0);
       else printf "%d: no-assignment line (%d chars)\n", NR, length($0) }' ~/.config/duplicati-backup/web-credential

Paste the output. Depending on what it shows, the next block will either:

- keep the file, if it already carries the S-5 value (checked by hash against a hidden prompt), or
- move it aside and write the single line, using the recovery plan's §6.4 step 11 rule about outer quotes (…RECOVERY-PLAN.md).

The --print-command dry run, the start, serverstate (exit 2) and the journal counts come after that.

Two notes on step 10's journal checks

- The Unknown option supplied count (AC-14) can't see anything. The installed defaults don't pass --log-console, so that warning never reaches the journal, and a count of 0 proves nothing. The record will say so, and AC-14 stays with its Phase E ruling.
- For the "no encryption warning" check, I'll count stored unencrypted. That phrase comes from the 09-17 journal line No database encryption key was found. The database will be stored unencrypted., and that line did reach the journal without --log-console. The recovery plan names no string for this check, so object if you want a different one.

The file is 17 comment and blank lines plus one DUPLICATI_WEB_CREDENTIAL= line.
So the only question is whether its value is already the S-5 password the restored database holds.
The block below finds out without showing either value.
It uses the API client's own parser (read_credential() in util/ad-hoc/yamaguchi_server_api.py), so whitespace and the one pair of outer quotes are stripped exactly as the client will strip them.
It then compares that value with the S-5 value you type at a hidden prompt.
Importing the module runs nothing (its main is guarded), and I checked that the file is identical in this worktree and in the main checkout.

pcalnon shell, from the main checkout (~/Development/python/Juniper/juniper-ml):
python3 -I -c '
import getpass, hmac, importlib.util
s = importlib.util.spec_from_file_location("api", "util/ad-hoc/yamaguchi_server_api.py")
m = importlib.util.module_from_spec(s); s.loader.exec_module(m)
cur = m.read_credential()
v = getpass.getpass("S-5 password (hidden): ")
print("credential vs S-5:", "SAME" if hmac.compare_digest(cur.encode(), v.encode()) else "DIFFERENT")
'; echo "exit=$?"

- SAME: the file stays as it is, and step 10's write is already done. I'll send the dry run, the start, serverstate and the journal counts next.
- DIFFERENT: don't change anything yet. Paste the result, and I'll give you an in-place rewrite of line 18 only, which keeps the 10-05 comment header and keeps a copy of the old file.
- A line starting FATAL:: paste only the text before its first --.

Step 10's write is already done: the existing credential file holds the S-5 password. Below is the rest of step 10.

A note on the dry run: run under sudo -u duplicati, there's no systemd credential, so the wrapper will report settings encryption key: NOT SET. That's expected there. The real start gets the key through LoadCredential. The wrapper never prints the key; --print-command hides key options and prints a would exec: line. I checked that the installed wrapper is identical to scripts/duplicati-wrapper.bash.

pcalnon shell, from ~/Development/python/Juniper/juniper-ml:

1. dry run (no start)

sudo -u duplicati /usr/local/lib/duplicati/duplicati-wrapper.bash --print-command 2>&1 | sed -E 's/^(would exec: [^ ]+).*/\1 …(options elided)/'; echo "print-command exit=${PIPESTATUS[0]}"

Stop there if the exit isn't 0. Otherwise:

2. the first start

ts=$(date '+%Y-%m-%d %H:%M:%S'); echo "ts=$ts"
sudo systemctl start duplicati.service; echo "start exit=$?"
for i in $(seq 60); do ss -ltn 'sport = :8300' | grep -q ':8300' && break; sleep 1; done; echo "port 8300 after ${i}s"
systemctl show duplicati.service -p ActiveState -p SubState -p NRestarts -p Result

3. must be Paused (exit 2); if Running (exit 0), stop at once

python3 util/ad-hoc/yamaguchi_server_api.py serverstate; rc=$?; echo "serverstate exit=$rc"
if [ "$rc" -eq 0 ]; then sudo systemctl stop duplicati.service; echo "STOPPED: server read Running"; fi

4. journal counts only, never the raw journal

j() { sudo journalctl -u duplicati.service --since "$ts" --no-pager -o cat | grep -c -- "$1"; }
echo "Server has started:            $(j 'Server has started')"
echo "key via systemd credential:    $(j 'systemd credential settings-key (64 chars)')"
echo "Unknown option supplied:       $(j 'Unknown option supplied')"
echo "stored unencrypted:            $(j 'stored unencrypted')"
echo "FATAL:                         $(j 'FATAL')"

## Step 11

I've read step 11 in the recovery plan (…RECOVERY-PLAN.md §6.4) and in the design (…INTEGRATED-DESIGN.md §8 P0 steps 9–10), and I'm splitting it in two:

- Part A (this block): change the UI password, rewrite the credential, retire the S-5 line.
- Part B (after you paste): pause, the job edits, the guard dry run, the restart, the read-back, then resume.

Both happen while the job sits queued but held by the pause.

## Section A

Step 11, part A: rotate the UI password

Watchdog: no redeploy needed under A0. The job ID is still 2, which is what the 10-05 deploy used. The watchdog reads the same credential file, so its daily 401 ends once that file holds the new password.

1. Browser, <http://localhost:8300>:
    - Log in with the S-5 password.
    - In Settings, set a new UI password. Generate it in the password manager and save it there first. A random one with no spaces is best.
    - Log out, then log in again with the new password to prove it works.

2. pcalnon shell, from ~/Development/python/Juniper/juniper-ml. This rewrites only the DUPLICATI_WEB_CREDENTIAL= line in place, keeping the 10-05 comment header and mode 0600. It applies the rule about outer quotes, then reads the file back through the client's own parser:

python3 -I -c '
import getpass, hmac, importlib.util, os, re
p = os.path.expanduser("~/.config/duplicati-backup/web-credential")
s = importlib.util.spec_from_file_location("api", "util/ad-hoc/yamaguchi_server_api.py")
m = importlib.util.module_from_spec(s); s.loader.exec_module(m)
a = getpass.getpass("NEW UI password (hidden): "); b = getpass.getpass("again: ")
if not a or a != b: raise SystemExit("REFUSE: empty or the two entries differ")
w = a
if a != a.strip() or (len(a) >= 2 and a[0] == a[-1] and a[0] in "\x27\""): w = "\"" + a + "\""
lines = open(p, encoding="utf-8").read().splitlines()
hits = [i for i, l in enumerate(lines) if re.match(r"^\s*(export\s+)?DUPLICATI_WEB_CREDENTIAL=", l)]
if len(hits) != 1: raise SystemExit(f"REFUSE: {len(hits)} credential lines")
lines[hits[0]] = "DUPLICATI_WEB_CREDENTIAL=" + w
tmp = p + ".new"; fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
with os.fdopen(fd, "w", encoding="utf-8") as f: f.write("\n".join(lines) + "\n")
os.replace(tmp, p)
print("lines:", len(lines), "| credential line:", hits[0] + 1, "| quoted:", w != a)
print("read-back equals new:", hmac.compare_digest(m.read_credential().encode(), a.encode()))
'; echo "exit=$?"; stat -c '%a %U %s' ~/.config/duplicati-backup/web-credential
python3 util/ad-hoc/yamaguchi_server_api.py serverstate >/dev/null; echo "serverstate exit=$? (want 2: logs in with the NEW password, still Paused)"

Want: lines: 18 | credential line: 18, then read-back equals new: True, exit=0 and 600 pcalnon …, then serverstate exit=2.

3. Retire the S-5 line from the main checkout's .env. This prints counts only:

grep -c -E '^[[:space:]]*(export[[:space:]]+)?DUPLICATI_WEB_CREDENTIAL=' .env
sed -i -E '/^[[:space:]]*(export[[:space:]]+)?DUPLICATI_WEB_CREDENTIAL=/d' .env; echo "sed exit=$?"
grep -c -E 'DUPLICATI_WEB_CREDENTIAL' .env; stat -c '%a %U %s' .env

Want: 1 before, then 0 after. If the first count is 0, skip the sed and tell me.

Stop and paste if:

- the login with the new password fails;
- read-back is False;
- serverstate exits anything but 2. That includes a FATAL: login failed line; paste only its first clause.

Two notes:

- os.replace and sed -i each write a new file. The old blocks, holding the retired S-5 value, stay on disk unshredded. That's acceptable: S-5 is being retired precisely because it was exposed.
- Coming in part B: creating /home/duplicati/.cache/duplicati-tmp (0700 duplicati), and the UI edits to job 2:
  - --tempdir;
  - --run-script-before-required=/usr/local/lib/duplicati/yamaguchi-pre-backup-guard.bash;
  - --aes-version=2;
  - "Keep all backups", from the legacy UI;
  - additional-report-url stays, per the O-13 ruling.

  After the edits come the guard dry run with id=2, the restart, a filtered export 2 read-back (the passphrase is already excluded by export-passwords=false, and the report-URL values will be hidden), and then resume.

Changed: tmp/phase-d-sitting/running-record.md (gitignored), with step 10's result.

## Section B

This follows the integrated design (JUNIPER_2026-09-21_…INTEGRATED-DESIGN.md §8 P0 step 10). I checked /home/duplicati/.cache: it exists, mode 700, owned duplicati:duplicati, so the install -d below only adds the leaf directory.

### B1: Command Set 1

Sample the state, save a read-back filter, then pause

#### Constraints

- shell: pcalnon
- cwd: ~/Development/python/Juniper/juniper-ml

#### Commands

```bash
python3 util/ad-hoc/yamaguchi_server_api.py serverstate; echo "serverstate exit=$?"
mkdir -p tmp/phase-d-sitting && cat > tmp/phase-d-sitting/export_filter.py <<'PY'

import json, sys
d = json.load(sys.stdin); b = d["Backup"]; opts = {}
for s in b.get("Settings") or []:
    opts.setdefault(s["Name"].lstrip("-"), []).append(s.get("Value"))
for k in ("tempdir", "run-script-before-required", "aes-version"):
    print(k + ":", opts.get(k))
for k in ("retention-policy", "keep-time", "keep-versions"):
    print(k + ":", "PRESENT" if k in opts else "absent")
print("additional-report-url:", "present" if "additional-report-url" in opts else "absent", "(value not shown)")
print("TargetURL set:", bool(b.get("TargetURL")), "(value not shown)")
sc = d.get("Schedule") or {}
print("schedule:", sc.get("Time"), sc.get("Repeat"))
print("option names:", ", ".join(sorted(opts)))

PY
python3 util/ad-hoc/yamaguchi_server_api.py export 2 | python3 -I tmp/phase-d-sitting/export_filter.py; echo "pipe exit=${PIPESTATUS[*]}"
python3 util/ad-hoc/yamaguchi_server_api.py pause; echo "pause exit=$?"
```

#### Configuration

- serverstate exits 2 with the same fields as at step 10 (Paused, queue [(2,"2")], no active task);
- the "before" read-back shows tempdir: ['/home/pcalnon/.cache/duplicati-tmp'] and retention-policy: PRESENT;
- pipe exit=0 0;
- pause exit=0.

The filter never prints the target URL, the report URL or the passphrase. export already omits the passphrase, because it sets export-passwords=false.

---

### B2 Duplicati install

#### Constraints

- shell: root
- with CONDA_SHLVL=0
- TMPDIR exported
- no sudo

#### Commands

```bash
install -d -m 0700 -o duplicati -g duplicati /home/duplicati/.cache/duplicati-tmp; echo "install exit=$?"
stat -c '%a %U:%G %n' /home/duplicati/.cache/duplicati-tmp
```

#### Configuration

700 duplicati:duplicati

---

### B3 Duplicati Local Server Configuration

#### Constraints

Browser
legacy UI
localhost:8300
(the "ngax" client)

#### Commands

Edit job 2

- In the options step:
  - set Backup retention to: Keep all backups
  - Only that setting removes all three of retention-policy, keep-time and keep-versions.
- Under Advanced options, make these changes:
  - tempdir: → /home/duplicati/.cache/duplicati-tmp
  - run-script-before-required: → /usr/local/lib/duplicati/yamaguchi-pre-backup-guard.bash
  - aes-version: → 2
  - Leave additional-report-url exactly as it is (the O-13 ruling).
- Do _NOT_ change the passphrase, the destination or the schedule
- Save the job

#### Configuration

Report Settings: **Without changing anything:**

- Open Settings
  - the server settings, not the job's
- Look at the default options
- Tell me two things:
  - Is additional-report-url listed?
    - Answer yes or no only; don't copy its value.
  - Is retention-policy, keep-time or keep-versions listed there?
    - Answer yes or no.

**WARNING: If the legacy UI or Keep all backups isn't where this says, stop and tell me. Don't use a substitute.**

---

### B4 Guard Verification

#### Constraints

- shell: pcalnon
- dry-run the guard

#### Code

This is the integrated design's block, verbatim, with only the second line filled in. sudo will ask for your password.

```bash
unset url id
id=2
case "$id" in ''|*[!0-9]*) echo "REFUSE: set id to the job's number" >&2; false ;; esac && url="$(python3 util/ad-hoc/yamaguchi_server_api.py export "$id" | python3 -c 'import json,sys; print(json.load(sys.stdin)["Backup"]["TargetURL"])')"
test -n "$url" || { echo "REFUSE: export $id gave no TargetURL" >&2; false; } && sudo -u duplicati env DUPLICATI__REMOTEURL="$url" /usr/local/lib/duplicati/yamaguchi-pre-backup-guard.bash; echo "guard exit=$?"
unset url
```

#### Configuration

- guard exit=0
- If it fails, it prints a GUARD(...) line.
  - That line is safe to paste: it shows only the URL's scheme, its length and a hash prefix.

---

### B5 Service Restart

#### Constraints

shell: root
restart so the stale queued copy is dropped

#### Code

```bash
systemctl stop duplicati.service; echo "stop exit=$?"
ts="$(date '+%F %T')"; echo "ts=$ts"
systemctl start duplicati.service; echo "start exit=$?"
for i in $(seq 1 30); do ss -ltn 'sport = :8300' | grep -q LISTEN && break; sleep 1; done; echo "port 8300 after ${i}s"
systemctl show duplicati.service -p ActiveState -p SubState -p NRestarts -p Result
for p in 'Server has started' 'via systemd credential' 'stored unencrypted' 'FATAL'; do printf '%s: ' "$p"; journalctl -u duplicati.service --since "$ts" -o cat | grep -c -- "$p"; done
```

#### Configuration

- stop exit=0
- start exit=0;
- port 8300 listening within a few seconds
- active/running
- NRestarts=0;
- counts → 1, 1, 0, 0
  - in that order

---
  →

### B6

#### Constraints

shell: pcalnon
check the state and the edits
stop before resuming

#### Code

```bash
python3 util/ad-hoc/yamaguchi_server_api.py serverstate; echo "serverstate exit=$?"
python3 util/ad-hoc/yamaguchi_server_api.py export 2 | python3 -I tmp/phase-d-sitting/export_filter.py; echo "pipe exit=${PIPESTATUS[*]}"
```

#### Configuration

- serverstate exit=2
- Paused
- with job 2 queued again
  - this time from the edited database
- the read-back shows tempdir: ['/home/duplicati/.cache/duplicati-tmp']
- run-script-before-required: ['/usr/local/lib/duplicati/yamaguchi-pre-backon: ['2']]
- all three retention options: absent
- additional-report-url: present

---

## C. Resume Block

Paste B1 to B6 and stop there.

I'll check the read-back before giving you the resume block.

That block covers:

- resume;
- a serverstate sample, which should exit 0 (Running);
- watching the AC-3 run;
- a manual run 2 if the overdue slot isn't used.

Stop and paste early if:

- any exit code differs from the "Want" lines;
- the guard fails;
- serverstate reads Running at any point before resume.

---
