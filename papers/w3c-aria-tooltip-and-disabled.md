# W3C WAI-ARIA: Tooltip Pattern & `aria-disabled` vs HTML `disabled`

Authoritative external literature for the juniper-canopy compatibility-gated dropdown design
(wrapper-targeted tooltip + soft-gate). All quotes below are verbatim from pages that were
successfully fetched. Quotes are <= 30 words each.

---

## Source 1 — ARIA Authoring Practices Guide (APG): Tooltip Pattern

- **Title:** Tooltip Pattern | APG | WAI | W3C
- **Org:** W3C (Web Accessibility Initiative — ARIA Authoring Practices Guide)
- **Canonical URL:** <https://www.w3.org/WAI/ARIA/apg/patterns/tooltip/>
- **Accessed:** 2026-06-16

**Key claims (verbatim quotes):**

1. *About This Pattern* — "A tooltip is a popup that displays information related to an element
   when the element receives keyboard focus or the mouse hovers over it."
2. *WAI-ARIA Roles, States, and Properties* — "The element that triggers the tooltip references
   the tooltip element with aria-describedby."
3. *WAI-ARIA Roles, States, and Properties* — "The element that serves as the tooltip container
   has role tooltip."
4. *Keyboard Interaction* — "Escape: Dismisses the Tooltip."

---

## Source 2 — ARIA Authoring Practices Guide (APG): Developing a Keyboard Interface

- **Title:** Developing a Keyboard Interface | APG | WAI | W3C
- **Org:** W3C (Web Accessibility Initiative — ARIA Authoring Practices Guide)
- **Canonical URL:** <https://www.w3.org/WAI/ARIA/apg/practices/keyboard-interface/>
- **Accessed:** 2026-06-16

**Key claims (verbatim quotes):**

1. *Focusability of disabled controls* — "Browsers remove HTML input elements with the `disabled`
   attribute from the tab sequence."
2. *Focusability of disabled controls* — "However, there are some contexts where it is useful for
   an element to convey a disabled state while remaining focusable, especially inside of composite
   widgets. This can be accomplished by applying the state `aria-disabled="true"`."
3. *Focusability of disabled controls* — "When a disabled element _does_ need to remain
   discoverable, `aria-disabled="true"` is applied so that it will remain focusable."

---

## Source 3 — Accessible Rich Internet Applications (WAI-ARIA): `aria-disabled` (state)

- **Title:** Supported States and Properties — `aria-disabled` (state), Accessible Rich Internet
  Applications (WAI-ARIA)
- **Org:** W3C (WAI-ARIA Recommendation — normative state/property definitions)
- **Canonical URL:** <https://www.w3.org/TR/wai-aria-1.0/states_and_properties>
  (definition section `#aria-disabled`; same normative text carried forward in WAI-ARIA 1.1 / 1.2)
- **Accessed:** 2026-06-16

**Key claims (verbatim quotes):**

1. *aria-disabled (state)* — "Indicates that the element is perceivable but disabled, so it is not
   editable or otherwise operable."
2. *aria-disabled (state)* — "Disabled elements might not receive focus from the tab order."
3. *aria-disabled (state)* — "For some disabled elements, applications might choose not to support
   navigation to descendants."

> Note: the `#aria-disabled` anchor under the WAI-ARIA 1.1 and 1.2 `/TR/` pages was not directly
> extractable (the fetched body truncated before the States & Properties definition section).
> The definition above is from the W3C-published WAI-ARIA 1.0 `states_and_properties` page, where
> the same normative wording originates and is carried forward unchanged in 1.1/1.2.

---

## Source 4 (SECONDARY) — MDN: `aria-disabled`

- **Title:** aria-disabled — ARIA | MDN
- **Org:** MDN (Mozilla — secondary corroborating source, clearly labeled secondary)
- **Canonical URL:** <https://developer.mozilla.org/en-US/docs/Web/Accessibility/ARIA/Reference/Attributes/aria-disabled>
- **Accessed:** 2026-06-16

**Key claims (verbatim quotes):**

1. *Description* — "the `aria-disabled="true"` **only** semantically exposes these elements as
   being disabled. Web developers must manually ensure such elements have their functionality
   suppressed when exposed to the disabled state."
2. *Description* — "they will not be removed from the focus order of the web page, as
   `aria-disabled` does not change the focusability of such elements".
3. *Description* — "Unlike HTML's `disabled` Boolean attribute, which will communicate a form
   control as semantically being disabled, change its styling ... and suppress all functionality".

---

## Applies to canopy

The compatibility-gated dropdown design ("soft gate" + wrapper-targeted tooltip) is directly
justified by the W3C guidance above:

- **Why not native `disabled`:** Per Source 2, browsers remove a natively `disabled` control from
  the tab sequence; per Source 3 such elements "might not receive focus from the tab order." A
  control that is never focused/hovered fires no events, so a tooltip explaining *why* an option is
  unavailable can never surface. Native `disabled` also visually dims the control (Source 4).
- **Why `aria-disabled="true"` (soft gate):** Source 2 endorses exactly our use case — "it is
  useful for an element to convey a disabled state while remaining focusable" — and Source 4
  confirms `aria-disabled` "does not change the focusability of such elements," keeping the
  incompatible option in the focus order so the explanation is *discoverable*. Source 4 also warns
  the gate is semantic-only: canopy must **manually suppress** selection of the gated option
  (reject the value / no-op the callback), since `aria-disabled` does not block activation.
- **Tooltip wiring (wrapper-targeted):** Per Source 1, the trigger references the tooltip via
  `aria-describedby` and the popup container carries `role="tooltip"`; it appears on focus *or*
  hover. Because the gated item stays focusable, wiring `aria-describedby` from the (wrapper)
  trigger to a `role="tooltip"` element lets the "incompatible because…" explanation show on both
  hover and keyboard focus, and `Escape` dismisses it (Source 1, Keyboard Interaction).

Net: keep the gated dropdown option `aria-disabled="true"` (not HTML `disabled`) inside/served by a
focusable wrapper, attach a `role="tooltip"` element via `aria-describedby`, and enforce the gate
in application logic.

---

### URL resolution note

All four cited pages were fetched successfully. One anchor did not resolve as a directly
extractable definition: the `#aria-disabled` state definition under `https://www.w3.org/TR/wai-aria-1.2/`
(and the 1.1 equivalent) truncated before the States & Properties section; the canonical W3C
definition was instead sourced from `https://www.w3.org/TR/wai-aria-1.0/states_and_properties`
(same normative wording). No 404s; no fabricated URLs or quotes.
