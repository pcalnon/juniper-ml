# yamaguchi securityfs / AppArmor incident — evidence (2026-11-07/08)

These files are the evidence for
`notes/JUNIPER_2026-11-07_JUNIPER-ECOSYSTEM_YAMAGUCHI-SECURITYFS-UNMOUNT-ROOT-CAUSE-ANALYSIS.md`
(the RCA). The owner executed
`notes/JUNIPER_2026-11-07_JUNIPER-ECOSYSTEM_YAMAGUCHI-API-FILESYSTEM-REMOUNT-RUNBOOK.md`
(the runbook) on 2026-11-08 to fix the host.

Every file was produced by a retained script or command, named below, so it can be regenerated.
None needed root. The files in the first table were captured in the **incident state**, before any
remediation, with securityfs, pstore and bpf unmounted since 2026-10-27 22:55:28Z. The second
table records the remediation, on 2026-11-08 from 08:23Z (RCA §14). The repository is public, so
hardware identifiers are kept out. Two unredacted originals are retained locally on yamaguchi, in
`juniper-ml/tmp/2026-11-07_yamaguchi-securityfs-unmount_private/`, and never committed.

### Incident state

| File (UTC of capture) | What it shows | Produced by |
|---|---|---|
| `2026-11-08T0135Z_probe-before-remediation.txt` | The host state in 10 sections: kernel AppArmor state; expected vs mounted API filesystems (securityfs, pstore, bpf `MISSING`); systemd's unit records; daemon start times; Docker's view; the failing consumers (166,412 snap-kubelet `aa_is_enabled` failures since the journal's horizon; 6 Docker start failures; 4 failed snap refreshes); the k8s install's state; desktop FUSE residue; journal retention. `/proc/cmdline`'s root `UUID=` is redacted. | `bash util/ad-hoc/2026-11-07_securityfs_apparmor_probe.bash` |
| `2026-11-08T0130Z_systemd-timeline-system-public_2026-10-27T2230Z-2026-10-28T0200Z.tsv` | Every PID 1 unit transition from 22:30Z to 02:00Z. **The sweep**: 298 snap mounts, media, `binfmt_misc` and the `/sys` and `/dev` API mounts at 22:55:25–28Z. The repair: snaps at 01:18:17Z, the six unit-file mounts at 01:18:38Z. | `python3 util/ad-hoc/2026-11-07_systemd_unit_timeline.py --public --since 2026-10-27T22:30:00Z --until 2026-10-28T02:00:00Z` |
| `2026-11-08T0130Z_systemd-timeline-user-public_2026-10-27T2230Z-2026-10-28T0200Z.tsv` | The same window, as the user manager saw it (`snap-kubelet-3848.mount` back at 22:55:28.39Z). | the same, with `--user` |
| `2026-11-08T0110Z_upstream-source-pins.txt` | The upstream code lines behind each mechanism claim, at resolved SHAs for the host's exact versions: moby `docker-v29.7.2` (`6a43e3d5`), systemd `v259.5` (`b3d8fc43`), snapd `2.77.1` (`8a77c501`). `tests/test_host_api_filesystems_check.py` parses this file to pin the check's mount options to systemd's. | `bash util/ad-hoc/2026-11-07_upstream_source_pins.bash` |
| `2026-11-08T0215Z_remount-fingerprint-incident-state.txt` | The fingerprint the runbook's validator diffs: held kube debs, `kubelet.service`, `/etc/kubernetes` and `/var/lib/kubelet` trees, containerd's config hash, k8s listeners, `juniper-k8s` HEAD, daemon identities, the legacy snap services, the three mounts. | `bash util/ad-hoc/2026-11-07_securityfs_remount_validate.bash capture …` |
| `2026-11-08T0216Z_remount-validate-negative-control-incident-state.txt` | The validator run against the broken host: E1–E5 all `FAIL` (E4 reproduces Docker's exact error; E5 snap-confine's); fingerprint unchanged. It proves the validator detects the incident, so a later `PASS` means something. E5 ran `snap run helm version --short` here; the validator now runs `snap run helm version`, which works on any helm major. snap-confine dies before helm reads its arguments, so this result is the same under either form. | `bash util/ad-hoc/2026-11-07_securityfs_remount_validate.bash verify …` |
| `2026-11-08T0225Z_juniper-deploy-full-suite-main-vs-branch.txt` | The juniper-deploy suite on `main` and on the preflight branch: identical 17-test failure set, every failure helm-as-a-snap dying in snap-confine; the branch adds 18 passing tests. | `python3 -m pytest tests/ -q -p no:cacheprovider` in each checkout |
| `2026-11-08T0205Z_mutation-check_juniper-deploy_preflight-apparmor.txt` | 14 of 14 seeded defects in `scripts/preflight_apparmor.sh` caught by its suite. | juniper-deploy `python3 util/ad-hoc/2026-11-07_apparmor_preflight_mutation_check.py` |
| `2026-11-08T0210Z_mutation-check_juniper-ml_host-api-filesystems-check.txt` | 11 of 11 seeded defects in `util/host_api_filesystems_check.py` caught, including the incomplete repair's own logic ("judge only unit-file mounts"). | `python3 util/ad-hoc/2026-11-07_host_api_fs_check_mutation_check.py` |

### The remediation (2026-11-08)

| File (UTC of capture) | What it shows | Produced by |
|---|---|---|
| `2026-11-08T0823Z_owner-run-runbook-steps-1-to-4.txt` | The owner's terminal output for runbook steps 1–4, verbatim, with times from the host. Step 1 ran on a checkout not yet pulled, so it captured no baseline and left `probe-before.txt` empty. Step 4's `verify` against that empty file listed 22 `UNEXPECTED` lines: an empty baseline, not a regression (RCA §14 F2, F4). | Pasted by the owner; the header was written in the session |
| `2026-11-08T0851Z_remount-validate-after-remediation-vs-incident-fingerprint.txt` | `verify` on the remediated host against the 02:15Z incident-state fingerprint: E1–E5 `PASS`, and only `mount.*` and `snap_service.*` differ. Re-run with the hardened validator at 09:06Z and again at 09:11Z: byte-identical output (`diff` exit 0). | `bash util/ad-hoc/2026-11-07_securityfs_remount_validate.bash verify reports/2026-11-07_yamaguchi-securityfs-unmount/2026-11-08T0215Z_remount-fingerprint-incident-state.txt` |
| `2026-11-08T0852Z_make-up-refused-by-image-provenance-preflight.txt` | `make up` refused by the image-provenance preflight before the AppArmor one ran: canopy 0.9.0 and data 0.17.1 are each 2 commits behind their checkouts (RCA §14 F6). | `make -C juniper-deploy up`, colour codes stripped |
| `2026-11-08T0853Z_probe-after-remediation.txt` | The probe's 10 sections after the remount. Against the before-probe, only the expected changes. securityfs's inodes carry the boot time. | `bash util/ad-hoc/2026-11-07_securityfs_apparmor_probe.bash` |
| `2026-11-08T0853Z_juniper-deploy-full-suite-after-remediation.txt` | juniper-deploy at `53b948d8`: 409 passed, 48 skipped, **0 failed**. The 17 helm tests that failed in the incident state pass. | `python3 -m pytest tests/ -q -p no:cacheprovider` in the juniper-deploy checkout |
| `2026-11-08T0857Z_make-up-after-remediation-released-images.txt` | `make up` with the owner's choice to run the released images: all four preflights pass, the AppArmor one with `[OK]`, and all seven containers start. | `JUNIPER_IMAGE_STALE_OK=1 make -C juniper-deploy up`, colour codes stripped |
| `2026-11-08T0858Z_make-health-after-remediation.txt` | All four services ready. canopy and data show `STALE`: drift against the checkouts, as chosen. | `make -C juniper-deploy health`, colour codes stripped |
| `2026-11-08T0905Z_upstream-source-pins.txt` | The 01:10Z pins plus three systemd v259.5 sites behind the F1 correction: `mount_point_is_api()`, the skip in `mount_setup_unit()`, and the refusal in `mount_verify()`. The 01:10Z file is kept unchanged: `tests/test_host_api_filesystems_check.py` parses it. | `bash util/ad-hoc/2026-11-07_upstream_source_pins.bash` |
| `2026-11-08T0908Z_remount-validate-baseline-gate-check_first-gate-FAILED.txt` | The first version of the validator's baseline gate, failing cases C3 and C10: it passed the probe's report as a baseline. Kept as the evidence for F3. | `python3 util/ad-hoc/2026-11-08_remount_validate_baseline_gate_check.py` |
| `2026-11-08T0911Z_remount-validate-baseline-gate-check.txt` | The fixed gate: 14 of 14 cases pass, and 10 of 10 seeded defects are caught. | the same |
| `2026-11-08T0912Z_systemd-api-mount-units.txt` | F1, live: none of the ten mounted `mount_table` points has a unit (seven never unmounted since boot), and all six unit-file mounts are loaded units. | `bash util/ad-hoc/2026-11-08_api_mount_units_check.bash` |
| `2026-11-08T0913Z_stack-containers-apparmor-profile.txt` | Each of the seven running containers: AppArmor profile `docker-default`, `running`, `healthy`. | `docker inspect -f '{{.Name}} apparmor={{.AppArmorProfile}} …'` on the seven containers |
| `2026-11-08T0917Z_bash-empty-assoc-key-abort-repro.txt` | bash 5.3.9 abandons a function on an empty associative-array key, silently to a command substitution, which is how the first gate passed the probe's report (F3). | `bash util/ad-hoc/2026-11-08_bash_empty_assoc_key_abort_repro.bash` |

Not committed, and why:

- The **transcript scan's output** (`util/ad-hoc/2026-11-07_transcript_window_scan.py`) quotes other
  sessions' commands. The RCA §7 states its result: no mount-family command near the event. Re-run
  the script to see the rows.
- The **unredacted timelines** carry USB serials and port paths, and the **first probe run** carries
  the root filesystem UUID. Both are in the private directory named above.
- The **remediation's working directory**, `juniper-ml/tmp/2026-11-07_remount/` on yamaguchi, is kept
  locally. It holds the empty `probe-before.txt` and the session's outputs under their first,
  approximate names. The second table's files are copies of those outputs, under their capture
  times.
