#!/usr/bin/env bash

echo "Running Test 000"
./wake_the_claude.bash  --id --worktree --skip-permissions --path "../../../Juniper/juniper-ml/scripts/test_prompt-000.md" -- --effort high --print
echo "Completed Launching Test 000"

echo "Sleepytime"
sleep 12

TEST_000_SESSION_FILE="$(ls -atr *.txt | tail -1)"
RESUME_ID="${TEST_000_SESSION_FILE}"

echo "Running Test 001"
./wake_the_claude.bash  --resume "${RESUME_ID}" --worktree --skip-permissions --path "../../../Juniper/juniper-ml/scripts/test_prompt-001.md" -- --effort high --print
echo "Completed Launching Test 001"


echo "Sleepytime"
sleep 12

cat nohup.out
