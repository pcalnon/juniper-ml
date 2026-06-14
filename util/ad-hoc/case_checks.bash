#!/usr/bin/env bash
########################################################################################################################################################
#
########################################################################################################################################################


########################################################################################################################################################
# Non-Test-Array Testing Constants

# MODEL_NAME_CHECK="claude-opus-4-6"
# MODEL_NAME_CHECK="claude-haiku-4-6"
# MODEL_NAME_CHECK="claude-sonnet-4-6"
# MODEL_NAME_CHECK="claude-fable-4-6"

# MODEL_NAME_CHECK="opus"
# MODEL_NAME_CHECK="haiku"
# MODEL_NAME_CHECK="sonnet"
# MODEL_NAME_CHECK="fable"
########################################################################################################################################################


########################################################################################################################################################
# Define Constants for test script

# Define Model Name Constants for Testing
CLAUDE_OPUS_NAME="claude-opus-4-6"
CLAUDE_HAIKU_NAME="claude-haiku-4-6"
CLAUDE_SONNET_NAME="claude-sonnet-4-6"
CLAUDE_FABLE_NAME="claude-fable-4-6"

# Define Model Alias Constants for Testing
CLAUDE_OPUS_ALIAS="opus"
CLAUDE_HAIKU_ALIAS="haiku"
CLAUDE_SONNET_ALIAS="sonnet"
CLAUDE_FABLE_ALIAS="fable"


########################################################################################################################################################
# Define Array for Model Name and Alias Testing
declare -a MODEL_TEST_ARRAY
MODEL_TEST_ARRAY+=("${CLAUDE_OPUS_NAME}")
MODEL_TEST_ARRAY+=("${CLAUDE_HAIKU_NAME}")
MODEL_TEST_ARRAY+=("${CLAUDE_SONNET_NAME}")
MODEL_TEST_ARRAY+=("${CLAUDE_FABLE_NAME}")
MODEL_TEST_ARRAY+=("${CLAUDE_OPUS_ALIAS}")
MODEL_TEST_ARRAY+=("${CLAUDE_HAIKU_ALIAS}")
MODEL_TEST_ARRAY+=("${CLAUDE_SONNET_ALIAS}")
MODEL_TEST_ARRAY+=("${CLAUDE_FABLE_ALIAS}")


########################################################################################################################################################
echo -ne "\n\nValidating Model Names and Aliases: ${MODEL_TEST_ARRAY[*]}\n\n"

for MODEL_NAME_CHECK in "${MODEL_TEST_ARRAY[@]}"; do
    echo -ne "\tValidate Model: ${MODEL_NAME_CHECK} (${MODEL_NAME_CHECK^^}):      \t"
    case "${MODEL_NAME_CHECK^^}" in
        "${CLAUDE_HAIKU_NAME^^}" | \
        "${CLAUDE_SONNET_NAME^^}" | \
        "${CLAUDE_FABLE_NAME^^}" | \
        "${CLAUDE_OPUS_NAME^^}" | \
        "${CLAUDE_OPUS_ALIAS^^}" | \
        "${CLAUDE_HAIKU_ALIAS^^}" | \
        "${CLAUDE_SONNET_ALIAS^^}" | \
        "${CLAUDE_FABLE_ALIAS^^}")
             echo -ne "Valid\n"
        ;;
        *) echo -ne "Nope\n";;
    esac
done
