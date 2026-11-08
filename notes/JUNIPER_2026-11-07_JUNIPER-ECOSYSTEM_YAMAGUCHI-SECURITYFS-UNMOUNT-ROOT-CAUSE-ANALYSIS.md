# yamaguchi: `make up` fails on "docker-default AppArmor profile" — root-cause analysis

**Date**: 2026-11-07 (investigated 2026-11-07 23:30 CST to 2026-11-08 02:30 UTC)
**Host**: yamaguchi (Ubuntu 26.04.1 LTS, kernel 7.0.0-31-generic, systemd 259.5, docker-ce 29.7.2, snapd 2.77.1)
**Status**: root cause established; host remediation written and vetted, **awaiting the owner** (it needs root)
**Author**: Paul Calnon (investigation session `piped-exploring-raven`)
**Remediation**: `notes/JUNIPER_2026-11-07_JUNIPER-ECOSYSTEM_YAMAGUCHI-API-FILESYSTEM-REMOUNT-RUNBOOK.md`
**Evidence**: `reports/2026-11-07_yamaguchi-securityfs-unmount/` (its `README.md` lists every file and the command that made it)

---

## 1. Summary

`make up` in juniper-deploy creates every container and starts none:

```text
Error response from daemon: Could not check if docker-default AppArmor profile was loaded:
open /sys/kernel/security/apparmor/profiles: no such file or directory
```

The AppArmor profile is not the problem. The filesystem that exposes AppArmor's interface is.
**securityfs is not mounted on `/sys/kernel/security`**, and has not been since **2026-10-27 at
17:55:25 CDT**. At that moment a root `umount -a`-like operation unmounted every filesystem that was
not in use. The repair made that evening restarted what `systemctl` could see:
`snapd.mounts.target` and the six API mounts that have unit files. It could not see three more,
**securityfs, pstore and bpffs**. systemd's PID 1 mounts those itself at boot, from a table in its
source, and they have no unit file. Once unmounted they leave no unit behind, so they appear in no
`systemctl` listing and nothing remounts them.

dockerd decides "this host supports AppArmor" once, when it starts. On yamaguchi that was
2026-09-07, while securityfs was mounted. So it keeps applying `docker-default` and checks the
missing interface before every start. The same missing mount also breaks every snap (snap-confine
dies in `aa_is_enabled()`), so every snapd refresh fails. That includes the legacy Kubernetes
component snaps, which have been crash-looping since, and `helm`, which is a snap here.

The fix is three `mount` commands with systemd's own options. Before running them, quiet the legacy
snap k8s services, which the remount would otherwise bring back to life. Neither step touches the
ongoing kubeadm install (§10). The runbook has the steps and a before/after validator.

## 2. The report

The owner ran `make up` in juniper-deploy (the paste says `make up`; the Makefile has no `go`
target). All four preflights passed: bind posture, image provenance, and the snapshot root with one
warning. Then `docker compose up` failed on `juniper-data` and `juniper-redis`, the first two
containers it starts.

The owner read this as "the docker daemon is missing an AppArmor profile". The error says something
narrower. The daemon could not *check* whether the profile is loaded, because the file it reads to
check does not exist.

## 3. Causal chain

Each link names the evidence that establishes it. Evidence files are in
`reports/2026-11-07_yamaguchi-securityfs-unmount/`. Upstream code lines are pinned at the host's
exact versions in `…/2026-11-08T0110Z_upstream-source-pins.txt`.

| # | Link | Evidence |
|---|------|----------|
| L1 | **Boot, 2026-09-07 23:12:17 CDT.** PID 1 mounts securityfs, pstore and bpf from `mount_table` in `src/shared/mount-setup.c`. They have no unit file. | `uptime -s`. systemd v259.5 `src/shared/mount-setup.c:112-140`, `:205-232` (pins file). |
| L2 | **dockerd starts at 23:13:03 CDT and caches AppArmor support.** `appArmorSupported()` is containerd's `apparmor.HostSupports()`, a `sync.Once`. It is true when `/sys/kernel/security/apparmor` exists, `/sbin/apparmor_parser` exists, and `/sys/module/apparmor/parameters/enabled` starts with `Y`. It has been true since, and `docker info` still lists `name=apparmor`. | `ps -o lstart` for pid 13298 (probe §5). moby `docker-v29.7.2` `daemon/apparmor_linux.go:1-16`, vendored containerd v2.3.3 `pkg/apparmor/apparmor_linux.go:17-45`. Probe §6. |
| L3 | **2026-10-27 17:55:25.43–17:55:28.30 CDT (22:55:25–28Z): every filesystem not in use is unmounted.** systemd recorded the deactivations. 298 snap mounts still carry an `InactiveEnterTimestamp` inside those three seconds; the backup arc counted 299 on the day. Also unmounted: the `extruder` and `EBC5-F0A3` media mounts (`DFF3-2782` was remounted later, which overwrote its timestamp), `binfmt_misc` (17:55:27.03), and at 17:55:28.26 `fusectl`, `configfs`, `tracefs`, `hugetlbfs`, `debugfs` and `mqueue`. Mounts in use survived: `/`, `/home`, `/mnt/Backups`, `/run`, and `cgroup2`, which systemd holds. | `…systemd-timeline-system-public_….tsv` (rows `InactiveEnterTimestamp`, 22:55:25–28Z). `util/ad-hoc/2026-11-07_systemd_unit_timeline.py`. |
| L4 | **securityfs, pstore and bpf went in the same sweep. This is inferred: they left no record.** They were mounted at boot (L1), and dockerd's cached support (L2) shows securityfs was present at 23:13 CDT. They are absent now. The sweep took every mount not in use, and nothing holds these three open, so it would have taken them. The only alternative is a separate, traceless root unmount of exactly these three, and nothing points to one. Consistent with the inference: the snap kubelet was already failing in `aa_is_enabled()` at the journal's horizon (2026-10-30). | Probe §3 shows all three `MISSING`, while every other `/sys` API mount carries the high mount ids of its 2026-10-28 remount (`14679`–`14825`). `sys-kernel-security.mount`, `sys-fs-pstore.mount` and `sys-fs-bpf.mount` are `LoadState=not-found` (probe §4). A mount with no unit file is garbage-collected once inactive, so systemd kept no timestamp for them. |
| L5 | **The 20:18 CDT repair restored only what `systemctl` could list.** `systemctl start snapd.mounts.target` remounted the snaps at 01:18:17Z (snap mounts carry that `ActiveEnterTimestamp`). The six unit-file mounts followed at 01:18:38Z, all six within 0.33 s. The repair record calls it complete: *"It was repaired without a reboot (`systemctl start snapd.mounts.target` and the six unit-file mounts)"* (`JUNIPER_2026-10-03_JUNIPER-ECOSYSTEM_BACKUP-SYSTEM-STATE-ASSESSMENT-AND-RECOVERY-PLAN.md` §6 finding 17). Its list of unmounted filesystems omits securityfs, pstore and bpf. | `systemctl show --timestamp=us+utc` for `snap-*.mount` and the six units. Timeline TSV rows at 01:18:38Z. |
| L6 | **Every container start now fails.** `WithApparmor` sees `appArmorSupported()` true and the default profile in use, so it calls `loadDefaultAppArmorProfileIfMissing()`. That calls `aaprofile.IsLoaded()`, which opens `/sys/kernel/security/apparmor/profiles` and gets ENOENT. The result is the reported error. | moby `daemon/oci_linux.go:124-150`, `daemon/apparmor_default.go:26-40`, vendored `moby/profiles/apparmor/apparmor.go:110-120`. `journalctl -u docker`: 6 failures, from 2026-11-06 07:29:43 CST, the first start attempt since the event. |

The kernel's AppArmor is still active and enforcing. `/sys/module/apparmor/parameters/enabled` is
`Y`, `CONFIG_LSM` includes `apparmor`, and `/proc/self/attr/apparmor/current` reads `unconfined`
through procfs, which needs no securityfs (probe §2). Loaded profiles live in the kernel, not in
securityfs. **Only the interface is gone.**

## 4. Root causes

- **RC-1 (trigger).** A root process unmounted every filesystem not in use, at 17:55:25 CDT on
  2026-10-27 (§7). Unmounting the system's API filesystems has no legitimate everyday use.
- **RC-2 (the defect that persisted).** The repair was scoped by systemd's unit list, and that list
  cannot show the mounts PID 1 makes itself. `systemctl list-units --type=mount --all` lists only
  *loaded* units. An inactive mount unit with no fragment is unloaded, so securityfs, pstore and bpf
  vanished from the inventory used to judge the repair complete. This is the
  "conformance to a declared set" trap: the check passed against the set it was given, not the
  system.
- **RC-3 (why it surfaced eleven days late, and misleadingly).**
  - dockerd caches AppArmor support once, at start, so the host stayed "AppArmor-capable" to Docker
    with the interface gone.
  - Nothing on the host checks that the API filesystems are mounted.
  - Docker's error names a profile, not a mount.
  - The stack was not started between 2026-10-27 and 2026-11-06, so the first container start after
    the event came ten days later.
- **RC-4 (why the actor cannot be named from logs).** The journal sits at its 4 GB cap ("Archived
  and active journals take up 4G"), and its oldest entry is 2026-10-30 14:04 CDT. syslog and
  auth.log begin 2026-10-28 00:0x CDT. All three begin after the event. Since the event, the legacy
  snap kubelet has crash-looped every ~4.5 s: 4,216 journal lines in the last hour, 166,412 failures
  since the journal's horizon. That loop is one of the event's own consequences, and it is filling
  the journal that would have recorded the event.

## 5. Timeline

| CDT / CST | UTC | Event | Source |
|---|---|---|---|
| 2026-09-07 23:12:17 | 09-08 04:12:17 | Boot; PID 1 mounts securityfs, pstore, bpf | `uptime -s` |
| 23:12:57 / 23:13:03 | 04:12:57 / 04:13:03 | containerd (pid 11194), dockerd (pid 13298) start; AppArmor support cached | `ps -o lstart` |
| 2026-09-26 02:43:29 | 07:43:29 | `apt-get install -y kubelet kubeadm kubectl` (1.36.5, then held) | `/var/log/apt/history.log*` |
| 2026-10-27 17:25:58–17:38:43 | 22:25:58–22:38:43 | Backup Tier 2 OK run, both sticks mounted | recovery plan, Tier 2 item 8 |
| **17:55:25.43–17:55:28.30** | **22:55:25–28** | **The sweep: 298+ snap mounts, media, binfmt_misc, /sys and /dev API mounts, securityfs, pstore, bpf** | timeline TSV |
| 17:55:35 | 22:55:35 | `sdj1`/`sdj2` (backup stick `EBC5-F0A3`) re-appear: a partition-table re-read | timeline TSV (device rows) |
| 20:18:17 | 10-28 01:18:17 | `systemctl start snapd.mounts.target`: snaps back | snap-mount `ActiveEnterTimestamp` |
| 20:18:38 | 01:18:38 | The six unit-file API mounts back. securityfs, pstore, bpf **not** | timeline TSV |
| 2026-10-28 | | Backup handoff records "repaired without a reboot" | `HANDOFF_2026-10-28_backup-tiers-2-3-running-record-landed-then-phase-d.md` |
| 2026-10-30 14:04:12 | 19:04:12 | Oldest retained journal entry; the snap kubelet is already failing in `aa_is_enabled()` | probe §7, §10 |
| 2026-11-06 07:29:43 | 13:29:43 | First `make up` after the event: every start fails | `journalctl -u docker` |
| 2026-11-06 19:20 → 11-07 17:10 | | Four snapd auto-refreshes fail at security-profile setup (14 snaps in the last) | `snap changes` (probe §7) |
| 2026-11-07 17:05–17:08 | 23:05–23:08 | The failed refresh restarts the legacy k8s snaps; four hit systemd's start limit | `journalctl -u snap.kube-*` |
| 2026-11-07 16:26, 17:12 | 22:26, 23:12 | Further `make up` failures; the report | `journalctl -u docker` |

## 6. Blast radius (as of 2026-11-08)

| Consumer | State | Evidence |
|---|---|---|
| Docker | Every non-privileged container start fails. Seven juniper containers sit in `created`. | probe §6, §7 |
| Every snap app and snap service | snap-confine dies: `aa_is_enabled() failed unexpectedly (No such file or directory)`. snapd 2.77.1 treats ENOENT as tampering and refuses to run. | `cmd/libsnap-confine-private/apparmor-support.c:44-76` (pins file) |
| `helm` (a snap on yamaguchi) | Cannot run. 17 juniper-deploy tests fail locally for this reason alone (`test_helm_chart_probes.py`, `test_helm_networkpolicy_data_egress.py`). | `…juniper-deploy-full-suite-main-vs-branch.txt` |
| Legacy k8s component snaps (kubelet, kube-apiserver, kube-proxy, kube-scheduler, kube-controller-manager 1.35.9; etcd 3.4.36) | kubelet is crash-looping (`NRestarts=1136`). The other four are `failed` at the start limit since the 17:05 refresh. | probe §8 |
| snapd refresh | Fails for every snap at "security profile setup" (four `Error` changes), so no snap, chromium included, receives updates. | `snap changes` |
| AppArmor userspace | `apparmor_parser` cannot load or replace profiles, and `aa-status` cannot read them. A package upgrade that ships a profile cannot load it. | follows from L4 |
| bpffs, pstore | `/sys/fs/bpf` and `/sys/fs/pstore` are absent. Cilium (the primer's CNI) mounts its own bpffs if needed. pstore records are unreadable until remounted. | probe §3 |
| Desktop session | `/run/user/1000/doc` (document portal) and `/run/user/1000/gvfs` are not mounted. | probe §9 |
| ExpressVPN | The recovery plan lists "ExpressVPN's cgroup" among the unmounted. No cgroup v1 mount exists now. Unverified whether split tunnelling depends on it. | probe §3, `findmnt -t cgroup` |
| Journal | At its 4 GB cap; ~8-day horizon; filled by the kubelet loop. | probe §10 |

Not affected:

- Kernel AppArmor enforcement of already-confined processes.
- The kubeadm/kubelet/kubectl packages, `kubelet.service`, `/etc/kubernetes` and `/var/lib/kubelet` (fingerprint file).
- containerd's process and configuration.
- The cluster's own nodes. They are the Raspberry Pis and turing's VM, per `juniper-k8s/inventory/hosts.yaml`, which lists yamaguchi as the **workstation**, not a node.

## 7. The actor (unconfirmed)

What the evidence fixes:

1. **One sweep, in one direction.** About 300 unmounts happened in three seconds. They interleave the
   way a reverse walk of the mount table does: recently mounted snaps and media first, boot-time
   API mounts last. That is what `umount -a` does (it skips `proc`, `sysfs`, `devpts` and a few
   other types, and anything busy). A recursive unmount of a `--rbind` copy of `/` with shared
   propagation would look the same. Either needs root.
2. **It coincides with backup drive work.** Both Tier 2 sticks were unmounted in the sweep. Ten
   seconds later the `EBC5-F0A3` stick's partition table was re-read (`sdj1`/`sdj2` re-appear at
   22:55:35Z). The backup arc's next handoff added: *"To eject a backup drive, use the desktop's
   Eject or `udisksctl unmount`, never `umount -a`"*
   (`HANDOFF_2026-10-28_backup-tiers-2-3-running-record-landed-then-phase-d.md`, Key context).
3. **No Claude session ran it.** `util/ad-hoc/2026-11-07_transcript_window_scan.py` read all 340
   transcripts under `~/.claude/projects/`. No `mount`, `umount`, `unshare`, `nsenter`, `chroot`,
   `--rbind` or `make-r*` command ran anywhere near the event. The commands at 22:55:2x were `git`,
   `gh api` and `sed` reads. The only `unshare … --mount` (2026-10-30) ran in an unprivileged user
   namespace, three days later.
4. **The logs that would name it are gone** (RC-4). The owner's `~/.bash_history` has no `umount`
   line, but it holds only the last 2,000 commands of shells that have *exited*. Four root sessions
   from before the event are still open (pts/14, pts/16, pts/20, pts/22, per `loginctl`), and a shell
   still running has not written its history.

**To confirm it** (owner, optional; this changes nothing): run `history | grep -n umount` in each open
root terminal, and `sudo grep -n umount /root/.bash_history`. Knowing the actor changes the
prevention advice, not the remediation.

## 8. Hypotheses considered and rejected

| Hypothesis | Rejected because |
|---|---|
| A kernel 7.0 / AppArmor 5.0 regression removed the interface | AppArmor is the active LSM (`enabled=Y`, `CONFIG_LSM`, procfs labels work). `/sys/kernel/security` is an empty sysfs mount point (`dr-xr-xr-x`, two links). securityfs is simply not mounted. |
| dockerd sees a different mount namespace (snap Docker, rootless, a hardening drop-in) | The context is `default` → `unix:///var/run/docker.sock`, and docker-ce comes from Docker's apt repo. dockerd's own `/proc/13298/mountinfo` has no securityfs line either. This session runs in the initial mount namespace (`mnt:[4026531832]`, the fixed init inode on 7.0). |
| The Kubernetes install changed something | Its packages landed on 2026-09-26, a month before the event. `kubeadm init` has never run (`/etc/kubernetes/manifests` holds only `.kubelet-keep`), and no k8s port is listening. The legacy snaps are victims (§6), not the cause. |
| A Claude session unmounted it | Transcript scan (§7 item 3). |
| The `docker-default` profile was unloaded | Not established, and not the error: the daemon could not *check*. The profile persists in the kernel unless explicitly removed. If it is missing after the remount, dockerd reloads it itself (`installDefaultAppArmorProfile`). |
| Raspberry Pi Imager (in `juniper-k8s/resources/`) | No evidence: its config was last written 2026-10-08. |

## 9. Remediation

Owner-executed, root, no reboot. It takes under ten minutes:
`notes/JUNIPER_2026-11-07_JUNIPER-ECOSYSTEM_YAMAGUCHI-API-FILESYSTEM-REMOUNT-RUNBOOK.md`. In short:

1. Capture the before-state.
2. Stop and disable the legacy snap k8s services (decision D-1).
3. Mount the three filesystems with systemd's own options:
   `sudo mount -t securityfs -o nosuid,nodev,noexec securityfs /sys/kernel/security`, the same for
   `pstore`, and `bpf` with `mode=0700`.
4. Verify efficacy, and that nothing else changed.
5. Run `make up`.
6. Run the regression suites.

Alternatives rejected:

- **Reboot.** It would remount everything, but finding 17 of
  `JUNIPER_2026-10-03_JUNIPER-ECOSYSTEM_BACKUP-SYSTEM-STATE-ASSESSMENT-AND-RECOVERY-PLAN.md`
  forbids a reboot until its §6.4 step 10: `duplicati.service` is enabled, and that restart fails.
- **Restart dockerd only.** Its cached support would become *false*, so containers would start
  **without AppArmor confinement**, silently. A security regression traded for a symptom.
- **`security_opt: apparmor=unconfined` in compose.** The same regression, made permanent and
  per service.
- **`systemctl daemon-reexec`.** It would work: PID 1 runs `mount_setup()` on a re-exec too
  (`src/core/main.c:3184-3195`, `:3005-3019`). It also re-executes PID 1 with 3,062 loaded units
  during an active backup arc, which is a larger change than three mounts. It is the fallback if a
  `mount` is refused.

## 10. Vetting against the ongoing Kubernetes install

The install is the juniper-k8s primer's: kubeadm and upstream debs, containerd, Cilium
(`juniper-k8s/notes/JUNIPER_2026-09-24_JUNIPER-ECOSYSTEM_KUBERNETES-PRIMER.md`). Its nodes are the
Pis and turing's VM. yamaguchi is the workstation, and carries the held 1.36.5 debs.

| Component | What the remediation does to it |
|---|---|
| kubeadm / kubelet / kubectl 1.36.5 (held), `kubelet.service` (enabled, inactive), `/etc/kubernetes`, `/var/lib/kubelet` | **Nothing.** The validator fingerprints all of them and fails on any change. |
| containerd (pid 11194) and its config | **Nothing.** No restart. Restoring securityfs first is a benefit: had containerd been restarted for CRI (primer §2.4) while securityfs was missing, its own `HostSupports()` would be false, and pods would run unconfined. |
| Legacy snap k8s services (1.35.9; not in the primer) | **Without step 2, the remount revives them.** The crash-looping kubelet would start within ~5 s. The next snap refresh, which would now succeed, restarts every enabled service: kube-apiserver (:6443), etcd (:2379), and the rest. They would contend for `/var/lib/kubelet` and the ports `kubeadm init` checks. Step 2 stops and disables them first. That is reversible (`snap start --enable …`) and removes nothing. |
| `helm` (snap) and other snap tooling the install drives from yamaguchi | **Restored.** Broken since 2026-10-27. |
| Cilium | yamaguchi is not a node. On a node, a mounted bpffs is what Cilium expects. |
| The Pis, turing's VM, the juniper-k8s checkout | Not touched. The fingerprint records `juniper-k8s` HEAD. |

## 11. Fixes delivered

| Change | Repo | What it does | Tests |
|---|---|---|---|
| `scripts/preflight_apparmor.sh`, wired into `make up` / `demo` / `dev` / `monitor` / `obs-demo`, and `make apparmor-preflight` | juniper-deploy#270 (merged 2026-11-08, `5ed14290`) | Names the missing mount before `docker compose up` does. Fails when AppArmor is enabled but the interface is gone, whether dockerd still uses AppArmor (every start would fail) or no longer does (containers would run unconfined). Warns when the interface is back but dockerd never re-detected it. Bypass: `JUNIPER_APPARMOR_OK=1`. | `tests/test_apparmor_preflight.py` (18 tests). Mutation check 14 of 14. The full suite's failure set is identical to `main`'s (17 helm-snap failures, the same root cause). |
| `util/host_api_filesystems_check.py` | juniper-ml#2516 | Judges `/proc/self/mountinfo` against systemd's API-filesystem table (PID 1's and the unit-file mounts), plus AppArmor consistency. Prints systemd's exact remount commands. Exit codes 0/1/2; `--json`. | `tests/test_host_api_filesystems_check.py` (25 tests, CI-wired). Mutation check 11 of 11, including the RC-2 mutant ("judge only unit-file mounts"). |
| `util/ad-hoc/2026-11-07_securityfs_remount_validate.bash` | juniper-ml | The runbook's before/after validator: five efficacy checks (E1–E5) and a k8s/daemon fingerprint diff. | Negative control on the incident state: all five efficacy checks fail, and the fingerprint is unchanged (`…remount-validate-negative-control-incident-state.txt`). |
| Erratum on finding 17 | juniper-ml | Corrects "repaired without a reboot" in `JUNIPER_2026-10-03_JUNIPER-ECOSYSTEM_BACKUP-SYSTEM-STATE-ASSESSMENT-AND-RECOVERY-PLAN.md`. | — |

## 12. Recommendations not done here

1. **Retire the legacy snap k8s components** (owner). They predate the primer, conflict with a future
   kubeadm node on this host, and are the journal's largest writer. The runbook only disables them.
2. **Journal retention.** The 4 GB cap gives an ~8-day horizon at the current write rate. Stopping the
   kubelet loop (runbook step 2) removes most of it. A `MaxRetentionSec=` floor, or a larger
   `SystemMaxUse=`, would have kept 2026-10-27.
3. **Run the host check on a timer** or from the session launcher, so a lost API mount is caught the
   same day, not at the next container start.
4. **Desktop and VPN residue:** see runbook §8. Restarting `xdg-document-portal` and `gvfs-daemon`
   (user units) remounts the two FUSE mounts. Check ExpressVPN split tunnelling if it is used.
5. **Ejecting drives:** keep to the backup arc's rule: desktop Eject or `udisksctl unmount -b /dev/sdX1`,
   never `umount -a`.

## 13. Provenance

Scripts. All are retained, and none needs root:

| Script | Purpose |
|---|---|
| `util/ad-hoc/2026-11-07_securityfs_apparmor_probe.bash` | Read-only state capture (10 sections); run before and after remediation |
| `util/ad-hoc/2026-11-07_systemd_unit_timeline.py` | systemd's in-memory unit timestamps in a window; `--public` drops hardware-identity units |
| `util/ad-hoc/2026-11-07_transcript_window_scan.py` | Shell commands in Claude transcripts inside a window |
| `util/ad-hoc/2026-11-07_upstream_source_pins.bash` | moby / containerd / systemd / snapd lines at the host's exact versions |
| `util/host_api_filesystems_check.py` | The permanent host check |
| `util/ad-hoc/2026-11-07_host_api_fs_check_mutation_check.py` | Mutation check for that check's suite |
| `util/ad-hoc/2026-11-07_securityfs_remount_validate.bash` | The runbook's validator |
| juniper-deploy `util/ad-hoc/2026-11-07_apparmor_preflight_mutation_check.py` | Mutation check for the preflight's suite |

The repository is public, so two unredacted captures are kept out of it but retained on yamaguchi,
in `juniper-ml/tmp/2026-11-07_yamaguchi-securityfs-unmount_private/`:

- the timelines with device-alias units, which carry USB serials;
- the first probe run, which carried the root filesystem UUID.

The committed copies were regenerated with `--public` and the redaction.
