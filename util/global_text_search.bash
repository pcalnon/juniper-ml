#!/usr/bin/env bash
#########################################################################################################################################################################################################
#
# Notes:
#     grep
#         --exclude-dir juniper-legacy
#         --exclude-dir prompts
#         --exclude-dir logs
#         --exclude-dir reports
#         --exclude-dir notes
#         --exclude-dir docs
#         --exclude-dir util
#         --exclude-dir *.egg-info
#         --exclude-dir .mypy_cache
#         --exclude-dir .pytest_cache
#         --exclude-dir backups
#         --exclude-dir .serena
#
#         --exclude CHANGELOG.md
#         --exclude AGENTS.md
#         --exclude CLAUDE.md
#         --exclude .pre-commit-config.yaml
#
#         -rnI
#
#         "${SEARCH_TERM}"
#
#         "${SEARCH_DIR}"
#
#########################################################################################################################################################################################################

#########################################################################################################################################################################################################
# Define Script Constants
#########################################################################################################################################################################################################
SEARCH_LOCATION_DEFAULT="."

SEARCH_TERM_DEFAULT=""
EXCLUDE_DIR_PARAMS=""
EXCLUDE_FILE_PARAMS=""


#########################################################################################################################################################################################################
# Define grep command line parameters
#########################################################################################################################################################################################################
GREP_PARAMS_DIR_RECURSE="-r"
GREP_PARAMS_LINE_NUMBER="-n"
GREP_PARAMS_SKIP_BINARY="-I"

EXCLUDE_DIR_FLAG="--exclude-dir"
EXCLUDE_FILE_FLAG="--exclude"


#########################################################################################################################################################################################################
# Specify Files to exclude from Source Code String Search
#########################################################################################################################################################################################################
declare -a EXCLUDE_DIRS
echo "Pre-Initialized Exclude Dirs Array Length: ${#EXCLUDE_DIRS[@]}"
EXCLUDE_DIRS+=('juniper-legacy')
EXCLUDE_DIRS+=('prompts')
EXCLUDE_DIRS+=('logs')
EXCLUDE_DIRS+=('reports')
EXCLUDE_DIRS+=('notes')
EXCLUDE_DIRS+=('docs')
EXCLUDE_DIRS+=('util')
EXCLUDE_DIRS+=('*.egg-info')
EXCLUDE_DIRS+=('.mypy_cache')
EXCLUDE_DIRS+=('.pytest_cache')
EXCLUDE_DIRS+=('backups')
EXCLUDE_DIRS+=('.serena')
echo "Post-Initialized Exclude Dirs Array Length: ${#EXCLUDE_DIRS[@]}"
for DIRNAME in "${EXCLUDE_DIRS[@]}"; do
    echo "Excluding Dirname: \"${DIRNAME}\""
    EXCLUDE_DIR_PARAMS+="${EXCLUDE_DIR_FLAG} ${DIRNAME} "
done


#########################################################################################################################################################################################################
# Specify Files to exclude from Source Code String Search
#########################################################################################################################################################################################################
declare -a EXCLUDE_FILES
echo "Pre-Initialized Exclude Files Array Length: ${#EXCLUDE_FILES[@]}"

EXCLUDE_FILES+=('CHANGELOG.md')
EXCLUDE_FILES+=('AGENTS.md')
EXCLUDE_FILES+=('CLAUDE.md')
EXCLUDE_FILES+=('.pre-commit-config.yaml')

echo "Post-Initialized Exclude Files Array Length: ${#EXCLUDE_FILES[@]}"

for FILENAME in "${EXCLUDE_FILES[@]}"; do
    echo "Excluding Filename: \"${FILENAME}\""
    EXCLUDE_FILE_PARAMS+="${EXCLUDE_FILE_FLAG} ${FILENAME} "
done


#########################################################################################################################################################################################################
# Parse Script Input Parameters
#########################################################################################################################################################################################################
if [[ "$1" == "${SEARCH_TERM_DEFAULT}" ]]; then
    echo "Error: Source Code Search Term NOT Provided. Exiting..."
    exit 1
fi
SEARCH_TERM="$1"

SEARCH_LOCATION="${SEARCH_LOCATION_DEFAULT}"
if [[ "$2" != "" ]]; then
    SEARCH_LOCATION="$2"
fi


#########################################################################################################################################################################################################
#
# grep --exclude-dir juniper-legacy --exclude-dir prompts --exclude-dir logs --exclude-dir reports --exclude-dir notes --exclude-dir docs --exclude-dir util --exclude-dir *.egg-info --exclude-dir .mypy_cache --exclude-dir .pytest_cache --exclude-dir backups --exclude-dir .serena --exclude CHANGELOG.md --exclude AGENTS.md --exclude CLAUDE.md --exclude .pre-commit-config.yaml -rnI "remote_client" .
#########################################################################################################################################################################################################

echo "Executing grep command for search term in source code files."

echo "grep ${EXCLUDE_DIR_PARAMS} ${EXCLUDE_FILE_PARAMS} ${GREP_PARAMS_DIR_RECURSE} ${GREP_PARAMS_LINE_NUMBER} ${GREP_PARAMS_SKIP_BINARY} ${SEARCH_TERM} ${SEARCH_LOCATION}"
grep ${EXCLUDE_DIR_PARAMS} ${EXCLUDE_FILE_PARAMS} ${GREP_PARAMS_DIR_RECURSE} ${GREP_PARAMS_LINE_NUMBER} ${GREP_PARAMS_SKIP_BINARY} "${SEARCH_TERM}" ${SEARCH_LOCATION}

echo "Completed Executing grep command for search term in source code files."
