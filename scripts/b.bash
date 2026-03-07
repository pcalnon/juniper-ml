#!/usr/bin/env bash

B="1"
C="2"
D="3"
E="4"
F="5"

echo "B: \"${B}\""
echo "C: \"${C}\""
echo "D: \"${D}\""
echo "E: \"${E}\""
echo "F: \"${F}\""

A="\"${B}\" | \"${C}\""
G="$(eval "echo \"${A}\"")"

VAL="${C}"
# VAL="${D}"

echo "awk: $(echo "${A}" | awk -F "|" '{print $1 | $2;}')"

echo "eval \\\"echo \\\"\\\${A}\\\" | awk -F \\\"|\\\" '{print \\\$1 | \\\$2;}'\\\""
Q="$(echo "eval \\\"echo \\\"\\\${A}\\\" | awk -F \\\"|\\\" '{print $1 | $2;}'\\\"")"
echo "Q: \"${Q}\""
# echo "$(eval \"echo \"\${A}\" | awk -F \"|\" '{print $1 | $2;}'\")"

echo "A: ${A}"
eval "echo \"Eval A: ${A}\""
echo "subs: $(echo "\"${A}\"")"
echo "eval: $(eval "echo \"${A}\"")"
echo "G: ${G}"

echo "Val: \"${VAL}\""

H="$(echo "1 | 2")"
echo "H: ${H}"

case "${VAL}" in
    eval "\"\${A}\"")
        # " | awk -F \"|\" '{print $1 | $2;}'")
        echo "VAL: \"${VAL}\" == ${Q} (eval ops -- based on Q)"
    ;;
    eval "echo \"\${A}\" | awk -F \"|\" '{print $1 | $2;}'")
        echo "VAL: \"${VAL}\" == ${Q} (eval ops -- based on Q)"
    ;;
    "${Q}")
        echo "VAL: \"${VAL}\" == ${Q} (eval Single Variable)"
    ;; 
    "$(echo "eval \\\"echo \\\"\\\${A}\\\" | awk -F \\\"|\\\" '{print $1 | $2;}'\\\"")")
        echo "VAL: \"${VAL}\" == ${Q} (eval ops -- based on Q)"
    ;;
    $(echo "${A}" | awk -F "|" '{print $1 | $2;}'))
        echo "VAL: \"${VAL}\" == $(echo "${A}" | awk -F "|" '{print $1 | $2;}') (constructed)"
    ;;
    "${A}")
        echo "VAL: \"${VAL}\" == ${A} (Single Variable)"
    ;;
    ${G})
        echo "VAL: \"${VAL}\" == ${G} (Eval Ops Variable)"
    ;; 
    # eval "echo \"${A}\""))
    # eval "\"\${A}\"")
    #     echo "VAL: \"${VAL}\" == ${A} (Eval Ops)"
    # ;;
    "${B}" | "${C}")
        echo "VAL: \"${VAL}\" == \"${B}\" | \"${C}\" (Multi Variable)"
    ;;
    1 | 2)
        echo "VAL: \"${VAL}\" == 1 | 2 (Literal)"
    ;;
    ${D})
        echo "VAL: \"${VAL}\" == ${D}"
    ;;
    *)
        echo "Ended up in the Default option"
    ;;
esac

