#!/usr/bin/env bash
# Install the duplicati.service lane from this repository: wrapper, unit, defaults file, guard,
# the env contract, and the server-DB snapshot lane (script, unit, timer).
#
# Project:      juniper-ml
# Sub-Project:  backup infrastructure
# Author:       Paul Calnon
# Version:      1.5.1 (2026-10-08: Phase B round-6 fold-in -- see History)
# License:      MIT
#
# Copies, never symlinks: a symlink into a git checkout turns a branch switch or a worktree
# removal into a silent change of what the service executes. Run with sudo. Does NOT start,
# stop or restart any unit; prints the verification commands instead.
#
# Usage:  sudo bash util/install_duplicati_service.bash [--dry-run] [--update-backup-behavior]
#   --dry-run                 run every check and print every action; write nothing, reload nothing.
#                             Works without root, so a reviewer can rehearse it.
#   --update-backup-behavior  bless the repository's current contents when they differ from what
#                             was last blessed (D-6's escape hatch; see the drift gate below). An
#                             installed file that itself drifted is copied aside first, never lost.
#
# Step numbers below are the assessment's section 6.4 checklist
# (notes/JUNIPER_2026-10-03_JUNIPER-ECOSYSTEM_BACKUP-SYSTEM-STATE-ASSESSMENT-AND-RECOVERY-PLAN.md),
# whose numbering differs from the design's P0 -- say "assessment step N" when citing them.
#
# History:
#   1.0.0  2026-09-21  design draft; blessed-checksum drift gate (D-6, ruled 2026-09-22).
#   1.1.0  2026-10-03  (a) FIRST-INSTALL FIX: with no blessed file, blessed_for() returned 1 and
#                      `want="$(blessed_for …)"` under `set -e` ended the script silently before
#                      any install -- the never-blessed path is exactly this host's (assessment
#                      I-36, validation Lane B B-3). (b) The snapshot lane joins the blessed set
#                      (STOP item 5 / P0.5a item 2: installed copy, hardened unit). (c) The env
#                      contract deploys to /etc/duplicati/env, outside the data folder (round 3's
#                      D13), and is never overwritten once present. (d) --dry-run. (e) The hint
#                      at the end says `start`, never `restart`: the design's rule is that the
#                      old server is stopped once, by P0 step 2, and started by P0 step 10.
#   1.2.0  2026-10-03  Phase B validation fold-in (lanes B and C): (a) the "no secret in the
#                      contract" gate refuses every secret-shaped assignment, commented or not, and
#                      every option line naming a key, password or the two insecure-mode flags --
#                      the 1.1.0 gate matched three names and let SETTINGS_ENCRYPTION_KEY_OLD, a
#                      commented key and --settings-encryption-key= through; (b) an installed file
#                      that DRIFTED is copied to <dst>.drifted-<UTC> before --update-backup-behavior
#                      overwrites it (the drift was "the only evidence" and 1.1.0 destroyed it);
#                      (c) DUPLICATI_INSTALL_PREFIX, for the hermetic test suite only, prefixes every
#                      destination so the never-blessed, drift and kept-existing paths can be
#                      rehearsed against a scratch tree instead of this host's real files; (d) the
#                      dry run verifies the three unit files on a temp copy (ExecStart rewritten,
#                      advisory); (e) no .pyc is written by the syntax check; (f) the guard hint
#                      uses `env VAR=value` (sudoers refuses the bare prefix, round-4 B14).
#   1.3.0  2026-10-08  Phase B round-3 fold-in: (a) the contract's --option lines are judged by
#                      the WRAPPER ITSELF (--print-command against a scratch data folder), so the
#                      installer and the wrapper apply one rule -- the 1.2.0 HAZARD_OPTION regex
#                      was a second copy that missed --parameters-file (R3A D-1, R3C D-3) and five
#                      lines the wrapper refuses (R3C N-6), and refused a tunable the wrapper
#                      allows (--webservice-token-duration); an existing /etc/duplicati/env is
#                      judged the same way, since the new wrapper reads it at the next start;
#                      (b) the secret gates see through any run of `#` (`## KEY=...`) and refuse a
#                      secret-valued --option line even when commented (R3A N-5); (c) a first
#                      install over a file that was never blessed but differs from the repository
#                      copies it to <dst>.pre-install-<UTC> first (R3C N-7); (d) a NOTE when the
#                      snapshot destination is absent: the unit's ReadWritePaths= has no `-` by
#                      design, so it fails closed until the directory exists (R3C N-13); (e) the
#                      guard check is printed in the design's step-10 form -- URL read from the job,
#                      after the start -- not with a hand-typed URL (R3B N-1).
#   1.4.0  2026-10-08  Phase B round-4 fold-in: (a) the contract gate's empty DUPLICATI_REQUIRE_MOUNT
#                      now really switches the wrapper's mount check off (wrapper 2.4.0), so an
#                      unmounted drive no longer reads as "the wrapper refuses the contract" (R4A
#                      D-1); (b) an installed file that differs from the repository and was never
#                      blessed -- including when the blessed file is absent or empty -- is UNBLESSED
#                      and needs --update-backup-behavior, as drift does (R4C N-5); (c) a real run
#                      says where it copied a file aside (R4C N-3); (d) an existing /etc/duplicati/env
#                      must be root:duplicati, group-readable and writable by root only (R4C N-4);
#                      (e) the NOTE's key write is the design's `sudo test ! -e … | sudo tee` form
#                      (R4A N-6); (f) "Next:" prints the step-8 prerequisites before the start and
#                      step 10's guard block verbatim, `unset url id` and numeric id included (R4A
#                      N-1, R4B N-7).
#   1.5.0  2026-10-08  Phase B round-5 fold-in: (a) an existing /etc/duplicati/env passes as EITHER
#                      of O-12's two forms, root:duplicati 0640 or duplicati:duplicati 0600 -- the
#                      installer does not settle O-12; 1.4.0 enforced one side (R5A DEFECT-2) and
#                      admitted an other-readable 0644 (R5A NIT-1); a symlink is refused by name;
#                      (b) "Next:" says stop the unit, never pause, when the first start reads
#                      Running, and prints step 10's restart before resume (R5A DEFECT-1, R5B N-1);
#                      (c) the key NOTE names Procedure A's random …-key.new (R5A NIT-2).
#   1.5.1  2026-10-08  Phase B round-6 fold-in (R6 NIT-3): after "stop the unit", the hint says what
#                      comes next -- read the stored paused-until before starting again (D step 8).
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# DUPLICATI_INSTALL_PREFIX and DUPLICATI_INSTALL_BLESSED exist for the hermetic test suite only:
# they point every destination (and the blessed file) into a scratch tree. Production never sets them.
PREFIX="${DUPLICATI_INSTALL_PREFIX:-}"
WRAPPER_SRC="${REPO_DIR}/scripts/duplicati-wrapper.bash"
UNIT_SRC="${REPO_DIR}/util/systemd/duplicati.service"
DEFAULTS_SRC="${REPO_DIR}/util/systemd/duplicati.default"
GUARD_SRC="${REPO_DIR}/util/yamaguchi-pre-backup-guard.bash"
ENV_SRC="${REPO_DIR}/util/systemd/duplicati-env.contract"
SNAP_SRC="${REPO_DIR}/util/ad-hoc/yamaguchi_server_db_snapshot.py"
SNAP_UNIT_SRC="${REPO_DIR}/util/systemd/yamaguchi-server-db-snapshot.service"
SNAP_TIMER_SRC="${REPO_DIR}/util/systemd/yamaguchi-server-db-snapshot.timer"
LIB_DIR="${PREFIX}/usr/local/lib/duplicati"
CREDSTORE_DIR="${PREFIX}/etc/credstore"
WRAPPER_DST="${LIB_DIR}/duplicati-wrapper.bash"
UNIT_DST="${PREFIX}/etc/systemd/system/duplicati.service"
DEFAULTS_DST="${PREFIX}/etc/default/duplicati"
GUARD_DST="${LIB_DIR}/yamaguchi-pre-backup-guard.bash"
ENV_DIR="${PREFIX}/etc/duplicati"
ENV_DST="${ENV_DIR}/env"
SNAP_DST="${LIB_DIR}/yamaguchi_server_db_snapshot.py"
SNAP_UNIT_DST="${PREFIX}/etc/systemd/system/yamaguchi-server-db-snapshot.service"
SNAP_TIMER_DST="${PREFIX}/etc/systemd/system/yamaguchi-server-db-snapshot.timer"
DATA_FOLDER="${PREFIX}/home/duplicati/.config/Duplicati"
CRED_DST="${CREDSTORE_DIR}/duplicati-settings-key"
# The snapshot unit's ReadWritePaths= (yamaguchi-server-db-snapshot.service); checked, never created.
SNAP_DEST_DIR="${PREFIX}/home/pcalnon/.local/state/duplicati-server-db"
BLESSED="${DUPLICATI_INSTALL_BLESSED:-${LIB_DIR}/.blessed.sha256}"

# The blessed set: every file a root unit executes or reads, as SRC:DST:MODE. The env contract
# is NOT in it -- it is installed only when absent and an operator may change it afterwards.
PAIRS=(
    "${WRAPPER_SRC}:${WRAPPER_DST}:0755"
    "${UNIT_SRC}:${UNIT_DST}:0644"
    "${DEFAULTS_SRC}:${DEFAULTS_DST}:0644"
    "${GUARD_SRC}:${GUARD_DST}:0755"
    "${SNAP_SRC}:${SNAP_DST}:0755"
    "${SNAP_UNIT_SRC}:${SNAP_UNIT_DST}:0644"
    "${SNAP_TIMER_SRC}:${SNAP_TIMER_DST}:0644"
)

DRY_RUN=0
UPDATE_BEHAVIOR=0
for arg in "$@"; do
    case "${arg}" in
        --dry-run) DRY_RUN=1 ;;
        --update-backup-behavior) UPDATE_BEHAVIOR=1 ;;
        *) echo "unknown argument: ${arg}" >&2; exit 2 ;;
    esac
done

say() { printf '%s\n' "$*"; }
act() {
    # act <description> <command...>: print, then run unless --dry-run.
    local what="$1"; shift
    if (( DRY_RUN )); then
        say "would: ${what}"
    else
        "$@"
    fi
}

if (( DRY_RUN == 0 )) && [[ "$(id -u)" -ne 0 ]]; then
    echo "run with sudo (or --dry-run to rehearse without root)" >&2
    exit 2
fi
for f in "${WRAPPER_SRC}" "${UNIT_SRC}" "${DEFAULTS_SRC}" "${GUARD_SRC}" "${ENV_SRC}" "${SNAP_SRC}" "${SNAP_UNIT_SRC}" "${SNAP_TIMER_SRC}"; do
    [[ -f "${f}" ]] || { echo "missing source: ${f}" >&2; exit 2; }
done
bash -n "${WRAPPER_SRC}"
bash -n "${GUARD_SRC}"
# A syntax check that writes no .pyc into the checkout (py_compile did, as root under sudo).
python3 -c 'import ast, sys; ast.parse(open(sys.argv[1], encoding="utf-8").read(), sys.argv[1])' "${SNAP_SRC}"

# --- the contract carries no secret, and the wrapper accepts it ----------------------------------
# Refused, commented or not (behind any run of `#`): an assignment whose NAME looks like a secret
# (…KEY…, …PASSPHRASE…, …PASSWORD…, …CREDENTIAL…, …TOKEN…, …SECRET…) with a value that is not
# empty, not a $variable and not a <placeholder>; and an --option line whose name carries a secret
# (…password…, …passphrase…, …secret…, …encryption-key…, …auth-token…) with such a value. A
# commented-out secret is still a secret on disk (AC-8), and the 2026-09-22 file's
# SETTINGS_ENCRYPTION_KEY_OLD line is exactly the shape the 1.1.0 gate missed.
SECRET_ASSIGN='^[[:space:]]*(#[#[:space:]]*)?(export[[:space:]]+)?[A-Za-z0-9_]*(KEY|PASSPHRASE|PASSWORD|CREDENTIAL|TOKEN|SECRET)[A-Za-z0-9_]*[[:space:]]*=[[:space:]]*["'"'"']?[^"'"'"'$<[:space:]]'
SECRET_OPTION='^[[:space:]]*(#[#[:space:]]*)?--[a-z0-9-]*(password|passphrase|secret|encryption-key|auth-token)[a-z0-9-]*=[[:space:]]*["'"'"']?[^"'"'"'$<[:space:]]'
if grep -Eiq "${SECRET_ASSIGN}" "${ENV_SRC}"; then
    echo "REFUSING: ${ENV_SRC} carries a secret-shaped assignment (commented or not); the contract allows none" >&2
    exit 2
fi
if grep -Eiq "${SECRET_OPTION}" "${ENV_SRC}"; then
    echo "REFUSING: ${ENV_SRC} carries an option line with a secret value (commented or not); the contract allows none" >&2
    exit 2
fi
# Which --option lines the env file may carry is the WRAPPER's rule (its ENV_OPTION_DENY and
# ENV_OPTION_ALLOW), so the wrapper being installed judges the file: one rule, not two copies.
# A clean environment, a scratch data folder and /bin/true as the server: nothing is started and
# no key reaches it (the wrapper prints option NAMES and lengths only). DUPLICATI_REQUIRE_MOUNT is
# set EMPTY, which since wrapper 2.4.0 really switches its mount check off (2.3.0's `:-` turned an
# empty value back into /mnt/Backups, so an unmounted drive read as "the wrapper refuses the
# contract" -- R4A D-1). That is deliberate: this gate judges the file's grammar, and a missing
# mount is not a contract fault -- the unit's own start checks the mount, every time.
wrapper_accepts() {
    # wrapper_accepts <env file>: 0 when the wrapper's env-file grammar accepts it; else prints why.
    local scratch out rc=0
    scratch="$(mktemp -d)"
    out="$(env -i PATH=/usr/bin:/bin DUPLICATI_ENV_FILE="$1" DUPLICATI_SERVER=/bin/true \
        DUPLICATI_DATA_FOLDER="${scratch}" DUPLICATI_REQUIRE_MOUNT= \
        "${BASH}" "${WRAPPER_SRC}" --print-command 2>&1 >/dev/null)" || rc=$?
    rm -rf "${scratch}"
    (( rc == 0 )) || printf '%s\n' "${out}" | sed 's/^/  wrapper: /' >&2
    return "${rc}"
}
if ! wrapper_accepts "${ENV_SRC}"; then
    echo "REFUSING: the wrapper refuses ${ENV_SRC} (see its lines above); it would exit 78 at the next start" >&2
    exit 2
fi
# The modes an existing env file may have. Which one is RIGHT is the owner's open decision O-12
# (the contract header, D's P1 item 2, A's O-12 row); this installer does NOT settle it, so it
# accepts either documented form and nothing else (R5A DEFECT-2):
#   root:duplicati 0640 -- what this installer creates, and what the design recommends;
#   duplicati:duplicati 0600 -- the dissent (Lane A3 / Lane B2 D15).
# Anything else is refused: another owner or group, any group- or other-writable file, and any
# other-readable one (the file may export SETTINGS_ENCRYPTION_KEY -- R5A NIT-1), and a group that
# cannot read it (root:root 0640 passes the root-run grammar gate and then fails every start with
# exit 78 -- R4C N-4). A SYMLINK is refused by name: stat would judge the link's own 0777, and the
# fix is a real file, not a chmod.
ENV_MODES_ACCEPTED="root:duplicati 0640 or duplicati:duplicati 0600 (O-12 is open; either form is accepted)"
if [[ -L "${ENV_DST}" ]]; then
    if (( DRY_RUN )); then
        say "would refuse: ${ENV_DST} is a symlink; it must be a regular file, ${ENV_MODES_ACCEPTED}"
    else
        echo "REFUSING: ${ENV_DST} is a symlink; replace it with a regular file, ${ENV_MODES_ACCEPTED}" >&2
        exit 2
    fi
elif [[ -e "${ENV_DST}" ]]; then
    if [[ ! -r "${ENV_DST}" ]]; then
        say "cannot judge the existing ${ENV_DST} without root (a dry run as a user); the real run does"
    elif ! wrapper_accepts "${ENV_DST}"; then
        echo "REFUSING: the wrapper being installed refuses the existing ${ENV_DST} (see above); it is never overwritten, so fix it by hand first" >&2
        exit 2
    fi
    # Refused on a real run; reported on a dry run, which as a user cannot tell a scratch prefix's
    # owner from the host's.
    env_meta="$(stat -c '%U:%G:%a' "${ENV_DST}")"
    case "${env_meta}" in
        root:duplicati:640|duplicati:duplicati:600) ;;
        *)
            if (( DRY_RUN )); then
                say "would refuse: ${ENV_DST} is ${env_meta}; it must be ${ENV_MODES_ACCEPTED}"
            else
                echo "REFUSING: ${ENV_DST} is ${env_meta}; the service reads it as duplicati -- make it ${ENV_MODES_ACCEPTED}" >&2
                exit 2
            fi
            ;;
    esac
fi

# --- D-6 drift gate (RULED 2026-09-22) -----------------------------------------------------
# The repository is canonical and what the unit executes is a COPY. Two different things can
# therefore drift, and they mean OPPOSITE things:
#
#   * the INSTALLED file no longer matches what was blessed -> someone edited the installed copy
#     outside this installer. Never overwrite that silently; it is the only evidence -- so with
#     --update-backup-behavior it is copied to <dst>.drifted-<UTC timestamp> before the install.
#   * the REPOSITORY no longer matches what was blessed -> an intended behaviour change. That
#     is legitimate, and is exactly what --update-backup-behavior authorises.
#
# A symlink into the checkout was considered for this job and rejected: on a fresh host the
# checkout does not exist yet, so ExecStart= would resolve to a dangling target and the service
# would not start -- failing in the bare-metal recovery case the symlink was proposed for.
#
# blessed_for prints the blessed checksum of a destination, or nothing. It must RETURN 0 either
# way: under `set -e`, `want="$(blessed_for …)"` inherits the substitution's status, and a
# helper that returned 1 on "no blessed file yet" ended the first install silently (1.1.0 (a)).
blessed_for() {
    if [[ -s "${BLESSED}" ]]; then
        awk -v d="$1" '$2 == d { print $1 }' "${BLESSED}"
    fi
    return 0
}

drift=0
declare -A DRIFTED=()
declare -A PREEXISTING=()
for triple in "${PAIRS[@]}"; do
    IFS=: read -r src dst _mode <<< "${triple}"
    want="$(blessed_for "${dst}")"
    if [[ -z "${want}" ]]; then
        # Never blessed: nothing to compare against -- but a file already there that differs from
        # the repository is someone's, and is copied aside before it is replaced (R3C N-7).
        if [[ -f "${dst}" ]] && ! cmp -s "${src}" "${dst}"; then
            PREEXISTING["${dst}"]=1
            # An absent or empty blessed file must not turn an edited installed file into a quiet
            # "first install" (R4C N-5): replacing a file nobody blessed takes the same switch.
            echo "UNBLESSED: installed ${dst} differs from the repository and was never blessed" >&2
            drift=1
        fi
        continue
    fi
    if [[ -f "${dst}" ]] && [[ "$(sha256sum "${dst}" | cut -d' ' -f1)" != "${want}" ]]; then
        echo "DRIFT: installed ${dst} does not match its blessed checksum -- changed outside this installer" >&2
        drift=1
        DRIFTED["${dst}"]=1
    fi
    if [[ "$(sha256sum "${src}" | cut -d' ' -f1)" != "${want}" ]]; then
        echo "BEHAVIOUR CHANGE: ${src} differs from the blessed checksum" >&2
        drift=1
    fi
done
if (( drift == 1 && UPDATE_BEHAVIOR == 0 )); then
    echo "Refusing to install. Inspect the differences, then re-run with --update-backup-behavior" >&2
    echo "to bless the current repository contents as what this host executes." >&2
    exit 4
fi
if [[ ! -s "${BLESSED}" ]]; then
    say "first install: no ${BLESSED} yet, nothing to compare"
fi

# --- unit files: a syntax pass on a temp copy, before anything is installed (advisory) --------
# The real `systemd-analyze verify` runs on the installed units at the end; on a first install it
# cannot run earlier, because the wrapper the unit executes is not installed yet. The dry run
# therefore verifies COPIES whose ExecStart is rewritten to /bin/true, so a directive typo is
# seen before the install. Advisory only: the verifier's output is printed, never fatal, because
# a runner without the duplicati user or this host's systemd would otherwise refuse a good unit.
if (( DRY_RUN )) && command -v systemd-analyze >/dev/null 2>&1; then
    VERIFY_TMP="$(mktemp -d)"
    for u in "${UNIT_SRC}" "${SNAP_UNIT_SRC}" "${SNAP_TIMER_SRC}"; do
        sed -E 's#^ExecStart=.*#ExecStart=/bin/true#' "${u}" > "${VERIFY_TMP}/$(basename "${u}")"
    done
    say "dry run: systemd-analyze verify on temp copies (ExecStart rewritten to /bin/true):"
    systemd-analyze verify --man=no "${VERIFY_TMP}"/*.service "${VERIFY_TMP}"/*.timer 2>&1 | sed 's/^/  verify: /' || true
    rm -rf "${VERIFY_TMP}"
fi

# --- install ---------------------------------------------------------------------------------
act "install -d -m 0755 -o root -g root ${LIB_DIR}" install -d -m 0755 -o root -g root "${LIB_DIR}"
act "install -d -m 0700 -o root -g root ${CREDSTORE_DIR}" install -d -m 0700 -o root -g root "${CREDSTORE_DIR}"
act "install -d -m 0755 -o root -g root ${ENV_DIR}" install -d -m 0755 -o root -g root "${ENV_DIR}"
for triple in "${PAIRS[@]}"; do
    IFS=: read -r src dst mode <<< "${triple}"
    if [[ -n "${DRIFTED[${dst}]+x}" ]]; then
        aside="${dst}.drifted-$(date -u +%Y%m%dT%H%M%SZ)"
        act "cp -p ${dst} ${aside}  (the drifted installed copy is kept as evidence)" cp -p "${dst}" "${aside}"
        (( DRY_RUN )) || say "kept the drifted ${dst} as ${aside}"
    elif [[ -n "${PREEXISTING[${dst}]+x}" ]]; then
        aside="${dst}.pre-install-$(date -u +%Y%m%dT%H%M%SZ)"
        act "cp -p ${dst} ${aside}  (a never-blessed file that differs from the repository is kept)" cp -p "${dst}" "${aside}"
        (( DRY_RUN )) || say "kept the never-blessed ${dst} as ${aside}"
    fi
    act "install -m ${mode} -o root -g root ${src#"${REPO_DIR}"/} ${dst}" install -m "${mode}" -o root -g root "${src}" "${dst}"
done

# The env contract: installed once, 0640 root:duplicati, never overwritten (an operator's
# tunables are theirs). The service user reads it through the group and cannot replace it:
# /etc/duplicati is root-owned 0755, so the unlink-and-recreate path the data folder allowed
# (round 3's D13) does not exist here.
if [[ -e "${ENV_DST}" ]]; then
    say "kept existing ${ENV_DST} (not overwritten; diff against ${ENV_SRC#"${REPO_DIR}"/} by hand)"
else
    act "install -m 0640 -o root -g duplicati ${ENV_SRC#"${REPO_DIR}"/} ${ENV_DST}" install -m 0640 -o root -g duplicati "${ENV_SRC}" "${ENV_DST}"
fi

# The data folder: 0700 duplicati:duplicati or the server refuses it at every start. `install -d`
# re-modes an existing folder too, so a 0777 folder left over from the migration is corrected
# here -- but P0 moves that folder aside first (D's step 2) and places the recovered database
# before this installer runs (assessment step 9), so on the recovery day this creates nothing new.
act "install -d -m 0700 -o duplicati -g duplicati ${DATA_FOLDER}" install -d -m 0700 -o duplicati -g duplicati "${DATA_FOLDER}"
if (( DRY_RUN == 0 )) && [[ "$(stat -c '%U:%a' "${DATA_FOLDER}")" != "duplicati:700" ]]; then
    echo "${DATA_FOLDER} must be duplicati-owned mode 0700 (Duplicati refuses anything else)" >&2
    exit 1
fi

# --- bless -----------------------------------------------------------------------------------
if (( DRY_RUN )); then
    say "would: write ${BLESSED} with the sha256 of each of the ${#PAIRS[@]} installed files"
else
    : > "${BLESSED}.new"
    for triple in "${PAIRS[@]}"; do
        IFS=: read -r src dst _mode <<< "${triple}"
        cmp -s "${src}" "${dst}" || { echo "checksum mismatch after install: ${dst}" >&2; exit 1; }
        printf '%s  %s\n' "$(sha256sum "${dst}" | cut -d' ' -f1)" "${dst}" >> "${BLESSED}.new"
        echo "installed ${dst} ($(sha256sum "${dst}" | cut -c1-16))"
    done
    install -m 0644 -o root -g root "${BLESSED}.new" "${BLESSED}"
    rm -f "${BLESSED}.new"
    echo "blessed ${BLESSED} (${#PAIRS[@]} files; re-bless deliberately with --update-backup-behavior)"
fi

# --- the settings key ------------------------------------------------------------------------
if (( DRY_RUN )); then
    say "would: check ${CRED_DST} exists, is root-owned and mode 0600 (its content is never read here)"
elif [[ ! -s "${CRED_DST}" ]]; then
    # The design's step-8 form, character for character (R4A N-6): `test ! -e`, not `! -s` -- an
    # EMPTY file is still refused, because writing over anything that exists is the hazard.
    printf '%s\n' "NOTE: ${CRED_DST} is absent or empty. On A0, A2 and B create it before starting (on Procedure A, place the accepted 09-18 key here instead, and a random one at ${CRED_DST}.new, which P0.5b swaps in -- the same command with .new):" \
        "      sudo test ! -e ${CRED_DST} && { umask 077; openssl rand -base64 48 | tr -d '\\n' | sudo tee ${CRED_DST} >/dev/null; }" \
        "      and escrow it with the passphrases (it is a third key) BEFORE the first start. An EMPTY file is refused" \
        "      by that test on purpose: remove it by hand first, after checking that nothing was ever encrypted under it." >&2
else
    [[ "$(stat -c '%U:%a' "${CRED_DST}")" == "root:600" ]] || { echo "${CRED_DST} must be root-owned mode 0600" >&2; exit 1; }
fi

# The snapshot unit's ReadWritePaths= deliberately has NO `-` prefix: a missing destination fails
# the unit at namespace setup (226/NAMESPACE) -- loud, and seen by the watchdog -- rather than
# running the script under ProtectHome=read-only, where its makedirs could not create the
# directory either. So the directory must exist. This installer does not create it: `install -d`
# would leave any missing parent (~/.local, ~/.local/state) owned by root.
if [[ ! -d "${SNAP_DEST_DIR}" ]]; then
    printf '%s\n' "NOTE: ${SNAP_DEST_DIR} is absent; the snapshot unit fails until it exists. As pcalnon:" \
        "      mkdir -p -m 0700 ${SNAP_DEST_DIR}" >&2
fi

act "systemctl daemon-reload" systemctl daemon-reload
act "systemd-analyze verify ${UNIT_DST} ${SNAP_UNIT_DST} ${SNAP_TIMER_DST}" systemd-analyze verify "${UNIT_DST}" "${SNAP_UNIT_DST}" "${SNAP_TIMER_DST}"
echo
echo "Next -- the design's P0 steps 8 to 10 (assessment steps 9 to 11); the design is the authority:"
echo "  1. sudo -u duplicati ${WRAPPER_DST} --print-command   (dry run, no server started)"
echo "  2. BEFORE the first start (step 8): the settings key is in place (see any NOTE above); the placed database"
echo "     holds paused-until = 0, read back with startup-delay; the web credential is written"
echo "     (~/.config/duplicati-backup/web-credential, 0600, one line DUPLICATI_WEB_CREDENTIAL=<password>);"
echo "     on Procedures A2 and B the password-init hand start has run."
echo "  3. sudo systemctl start duplicati.service   (START, never restart: the old server was stopped once, by step 2)"
echo "     python3 util/ad-hoc/yamaguchi_server_api.py serverstate   must exit 2 (Paused). If it reads Running, stop the unit at once"
echo "     (sudo systemctl stop duplicati.service) and record it; do not pause -- pause only suspends a job that may already"
echo "     be running, and step 10's resume would continue it with the options it started with."
echo "     Then read the stored paused-until (step 8's read-back) before starting again."
echo "  4. Before any resume (step 10), dry-run the guard with the URL read FROM THE JOB; replace <id> on the second"
echo "     line only, and require guard exit=0:"
cat <<'EOF'
unset url id
id=<id>
case "$id" in ''|*[!0-9]*) echo "REFUSE: set id to the job's number" >&2; false ;; esac &&
url="$(python3 util/ad-hoc/yamaguchi_server_api.py export "$id" \
  | python3 -c 'import json,sys; print(json.load(sys.stdin)["Backup"]["TargetURL"])')"
test -n "$url" || { echo "REFUSE: export $id gave no TargetURL" >&2; false; } &&
sudo -u duplicati env DUPLICATI__REMOTEURL="$url" \
EOF
# shellcheck disable=SC2016  # the $? is the operator's, printed literally
printf '  %s; echo "guard exit=$?"\n' "${GUARD_DST}"
echo "  5. Then, on A0, A2 and B, restart the unit before resume (step 10): sudo systemctl stop duplicati.service,"
echo "     then sudo systemctl start duplicati.service; serverstate must exit 2 again; read the edits back with"
echo "     export <id> (step 10 lists what to check) -- and only then resume. On Procedure A, P0.5b runs here instead."
echo
echo "      systemd-analyze security duplicati.service"
echo "      the snapshot timer stays disabled until the first start has re-encrypted the database:"
echo "        systemctl enable --now yamaguchi-server-db-snapshot.timer   (assessment step 13, not before)"
