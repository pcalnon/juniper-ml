# yamaguchi securityfs / AppArmor incident — evidence (2026-11-07/08)

These files are the evidence for
`notes/JUNIPER_2026-11-07_JUNIPER-ECOSYSTEM_YAMAGUCHI-SECURITYFS-UNMOUNT-ROOT-CAUSE-ANALYSIS.md`
(the RCA). The owner executes
`notes/JUNIPER_2026-11-07_JUNIPER-ECOSYSTEM_YAMAGUCHI-API-FILESYSTEM-REMOUNT-RUNBOOK.md`
(the runbook) to fix the host.

Every file was produced by a retained script, named below, so it can be regenerated. Every capture
was taken in the **incident state**, before any remediation: securityfs, pstore and bpf unmounted
since 2026-10-27 22:55:28Z. None needed root. The repository is public, so hardware identifiers
are kept out. Two unredacted originals are retained locally on yamaguchi, in
`juniper-ml/tmp/2026-11-07_yamaguchi-securityfs-unmount_private/`, and never committed.

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

Not committed, and why:

- The **transcript scan's output** (`util/ad-hoc/2026-11-07_transcript_window_scan.py`) quotes other
  sessions' commands. The RCA §7 states its result: no mount-family command near the event. Re-run
  the script to see the rows.
- The **unredacted timelines** carry USB serials and port paths, and the **first probe run** carries
  the root filesystem UUID. Both are in the private directory named above.

After the runbook runs, add `<UTC>_probe-after-remediation.txt` here (runbook step 6d).
