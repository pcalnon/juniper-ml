#!/usr/bin/env bash


COUNTER=0
OLD_IFS="${IFS}"
IFS=$'\n'

for i in $(git worktree list | grep "worktrees"); do
    COUNTER=$(( COUNTER + 1 ))
    echo "${COUNTER}: ${i}"
    WT="$(echo "${i}" | awk -F " " '{print $1;}')"
    echo "${COUNTER}. ${WT}"
    git worktree remove "${WT}"
done

IFS="${OLD_IFS}"
