# NNg Guidance: Disabled / Greyed-Out Buttons and Controls

Citation record for the juniper-canopy model-selection compatibility-gating design.
All quotes below are verbatim from pages that were successfully fetched on the access
date. No fabricated URLs or quotes.

---

## Source 1 — Button States: Communicate Interaction

- **Title**: Button States: Communicate Interaction
- **Author / Org**: Kelley Gordon, Nielsen Norman Group
- **Published**: April 25, 2025
- **Canonical URL**: <https://www.nngroup.com/articles/button-states-communicate-interaction/>
- **Accessed**: 2026-06-16

### Key claims (verbatim quotes)

1. *Section "Disabled State"* — "This state **indicates that the button's action is
   unavailable** — the button can't currently be clicked or tapped."
2. *Section "Disabled State"* — "A light gray or otherwise desaturated color or a more
   muted version of its abled state to signal it isn't clickable or tappable"
3. *Section "Disabled State"* — "_Disabled_ button states should also have the
   _ARIA-disabled: true_ attribute added to the code."
4. *Section "Disabled State"* — "This attribute will allow the button to still receive
   tab focus but will indicate to screen readers that the button is inactive"

**Applies to canopy**: Disabled model×dataset options must read as unavailable (claim 1)
and use a desaturated/greyed treatment (claim 2). Claims 3–4 are the direct fix for the
"disabled controls fire no hover/focus events" problem: render incompatible options with
`aria-disabled="true"` rather than the native `disabled` attribute so the control still
takes tab focus and can surface the compatibility reason to keyboard and screen-reader
users.

---

## Source 2 — Tooltip Guidelines

- **Title**: Tooltip Guidelines
- **Author / Org**: Alita Kendrick, Nielsen Norman Group
- **Published**: January 27, 2019
- **Canonical URL**: <https://www.nngroup.com/articles/tooltip-guidelines/>
- **Accessed**: 2026-06-16

### Key claims (verbatim quotes)

5. *Section "Defining Tooltips"* — "A **tooltip** is a brief, informative message that
   appears when a user interacts with an element in a graphical user interface (GUI)."
6. *Section "Tooltip-Usage Guidelines", Guideline 3 ("Support both mouse and keyboard
   hover")* — "Tooltips that appear only on mouse hover are inaccessible for users that
   rely on keyboards to navigate."

**Applies to canopy**: A tooltip is the right vehicle for the "why is this disabled"
message (claim 5), but it must not be hover-only (claim 6). The gating UI must trigger
the explanatory tooltip on keyboard focus as well as mouse hover — which is only possible
if the option remains focusable (see Source 1, claims 3–4), since a natively `disabled`
control receives neither hover nor focus.

---

## Source 3 — Why Disabled Buttons Hurt UX (and How to Fix Them) [Video]

- **Title**: Why Disabled Buttons Hurt UX (and How to Fix Them) (Video)
- **Author / Org**: Huei-Hsin Wang, Nielsen Norman Group
- **Published**: August 25, 2025
- **Canonical URL**: <https://www.nngroup.com/videos/why-disabled-buttons-hurt-ux-and-how-to-fix-them/>
- **Accessed**: 2026-06-16
- *Note*: Video page. The video transcript was not exposed to the fetcher; the quote
  below is the verbatim page summary (NNg-authored editorial copy), not a transcript line.

### Key claims (verbatim quote)

7. *Page summary* — "Disabled buttons often confuse users by appearing clickable but
   providing no response or feedback. Designers should use them sparingly, ensure they're
   accessible, and clearly explain why the button is disabled."

**Applies to canopy**: Direct authority for two design pillars — (a) prefer soft-gating
and use hard-disable sparingly, and (b) a disabled control must clearly explain *why* it
is disabled. For the compatibility dropdown this argues for keeping incompatible options
visible-but-gated with an inline reason ("incompatible with the selected dataset") rather
than silently removing or inertly greying them.

---

## Negative result (do not cite)

- <https://www.nngroup.com/articles/disabled-accessibility-the-pragmatic-approach/> —
  fetched successfully, but it is Jakob Nielsen (1999) on staged WAI/accessibility-standard
  rollout, **not** about disabled-button UX. The title is a false match; excluded from
  citations.

## Synthesis for the design doc

- **Disable vs soft-gate (a)**: Source 3 — disable sparingly; keep gated options visible
  with a stated reason.
- **Communicate WHY (b)**: Source 3 (clearly explain why) + Source 2 claim 5 (tooltip as
  the message vehicle).
- **Disabled elements fire no hover/focus, so a tooltip on a `disabled` control never
  appears (c)**: Source 1 claims 3–4 (use `aria-disabled` to keep tab focus + screen-reader
  awareness) + Source 2 claim 6 (tooltip must work on keyboard focus, not hover-only).
