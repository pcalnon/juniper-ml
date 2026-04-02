#!/usr/bin/env bash

JUNIPER_PROJECT_WORKTREE_DIR="${HOME}/Development/python/Juniper/worktrees"
JUNIPER_WORKTREE_NAME="juniper-canopy-cascor--fix--connect-canopy-cascor--$(date +%Y%m%d-%H%M)--$(uuidgen)"
JUNIPER_WORKTREE_NEW="${JUNIPER_PROJECT_WORKTREE_DIR}/${JUNIPER_WORKTREE_NAME}"

CONDA_ROOT_DIR="/opt/miniforge3/etc/profile.d"
CONDA_ACTIVATE_SCRIPT="conda.sh"
CONDA_ACTIVATE="${CONDA_ROOT_DIR}/${CONDA_ACTIVATE_SCRIPT}"

CONDA_ENV_NAME="JuniperCascor"

# Verify worktree doesn't already exist
if [[ -d "${JUNIPER_WORKTREE_NEW}" ]]; then
    echo "Error: Unable to add new worktree: \"${JUNIPER_WORKTREE_NAME}\"."
    echo "Error: Worktree directory already exists: \"${JUNIPER_WORKTREE_NEW}}\""
    exit 1
fi

# Create the new worktree
echo "git worktree add \"${JUNIPER_WORKTREE_NEW}\""
git worktree add "${JUNIPER_WORKTREE_NEW}"

# Verify new worktree
if [[ ! ( -d "${JUNIPER_WORKTREE_NEW}" ) ]]; then
    echo "Error: Failed to Add New Worktree: \"${JUNIPER_WORKTREE_NAME}\"."
    exit 1
fi

echo "cd \"${JUNIPER_WORKTREE_NEW}\""
cd "${JUNIPER_WORKTREE_NEW}" || exit
pwd

# source /opt/miniforge3/etc/profile.d/conda.sh && conda activate JuniperCascor
# echo "source \"${CONDA_ACTIVATE}\""
# shellcheck source=/dev/null
source "${CONDA_ACTIVATE}"

# echo "conda activate \"${CONDA_ENV_NAME}\""
conda activate "${CONDA_ENV_NAME}"

# exec conda activate "${CONDA_ENV_NAME}"
exec bash
