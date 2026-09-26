# Defect-register round 42 -- the owner's "Key leaks" ruling, verbatim

Extracted by `util/ad-hoc/2026-09-24_extract_mixed_provenance_rulings.py --topic key-leaks` from the session transcripts. It
selects every AskUserQuestion call with a question headed "Key leaks" and keeps the WHOLE call. The questions and options
are the call's input as sent, JSON-dumped; the answer is the tool_result as returned. Nothing is paraphrased.

## Session `bc31e993`, asked 2026-09-24T10:22:00.792Z, answered 2026-09-24T18:30:09.820Z

Question(s) and options, as sent:

```json
[
  {
    "question": "canopy#683's validation found two HIGH secret-exposure defects that predate #683. (1) A padded outbound key (cascor/data/recurrence, e.g. a k8s secret's trailing newline) is quoted in client errors that canopy logs at ERROR, sends to Sentry, and returns in API bodies. With auth on, an anonymous caller reads the cascor key from POST /api/train/start's 409. (2) An anonymous non-ASCII X-API-Key makes compare_digest raise, and Sentry's default local-variable capture records the real canopy key. The sibling compare loops share that shape. How far should this session fix it?",
    "header": "Key leaks",
    "multiSelect": false,
    "options": [
      {
        "label": "Fix everywhere now (Recommended)",
        "description": "Up to four PRs. canopy: check outbound keys where they're read, stop returning transport errors in API bodies, compare keys as bytes, plus #683's two LOW gaps. juniper-ml: observability stops capturing local variables, and service-core compares as bytes. juniper-data and juniper-cascor: bytes compare, keeping the drift-gate markers. Releases stay yours."
      },
      {
        "label": "Fix canopy now, file rest",
        "description": "One canopy PR here closes both leaks in canopy. The ecosystem-wide Sentry and compare_digest issue goes to the other session's register as rows for a later ruling."
      },
      {
        "label": "File everything",
        "description": "No code now. The other session files all of it as register rows for your ruling, and #683 merges as it is."
      }
    ]
  }
]
```

Answer, as returned:

```text
Your questions have been answered: "canopy#683's validation found two HIGH secret-exposure defects that predate #683. (1) A padded outbound key (cascor/data/recurrence, e.g. a k8s secret's trailing newline) is quoted in client errors that canopy logs at ERROR, sends to Sentry, and returns in API bodies. With auth on, an anonymous caller reads the cascor key from POST /api/train/start's 409. (2) An anonymous non-ASCII X-API-Key makes compare_digest raise, and Sentry's default local-variable capture records the real canopy key. The sibling compare loops share that shape. How far should this session fix it?"="Fix everywhere now (Recommended)". You can now continue with these answers in mind.
```
