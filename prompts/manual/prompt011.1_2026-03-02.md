# Slack Startup problem, Investigate and Fix

## Primary Objective

Continue investigating and fixing Slack launch failures on Ubuntu 25.10 (Wayland, NVIDIA RTX 2080).

## Completed so far

- Full root cause analysis performed and presented to user
- Root Cause 1 (PRIMARY): NVIDIA kernel module 580.126.09 is loaded, but ALL userspace packages are missing (libnvidia-gl-580, nvidia-driver-580-open, nvidia-utils-580).
  - OpenGL falls back to llvmpipe (CPU), Vulkan shows CPU-only device.
  - Electron's GPU process crashes → window created but never becomes visible under Wayland (isVisible: false)
- Root Cause 2: Unrelated Debian package slack (v1:0.15.2-11, "configuration management for lazy admins") in config-files state, leaving /etc/slack.conf and /etc/cron.daily/slack
- Root Cause 3: Dual Slack installation — apt slack-desktop v4.47.69 AND snap slack v4.46.99. Two .desktop files in launcher
- User chose "Fixes only, no reboot" option
- sudo authentication failed from Claude Code terminal — commands need to be run manually

## Remaining work

- User needs to run these 3 commands in a regular terminal:
  a. sudo apt install -y nvidia-driver-580-open
  b. sudo dpkg --purge slack
  c. sudo snap remove slack
- User needs to reboot afterward
- Post-reboot verification:
  a. Run nvidia-smi, glxinfo | grep "OpenGL renderer" (should show NVIDIA, not llvmpipe)
  b. Run slack to confirm window appears
- If Slack still fails after NVIDIA fix, investigate Electron/Wayland flags as secondary fix
  a. --ozone-platform=wayland
  b. --enable-features=UseOzonePlatform

## Key context

- System: Ubuntu 25.10 (Questing Quokka), kernel 6.17.0-14-generic, Wayland, NVIDIA RTX 2080 (PCI 10de:1e87)
- NVIDIA kernel module: /lib/modules/6.17.0-14-generic/kernel/nvidia-580-open/nvidia.ko v580.126.09
- Slack apt binary: /usr/lib/slack/slack (symlinked from /usr/bin/slack), Electron-based v4.47.69
- Slack apt source: <https://packagecloud.io/slacktechnologies/slack/debian/> (jessie)
- Critical Slack error log: ERROR:components/viz/service/main/viz_main_impl.cc:189] Exiting GPU process due to errors during initialization
- Slack config at ~/.config/Slack/ — not corrupt, just can't render without GPU

---

## Launch Command

```bash
claude --dangerously-skip-permissions --rename "P11.1: Slack Startup problem, Investigate and Fix"
```

---
