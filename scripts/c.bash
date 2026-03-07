#!/usr/bin/env bash

A="1 | 2"

# input="1"
# input="2"
# input="1 | 2"
input="${input:-2}"

echo "A: ${A}"

echo "Full Eval:"
eval "case \"\$input\" in
    ${A})
        echo \"  MATCH   — '\$input' matched pattern: ${A}\"
    ;;
    *)
        echo \"  NO MATCH — '\$input' did not match pattern: ${A}\"
    ;;
esac"

echo "Partial Eval:"
# Must use eval: when pattern comes from expansion, | is literal. Eval injects ${A}
# at parse time so "1 | 2" is parsed as alternation (match "1" or "2").
eval "case \"\$input\" in
    ${A})
        echo \"  MATCH   — '\$input': \${input} matched eval'd pattern: ${A}\"
    ;;
    *)
        echo \"  NO MATCH — '\$input': \${input} did not match eval'd pattern: ${A}\"
    ;;
esac"

echo "done"
