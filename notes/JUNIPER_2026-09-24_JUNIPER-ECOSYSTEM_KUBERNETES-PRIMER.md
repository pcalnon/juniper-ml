# Kubernetes Primer: an End-to-End, Secure, Automated Juniper Cluster

**Project**: Juniper · **Scope**: ecosystem (juniper-deploy chart, all service images) · **Author**: Paul Calnon (drafted with Claude Code) · **Date**: 2026-09-24
**Status**: procedure of record, not yet executed on the hardware. **Version facts verified**: 2026-09-24 (§0.4). Anything this primer did not verify is marked **VERIFY**.

This is a procedure, not a survey. It runs as ordered phases, and each phase has three layers:

- **Architecture**: what gets built, and where it sits.
- **Analysis**: why this choice, what the alternatives are, and what can go wrong.
- **Commands**: what to type. Unless a step says otherwise, run it from the workstation. Commands tagged `[node]` run on a cluster node over ssh.

Placeholders appear in angle brackets (`<server>`, `<pi-01>`, `<vip>`, `<wired-cidr>`). Fill them in from the inventory (§0.3). **Never commit real addresses, tokens or keys to a public repository**, and keep secrets SOPS-encrypted (§8).

---

## 0. Before you start

### 0.1 Hardware as specified vs hardware as it will measure

These are the owner's specifications. Two of them conflict with the manufacturers' published specifications, so measure every host before sizing anything.

| Host | As specified | Primary-source / measured correction | Measure with |
|------|--------------|--------------------------------------|--------------|
| Dedicated server `<server>` | Ubuntu 26.04 server, Intel 8-core, 64 GB ECC, 1 TB SSD, Wi-Fi uplink, wired LAN | Not measured (no inventory entry yet) | `nproc; lscpu \| grep -E 'Model name\|Thread\|Core'; free -g; lsblk -d -o NAME,SIZE,ROTA,TRAN; ip -br a; cat /etc/os-release` |
| Raspberry Pi 5 ×8 `<pi-01>`…`<pi-08>` | "8-core ARM", 8 GB, SATA-over-USB or NVMe-HAT SSD | **Quad-core**: the BCM2712 is a "2.4GHz quad-core 64-bit Arm Cortex-A76" (raspberrypi.com product page, fetched 2026-09-24). An 8-node cluster has 32 cores, not 64. | same as server, plus `vcgencmd get_throttled; getconf PAGESIZE` |
| MacBook Pro `turing` | Intel, "12 core", 64 GB, Sequoia, Wi-Fi + USB-C→RJ45 | Likely **6 physical cores / 12 threads** (the 16" 2019 i7 tops out at 64 GB). Unverified: `turing` was unreachable (`No route to host`) on 2026-09-24. | `sysctl -n hw.physicalcpu hw.logicalcpu hw.memsize machdep.cpu.brand_string; sw_vers` |

**macOS cannot run a kubelet.** `turing` can take part only as a **Linux VM** (§4), or as an admin client.

### 0.2 Hardware profiles: include or exclude any category

Every phase is written against Ansible **inventory groups** (§1.4), so dropping a hardware category means leaving its group empty. The control-plane (CP) layout is the only thing that changes with the profile.

| Profile | Control plane | Workers | CP HA? | Notes |
|---------|---------------|---------|--------|-------|
| Server only | `<server>` (untainted, also runs workloads) | none | **No.** Single etcd member; losing it loses the cluster. | Longhorn replication gives nothing here; use local-path (§6). |
| Pi only | `<pi-01..03>` | `<pi-04..08>` | **Yes.** 3 etcd members, tolerates 1 loss. | Needs SSD boot on all three CPs (§3). |
| Mac VM only | the VM | none | **No.** | A laptop is not a production host. Use this for lab work only. |
| Server + Pi | `<pi-01..03>` | `<server>`, `<pi-04..08>` | **Yes** | Recommended. The server's 64 GB goes to workloads, not etcd. |
| Server + Mac VM | `<server>` | Mac VM | **No.** Two members would be *worse* than one: etcd quorum is 2 of 2. | Never run an even-sized etcd. |
| Pi + Mac VM | `<pi-01..03>` | `<pi-04..08>`, Mac VM | **Yes** | |
| All three | `<pi-01..03>` | `<server>`, `<pi-04..08>`, Mac VM | **Yes** | The full target. |

Rules behind the table:

- etcd needs an **odd** member count (quorum is ⌊n/2⌋+1).
- The Mac VM is **never** a control-plane node: the laptop sleeps, travels, and depends on a USB dongle.
- The server is not the only CP in any HA profile, so the cluster survives the one host with the most eggs.
- If you have no Pis, you have **no control-plane HA**. It takes three always-on machines, and the server is one.

### 0.3 Inventory to fill in (keep the filled copy private)

| Name | Group(s) | Arch | Wired IF | Wired IP | Wi-Fi IP (ssh) | Boot disk | Measured cores / RAM |
|------|----------|------|----------|----------|----------------|-----------|----------------------|
| `<server>` | `server`, `workers` (or `control_plane` in the server-only / server + Mac profiles) | amd64 | `<enpXsY>` | `<wired-ip>` | `<wifi-ip>` | `<nvme0n1/sda>` | |
| `<pi-01>`…`<pi-03>` | `pis`, `control_plane` | arm64 | `eth0` | | | NVMe / USB-SATA | |
| `<pi-04>`…`<pi-08>` | `pis`, `workers` | arm64 | `eth0` | | | | |
| `<macvm>` | `macvm`, `workers` | amd64 | `<enp0s3>` (bridged to the dongle) | | | virtual disk | |
| VIP `<vip>` | control-plane endpoint | n/a | wired | `<vip>` | n/a | n/a | n/a |
| LB pool `<lb-range>` | MetalLB | n/a | wired | e.g. `<first>-<last>` | n/a | n/a | n/a |

Pick `<wired-cidr>` (for example a private /24) so that it does **not** overlap the Wi-Fi network, the pod CIDR `10.244.0.0/16`, or the service CIDR `10.96.0.0/12`. Reserve `<vip>` and `<lb-range>` outside any DHCP scope.

### 0.4 Versions verified on 2026-09-24

| Component | Chosen | Evidence (primary source, fetched 2026-09-24) |
|-----------|--------|-----------------------------------------------|
| Kubernetes | **v1.36.x** (1.36.4 at authoring) | kubernetes.io/releases lists 1.37 (1.37.0, released 2026-08-26), 1.36 (1.36.4) and 1.35 (1.35.8) as supported. 1.36 is chosen because Cilium's compatibility page e2e-tests **1.33–1.36**, not 1.37. Move to 1.37 once Cilium lists it (§9.3). |
| apt repo | `pkgs.k8s.io/core:/stable:/v1.36/deb/` | kubeadm install page. The repo is **per minor**, so an upgrade edits this line. |
| containerd | Ubuntu archive `containerd` **2.2.2** (`2.2.2-0ubuntu1.1`) | packages.ubuntu.com/resolute. Built for amd64 and arm64. |
| OS | Ubuntu **26.04.1 LTS** ("resolute"); Pis use `ubuntu-26.04.1-preinstalled-server-arm64+raspi.img.xz` | cdimage.ubuntu.com lists the raspi server image with Pi 5 support. The workstation itself reports Ubuntu 26.04.1 LTS. |
| CNI | Cilium **1.20.x** (1.20.2 latest) | github.com/cilium/cilium releases; maintained minors are 1.18–1.20. |
| Gateway API CRDs | **v1.6.1** (standard channel) | The Cilium Gateway API page's prerequisites. |
| Storage | Longhorn **1.12.x** (1.12.1) | longhorn.io install docs: AMD64 and ARM64; needs `open-iscsi`, `nfs-common`, `cryptsetup`, `dmsetup`. |
| Log shipper | Grafana **Alloy** | Grafana docs: "Promtail is end of life (EOL) as of March 2, 2026." |
| Ingress | **Gateway API**, not ingress-nginx | kubernetes.io blog, 2025-11-11: ingress-nginx best-effort maintenance ends March 2026, with no releases or security fixes after that. |
| Juniper images | `ghcr.io/pcalnon/juniper-{data:0.16.0, cascor:0.11.0, canopy:0.8.1, cascor-worker:0.6.1}` | `docker buildx imagetools inspect`: every one is a **linux/amd64 + linux/arm64** manifest list. Docker Hub `pcalnon/juniper-*` returns **404**, so the images are on **GHCR, not Docker Hub**. |

Charts not listed here (kube-vip, MetalLB, cert-manager, kube-prometheus-stack, Loki, Alloy, Flux) are **not pinned by this primer**. Resolve each one's current version when you install it, then pin it in Git (§8). An unpinned `helm install` is not reproducible.

### 0.5 Architecture at a glance

```text
            workstation (Wi-Fi)  ──ssh──►  every node's Wi-Fi IP  (Ansible, admin)
                  │
                  └─ssh -L 6443 tunnel─►  <vip>:6443 on the wired segment
   ┌──────────────────────── wired switch  <wired-cidr>  ────────────────────────┐
   │ pi-01 pi-02 pi-03   control plane: apiserver, etcd, kube-vip (VIP via ARP)    │
   │ pi-04 … pi-08       workers (arm64)                                            │
   │ server              worker (amd64, big memory: cascor pinned here)            │
   │ macvm               worker (amd64, bridged on the USB-C NIC)                   │
   │ MetalLB L2 pool <lb-range> → Cilium Gateway → canopy / grafana                │
   └─────────────────────────────────────────────────────────────────────────────┘
   Each node: Ubuntu 26.04 · containerd 2.2 · kubelet 1.36 · Cilium (eBPF, no kube-proxy)
   Storage: Longhorn on each node's SSD (RWO, replicated)
   GitOps: Flux ← private Git repo (SOPS/age-encrypted secrets)
   Observability: kube-prometheus-stack + Loki + Alloy; Juniper ServiceMonitors
```

### 0.6 Key decisions and the alternatives rejected

| Area | Chosen | Alternatives | Why chosen |
|------|--------|--------------|------------|
| Distribution | **kubeadm** + upstream debs | k3s, RKE2, k0s, Talos, MicroK8s | Upstream conformance, with arm64 and amd64 debs from pkgs.k8s.io; every component is explicit and hardenable; an 8 GB Pi has room for upstream's overhead. **k3s** is the strongest alternative: a single binary, lower RAM, built-in HA with embedded etcd, and much less toil. Pick it if operator time matters more than learning or controlling every flag. **RKE2** is CIS-hardened by default but heavier. **Talos** is immutable and API-only, which is excellent security, but **VERIFY Pi 5 support** in its SBC list; this primer did not confirm it. **MicroK8s** is snap-based, and dqlite HA has had operational rough edges. **k0s** is viable and similar to k3s. |
| Runtime | containerd (Ubuntu archive) | CRI-O, Docker Engine + cri-dockerd | containerd is the default CRI and ships in Ubuntu main for both architectures. |
| CNI | **Cilium**, kube-proxy replacement | Calico, Flannel | eBPF dataplane, NetworkPolicy plus L7 policy, Hubble flow visibility, and a built-in **Gateway API** implementation. Calico is equally production-grade (choose it if you want BGP to the switch). Flannel has no NetworkPolicy. |
| CP endpoint | **kube-vip** (static pod, ARP) | keepalived + HAProxy, a DNS round-robin | A single component, it runs as a pod, and it needs no extra host daemons. |
| LoadBalancer | **MetalLB** (L2) | Cilium LB-IPAM + L2 announcements | Cilium's L2 announcements are documented as **beta**. MetalLB L2 is the mature, widely deployed option. |
| North-south HTTP | **Gateway API via Cilium** | ingress-nginx (retired), Traefik, Envoy Gateway | ingress-nginx gets no security fixes after March 2026. Cilium already runs Envoy, so it adds no new controller. |
| Block storage | **Longhorn** (v1 data engine) | Rook-Ceph, OpenEBS, local-path, NFS-CSI from the server | Replicated RWO on commodity SSDs, arm64 support, a UI and backups. **Rook-Ceph** is more capable, but each OSD has large RAM needs, too much for 8 GB Pis. **local-path** has no replication; use it for server-only. **NFS from the server** makes the server a single point of failure for every volume. |
| GitOps | **Flux** + SOPS/age | Argo CD | Native SOPS decryption, and juniper-ml already uses SOPS+age (`.sops.yaml`). Argo CD has the better UI but needs a plugin for SOPS. |
| Host automation | **Ansible** | cloud-init only, Kubespray | Agentless over the ssh you already have. Kubespray is Ansible too, but it is large and hides the kubeadm steps this primer wants explicit. |

---

## 1. Workstation preparation

**Architecture.** The workstation is the only place humans act from. It holds ssh keys, the kubeconfig (reached through an ssh tunnel, §5.6), Ansible, Helm, Flux and SOPS. It is not a cluster member.

**Analysis.** Running everything from one host keeps the credentials in one place. The API server's VIP lives on the wired segment, and the workstation is on Wi-Fi. Rather than exposing 6443 on Wi-Fi, reach it through an **ssh local forward** via a CP node's Wi-Fi address. `127.0.0.1` is in the certificate's SANs, so TLS still validates.

### 1.1 Tools

```bash
# kubectl from the same per-minor repo the nodes use (§2.6), or pin a binary
sudo apt-get install -y ansible jq age
curl -fsSL https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-4 | bash   # helm.sh's documented installer (Helm 4)
curl -s https://fluxcd.io/install.sh | sudo bash                                         # installs the flux CLI
# sops: download the release binary for linux/amd64 from github.com/getsops/sops/releases and verify its checksum
# cilium CLI: follow docs.cilium.io "Cilium Quick Installation" → "Install the Cilium CLI"
```

GUI tools are optional and run on the workstation only: **Headlamp** or **k9s** (a TUI) against the tunnelled kubeconfig, **Grafana** via the Gateway (§10), and the **Longhorn UI** via `kubectl port-forward`.

### 1.2 ssh keys (one key per purpose)

```bash
ssh-keygen -t ed25519 -f ~/.ssh/juniper_cluster -C "juniper-cluster-admin"
for h in <server> <pi-01> <pi-02> <pi-03> <pi-04> <pi-05> <pi-06> <pi-07> <pi-08> <macvm>; do
  ssh-copy-id -i ~/.ssh/juniper_cluster.pub <admin-user>@"$h"
done
```

Add a `Host` block per node to `~/.ssh/config` (with `IdentityFile ~/.ssh/juniper_cluster`). Keep the addresses in that file, not in Git.

### 1.3 A private repository for cluster state

Create a **private** Git repository (placeholder `<cluster-repo>`) to hold the Ansible inventory, playbooks and Flux manifests. Everything with a real IP, hostname or encrypted secret goes there, not into this public repo.

### 1.4 Ansible inventory (`<cluster-repo>/inventory/hosts.yaml`)

```yaml
all:
  vars:
    ansible_user: <admin-user>
    ansible_ssh_private_key_file: ~/.ssh/juniper_cluster
    k8s_minor: "1.36"
    wired_cidr: "<wired-cidr>"
    pod_cidr: "10.244.0.0/16"
    workstation_ip: "<workstation-wifi-ip>"
  children:
    server:  { hosts: { <server>: { wired_if: <enpXsY>, wired_ip: <ip> } } }
    pis:
      hosts:
        <pi-01>: { wired_if: eth0, wired_ip: <ip> }
        # … <pi-08>
    macvm:   { hosts: { <macvm>: { wired_if: <enp0s3>, wired_ip: <ip> } } }
    control_plane: { hosts: { <pi-01>: {}, <pi-02>: {}, <pi-03>: {} } }   # per §0.2
    workers:       { hosts: { <server>: {}, <pi-04>: {}, <macvm>: {} } }  # … per §0.2
    k8s_cluster:   { children: { control_plane: {}, workers: {} } }
```

**To exclude a hardware category**, empty its group, and remove its hosts from `control_plane` / `workers`. No playbook changes.

---

## 2. Node pre-configuration (every Linux node)

**Architecture.** Every node, whether amd64, arm64 or VM, converges to the same baseline: Ubuntu 26.04, a static wired address, time sync, kernel prerequisites, containerd with the systemd cgroup driver, and kubelet/kubeadm/kubectl pinned to 1.36.

**Analysis: the dual-homing trap.** Each node has a Wi-Fi interface that carries the default route and a wired interface on the switch. kubeadm, the kubelet and CNIs **auto-detect the default-route interface**, so left alone they would advertise the Wi-Fi address and put cluster traffic on Wi-Fi. This primer pins the wired address in four places: kubeadm `advertiseAddress`, kubelet `node-ip` (§5.2), Cilium `devices` (§5.4), and kube-vip / MetalLB interfaces (§5.1, §6.2). If you can give the switch an internet uplink, removing Wi-Fi from the nodes entirely is simpler and more secure.

### 2.1 Static wired addressing (netplan) `[node]`

A switch with no DHCP server needs static addresses. Do **not** set a gateway on the wired interface, so the default route stays on Wi-Fi.

```yaml
# /etc/netplan/60-wired.yaml   (chmod 600)
network:
  version: 2
  ethernets:
    <wired-if>:
      dhcp4: false
      addresses: [<wired-ip>/<prefix>]
```

```bash
sudo netplan try && sudo netplan apply
ip -br a; ip route        # default via the Wi-Fi interface; <wired-cidr> via <wired-if>
```

Make hostnames resolvable over the wired network: either local DNS on your router, or an Ansible-managed `/etc/hosts` block. Every node needs a **unique hostname, MAC address and `/sys/class/dmi/id/product_uuid`** (kubeadm requirement); cloned VMs are the usual violator.

### 2.2 Time `[node]`

etcd leases and TLS validity depend on the clock. The Pi 5's RTC keeps time only with its optional battery.

```bash
sudo apt-get install -y chrony        # may already be the default time daemon on 26.04: check `timedatectl`
chronyc tracking                       # "Leap status : Normal" before continuing
sudo systemctl enable chrony-wait.service 2>/dev/null || true   # VERIFY the unit ships in the 26.04 chrony package
sudo mkdir -p /etc/systemd/system/kubelet.service.d
printf '[Unit]\nWants=time-sync.target\nAfter=time-sync.target\n' | sudo tee /etc/systemd/system/kubelet.service.d/10-time-sync.conf
```

### 2.3 Swap, kernel modules, sysctls `[node]`

The kubelet's default is to **fail to start if swap is detected**. Disable it; do not tolerate it.

```bash
sudo swapoff -a && sudo sed -ri '/\sswap\s/s/^/#/' /etc/fstab
systemctl list-units --type swap        # none may remain (Ubuntu images can ship /swap.img)
cat <<'EOF' | sudo tee /etc/modules-load.d/k8s.conf
overlay
br_netfilter
EOF
sudo modprobe overlay; sudo modprobe br_netfilter
cat <<'EOF' | sudo tee /etc/sysctl.d/90-k8s.conf
net.ipv4.ip_forward = 1
net.bridge.bridge-nf-call-iptables = 1
net.bridge.bridge-nf-call-ip6tables = 1
# required by kubelet protectKernelDefaults (§5.2)
vm.overcommit_memory = 1
vm.panic_on_oom = 0
kernel.panic = 10
kernel.panic_on_oops = 1
EOF
sudo sysctl --system
stat -fc %T /sys/fs/cgroup     # must print cgroup2fs: cgroup v2 is required in practice (§0.4 docs recommend the systemd driver on v2)
```

### 2.4 containerd 2.2 `[node]`

```bash
sudo apt-get install -y containerd
sudo mkdir -p /etc/containerd
containerd config default | sudo tee /etc/containerd/config.toml >/dev/null
sudo sed -i 's/SystemdCgroup = false/SystemdCgroup = true/' /etc/containerd/config.toml
grep -n 'SystemdCgroup' /etc/containerd/config.toml       # must show "= true" under the runc options table
sudo systemctl restart containerd && sudo systemctl enable containerd
```

If `grep` shows no `SystemdCgroup` line, containerd 2.x's default dump left the key out. Add `SystemdCgroup = true` under `[plugins.'io.containerd.cri.v1.runtime'.containerd.runtimes.runc.options]` (containerd 2.x, config version 3) and restart. After installing kubeadm (§2.6), compare the pause image it expects (`kubeadm config images list | grep pause`) with the sandbox image in `config.toml` (`grep -n pause`), and align them to silence kubeadm's warning.

### 2.5 Longhorn and host prerequisites `[node]`

```bash
sudo apt-get install -y open-iscsi nfs-common cryptsetup dmsetup
sudo systemctl enable --now iscsid
sudo modprobe iscsi_tcp && echo iscsi_tcp | sudo tee /etc/modules-load.d/iscsi.conf
```

On the Pis, if `modprobe iscsi_tcp` fails, the module lives in the raspi kernel's extra-modules package. **VERIFY** its exact name with `apt-cache search linux-modules-extra | grep raspi`.

### 2.6 kubelet / kubeadm / kubectl 1.36 `[node]`

```bash
sudo apt-get install -y apt-transport-https ca-certificates curl gpg
sudo mkdir -p -m 755 /etc/apt/keyrings
curl -fsSL https://pkgs.k8s.io/core:/stable:/v1.36/deb/Release.key | sudo gpg --dearmor -o /etc/apt/keyrings/kubernetes-apt-keyring.gpg
echo 'deb [signed-by=/etc/apt/keyrings/kubernetes-apt-keyring.gpg] https://pkgs.k8s.io/core:/stable:/v1.36/deb/ /' | sudo tee /etc/apt/sources.list.d/kubernetes.list
sudo apt-get update && sudo apt-get install -y kubelet kubeadm kubectl
sudo apt-mark hold kubelet kubeadm kubectl        # upgrades happen deliberately (§9.3), never via unattended-upgrades
sudo systemctl enable kubelet                      # it crash-loops until kubeadm init/join; that is expected
```

---

## 3. Raspberry Pi 5 nodes

**Architecture.** Eight Pi 5s (4 × Cortex-A76, 8 GB each), booting Ubuntu 26.04 raspi server **from the SSD**. `<pi-01..03>` form the control plane in every HA profile, and the rest are workers.

**Analysis.**

- **etcd needs a real SSD.** It fsyncs on every write, and SD cards give slow, erratic latency. Boot the CP Pis from NVMe (best) or USB-SATA.
- **Power.** The Pi 5 specifies **5 V / 5 A** over USB-C PD. With a lesser supply, firmware caps USB current, and a USB-SATA SSD can brown out under load. Use the official 27 W supply, or an NVMe HAT, which is powered from the board. `usb_max_current_enable=1` in `config.txt` lifts the cap, but that **only** makes sense when the supply really delivers 5 A.
- **USB-SATA bridges.** Some bridges misbehave with UAS. If `dmesg` shows resets, add a `usb-storage.quirks=<vid>:<pid>:u` quirk (IDs from `lsusb`) to `cmdline.txt`.
- **Page size.** Raspberry Pi OS boots a 16K-page kernel on the Pi 5, and some jemalloc-linked arm64 images crash on it. **Ubuntu's raspi kernel is used here**, so check `getconf PAGESIZE` on the booted Pi: `4096` is the expected result. If it prints `16384`, fix that before scheduling workloads.
- **Memory cgroup.** Verify `grep -w memory /sys/fs/cgroup/cgroup.controllers`. If it is absent, append `cgroup_enable=memory cgroup_memory=1` to `/boot/firmware/cmdline.txt` and reboot.
- **Thermals.** A throttling Pi misses etcd heartbeats. Use active cooling, and watch `vcgencmd get_throttled` (it should print `throttled=0x0`) plus the node-exporter temperature (§10).

### 3.1 Flash and first boot

```bash
# on the workstation: write the image to the SSD itself (NVMe or SATA in a USB enclosure)
xz -dc ubuntu-26.04.1-preinstalled-server-arm64+raspi.img.xz | sudo dd of=/dev/<ssd> bs=4M conv=fsync status=progress
# optionally seed cloud-init user-data (ssh key, hostname) on the system-boot partition before first boot
```

### 3.2 Bootloader: boot order and PCIe `[node]`

```bash
sudo apt-get install -y rpi-eeprom
sudo rpi-eeprom-update                                  # update the bootloader first if it is old
sudo -E rpi-eeprom-config --edit
#   BOOT_ORDER=0xf416     # read right to left: 6 = NVMe, then 1 = SD, then 4 = USB, f = restart the loop
#   PCIE_PROBE=1          # only for non-HAT+ NVMe adapters that the firmware does not detect
sudo reboot
```

For a USB-SATA boot with **no SD card inserted**, the default order already reaches USB. Verify the change with `rpi-eeprom-config | grep BOOT_ORDER`.

### 3.3 Apply §2, then check

```bash
getconf PAGESIZE; grep -w memory /sys/fs/cgroup/cgroup.controllers; vcgencmd get_throttled
lsblk -d -o NAME,SIZE,TRAN,MODEL; sudo fio --name=etcd --rw=write --ioengine=sync --fdatasync=1 --size=22m --bs=2300 --directory=/var/lib 2>/dev/null | grep -A7 'fsync/fdatasync'
```

The `fio` probe is the one etcd's maintainers suggest: the 99th-percentile `fdatasync` should be **under 10 ms**. If it is not, that Pi does not belong in `control_plane`.

---

## 4. MacBook Pro `turing` as a worker VM

**Architecture.** `turing` runs one Ubuntu 26.04 server **amd64 VM** with a bridged NIC on the **USB-C→RJ45 dongle**. The VM becomes a normal worker. macOS itself is only a host and an admin client.

**Analysis.**

- **Bridge on the wired dongle, never Wi-Fi.** Most Wi-Fi access points drop frames from a second MAC address on one station, so bridging over Wi-Fi is unreliable.
- **VM size.** Measure first (§0.1). Leave at least 4 threads and 16 GB to macOS, so a 12-thread / 64 GB machine gives roughly 8 vCPU and 44 GB.
- **Hypervisor.** VirtualBox and UTM (QEMU) both run on Intel Macs and both offer bridged networking. VirtualBox is used below because `VBoxManage` scripts headless start cleanly.
- **Sleep and lid.** A sleeping host freezes the VM, and the node goes `NotReady`, which is why it is a worker only. Keep it on AC with the lid open, or accept that the node comes and goes.
- **Security.** The Mac becomes infrastructure, so apply the macOS hardening in §7.1.

### 4.1 Host settings (on `turing`)

```bash
sudo pmset -c sleep 0 disksleep 0 standby 0 autorestart 1   # on AC power: never sleep, restart after power loss
pmset -g                                                    # confirm
```

Closing the lid still sleeps a Mac with no external display. The undocumented `sudo pmset -a disablesleep 1` changes that, but it is unsupported, so **VERIFY** it on Sequoia before relying on it.

### 4.2 Create and autostart the VM

```bash
VBoxManage createvm --name juniper-macvm --ostype Ubuntu_64 --register
VBoxManage modifyvm juniper-macvm --cpus <n> --memory <MiB> --nic1 bridged --bridgeadapter1 "<enX: USB 10/100/1000 LAN>"
# attach a disk and the ubuntu-26.04.1-live-server-amd64.iso, install, then detach the ISO
VBoxManage startvm juniper-macvm --type headless
```

For autostart at boot, add a LaunchDaemon (`/Library/LaunchDaemons/local.juniper-macvm.plist`, `RunAtLoad` true) that runs `/usr/local/bin/VBoxManage startvm juniper-macvm --type headless` as the user that owns the VM. Then apply §2 inside the VM.

---

## 5. Kubernetes install: HA control plane with kubeadm

**Architecture.** Three stacked-etcd control-plane nodes (`<pi-01..03>`, or `<server>` alone in non-HA profiles) behind a **kube-vip** VIP. The cluster uses **Cilium** as CNI in kube-proxy-replacement mode, with secrets encrypted at rest and API audit logging from the first boot.

**Analysis.** Encryption at rest and auditing are cheap to set up at `init` and awkward to retrofit (existing Secrets must be rewritten). `serverTLSBootstrap` gives kubelets CA-signed serving certificates, so metrics-server and Prometheus never need `--kubelet-insecure-tls`. kube-proxy is skipped because Cilium replaces it, and the Cilium Gateway requires that.

### 5.1 kube-vip static pod (first CP, before `init`) `[node]`

```bash
export VIP=<vip> INTERFACE=<wired-if>
export KVVERSION=$(curl -sL https://api.github.com/repos/kube-vip/kube-vip/releases | jq -r '.[0].name')
sudo ctr image pull ghcr.io/kube-vip/kube-vip:$KVVERSION
sudo ctr run --rm --net-host ghcr.io/kube-vip/kube-vip:$KVVERSION vip /kube-vip manifest pod \
  --interface $INTERFACE --address $VIP --controlplane --arp --leaderElection \
  | sudo tee /etc/kubernetes/manifests/kube-vip.yaml
```

On Kubernetes ≥ 1.29, `admin.conf` has no cluster-admin rights until `kubeadm init` finishes, so kube-vip cannot lead during the first init. On the **first** CP only, point the manifest at `super-admin.conf` for the init, and revert it afterwards (§5.3):

```bash
sudo sed -i 's#path: /etc/kubernetes/admin.conf#path: /etc/kubernetes/super-admin.conf#' /etc/kubernetes/manifests/kube-vip.yaml
```

### 5.2 Encryption, audit and kubeadm config (every CP) `[node]`

```bash
sudo mkdir -p /etc/kubernetes/enc /etc/kubernetes/audit /var/log/kubernetes/audit
KEY=$(head -c 32 /dev/urandom | base64)      # generate ONCE; copy the same file to every CP
cat <<EOF | sudo tee /etc/kubernetes/enc/encryption-config.yaml
apiVersion: apiserver.config.k8s.io/v1
kind: EncryptionConfiguration
resources:
  - resources: ["secrets"]
    providers:
      - secretbox:
          keys:
            - name: key1
              secret: ${KEY}
      - identity: {}
EOF
sudo chmod 600 /etc/kubernetes/enc/encryption-config.yaml
cat <<'EOF' | sudo tee /etc/kubernetes/audit/policy.yaml
apiVersion: audit.k8s.io/v1
kind: Policy
omitStages: ["RequestReceived"]
rules:
  - level: Metadata
    resources: [{ group: "", resources: ["secrets", "configmaps"] }]
  - level: None
    nonResourceURLs: ["/healthz*", "/livez*", "/readyz*", "/version"]
  - level: Metadata
EOF
```

**Back up the encryption key off-cluster**, SOPS-encrypted (§8). Losing it makes every Secret in an etcd backup unreadable.

`kubeadm-init.yaml` (first CP):

```yaml
apiVersion: kubeadm.k8s.io/v1beta4
kind: InitConfiguration
localAPIEndpoint:
  advertiseAddress: <cp1-wired-ip>
  bindPort: 6443
nodeRegistration:
  criSocket: unix:///run/containerd/containerd.sock
  kubeletExtraArgs:
    - name: node-ip
      value: <cp1-wired-ip>
skipPhases:
  - addon/kube-proxy
---
apiVersion: kubeadm.k8s.io/v1beta4
kind: ClusterConfiguration
kubernetesVersion: v1.36.4
clusterName: juniper
controlPlaneEndpoint: "<vip>:6443"
networking:
  podSubnet: 10.244.0.0/16
  serviceSubnet: 10.96.0.0/12
etcd:
  local:
    extraArgs:
      - { name: listen-metrics-urls, value: "http://0.0.0.0:2381" }   # lets Prometheus scrape etcd (§10.4); §7.1 keeps it off Wi-Fi
apiServer:
  certSANs: ["<vip>", "127.0.0.1", "localhost"]
  extraArgs:
    - { name: encryption-provider-config, value: /etc/kubernetes/enc/encryption-config.yaml }
    - { name: audit-policy-file, value: /etc/kubernetes/audit/policy.yaml }
    - { name: audit-log-path, value: /var/log/kubernetes/audit/audit.log }
    - { name: audit-log-maxage, value: "30" }
    - { name: audit-log-maxbackup, value: "10" }
    - { name: audit-log-maxsize, value: "100" }
  extraVolumes:
    - { name: enc, hostPath: /etc/kubernetes/enc, mountPath: /etc/kubernetes/enc, readOnly: true, pathType: DirectoryOrCreate }
    - { name: audit-policy, hostPath: /etc/kubernetes/audit, mountPath: /etc/kubernetes/audit, readOnly: true, pathType: DirectoryOrCreate }
    - { name: audit-log, hostPath: /var/log/kubernetes/audit, mountPath: /var/log/kubernetes/audit, readOnly: false, pathType: DirectoryOrCreate }
---
apiVersion: kubelet.config.k8s.io/v1beta1
kind: KubeletConfiguration
cgroupDriver: systemd
serverTLSBootstrap: true
rotateCertificates: true
seccompDefault: true
protectKernelDefaults: true
```

`extraArgs` and `extraVolumes` are name/value **lists** in `v1beta4`; the `v1beta3` map form is rejected. The `ClusterConfiguration` applies to every CP that joins later, so the `enc/` and `audit/` files must exist on each CP **before** it joins.

### 5.3 Initialise the first CP `[node]`

```bash
sudo kubeadm config validate --config kubeadm-init.yaml
sudo kubeadm init --config kubeadm-init.yaml --upload-certs | tee ~/kubeadm-init.log
```

Then restore kube-vip's normal kubeconfig and set up `kubectl` on the node:

```bash
sudo sed -i 's#path: /etc/kubernetes/super-admin.conf#path: /etc/kubernetes/admin.conf#' /etc/kubernetes/manifests/kube-vip.yaml
mkdir -p ~/.kube && sudo cp /etc/kubernetes/admin.conf ~/.kube/config && sudo chown "$(id -u):$(id -g)" ~/.kube/config
```

Nodes stay `NotReady` until Cilium is installed (§5.4); install it next, before joining the others.

### 5.4 Cilium

Install the Gateway API CRDs (v1.6.1, standard channel) **first**. Cilium enables its Gateway controller only if the CRDs exist when it starts; if they were added later, restart the operator.

```bash
for c in gatewayclasses gateways httproutes referencegrants grpcroutes backendtlspolicies tlsroutes; do
  kubectl apply --server-side -f https://raw.githubusercontent.com/kubernetes-sigs/gateway-api/v1.6.1/config/crd/standard/gateway.networking.k8s.io_${c}.yaml
done
```

```bash
helm repo add cilium https://helm.cilium.io && helm repo update
helm install cilium cilium/cilium --version <1.20.x> -n kube-system \
  --set kubeProxyReplacement=true \
  --set k8sServiceHost=<vip> --set k8sServicePort=6443 \
  --set ipam.mode=kubernetes \
  --set devices='{<wired-if-regex>}' \
  --set gatewayAPI.enabled=true \
  --set hubble.relay.enabled=true --set hubble.ui.enabled=true \
  --set operator.replicas=2
cilium status --wait
```

- **`ipam.mode=kubernetes`** is essential. Cilium's default `cluster-pool` IPAM ignores kubeadm's `podSubnet` and allocates from its own range.
- **`devices`** pins the dataplane to the wired NICs. The names differ between Pi (`eth0`), server and VM, so pass a pattern that matches all of them (for example `{eth0,enp+}`). **VERIFY** the wildcard syntax against your Cilium version's Helm reference.

### 5.5 Join the other nodes `[node]`

On CP1, print fresh credentials (tokens expire after 24 h, and the uploaded certs after 2 h):

```bash
kubeadm token create --print-join-command
sudo kubeadm init phase upload-certs --upload-certs      # prints the certificate key
```

`kubeadm-join.yaml` (per node; drop the `controlPlane` block for workers):

```yaml
apiVersion: kubeadm.k8s.io/v1beta4
kind: JoinConfiguration
discovery:
  bootstrapToken:
    apiServerEndpoint: <vip>:6443
    token: <token>
    caCertHashes: ["sha256:<hash>"]
nodeRegistration:
  kubeletExtraArgs:
    - name: node-ip
      value: <this-node-wired-ip>
controlPlane:
  localAPIEndpoint:
    advertiseAddress: <this-node-wired-ip>
  certificateKey: <certificate-key>
```

On CP2 and CP3, run §5.1 **without** the `super-admin.conf` edit and put the §5.2 files in place, then `sudo kubeadm join --config kubeadm-join.yaml`. Workers need only §2 plus the join. Afterwards, approve the kubelet serving CSRs (they come from `serverTLSBootstrap`):

```bash
kubectl get csr | awk '/kubelet-serving/ && /Pending/ {print $1}' | xargs -r kubectl certificate approve
```

Approve these **only** after checking that each requester is one of your nodes. For steady state, deploy an approver that validates the requester (for example postfinance `kubelet-csr-approver`) rather than approving blindly.

### 5.6 Workstation access through an ssh tunnel

```bash
scp <pi-01>:.kube/config ~/.kube/juniper.conf
sed -i 's#server: https://.*:6443#server: https://127.0.0.1:6443#' ~/.kube/juniper.conf
ssh -fN -L 6443:<vip>:6443 <pi-01>                 # <pi-01> reached over its Wi-Fi address
KUBECONFIG=~/.kube/juniper.conf kubectl get nodes -o wide   # INTERNAL-IP must be the WIRED address on every node
```

`admin.conf` is a break-glass credential. For daily work, create a dedicated user or ServiceAccount with the least role it needs (§7.2).

---

## 6. Storage, load balancing, gateway and TLS

**Architecture.** Longhorn provides replicated block volumes on every node's SSD and is the default StorageClass. MetalLB hands out LoadBalancer IPs from `<lb-range>` via ARP on the wired segment. A single Cilium `Gateway` terminates TLS with certificates from cert-manager's private CA.

**Analysis.**

- **Replica count.** 2 replicas is the practical default with 8 Pis. 3 is safer, but each replica costs disk and write bandwidth over 1 GbE.
- **Placement.** Keep the Mac VM out of storage (below): a laptop node that disappears should not hold replicas.
- **Backups.** Longhorn backups must go **off-cluster**: an NFS export on a host that is not a node, or S3-compatible storage. A snapshot on the same disks is not a backup.
- **TLS.** `.local` / internal names cannot get public ACME certificates without public DNS, so a private CA is used here. Distribute its root certificate to the workstation's trust store.

### 6.1 Longhorn

```bash
# BEFORE installing: label every storage node. The Mac VM stays unlabelled, so it gets no disk and no replicas.
for n in <server> <pi-01> <pi-02> <pi-03> <pi-04> <pi-05> <pi-06> <pi-07> <pi-08>; do kubectl label node "$n" node.longhorn.io/create-default-disk=true; done
helm repo add longhorn https://charts.longhorn.io && helm repo update
helm install longhorn longhorn/longhorn --version <1.12.x> -n longhorn-system --create-namespace \
  --set persistence.defaultClassReplicaCount=2 \
  --set defaultSettings.defaultDataPath=/var/lib/longhorn \
  --set defaultSettings.createDefaultDiskLabeledNodes=true
kubectl -n longhorn-system rollout status deploy/longhorn-driver-deployer
```

**Server-only profile:** use `rancher/local-path-provisioner` instead, since replication across one node is meaningless.

### 6.2 MetalLB (L2 on the wired segment)

```bash
helm repo add metallb https://metallb.github.io/metallb && helm install metallb metallb/metallb -n metallb-system --create-namespace
cat <<'EOF' | kubectl apply -f -
apiVersion: metallb.io/v1beta1
kind: IPAddressPool
metadata: { name: wired, namespace: metallb-system }
spec: { addresses: ["<lb-range>"] }
---
apiVersion: metallb.io/v1beta1
kind: L2Advertisement
metadata: { name: wired, namespace: metallb-system }
spec: { ipAddressPools: ["wired"], interfaces: ["<wired-if>"] }
EOF
```

### 6.3 cert-manager and a private CA

```bash
helm upgrade --install cert-manager oci://quay.io/jetstack/charts/cert-manager -n cert-manager --create-namespace \
  --set crds.enabled=true \
  --set config.gatewayAPI.enabled=true
```

Create a self-signed `ClusterIssuer` that issues a CA `Certificate` (`isCA: true`), then a CA `ClusterIssuer` named `juniper-ca` from that secret. Install the CA's `tls.crt` into the workstation's trust store.

### 6.4 The Gateway

```yaml
apiVersion: gateway.networking.k8s.io/v1
kind: Gateway
metadata:
  name: juniper
  namespace: juniper
  annotations: { cert-manager.io/cluster-issuer: juniper-ca }
spec:
  gatewayClassName: cilium
  listeners:
    - name: https
      protocol: HTTPS
      port: 443
      hostname: "*.juniper.<internal-domain>"
      tls: { mode: Terminate, certificateRefs: [{ name: juniper-wildcard-tls }] }
      allowedRoutes:
        namespaces:
          from: Selector
          selector:
            matchExpressions:
              - { key: kubernetes.io/metadata.name, operator: In, values: [juniper, monitoring] }
```

The Gateway gets a MetalLB IP. Point `canopy.juniper.<internal-domain>` (and `grafana…`) at that IP in local DNS.

---

## 7. Hardening

### 7.1 Hosts (Ansible role `harden`)

**Analysis.** Wi-Fi is the untrusted side, so restrict it to ssh from the workstation. The wired segment and the pod CIDR carry cluster traffic, so allow them wholesale. **Host firewalls are a classic source of Kubernetes breakage**, so run `cilium connectivity test` after enabling one.

```bash
sudo ufw default deny incoming && sudo ufw default allow outgoing && sudo ufw default allow routed
sudo ufw allow in on <wired-if> from <wired-cidr>
sudo ufw allow from 10.244.0.0/16                       # pods → host (kubelet, node-exporter, apiserver on CPs)
sudo ufw allow in on <wifi-if> from <workstation-wifi-ip> to any port 22 proto tcp
sudo ufw enable
```

- **sshd** (`/etc/ssh/sshd_config.d/10-harden.conf`): `PasswordAuthentication no`, `KbdInteractiveAuthentication no`, `PermitRootLogin no`, `AllowUsers <admin-user>`.
- **Patching**: `unattended-upgrades` for security updates. The kube packages stay held (§2.6). Deploy **kured** so nodes that need a reboot drain and reboot one at a time.
- **Accounts**: remove the default `ubuntu` password login on the Pis, and keep the admin's sudo behind the key-only login.
- **Mac host** (`turing`): FileVault on, macOS firewall on (System Settings → Network → Firewall), automatic security updates, and Remote Login restricted to the admin user.

### 7.2 Kubernetes

| Control | How |
|---------|-----|
| Secrets at rest | Done at init (§5.2). Verify: `kubectl create secret generic t -n default --from-literal=a=b`, then run `etcdctl get /registry/secrets/default/t` on a CP, through the §9.2 `crictl exec` form with its TLS flags. The raw value must start with `k8s:enc:secretbox:v1:key1`. |
| Audit log | Done at init. Ship `/var/log/kubernetes/audit/` to Loki (§10.2). |
| Pod Security Admission | Label namespaces `pod-security.kubernetes.io/enforce=baseline`, plus `warn=restricted` and `audit=restricted`. The Juniper chart sets non-root, read-only root, and drops all capabilities, but it **sets no `seccompProfile`**, so `restricted` enforcement would reject its pods until the chart adds `RuntimeDefault`. |
| NetworkPolicy | The Juniper chart ships default-deny plus per-service policies (`networkPolicies.enabled: true`). Apply default-deny to the platform namespaces too, where their charts support it. |
| RBAC | No daily use of `admin.conf`; per-person least-privilege Roles; a read-only `ClusterRole` for GUI tools. |
| Supply chain | Pin image tags (the chart already does, DEPLOY-15). Consider digest pins and a policy engine (Kyverno) to reject `:latest` and unsigned images. |
| Benchmark | `kubectl apply -f https://raw.githubusercontent.com/aquasecurity/kube-bench/main/job.yaml`, then `kubectl logs job/kube-bench`. Triage each FAIL, and record accepted exceptions in `<cluster-repo>`. |
| etcd | Only on CP nodes; peer/client TLS comes from kubeadm by default; snapshots in §9.2. |

---

## 8. Automation and GitOps

**Architecture.** Two layers.

- **Ansible** converges hosts: §2, §3, §7.1, joins, upgrades.
- **Flux** converges everything inside the cluster from `<cluster-repo>`: MetalLB pools, Longhorn, cert-manager, the Gateway, monitoring, and the Juniper release.

Secrets live in Git **encrypted with SOPS/age**. Flux decrypts them in-cluster with a key that never leaves the cluster and the owner's offline backup.

**Analysis.** Helm commands in §5 and §6 bootstrap the cluster once. After Flux is running, the same releases move into Git as `HelmRelease` objects, and manual `helm upgrade` stops. Drift then shows up as a Git diff, or Flux reverts it. Use a **dedicated age key for the cluster**, not the key that encrypts juniper-ml's `.env`, so one leak does not compromise the other.

### 8.1 Playbooks (in `<cluster-repo>`)

| Playbook | Does | Idempotent check |
|----------|------|------------------|
| `prepare.yml` | §2 (+ §3 on `pis`) | `--check --diff` shows no change on a converged node |
| `harden.yml` | §7.1 | ditto |
| `join.yml` | fetches a join command from CP1 (`kubeadm token create --print-join-command`, delegated), skips nodes where `/etc/kubernetes/kubelet.conf` exists | re-run is a no-op |
| `upgrade.yml` | §9.3, `serial: 1`, drain → upgrade → uncordon | |

A minimal task shape (the rest follows the same pattern):

```yaml
- hosts: k8s_cluster
  become: true
  tasks:
    - name: kube repo
      ansible.builtin.copy:
        dest: /etc/apt/sources.list.d/kubernetes.list
        content: "deb [signed-by=/etc/apt/keyrings/kubernetes-apt-keyring.gpg] https://pkgs.k8s.io/core:/stable:/v{{ k8s_minor }}/deb/ /\n"
    - name: kube packages held
      ansible.builtin.dpkg_selections: { name: "{{ item }}", selection: hold }
      loop: [kubelet, kubeadm, kubectl]
```

### 8.2 Flux bootstrap with SOPS

```bash
age-keygen -o juniper-cluster.agekey                       # back this file up OFFLINE; never commit it
kubectl create namespace flux-system
kubectl -n flux-system create secret generic sops-age --from-file=age.agekey=juniper-cluster.agekey
export GITHUB_TOKEN=<fine-grained PAT, this repo only>
flux bootstrap github --owner=pcalnon --repository=<cluster-repo> --private=true --personal --path=clusters/juniper
```

The `Kustomization` that holds secrets must enable decryption:

```yaml
spec:
  decryption:
    provider: sops
    secretRef: { name: sops-age }
```

`.sops.yaml` in `<cluster-repo>` should encrypt only `data`/`stringData` (`encrypted_regex: ^(data|stringData)$`) with the cluster's age public key, so diffs stay reviewable.

---

## 9. Day-2 maintenance

### 9.1 Health checks

```bash
kubectl get nodes -o wide; kubectl get pods -A | grep -v -E 'Running|Completed'
cilium status; kubectl -n longhorn-system get volumes.longhorn.io
flux get all -A | grep -v True
```

### 9.2 etcd snapshots (on a CP, via Ansible timer or cron)

```bash
sudo crictl exec $(sudo crictl ps --name etcd -q) etcdctl \
  --endpoints=https://127.0.0.1:2379 --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt --key=/etc/kubernetes/pki/etcd/server.key \
  snapshot save /var/lib/etcd/snapshot-$(date +%F).db
```

`/var/lib/etcd` is the etcd pod's hostPath, so the snapshot lands on the host. Copy it off-cluster, together with `/etc/kubernetes/pki` and the encryption config. Without the key, the Secrets in the snapshot are unreadable (§5.2). **Rehearse a restore** on a scratch VM once. A backup that was never restored is untested.

### 9.3 Kubernetes minor upgrades (one minor at a time)

1. Read the target's changelog. Confirm Cilium, Longhorn and MetalLB support it.
2. Edit the apt line from `v1.36` to `v1.37` on every node.
3. First CP: `apt-mark unhold kubeadm && apt-get install -y kubeadm='1.37.*' && apt-mark hold kubeadm`, then `kubeadm upgrade plan`, then `kubeadm upgrade apply v1.37.<z>`.
4. Other CPs: install the same kubeadm, then `kubeadm upgrade node`.
5. Workers: install the same kubeadm, then `sudo kubeadm upgrade node`. That step upgrades the node's local kubelet configuration.
6. Every node, one at a time (CPs first): `kubectl drain <n> --ignore-daemonsets --delete-emptydir-data`, upgrade the kubelet and kubectl, `systemctl daemon-reload && systemctl restart kubelet`, then `kubectl uncordon <n>`.

`upgrade.yml` (§8.1) encodes steps 3–6 with `serial: 1`.

### 9.4 Certificates

kubeadm's client certificates last one year, and a `kubeadm upgrade apply` renews them. Check with `kubeadm certs check-expiration`. Alert on expiry in Prometheus rather than discovering it.

---

## 10. Monitoring: hardware, Kubernetes, Juniper

**Architecture.** The monitoring stack runs in its own `monitoring` namespace:

- **kube-prometheus-stack**: Prometheus, Alertmanager, Grafana, node-exporter on every node (CPU, memory, disk, network, **temperature** via hwmon), and kube-state-metrics.
- **Loki** (single binary) with **Grafana Alloy** as the log agent.
- **Juniper services** expose `/metrics` (juniper-observability), scraped through the chart's `ServiceMonitor`s.

**Analysis: two chart traps.**

1. The Juniper chart **bundles** kube-prometheus-stack **72.6.3**, which is old, and `values-production.yaml` **turns it on**. Set `kube-prometheus-stack.enabled=false` **explicitly** in `values-cluster.yaml` (§11), and run the stack separately; otherwise its CRDs collide with the separate release.
2. The chart's NetworkPolicies admit Prometheus **only when the bundled subchart is enabled**, and only from a `podSelector` in the **same namespace**. A Prometheus in `monitoring` is blocked, so add the policy in §10.3. In addition:
   - The ServiceMonitors need the label that the stack's `serviceMonitorSelector` matches, which is `release: <kps-release-name>` by default.
   - juniper-data's `/metrics` has an **IP allowlist** (`JUNIPER_DATA_METRICS_TRUSTED_IPS`) that must include the pod CIDR.

### 10.1 kube-prometheus-stack

```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm install kps prometheus-community/kube-prometheus-stack -n monitoring --create-namespace \
  --set prometheus.prometheusSpec.retention=15d \
  --set prometheus.prometheusSpec.storageSpec.volumeClaimTemplate.spec.resources.requests.storage=50Gi \
  --set grafana.admin.existingSecret=grafana-admin
```

Pin the Prometheus pod to `<server>` with a `nodeSelector` when the server is present: it is the heaviest tenant. Hardware SMART data needs `smartctl-exporter`, but many USB-SATA bridges do not pass SMART through, so check `smartctl -a /dev/sda` first.

### 10.2 Loki and Alloy

Since 2026-03-16 the open-source Loki chart is published as **`grafana-community/loki`**. `grafana/loki` is maintained only for Grafana Enterprise Logs (grafana/loki#20705). In the community chart, `deploymentMode: SingleBinary` still works but is deprecated in favour of `Monolithic`. **VERIFY** the values keys for your chart version against its `values.yaml`.

Loki values (`loki-values.yaml`; monolithic mode):

```yaml
deploymentMode: SingleBinary
loki:
  auth_enabled: false
  commonConfig: { replication_factor: 1 }
  storage: { type: filesystem }
  schemaConfig:
    configs:
      - from: "2024-04-01"
        store: tsdb
        object_store: filesystem
        schema: v13
        index: { prefix: loki_index_, period: 24h }
singleBinary: { replicas: 1, persistence: { enabled: true, size: 20Gi } }
backend: { replicas: 0 }
read: { replicas: 0 }
write: { replicas: 0 }
chunksCache: { enabled: false }
resultsCache: { enabled: false }
```

Alloy config (`alloy.configMap.content` in the `grafana/alloy` chart). `loki.source.kubernetes` tails pods **through the API server**, so it runs as **one Deployment replica** (`controller.type: deployment`, `controller.replicas: 1`). The chart's default DaemonSet without clustering would collect every line once per node. Alloy syntax needs **one attribute per line**:

```alloy
discovery.kubernetes "pods" { role = "pod" }
discovery.relabel "pods" {
  targets = discovery.kubernetes.pods.targets
  rule {
    source_labels = ["__meta_kubernetes_namespace"]
    target_label  = "namespace"
  }
  rule {
    source_labels = ["__meta_kubernetes_pod_name"]
    target_label  = "pod"
  }
  rule {
    source_labels = ["__meta_kubernetes_pod_container_name"]
    target_label  = "container"
  }
}
loki.source.kubernetes "pods" {
  targets    = discovery.relabel.pods.output
  forward_to = [loki.write.default.receiver]
}
loki.write "default" {
  endpoint { url = "http://loki-gateway.monitoring.svc/loki/api/v1/push" }
}
```

```bash
helm repo add grafana https://grafana.github.io/helm-charts
helm repo add grafana-community https://grafana-community.github.io/helm-charts
helm install loki grafana-community/loki -n monitoring -f loki-values.yaml
helm install alloy grafana/alloy -n monitoring -f alloy-values.yaml
```

For the audit log, add a `local.file_match` + `loki.source.file` pipeline, running on CP nodes only, that reads `/var/log/kubernetes/audit/*.log` from a hostPath mount.

### 10.3 Let Prometheus scrape Juniper

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata: { name: allow-monitoring-scrape, namespace: juniper }
spec:
  podSelector: {}
  policyTypes: [Ingress]
  ingress:
    - from:
        - namespaceSelector: { matchLabels: { kubernetes.io/metadata.name: monitoring } }
      ports: [{ port: 8100, protocol: TCP }, { port: 8200, protocol: TCP }, { port: 8050, protocol: TCP }]
```

### 10.4 What to alert on (minimum)

| Signal | Source |
|--------|--------|
| Node down, NotReady, disk > 85 %, memory pressure | node-exporter / kube-state-metrics (stack defaults) |
| Pi temperature > 80 °C or throttling | node-exporter `node_hwmon_temp_celsius` |
| etcd leader changes, fsync p99 > 10 ms | stack's etcd rules (needs etcd metrics reachable; kubeadm binds them to `127.0.0.1:2381`, so §5.2's `etcd.local.extraArgs` sets `listen-metrics-urls` to `http://0.0.0.0:2381`. On a cluster initialised without it, edit `kubeadm-config` and re-run `kubeadm init phase etcd local --config <file>` on each CP in turn (kubernetes.io "Reconfiguring a kubeadm cluster")) |
| Certificate expiry < 30 d | apiserver client-cert metrics |
| Juniper `/v1/health/ready` failing, error rate, training stalled | Juniper ServiceMonitors + readiness probes |
| Longhorn volume degraded | Longhorn ServiceMonitor |

---

## 11. Go-live: deploy Juniper and run a real workload end to end

**Architecture.** The Juniper Helm chart is the one in `juniper-deploy/k8s/helm/juniper` (chart 1.1.0). It deploys **data** (8100), **cascor** (8200), **canopy** (8050) and **cascor-worker** (HPA 2–8, or 4–16 in `values-production.yaml`). All four images are multi-arch on `ghcr.io/pcalnon`, so they schedule on Pis and x86 alike. The end-to-end flow:

- juniper-data generates a dataset: an NPZ with **six** keys, `X_/y_` × `train`, `val`, `test`.
- cascor fetches it through `JUNIPER_DATA_URL` and trains, using the workers.
- canopy monitors through `CASCOR_SERVICE_URL`, and users reach it via the Gateway.

**Analysis: fix these before `helm install`.** Each was found in the chart on 2026-09-24.

1. **Redis is a Bitnami subchart** (`redis-20.7.1`, image `docker.io/bitnami/redis:7.4.2-debian-12-r2`). Bitnami moved versioned images to the unmaintained `bitnamilegacy` catalog in 2025, so this pull is expected to fail. canopy only receives `REDIS_URL` when `redis.enabled` is true, and uses it for a Redis status endpoint. **Set `redis.enabled=false`** for go-live. Never ship the `bitnamilegacy` override to production: it gets no updates.
2. **The juniper-data tag.** juniper-deploy `main` pins `0.16.0` since juniper-deploy#230 (2026-09-24); older clones show `0.15.0`. Confirm with `grep -n 'tag:' k8s/helm/juniper/values.yaml` after cloning.
3. **The ingress is an `Ingress`**, and ingress-nginx is retired. Set `canopy.ingress.enabled=false` and route through the Gateway (below). canopy's NetworkPolicy already admits any source on 8050.
4. **Secrets**: set `secrets.create=false` and `secrets.existingSecret=juniper-secrets`. Create that Secret from a SOPS-encrypted manifest in `<cluster-repo>` with the keys the chart expects: `juniper_data_api_keys`, `juniper_cascor_api_keys`, `canopy_api_key`, `cascor_sentry_dsn`, `grafana_admin_password`, `juniper_data_api_key`, `cascor_auth_token`. **Two pairs must agree:**
   - Workers send `cascor_auth_token` as `X-API-Key`, and cascor checks it against `juniper_cascor_api_keys`. A mismatch closes the worker socket with 4001.
   - cascor sends `juniper_data_api_key` to juniper-data, which checks it against `juniper_data_api_keys`.

   `grafana_admin_password` is not consumed by any chart template.
5. **Monitoring**: set `kube-prometheus-stack.enabled=false` (see §10 trap 1), and `serviceMonitor.enabled=true` with `serviceMonitor.labels.release=kps`, plus `*_METRICS_ENABLED=true` (`values-production.yaml` already does this), and add §10.3.
6. **Placement**: pin cascor to the server (`cascor.nodeSelector: { kubernetes.io/hostname: <server> }`) when it exists. It is the CPU- and memory-heavy trainer (production limits: 4 CPU / 4 Gi). Workers spread across the Pis.
7. **PSA**: `juniper` is `enforce=baseline` (§7.2).
8. **metrics-server**: the worker HPA scales on CPU through the resource-metrics API, which kube-prometheus-stack does not provide. Install metrics-server (`helm repo add metrics-server https://kubernetes-sigs.github.io/metrics-server/ && helm install metrics-server metrics-server/metrics-server -n kube-system`). It verifies kubelet TLS because of `serverTLSBootstrap` (§5.2). Check with `kubectl top nodes`.

### 11.1 Install

```bash
kubectl create namespace juniper
kubectl label namespace juniper pod-security.kubernetes.io/enforce=baseline pod-security.kubernetes.io/warn=restricted pod-security.kubernetes.io/audit=restricted
git clone https://github.com/pcalnon/juniper-deploy.git && cd juniper-deploy
helm dependency build k8s/helm/juniper
helm lint k8s/helm/juniper -f k8s/helm/juniper/values-production.yaml -f <cluster-repo>/juniper/values-cluster.yaml
helm upgrade --install juniper k8s/helm/juniper -n juniper \
  -f k8s/helm/juniper/values-production.yaml -f <cluster-repo>/juniper/values-cluster.yaml --wait --timeout 10m
kubectl -n juniper get pods -o wide              # note which arch each pod landed on
```

`values-cluster.yaml` carries items 1–6 above (item 8 is a separate install). In steady state this becomes a Flux `HelmRelease` pointing at the chart in the juniper-deploy Git repository.

Route canopy through the Gateway:

```yaml
apiVersion: gateway.networking.k8s.io/v1
kind: HTTPRoute
metadata: { name: canopy, namespace: juniper }
spec:
  parentRefs: [{ name: juniper }]
  hostnames: ["canopy.juniper.<internal-domain>"]
  rules: [{ backendRefs: [{ name: juniper-canopy, port: 8050 }] }]
```

The chart names the service `juniper-canopy` for a release named `juniper` (check with `kubectl -n juniper get svc`). canopy uses **WebSockets**, so confirm that its live updates work through the Gateway (browser dev tools show a `101 Switching Protocols`).

### 11.2 Health gates

```bash
for s in data:8100 cascor:8200 canopy:8050; do
  svc=$(kubectl -n juniper get svc -o name | grep "${s%%:*}" | head -1)
  kubectl -n juniper port-forward "$svc" 18080:"${s##*:}" >/dev/null & pf=$!; sleep 2
  curl -fsS localhost:18080/v1/health/ready && echo " ← ${s%%:*} ready"; kill $pf
done
```

### 11.3 End-to-end workload

**Two calls, not one.** On `POST /v1/training/start`, a `dataset.generator` builds the data **inside cascor**, and the route ignores `dataset.source` / `url`, so juniper-data would never see the request (`juniper-cascor/src/api/routes/training.py`). To exercise data → cascor:

1. **Stage** a juniper-data dataset with `POST /v1/training/dataset` (`StageDatasetRequest`). Its `params` are forwarded verbatim to juniper-data. `spirals` is cascor's alias for juniper-data's `spiral` generator, and `n_points_per_spiral` / `seed` are `SpiralParams` fields.
2. **Start** training, which consumes the staged config.

**Set BOTH `max_epochs` and `output_epochs`, to the same value.** Otherwise the service trains later output passes with `output_epochs` (default 10000), not the budget you asked for (juniper-ml `AGENTS.md` hazard).

```bash
kubectl -n juniper port-forward svc/juniper-cascor 18200:8200 &
KEY=<one of juniper_cascor_api_keys>
H=(-H "X-API-Key: $KEY" -H 'Content-Type: application/json')
curl -fsS -X POST localhost:18200/v1/training/dataset "${H[@]}" -d '{
  "dataset_type": "spirals", "n_spirals": 2, "noise": 0.1,
  "params": { "n_points_per_spiral": 200, "seed": 42 } }'
curl -fsS localhost:18200/v1/training/dataset/pending "${H[@]}" | jq .
curl -fsS -X POST localhost:18200/v1/training/start "${H[@]}" -d '{
  "start_fresh": true, "params": { "max_epochs": 500, "output_epochs": 500 } }'
curl -fsS localhost:18200/v1/training/status "${H[@]}" | jq .
```

**Go-live acceptance.** Every item must be observed, not assumed:

1. **Data generation.** juniper-data logs show the dataset created, and `GET /v1/datasets` on data lists it.
2. **Training.** cascor's `/v1/training/status` moves through training to completion, and its logs show the dataset fetched from `JUNIPER_DATA_URL`, not inline data.
3. **Workers.** `kubectl -n juniper get pods -l app.kubernetes.io/component=worker -o wide` shows workers on arm64 Pis, and cascor's worker endpoint lists them as connected.
4. **Monitoring.** canopy, via `https://canopy.juniper.<internal-domain>`, shows the run live. Grafana shows the Juniper metrics, and Loki holds all three services' logs.
5. **Persistence.** `kubectl -n juniper get pvc` shows `Bound` Longhorn volumes for cascor snapshots and logs, and they survive `kubectl -n juniper rollout restart deploy/juniper-cascor`. Restart only the pinned cascor: juniper-data's ReadWriteOnce volume can deadlock a rolling update that lands its new pod on another node. In a profile without `<server>`, cascor is unpinned and has two RWO volumes, so first pin it to one node with `cascor.nodeSelector: { kubernetes.io/hostname: <node> }` in `values-cluster.yaml`. A ReadWriteOnce volume can be mounted by several pods on the same node. The chart has no `strategy` value, so `Recreate` would need a post-renderer or an upstream chart change (§12).
6. **Resilience.** Drain one worker Pi mid-run (`kubectl drain`). The run continues, and the Pi's pods reschedule. In an HA profile, power off one CP: `kubectl get nodes` keeps answering through the VIP.

Record the outcome, including the pod-to-node placement and timings, in `<cluster-repo>` as the go-live record.

---

## 12. Known gaps and the things to VERIFY at execution time

- **Hardware.** The measurements in §0.1 are pending: `turing` was unreachable, and no Pi or server hostnames were available to the authoring session.
- **Unpinned charts** (§0.4): kube-vip, MetalLB, cert-manager, kube-prometheus-stack, Loki and Alloy. Pin each one in `<cluster-repo>` on first install.
- **Items marked VERIFY** in the text:
  - Talos Pi 5 support
  - the `chrony-wait` unit on 26.04
  - the raspi extra-modules package name
  - Cilium's `devices` wildcard syntax
  - the Longhorn disk-label setting
  - `pmset disablesleep` on Sequoia
- **Chart gaps** (fix upstream in juniper-deploy, not by forking values forever):
  - no `seccompProfile`, which blocks PSA `restricted`
  - Bitnami redis
  - a NetworkPolicy that cannot admit an external Prometheus
  - an `Ingress`-only north-south path
  - a bundled kube-prometheus-stack pinned at 72.6.3, which `values-production.yaml` turns on
  - no Deployment `strategy` value, so RWO-backed services cannot be switched to `Recreate`
- **Upgrade to Kubernetes 1.37** once Cilium's compatibility page lists it.
