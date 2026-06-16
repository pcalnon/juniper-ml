# Citation Record — React Controlled `<input>` `onChange` and the Native-Setter Workaround

**Topic**: Why programmatically setting a React controlled `<input>`'s `.value` does NOT fire the
`onChange` handler, and the native-setter + dispatched-`input`-event workaround.

**Compiled for**: juniper-canopy design document (Playwright numeric-input automation wall; L3 POC #2
native-value-setter approach).

**Accessed**: 2026-06-16

---

## Sources

### 1. `<input>` — React (Primary)

- **Title**: `<input>` – React
- **Org/Author**: Meta (React core team) — official React documentation
- **URL**: <https://react.dev/reference/react-dom/components/input>
- **Accessed**: 2026-06-16
- **Classification**: **Primary** (official framework documentation)

### 2. Element: `input` event — MDN Web Docs (Primary)

- **Title**: Element: input event – Web APIs
- **Org/Author**: Mozilla / MDN Web Docs
- **URL**: <https://developer.mozilla.org/en-US/docs/Web/API/Element/input_event>
- **Accessed**: 2026-06-16
- **Classification**: **Primary** (authoritative web-platform reference)

### 3. EventTarget: `dispatchEvent()` method — MDN Web Docs (Primary)

- **Title**: EventTarget: dispatchEvent() method – Web APIs
- **Org/Author**: Mozilla / MDN Web Docs
- **URL**: <https://developer.mozilla.org/en-US/docs/Web/API/EventTarget/dispatchEvent>
- **Accessed**: 2026-06-16
- **Classification**: **Primary** (authoritative web-platform reference)

### 4. Event: `bubbles` property — MDN Web Docs (Primary)

- **Title**: Event: bubbles property – Web APIs
- **Org/Author**: Mozilla / MDN Web Docs
- **URL**: <https://developer.mozilla.org/en-US/docs/Web/API/Event/bubbles>
- **Accessed**: 2026-06-16
- **Classification**: **Primary** (authoritative web-platform reference)

### 5. "Bug: React breaks HTMLInputElement.prototype.value interceptions" #27092 — facebook/react (Secondary)

- **Title**: Bug: React breaks HTMLInputElement.prototype.value interceptions #27092
- **Org/Author**: GitHub issue on facebook/react (issue reporter; closed "not planned / Stale")
- **URL**: <https://github.com/facebook/react/issues/27092>
- **Accessed**: 2026-06-16
- **Classification**: **Secondary** (community bug report on the React tracker; confirms the mechanism
  but is not normative documentation)

### 6. "Trigger Input Updates with React Controlled Inputs" — Cory Rylan (Secondary)

- **Title**: Trigger Input Updates with React Controlled Inputs
- **Org/Author**: Cory Rylan (personal technical blog)
- **URL**: <https://coryrylan.com/blog/trigger-input-updates-with-react-controlled-inputs>
- **Accessed**: 2026-06-16
- **Classification**: **Secondary** (community writeup)

### 7. "Updating Input and Triggering onChange Event Programmatically in React" — Ben's Code Base (Secondary)

- **Title**: Updating Input and Triggering onChange Event Programmatically in React
- **Org/Author**: Benjamin Ray (personal technical blog, "Ben's Code Base")
- **URL**: <https://benjaminray.com/codebase/updating-input-and-triggering-onchange-event-in-react/>
- **Accessed**: 2026-06-16
- **Classification**: **Secondary** (community writeup; attributes the workaround to Stack Overflow
  answer <https://stackoverflow.com/a/46012210/4669143>)

---

## Key Claims (verbatim quotes ≤ 30 words)

### Root cause — React controlled-input model

1. **[Primary — React `<input>`, "Controlling an input with a state variable"]**
   > "To render a _controlled_ input, pass the `value` prop to it (or `checked` for checkboxes and
   > radios). React will force the input to always have the `value` you passed."

2. **[Primary — React `<input>`, "Caveats"]**
   > "Every controlled input needs an `onChange` event handler that synchronously updates its backing
   > value."

### Root cause — the `input` event does not fire on programmatic `.value`

3. **[Primary — MDN `input` event, main description]**
   > "The `input` event fires when the `value` of an `<input>`, `<select>`, or `<textarea>` element has
   > been changed as a direct result of a user action (such as typing in a textbox or checking a checkbox)."

4. **[Primary — MDN `input` event, main description]**
   > "Note that the `input` event is not fired when JavaScript changes an element's `value`
   > programmatically."

### Root cause — React overloads the value setter / value tracker

5. **[Secondary — facebook/react #27092, issue body]**
   > "React intercepting the HTMLInputElement.prototype.value itself, and not running functions that
   > were added **after** React loads."

6. **[Secondary — Cory Rylan]**
   > "React will overload the input value setter to know when the input state has been set and changed."

### Workaround — native setter + dispatched bubbling event

7. **[Secondary — Cory Rylan, workaround]**
   > "Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set.call(input,
   > Math.random().toString())"

8. **[Secondary — Cory Rylan, workaround]**
   > "input.dispatchEvent(new Event('change', { bubbles: true }))"

9. **[Secondary — Ben's Code Base, workaround code]**
   > "const nativeInputValueSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype,
   > 'value')?.set;"
   >
   > "const event = new Event('change', { bubbles: true });"

### Why the dispatched event reaches React's handler

10. **[Primary — MDN `dispatchEvent()`, main description]**
    > "The normal event processing rules (including the capturing and optional bubbling phase) also
    > apply to events dispatched manually with `dispatchEvent()`."

11. **[Primary — MDN `dispatchEvent()`, main description]**
    > "`dispatchEvent()` invokes event handlers _synchronously_. All applicable event handlers are
    > called and return before `dispatchEvent()` returns."

12. **[Primary — MDN `Event.bubbles`, "Value"]**
    > "A boolean value, which is `true` if the event bubbles up through the DOM tree."

---

## Synthesis (one paragraph, no quote)

A React controlled `<input>` renders with `value` bound to state and relies on `onChange` to update
that state. React installs its own descriptor over `HTMLInputElement.prototype.value` (its internal
"value tracker") so it can detect real changes; assigning `element.value = x` writes through React's
overloaded setter and updates the tracked baseline, so React sees no *delta* and never dispatches its
synthetic `onChange`. Independently, the DOM spec says the native `input` event "is not fired when
JavaScript changes an element's `value` programmatically." The fix is to (a) fetch the *native*
prototype setter via `Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set`
and `.call(input, value)` it — bypassing React's tracker so the tracked baseline and the visible value
diverge — then (b) `dispatchEvent(new Event('input', { bubbles: true }))` (often followed by a
`change` event and `blur`). Because `dispatchEvent` honors normal capturing/bubbling rules and runs
handlers synchronously, the bubbling synthetic event reaches React's delegated listener, which now
observes a delta against its tracker and fires `onChange`, updating state.

---

## Applies to canopy

juniper-canopy renders parameter controls as Dash `dcc.Input(type="number")`, which under the hood is
a **React controlled input**. This is the root cause of the Playwright numeric-input wall recorded in
project memory ("Playwright cannot drive Dash `dbc.Input(type=number)`"): when browser automation does
`element.value = x`, React's overloaded value tracker (sources 5–6) absorbs the write and the synthetic
`onChange` never fires, so the Dash clientside/serverside callback receives `null` and the Dash `State`
stays unset — matching MDN's statement that the `input` event "is not fired when JavaScript changes an
element's `value` programmatically" (source 3). The **L3 POC #2 native-value-setter** approach is the
canonical remedy documented here: obtain the native `HTMLInputElement.prototype` value setter via
`Object.getOwnPropertyDescriptor(...).set` (sources 7–9), call it on the input element, then dispatch a
**bubbling** `input` event (plus `change` + `blur` for Dash debounce/commit semantics). Per MDN
`dispatchEvent` (sources 10–11) the event propagates through React's delegated listener synchronously,
React detects the value delta, fires `onChange`, and the Dash callback finally receives the numeric
value. The pre-existing canopy fallback — POSTing directly to `/api/set_params` instead of driving the
widget — remains the simplest non-browser path; the native-value-setter is the in-browser equivalent
when the UI control itself must be exercised end-to-end.

---

### Resolution note

- `https://stackoverflow.com/a/46012210/4669143` — the canonical Stack Overflow answer that originated
  the `nativeInputValueSetter` workaround **could not be fetched** (Claude Code blocks stackoverflow.com).
  Its content is preserved here indirectly via sources 6 (Cory Rylan) and 7 (Ben's Code Base), both of
  which reproduce the same `Object.getOwnPropertyDescriptor(...).set` + `dispatchEvent` pattern; source 7
  explicitly attributes it to that Stack Overflow answer.
- All other URLs resolved and were fetched successfully.
