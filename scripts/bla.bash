#!/usr/bin/env bash
####################################################################################################################################################################################
#
####################################################################################################################################################################################
# References
#
# ./bla.bash a b c d e f g h i j
# Script Params: "a b c d e f g h i j"
# Function Params: 0 1 2 3 4 5 6 7 8 9
# Parent Params: a b c d e f g h i j
# Script Params a b c d e f g h i j
# Function Params: 0 1 2 3 4 5 6 7 8 9
# Parent Params: a b c d e f g h i j
####################################################################################################################################################################################


echo "0. Script Call"
echo "1. Initial Script Params: \"${*}\""

declare -a PARAMS=("${@}")
echo "2. Script Params: \"${PARAMS[*]}\""

declare -a PPARAMS=()
declare -a SPPARAMS=()
declare -a FPARAMS=()
declare -a SFPARAMS=()

echo "3. Function Definition"
function bla() {
    FPARAMS=("${@}")
    echo "5.0. Function Param 1: \"${1}\""
    echo "5.1. Function Params: \"${FPARAMS[*]}\""
    shift 2
    echo "5.1.1. Function Param 1: \"${1}\""
    echo "5.2. Shifted Function Params: \"${*}\""
    SFPARAMS=("${@}")
    echo "5.3. Shifted Function Params: \"${SFPARAMS[*]}\""
    set "${PARAMS[@]}"
    echo "5.3.1. Function Param 1: \"${1}\""
    echo "5.4. Set Script Params: \"${*}\""
    PPARAMS=("${@}")
    echo "5.5. Parent Params: \"${PPARAMS[*]}\""
    shift 2
    SPPARAMS=("${@}")
    echo "5.5.1. Shifted Parent Param 1: \"${1}\""
    echo "5.6. Shifted Parent Params: \"${*}\""
    echo "5.7. Shifted Parent Params: \"${SPPARAMS[*]}\""
    set "${SFPARAMS[@]}"
    echo "5.7. Shifted Function Params: \"${*}\""
    shift 2
    echo "5.7.1. Function Param 1: \"${1}\""
    echo "5.8. Double Shifted Function Params: \"${*}\""
}

echo "4. Function Call"
echo "5. bla 0 1 2 3 4 5 6 7 8 9"
bla 0 1 2 3 4 5 6 7 8 9

echo "6. Final Script Params \"${*}\""
echo "6.1. Script Param 1: \"${1}\""
set "${SPPARAMS[@]}"
echo "7. Function Params: \"${SFPARAMS[*]}\""
echo "7.1. Final Script Params \"${*}\""
echo "7.2. Script Param 1: \"${1}\""
echo "8. Shifted Function Params: \"${SFPARAMS[*]}\""
echo "9. Shifted Parent Params: \"${SPPARAMS[*]}\""


