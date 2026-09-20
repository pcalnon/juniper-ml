#!/usr/bin/env bash
#############################################################################################################################################################################################
# Name: duplicati-wrapper.bash
# Author: Paul Calnon
# Email: paul.calnon@gmail.com
# Website: https://github.com/pcalnon
#
# Project: https://github.com/pcalnon/juniper-ml
# Date Created: 2026-09-20
# Version: 0.1.0
#############################################################################################################################################################################################
# Description:
#   Duplicati Server Wrapper script called by systemd unit file
#############################################################################################################################################################################################
# Notes:
#
#   The default environment file for duplicati systemd unit service:
#     /etc/default/duplicati
#   The systemd unit file for duplicati:
#     /usr/lib/systemd/system/duplicati.service
#   The environment file for duplicati:
#     /home/duplicati/.config/Duplicati/.env
#   The wrapper script for duplicati (this file):
#     /home/duplicati/bin/duplicati-wrapper.bash
#
#   Input parameter order of precedence:
#     1. Duplicati WrapperScript Input Parameters: ${*}
#     2. Duplicati Server Global Environment Variables: /etc/default/duplicati
#     3. Duplicati Server Local Environment File: /home/duplicati/.config/Duplicati/.env
#     4. Duplicati Wrapper Script Constants: /home/duplicati/bin/duplicati-wrapper.bash
#
#   Duplicati Server Global Environment Variables:
#     DAEMON_OPTS="--webservice-port=8300"
#
#############################################################################################################################################################################################
# References:
#
#   Old Unit file:
#
#     [Unit]
#     Description=Duplicati web-server
#     After=network.target
#
#     [Service]
#     Nice=19
#     User=duplicati
#     Group=duplicati
#     EnvironmentFile=-/etc/default/duplicati
#     Environment=SETTINGS_ENCRYPTION_KEY=65mOU0*B@Inc$PRhqElidUvnrJ6GoaN%6%xE
#     ExecStart=/home/duplicati/bin/duplicati-wrapper.bash
#     /usr/bin/duplicati-server $DAEMON_OPTS
#     IOSchedulingClass=idle
#     IOSchedulingPriority=7
#     Restart=always
#
#     [Install]
#     WantedBy=multi-user.target
#############################################################################################################################################################################################

#############################################################################################################################################################################################
# Define Script Environment Variables:
# DUPLICATI_SERVER="/usr/bin/duplicati-server"
DUPLICATI_SERVER="/usr/lib/duplicati/duplicati-server"
echo "DUPLICATI_SERVER: \"${DUPLICATI_SERVER}\""

DUPLICATI_ENV_GLOBAL="/etc/default/duplicati"
echo "DUPLICATI_ENV_GLOBAL: \"${DUPLICATI_ENV_GLOBAL}\""

DUPLICATI_ENV_LOCAL="/home/duplicati/.config/Duplicati/.env"
echo "DUPLICATI_ENV_LOCAL: \"${DUPLICATI_ENV_LOCAL}\""


#############################################################################################################################################################################################
# Define Default Duplicati Server Options:
DUPLICATI_PORT_LABEL="--webservice-port"
echo "DUPLICATI_PORT_LABEL: \"${DUPLICATI_PORT_LABEL}\""

DUPLICATI_PORT_DEFAULT="8300"
echo "DUPLICATI_PORT_DEFAULT: \"${DUPLICATI_PORT_DEFAULT}\""

DUPLICATI_ENCRYPTION_KEY_LABEL="SETTINGS_ENCRYPTION_KEY"
echo "DUPLICATI_ENCRYPTION_KEY_LABEL: \"${DUPLICATI_ENCRYPTION_KEY_LABEL}\""


#############################################################################################################################################################################################
# Initialize Duplicati Wrapper Script Variables:
DUPLICATI_INPUT_PARAMS=""
DUPLICATI_ENV_VARS_GLOBAL=""
DUPLICATI_ENV_VARS_LOCAL=""
DUPLICATI_OPTS=""


#############################################################################################################################################################################################
# Parse and validate Script Input Parameters:
echo "Wrapper Script Input Parameters: \"${*}\""
if [[ "${*}" != "" ]]; then
    DUPLICATI_INPUT_PARAMS=("${*}")
    echo "DUPLICATI_INPUT_PARAMS: \"${DUPLICATI_INPUT_PARAMS[*]}\""
fi

if [[ "${DAEMON_OPTS}" != "" ]]; then
    DUPLICATI_ENV_VARS_GLOBAL=("${DAEMON_OPTS}")
    echo "DUPLICATI_ENV_VARS_GLOBAL: \"${DUPLICATI_ENV_VARS_GLOBAL[*]}\""
fi

# Parse the Duplicati environment file
echo "Parsing Duplicati environment file: \"${DUPLICATI_ENV_LOCAL}\""
DUPLICATI_ENV_VARS_LOCAL=()
if [[ ( "${DUPLICATI_ENV_LOCAL}" != "" ) && ( -f "${DUPLICATI_ENV_LOCAL}" ) ]]; then
    echo "Duplicati environment file found: \"${DUPLICATI_ENV_LOCAL}\""
    while read -r line; do
        echo "LINE: \"${line}\""
        # Skip comments and empty lines
        if [[ (${line} == "" ) || ( $(echo "${line}" | grep -e "^#") != "" ) || ( $(echo "${line}" | grep -e "^ *$") != "" ) ]]; then
            continue
        fi
        echo "Parsed Environment Variable: \"${line}\""
        ENV_FILE_VAR_VALUE=""
        # Remove the export prefix if it exists
        if [[ "$(echo "${line}" | grep -e "^ *export ")" != "" ]]; then
            line="${line//export /}"
        fi
        # handle key=value pairs with missing value (e.g. --blalba)
        if [[ "$(echo "${line}" | grep "=")" != "" ]]; then
            ENV_FILE_VAR_KEY=$(echo "${line}" | cut -d '=' -f 1)
            echo "ENV_FILE_VAR_KEY: ${ENV_FILE_VAR_KEY}"
            ENV_FILE_VAR_VALUE=$(echo "${line}" | cut -d '=' -f 2)
            echo "ENV_FILE_VAR_VALUE: ${ENV_FILE_VAR_VALUE}"
        else
            ENV_FILE_VAR_KEY="${line}"
            echo "ENV_FILE_VAR_KEY: \"${ENV_FILE_VAR_KEY}\""
        fi
        # Check if the duplicati env file setting is an environment variable or a Duplicati server option
        if [[ "$(echo "${ENV_FILE_VAR_KEY}" | grep "^-")" == "" ]]; then
            # check if the environment variable is already defined
            DEFINED_ENV_VAR="$(env | grep "${ENV_FILE_VAR_KEY}")"
            if [[ "${DEFINED_ENV_VAR}" != "" ]]; then
                echo "Environment Variable \"${ENV_FILE_VAR_KEY}\" is already defined"
            else
                echo "Exporting Environment Variable ${ENV_FILE_VAR_KEY}=${ENV_FILE_VAR_VALUE}"
                EXPORT_CMD="export ${ENV_FILE_VAR_KEY}=${ENV_FILE_VAR_VALUE}"
                echo "EXPORT_CMD: ${EXPORT_CMD}"
                eval "${EXPORT_CMD}"
                echo "Environment Variable: $(env | grep "${ENV_FILE_VAR_KEY}")"
            fi
        else
            # Add the Duplicati server option to the local environment variables
            echo "Duplicati Server Option \"${ENV_FILE_VAR_KEY}\" is not an environment variable"
            LOCAL_VAR_VALUE="${ENV_FILE_VAR_KEY}"
            if [[ "${ENV_FILE_VAR_VALUE}" != "" ]]; then
                LOCAL_VAR_VALUE="${LOCAL_VAR_VALUE}=${ENV_FILE_VAR_VALUE}"
            fi
            DUPLICATI_ENV_VARS_LOCAL+=("${LOCAL_VAR_VALUE}")
            echo "DUPLICATI_ENV_VARS_LOCAL: \"${DUPLICATI_ENV_VARS_LOCAL[*]}\""
        fi
    done < "${DUPLICATI_ENV_LOCAL}"
fi


#############################################################################################################################################################################################
# Build Duplicati Server Command Line Options:

# Add wrapper script input parameters to the Duplicati server command line options
for PARAM in "${DUPLICATI_INPUT_PARAMS[@]}"; do
    echo "Wrapper Script Input Parameter: \"${PARAM}\""
    DUPLICATI_OPTS_VAR_KEY="${PARAM}"
    if [[ "$(echo "${DUPLICATI_OPTS_VAR_KEY}" | grep "=")" != "" ]]; then
        DUPLICATI_OPTS_VAR_KEY=$(echo "${DUPLICATI_OPTS_VAR_KEY}" | cut -d '=' -f 1)
    fi
    if [[ "$(echo "${DUPLICATI_OPTS}" | grep -- "${DUPLICATI_OPTS_VAR_KEY}")" == "" ]]; then
        DUPLICATI_OPTS="${DUPLICATI_OPTS}${PARAM} "
    fi
done

# Add global environment variables, ${DAEMON_OPTS}, to the Duplicati server command line options
for PARAM in "${DUPLICATI_ENV_VARS_GLOBAL[@]}"; do
    echo "Global Environment Variable: \"${PARAM}\""
    DUPLICATI_OPTS_VAR_KEY="${PARAM}"
    if [[ "$(echo "${DUPLICATI_OPTS_VAR_KEY}" | grep "=")" != "" ]]; then
        DUPLICATI_OPTS_VAR_KEY=$(echo "${DUPLICATI_OPTS_VAR_KEY}" | cut -d '=' -f 1)
    fi
    if [[ "$(echo "${DUPLICATI_OPTS}" | grep -- "${DUPLICATI_OPTS_VAR_KEY}")" == "" ]]; then
        DUPLICATI_OPTS="${DUPLICATI_OPTS}${PARAM} "
    fi
done

# Add local environment variables, from .env file, to the Duplicati server command line options
for PARAM in "${DUPLICATI_ENV_VARS_LOCAL[@]}"; do
    echo "Local Environment Variable: \"${PARAM}\""
    DUPLICATI_OPTS_VAR_KEY="${PARAM}"
    if [[ "$(echo "${DUPLICATI_OPTS_VAR_KEY}" | grep "=")" != "" ]]; then
        DUPLICATI_OPTS_VAR_KEY=$(echo "${DUPLICATI_OPTS_VAR_KEY}" | cut -d '=' -f 1)
    fi
    if [[ "$(echo "${DUPLICATI_OPTS}" | grep -- "${DUPLICATI_OPTS_VAR_KEY}")" == "" ]]; then
        DUPLICATI_OPTS="${DUPLICATI_OPTS}${PARAM} "
    fi
done

# Add the default port to the Duplicati server command line options if it is not already set
if [[ "$(echo "${DUPLICATI_OPTS}" | grep -- "${DUPLICATI_PORT_LABEL}")" == "" ]]; then
    DUPLICATI_OPTS="${DUPLICATI_OPTS}${DUPLICATI_PORT_LABEL}=${DUPLICATI_PORT_DEFAULT} "
fi


#############################################################################################################################################################################################
echo "Final Duplicati Server Command Line Options: \"${DUPLICATI_OPTS}\""
echo "Settings Encryption Key: $(env | grep "${DUPLICATI_ENCRYPTION_KEY_LABEL}")"
echo "Executing Duplicati Server: \"${DUPLICATI_SERVER} ${DUPLICATI_OPTS}\""

exec "${DUPLICATI_SERVER}" "${DUPLICATI_OPTS}"
