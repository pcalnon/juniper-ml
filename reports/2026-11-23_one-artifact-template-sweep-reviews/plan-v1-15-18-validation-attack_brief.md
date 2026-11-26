# Lens B: the completeness and consequence attack

Read `tmp/v1_15_18/val/VALIDATION_BRIEF_COMMON.md` first; it is part of this brief. Your output directory is
`tmp/v1_15_18/val/attack/`.

Your lens: what the draft leaves out, what it concludes wrongly from true premises, and where it contradicts the rest
of the plan. Grant the facts the other lens checks; attack the record's completeness and its conclusions.

1. **Omissions.** Build the list of what v1.15.18 must record from the sources, then check each against the draft:
   - `prompts/thread-handoff_automated-prompts/HANDOFF_2026-11-26_one-artifact-sweep-all-ports-landed-18-of-18-plan-v1-15-18-next.md`
     § "Remaining work: plan v1.15.18" (items 1 to 4, and what "It lands");
   - its predecessors' plan items (`HANDOFF_2026-11-25_…`, `HANDOFF_2026-11-24_…` ×2, `HANDOFF_2026-11-23_one-artifact-sweep-…`);
   - `…/ethereal-munching-peacock/tmp/arc/plan_v1_15_18_inputs.md` (every bullet);
   - `notes/JUNIPER_2026-11-23_JUNIPER-ECOSYSTEM_R-OBS-SC-2-FOLLOW-UPS-REMAINING-TASKS.md`: group C (R28 to R41), group E
     (R58 to R65) and §4's gaps 1 to 9 (and 16), each of which this revision is meant to take in;
   - every sentence in `REVIEW_DISPOSITIONS.md` that says "plan v1.15.18" or "record" (`command grep -n -i -e 'v1.15.18' -e 'record it' -e 'record in'`),
     and its residual lists (§ "Fix pass 10" "Residual risk", § "Fix pass 11" "Residuals for plan v1.15.18").
   For each item: RECORDED (quote where), MISSING, or MISREPRESENTED.
2. **Stale lines left behind.** Search the WHOLE post-edit plan for passages the arc has made false that the draft does
   not mark (for example: "Symlinks", "#772", "0.8.0", "eeb5c694", "0.4.0 and service-core 0.5.0", "No Release",
   "the ports", "sweep PR", "is open", "None is done", "worktree housekeeping", "plan v1.15.18"). For each, say whether
   it is still true, and if not, what a `v1.15.18:` note there should say.
3. **Conclusions.** Attack every sentence that draws a conclusion ("so", "therefore", "which cleared", "closes", "only",
   "every", "all", "none"): is the conclusion what the premises support, or a stronger claim? The arc's documented
   failure mode is a correct mechanism paired with a wrong consequence.
4. **Actionability.** Would a successor be misled about what is done, what is open, and who owns it (a session or the
   Overtoad)? Are the "What remains" and "Left with the Overtoad" lists complete and non-contradictory with each other
   and with §6?
5. **Internal consistency** of the new text with itself (counts, dates, names, the order of events).
