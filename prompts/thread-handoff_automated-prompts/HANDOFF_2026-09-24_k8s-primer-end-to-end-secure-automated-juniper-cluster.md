# Handoff: Kubernetes primer for an end-to-end, secure, automated, production-ready Juniper cluster

**Date**: 2026-09-24 · **Originating session**: `k8s` · **Status**: primer NOT started. **This handoff is UNVALIDATED**: the owner asked for no validation and for minimal token use, so treat every "lead" below as a hypothesis to check.

## Goal

Continue: write the Kubernetes primer specified verbatim below as one markdown file in juniper-ml `notes/`. Validate it by multi-agent consensus, with the emphasis on technical correctness and no hallucination. Then open a PR and merge it. **Merge approval is granted for the primer PR.**

## Completed so far

- Nothing on the primer. The originating session wrote only this handoff and opened a PR for it (branch `docs/k8s-primer-handoff`). It did not merge that PR.

## Remaining work

1. Create a worktree per the repo convention; use a branch like `docs/k8s-primer`.
2. Ground in the repos: read `juniper-deploy/AGENTS.md`. Find existing charts and manifests (`find /home/pcalnon/Development/python/Juniper/juniper-deploy -name Chart.yaml -o -name '*.yaml' -path '*k8s*'`). Find the image names, registries and architectures, the metrics endpoints (juniper-observability, juniper-service-core), and the service ports and env vars (parent `Juniper/CLAUDE.md`).
3. Measure the real hardware over ssh where you can. Linux: `nproc; free -g; lsblk; ip -br a; cat /etc/os-release`. Mac: `sysctl -n hw.physicalcpu hw.logicalcpu hw.memsize; sw_vers`. Only `turing` (the Mac) is named. `~/.ssh/config` on this workstation probably names the other hosts; otherwise ask the owner. Never invent hostnames or IPs. Use placeholders (`<server>`, `<pi-01>`…`<pi-08>`) plus an inventory table the owner fills in, and commit no secrets.
4. Check every version or currency claim against a primary source at authoring time (kubernetes.io, project docs via context7 or WebFetch), and record the verification date in the primer.
5. Draft `notes/JUNIPER_<YYYY-MM-DD>_JUNIPER-ECOSYSTEM_KUBERNETES-PRIMER.md`. The naming rules are in `notes/JUNIPER_2026-07-04_JUNIPER-ML_NOTES-FILE-NAMING-CONVENTION.md`. Structure it as ordered phases, each with three layers: architecture, then analysis and best practice, then commands. Add a hardware-profile matrix (server-only, Pi-only, Mac-VM, any combination) plus inventory groups, so any category can be dropped. Say explicitly when a profile loses control-plane HA.
6. Validate by consensus. Brief at least 3 independent validator agents (Agent tool) per the memory `feedback_multi_agent_adversarial_validation_sop.md`. Each validator re-derives claims from primary sources, and briefs carry no secrets or PII. Fix what they find and repeat until a round finds no defects. Do not call the Workflow tool unless the owner opts in.
7. Run pre-commit (markdownlint's 512-character line limit applies to table rows too) and the doc-link check. Open the PR with `util/open_signed_pr.py`: commits must be GitHub-signed, and local gpg signing hangs when headless. Merge with `util/safe_merge.py` and read its `MERGED` line, because exit 0 does not prove a merge.

## Original request (verbatim; this is the spec)

```text
Let's write a detailed kubernetes primer

the primer should be structured as a functional procedure to perform a full, end-to-end install and configuration of a secure, automated, and production ready k8s instance.
this primer should include correct, detailed information:

- high level architecture
- mid level analysis and best practices
- detailed, command level work

the primer should assume most, if not all, of the work will be performed on the command line.
where helpful, gui based tools can also be used with the assumption that they are being run from this workstation.
the primer should be written with the following hardware and architecture assumptions:

1. the following hardware should be included, or capable of being included, in the k8s instance:
    - a dedicated server with the following characteristics
      - running a server install of ubuntu 26.04
      - an intel CPU with 8 cores
      - 64 GB of ecc ram
      - 1 T solid state drive
      - a wireless internet connection
      - a wired, ethernet connection to an internal network switch that connects all involved hardware
    - an 8 node Raspberry Pi 5 cluster
      - with 8-core ARM cpus
      - with 8GB ram
      - a solid state drive that is one of the following:
        - sata ssd, connected to the raspi board via usb c 3.1
        - a nvme m.2 ssd, connected to the raspi board via an nvme m.2 pi hat
    - a macbook pro, intel 2nd gen.
      - 12 core cpu
      - 64 GB ram
      - internal ssd
      - MacOS Sequoia
      - a wireless internet connection
      - a wired network connection via usb c -> rj45 dongle
      - hostname: turing
2. the current workstation should have access to all participating hardware
    - the primary connection method will likely be ssh via shared keys
    - ssh connection is assumed to be over internal wireless network
3. all related juniper project applications are available, externally as
    - docker hub containers
    - pypi packages
    - github source code

the procedural structure of the primer should include, at the least, the following elements:

- pre-configuration and setup work needed for cluster nodes.
- the install of k8s and all of its dependencies and supporting software.
- the configuration of raspi arm cluster nodes as k8s resources as appropriate.
- the configuration of the dedicated ubuntu server as k8s resources as appropriate
- the configuration of the macbook pro as k8s resources as appropriate
- procedural flexibility to allow inclusion or exclusion of any of these hardware categories
- best-practice informed architecture and configuration choices for k8s storage, networking, and compute
- detailed discussion of alternative choices, their strengths and weakness, and why the chosed solutions were selected
- hardening and production preparation of the cluster nodes, server, and macbook pro.
- hardening and production preparation of the k8s configuration
- automation of k8s cluster install, configuration, and maintenance.
- monitoring of health and performance for hardware, k8s resources, and juniper project code.
- go-live implementation including a full, end-to-end processing of actual juniper workloads.

this primer should be written as a markdown file in the notes/ directory and validated by consensus with particular attention paid to technical correctness and preventing hallucinations.

merge approval granted.
```

## Leads to verify (unchecked: from the originating session's knowledge)

### Hardware

- The Pi 5 SoC is the BCM2712, a **4-core** Cortex-A76, but the request says 8-core. Measure it, and don't repeat "8-core" unless the measurement supports it.
- No Intel MacBook Pro has 12 physical cores. A 2019 16" i7 has 6 cores and 12 threads, and takes up to 64 GB. Measure it.
- macOS cannot run a kubelet. The Mac can join only as a Linux VM, bridged on the USB-C Ethernet (bridging over Wi-Fi is unreliable), or serve as an admin client only. Handle sleep and lid-close (`pmset`) and VM autostart.
- Pi 5 caveats:
  - USB current is capped at 600 mA without a 5 A PSU (`usb_max_current_enable`), so a USB SATA SSD can brown out.
  - Some USB-SATA bridges have UAS quirks.
  - NVMe boot needs the EEPROM `BOOT_ORDER` set.
  - Raspberry Pi OS boots a 16K-page kernel on the Pi 5, which breaks some jemalloc-linked arm64 images; `kernel=kernel8.img` switches to 4K pages.
  - The memory cgroup may need `cgroup_enable=memory` on the kernel command line.
  - The RTC needs its optional battery, so chrony must sync before etcd or TLS starts.
- Ubuntu 26.04: confirm that a Pi 5 image exists and that containerd and kubeadm packages are available for it.

### Networking

- The nodes are dual-homed: Wi-Fi carries the default route, and a wired switch connects the hardware. kubeadm, kubelet and the CNI auto-detect the default-route interface, so pin `advertiseAddress`, kubelet `node-ip` and the CNI interface to the wired NIC.
- The workstation reaches the nodes over Wi-Fi, so the apiserver `certSANs` and the VIP's reachability must cover it.
- L2 load-balancer announcements (MetalLB or kube-vip ARP) belong on the wired segment.
- The switch may have no DHCP server, in which case configure static addresses with netplan.

### Kubernetes currency (check before writing)

- Current minor version (kubernetes.io/releases), the per-minor pkgs.k8s.io apt repos, containerd 2.x vs 1.x support, cgroup v1 removal, and NodeSwap / `failSwapOn`.
- ingress-nginx's retirement was announced in 2025-11, with best-effort maintenance until 2026-03, so prefer a Gateway API implementation.
- Promtail is EOL, so use Grafana Alloy. The 2025 Bitnami catalog changes break charts that pull `docker.io/bitnami/*`.
- Distribution (kubeadm vs k3s vs RKE2 vs k0s vs Talos vs MicroK8s): check each one's Pi 5 and Ubuntu 26.04 support.
- Storage (Longhorn vs Rook-Ceph vs OpenEBS vs local-path vs NFS/CSI from the server): check arm64 support and RAM overhead on 8 GB Pis.

### Juniper

- Images: the request says Docker Hub, but `Juniper/CLAUDE.md` records juniper-data images on GHCR. Before any pull, resolve the registry, names, tags and **per-arch manifests** (`docker buildx imagetools inspect <ref>`). Keep amd64-only images off the Pis (`kubernetes.io/arch`).
- juniper-deploy probably has Helm charts (memories: Helm chart version convention; `global.imageRegistry` leaks into subcharts). Go-live should deploy those, not invented manifests.
- Current releases are in the data-contract section of `Juniper/CLAUDE.md` (data 0.16.0, canopy 0.8.1, cascor 0.11.0, ml 0.10.0); re-probe PyPI.
- Go-live end to end: data generates, cascor trains (via data-client and `JUNIPER_DATA_URL`), and canopy monitors (`CASCOR_SERVICE_URL`). Health is `/v1/health`. Set **both** `max_epochs` and `output_epochs` (juniper-ml `AGENTS.md` hazard). NPZ artifacts carry three partitions.
- The repo already uses SOPS+age (`.sops.yaml`), a natural fit for GitOps secrets (e.g. Flux's SOPS decryption).

## Verification (start of the new thread)

```bash
git fetch -q origin && git log --oneline -1 origin/main
gh pr list --repo pcalnon/juniper-ml --head docs/k8s-primer-handoff --state all
ls notes | grep -iE 'kube|k8s'   # expect no existing primer
find /home/pcalnon/Development/python/Juniper/juniper-deploy -name Chart.yaml
```

## Git state at handoff

- The originating worktree is `.claude/worktrees/zany-juggling-goblet`, on `main`, and was clean before this file.
- This file lands via a PR from `docs/k8s-primer-handoff`, created as a GitHub-signed API commit. The originating session did **not** merge it.
