# yamaguchi: remount the lost API filesystems (securityfs, pstore, bpf) — runbook

**Date**: 2026-11-07
**Host**: yamaguchi only
**Executor**: the owner. Steps 2, 3 and 6c need root; the session that wrote this has no sudo.
**Time**: about 10 minutes. **No reboot.**
**Why**: `notes/JUNIPER_2026-11-07_JUNIPER-ECOSYSTEM_YAMAGUCHI-SECURITYFS-UNMOUNT-ROOT-CAUSE-ANALYSIS.md`
(the RCA). Its §9 lists the rejected alternatives, and its §10 vets this against the Kubernetes install.

---

## 0. Before you start

- **Do not reboot.** Finding 17 of
  `JUNIPER_2026-10-03_JUNIPER-ECOSYSTEM_BACKUP-SYSTEM-STATE-ASSESSMENT-AND-RECOVERY-PLAN.md` still
  forbids it: `duplicati.service` is enabled, and its restart fails. Nothing here restarts Duplicati,
  dockerd, containerd or PID 1.
- **Do not restart dockerd to "fix" Docker.** A dockerd started without securityfs runs every
  container without AppArmor confinement (RCA §9).
- Run from a juniper-ml checkout that has this runbook's PR, juniper-ml#2516 (`git pull` the primary
  after the merge).
- The juniper-deploy checkout needs juniper-deploy#270, the AppArmor preflight, for check E3. It
  merged 2026-11-08 as `5ed14290`, so `git pull` that checkout. Without it E3 reports `SKIP`, not a
  failure.
- Every command below is shown as you run it. `J=~/Development/python/Juniper` in the examples.

## 1. Decision D-1: the legacy snap Kubernetes services (yours)

yamaguchi carries two Kubernetes installs:

- **Ongoing, the primer's.** kubeadm/kubelet/kubectl **1.36.5** from pkgs.k8s.io, held, installed
  2026-09-26, `kubeadm init` not yet run.
- **Legacy.** Component snaps at **1.35.9**: `kubelet`, `kube-apiserver`, `kube-proxy`,
  `kube-scheduler`, `kube-controller-manager`, `kubeadm` and `cdk-addons`, plus `etcd` 3.4.36. They
  are not in `juniper-k8s/notes/JUNIPER_2026-09-24_JUNIPER-ECOSYSTEM_KUBERNETES-PRIMER.md`. Their
  services are enabled and failing only because snap-confine cannot run (the snap kubelet has
  restarted more than 1,100 times).

**Step 3 makes snap-confine work again.** About 5 s later the snap kubelet starts for real. The next
snapd refresh then succeeds and starts every enabled service: kube-apiserver on :6443, etcd on
:2379, and the rest. They contend for `/var/lib/kubelet` and for the ports `kubeadm init` checks.

| Option | What it does |
|---|---|
| **A (recommended).** Stop and disable the legacy services before the remount (step 2). | Reversible: `sudo snap start --enable …`. Removes nothing. Touches none of the 1.36.5 install. |
| B. Leave them enabled. | Accept that they start after step 3. Skip step 2, and expect the validator to report their state change as `EXPECTED`. |
| C. Remove the legacy snaps. | Out of scope here. Do it after this runbook if you want it. |

## 2. Steps

### Step 1 — capture the before-state (no root)

```bash
cd $J/juniper-ml
mkdir -p tmp/2026-11-07_remount
bash util/ad-hoc/2026-11-07_securityfs_remount_validate.bash capture tmp/2026-11-07_remount/before.txt
bash util/ad-hoc/2026-11-07_securityfs_apparmor_probe.bash > tmp/2026-11-07_remount/probe-before.txt
```

### Step 2 — (D-1 = A) stop and disable the legacy snap k8s services (root)

```bash
sudo snap stop --disable kubelet kube-apiserver kube-proxy kube-scheduler kube-controller-manager etcd
systemctl is-enabled snap.kubelet.daemon.service snap.kube-apiserver.daemon.service snap.kube-proxy.daemon.service \
    snap.kube-scheduler.daemon.service snap.kube-controller-manager.daemon.service snap.etcd.etcd.service
```

Expect six `disabled`. This works while snap-confine is broken: `snap stop` talks to snapd and
systemd, not to snap-confine. The snap kubelet's journal loop (~4,200 lines an hour) stops here.

### Step 3 — remount the three PID 1 API filesystems (root)

These are systemd's own options (`src/shared/mount-setup.c`, systemd v259.5). Each line does nothing
if the filesystem is already mounted.

```bash
mountpoint -q /sys/kernel/security || sudo mount -t securityfs -o nosuid,nodev,noexec securityfs /sys/kernel/security
mountpoint -q /sys/fs/pstore       || sudo mount -t pstore     -o nosuid,nodev,noexec        pstore     /sys/fs/pstore
mountpoint -q /sys/fs/bpf          || sudo mount -t bpf        -o nosuid,nodev,noexec,mode=0700 bpf     /sys/fs/bpf
```

Each new mount sits under `/sys`, which is a shared mount, so it is shared too, as at boot. Snap
mount namespaces are its slaves and receive it.

If `mount` is refused, stop. The fallback is `sudo systemctl daemon-reexec`: PID 1 reruns
`mount_setup()` on a re-exec (RCA §9). Do not reach for it first.

### Step 4 — prove it worked, and that nothing else moved (no root)

```bash
bash util/ad-hoc/2026-11-07_securityfs_remount_validate.bash verify tmp/2026-11-07_remount/before.txt
```

Expect `== PASS`:

| Check | Pass means |
|---|---|
| E1 | `util/host_api_filesystems_check.py` exits 0. Every API filesystem is mounted and AppArmor is consistent. |
| E2 | `/sys/kernel/security/apparmor/profiles` exists. |
| E3 | juniper-deploy's `scripts/preflight_apparmor.sh` prints `[OK]`. |
| E4 | A throwaway container (no network, removed on exit) reads `docker-default (enforce)` from `/proc/self/attr/current`. It **started**, and it is **confined**. If `docker-default` had been unloaded, dockerd reloads it here, itself. |
| E5 | `snap run helm version` runs. |
| Regression | Only `snap_service.*` (step 2) and `mount.*` (step 3) keys changed. Unchanged: the held packages, `kubelet.service`, `/etc/kubernetes`, `/var/lib/kubelet`, containerd's config, the containerd/dockerd/PID 1 identities, k8s listeners (none) and `juniper-k8s` HEAD. |

Optional, root: `sudo aa-status | head -3` shows the profile count again, and
`sudo aa-status | grep docker-default` shows the profile.

### Step 5 — bring the stack up (no root)

```bash
cd $J/juniper-deploy
make up            # the preflights, now including AppArmor, then docker compose up
make health
```

The seven containers left in `created` on 2026-11-06 are started.

### Step 6 — regression suites and after-evidence

a. juniper-deploy:

```bash
python3 -m pytest tests/ -q -p no:cacheprovider
```

Expect **0 failed**. The 17 helm tests that fail in the incident state pass once helm can run
(`reports/2026-11-07_yamaguchi-securityfs-unmount/2026-11-08T0225Z_juniper-deploy-full-suite-main-vs-branch.txt`).

b. juniper-ml:

```bash
python3 -m unittest -v tests/test_host_api_filesystems_check.py
```

c. Snap refresh catches up at its next window. Optionally, root: `sudo snap refresh`. The disabled
legacy services stay disabled through a refresh.

d. Record the after-state for the evidence directory:

```bash
cd $J/juniper-ml
bash util/ad-hoc/2026-11-07_securityfs_apparmor_probe.bash > tmp/2026-11-07_remount/probe-after.txt
diff tmp/2026-11-07_remount/probe-before.txt tmp/2026-11-07_remount/probe-after.txt
```

Commit the after-probe as `reports/2026-11-07_yamaguchi-securityfs-unmount/<UTC>_probe-after-remediation.txt`.
Its `UUID=` is already redacted.

## 3. Test matrix

| Test | Proves | Incident state (measured 2026-11-08) | After the runbook |
|---|---|---|---|
| `util/host_api_filesystems_check.py` | All of systemd's API mounts are present; AppArmor consistent | exit 1, 4 problems | exit 0 |
| `scripts/preflight_apparmor.sh` (juniper-deploy) | dockerd can load `docker-default` | `[FAIL]`, exit 1 | `[OK]`, exit 0 |
| Validator E4 | A container starts AND is AppArmor-confined | the reported daemon error | `docker-default (enforce)` |
| Validator E5 | snap-confine works | `aa_is_enabled() failed unexpectedly` | helm prints its version |
| Validator regression diff | The k8s install, containerd and dockerd are untouched | unchanged (negative-control run) | only `snap_service.*` and `mount.*` change |
| juniper-deploy `pytest tests/` | No regression; helm works | 17 failed (helm snap), 392 passed | 0 failed |
| `tests/test_apparmor_preflight.py` / `tests/test_host_api_filesystems_check.py` | The new checks' behaviour | 18 / 25 pass (hermetic) | same |
| The two mutation checks | The suites catch seeded defects | 14 of 14, 11 of 11 killed | same |

## 4. Residue the remediation does not cover (optional)

- **Desktop FUSE mounts.** `/run/user/1000/doc` and `/run/user/1000/gvfs` went in the same sweep.
  `systemctl --user restart xdg-document-portal.service gvfs-daemon.service` (user units, no root)
  remounts them. Snapped apps' file dialogs use the first.
- **ExpressVPN's cgroup.** Listed as unmounted in the recovery plan's finding 17, and not present
  now. If you use split tunnelling, check it. Restarting the VPN daemon drops the tunnel briefly, so
  do it when nothing depends on it.

## 5. Rollback

- **Steps 1, 4, 5 and 6** change nothing that needs undoing. Step 5 starts the stack;
  `make down` stops it.
- **Step 2:**
  `sudo snap start --enable kubelet kube-apiserver kube-proxy kube-scheduler kube-controller-manager etcd`.
- **Step 3** restores the boot state, and there is no reason to undo it. Unmounting again would
  re-break Docker and snaps.

If any check fails, stop and keep the outputs under `tmp/2026-11-07_remount/`. They are what the
next session needs.
