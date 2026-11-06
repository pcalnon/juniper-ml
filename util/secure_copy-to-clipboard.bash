#!/usr/bin/bash

export TRUE=0
export FALSE=1

DEFAULT_INPUT="/home/pcalnon/.cache/yamaguchi-key-escrow-sheet.txt"

set +o history
export INPUT="${1:-"${DEFAULT_INPUT}"}"


# Validate the input is a file or a string
if [[ -f "${INPUT}" ]]; then
    echo "Secure Copy Input File: ${INPUT}"
    printf '%s' "$(<"${INPUT}")" | sha256sum | cut -c1-16
else
    echo "Secure Copy Input String:"
    read -rs v
    printf '%s' "${v}" | sha256sum | cut -c1-16
fi
unset v

set -o history
exit "${TRUE}"


