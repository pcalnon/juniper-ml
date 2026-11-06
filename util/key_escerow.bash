#!/usr/bin/bash

export TRUE=0
export FALSE=1

DEFAULT_PRINTER="HP_OfficeJet_Pro_6970_540AC0_USB"
DEFAULT_COPIES=3
DEFAULT_INPUT="/home/pcalnon/.cache/yamaguchi-key-escrow-sheet.txt"

set +o history
# Set the input, copies, and printer variables from the command line arguments or use defaults

export INPUT="${1:-"${DEFAULT_INPUT}"}" && shift
export COPIES="${1:-"${DEFAULT_COPIES}"}" && shift
export PRINTER="${1:-"${DEFAULT_PRINTER}"}" && shift

# Execute the yamaguchi key escrow script to get the key escrow sheet
python3 "${HOME}/Development/python/Juniper/juniper-ml/util/ad-hoc/yamaguchi_key_escrow.py" --execute

# Execute the secure copy to clipboard script to get the secure copy string
python3 "${HOME}/Development/python/Juniper/juniper-ml/util/ad-hoc/secure_copy-to-clipboard.py"


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

lpr -P "${PRINTER}" -# "${COPIES}" "${INPUT}"

ls -Fla /var/spool/cups

# Count .env* entries via glob (SC2010: avoid ls | grep; safe with odd filenames)
count_env_files() {
    local -a matches=()
    local saved_nullglob
    saved_nullglob="$(shopt -p nullglob)"
    shopt -s nullglob
    matches=(/home/duplicati/.config/Duplicati.empty-2026-09-20/.env*)
    eval "${saved_nullglob}"
    echo "${#matches[@]}"
}

count_env_files
shred -u /home/duplicati/.config/Duplicati.empty-2026-09-20/.env; echo "env shred exit=$?"
count_env_files


set -o history
exit "${TRUE}"


