#!/usr/bin/env bash

# TODO: Normalize this into a general purpose util script.

IFS=" "
for i in juniper-ml juniper-canopy juniper-cascor juniper-data juniper-data-client juniper-cascor-client juniper-cascor-worker juniper-deploy; do
    OLD_IFS="${IFS}"
    IFS=$'\n'
    cd ~/Development/python/Juniper/${i} || exit
    DIR="$(git worktree list | awk -F " " '{print $1;}')"
    for j in ${DIR}; do
        echo "Current worktree: ${j}"
        ls -Fla "${j}/notes/DOCUMENTATION_AUDIT_AND_UPGRADE_PLAN.md" 2>/dev/null
        echo " "
    done
done
IFS="${OLD_IFS}"
