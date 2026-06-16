# Dash Testing — `dash.testing` / `dash_duo`

**Title:** Dash Testing — `dash.testing` and the `dash_duo` browser fixture
**Org:** Plotly / Dash (Dash for Python Documentation)
**Canonical URL(s):**

- Primary: <https://dash.plotly.com/testing>
- Markdown mirror (same content, served by docs site): <https://dash.plotly.com/testing.md>
- Plotly-owned reference test (verbatim input-driving example): <https://github.com/plotly/dash-component-boilerplate/blob/master/%7B%7Bcookiecutter.project_shortname%7D%7D/tests/test_usage.py>

**Accessed:** 2026-06-16

**Version context:** The official testing page documents `dash[testing]` / `dash_duo` without
version-gating the browser-fixture methods (`start_server`, `find_element`, `send_keys`,
`clear_input`, `wait_for_*`); these are stable from Dash 2.x onward and apply unchanged to our
environment (**dash 4.1.0** running, **4.2.0** in the lockfile). The only version-specific marker
seen on the page is **"New in Dash 2.6"**, which applies to *unit testing of callbacks*, not to the
`dash_duo` end-to-end fixture. Install is unchanged: `python -m pip install dash[testing]` (escape
the bracket in zsh: `dash\[testing]`).

---

## Key facts (verbatim quotes, <= 30 words each)

1. **End-to-end intent** — *"dash.testing also supports end-to-end tests. End-to-end tests run programmatically, start a real browser session, and click through the Dash app UI."* (Section: "End-to-End Tests")

2. **Fixture / server startup** — *"the `start_server` API from `dash_duo` is called. This hosts the defined Dash app within a Python `threading.Thread` and initializes a Selenium WebDriver to navigate to the local server URL."* (Section: testing.md — start_server behavior)

3. **WebDriver requirement** — *"We recommend the ChromeDriver WebDriver, which we use for dash end-to-end tests."* (Section: "Installing a WebDriver"); Firefox geckodriver is also supported via a run-time flag.

4. **Finding elements** — `find_element(selector)`: *"return the first found element by the `CSS selector`, shortcut to `driver.find_element_by_css_selector`"*. (Section: "Browser APIs")

5. **Clearing an input** — `clear_input()`: *"simulate key press to clear the input"*. (Section: "Browser APIs")

6. **Waiting on callback output** — `wait_for_text_to_equal(selector, text, timeout=None)`: *"explicit wait until the element's text equals the expected `text`"*. (Section: "Browser APIs")

7. **Element presence wait** — `wait_for_element(selector, timeout=None)`: *"shortcut to `wait_for_element_by_css_selector`"*; the css-selector / id variants are *"explicit wait until the element is present, shortcut to `WebDriverWait` with `EC.presence_of_element_located`"*. (Section: "Browser APIs")

8. **Raw Selenium escape hatch** — *"Both `dash_duo` and `dash_br` expose the Selenium WebDriver via the property `driver`, e.g. `dash_duo.driver`, which gives you full access to the Python Selenium API."* (Section: "Browser APIs")

### How numeric/text inputs are driven (verbatim, plotly-owned reference test)

The canonical input-driving pattern from Plotly's own `dash-component-boilerplate`
`tests/test_usage.py` — find the inner `<input>`, clear it, then send keystrokes via the
returned Selenium WebElement's `send_keys`, and assert on the callback output:

```python
dash_duo.start_server(app)

my_component = dash_duo.find_element('#input > input')

dash_duo.clear_input(my_component)

my_component.send_keys('Hello dash')

dash_duo.wait_for_text_to_equal('#output', 'You have entered Hello dash')
```

Key point: text is delivered through **Selenium's native `send_keys`** on the element handle
(real keystroke events), not by setting the DOM `value` property programmatically. The CSS
selector `'#input > input'` reaches the inner native `<input>` rendered inside the Dash
component wrapper.

Canonical layout-test example from the official docs (`https://dash.plotly.com/testing.md`),
showing fixture-as-argument, `start_server`, callback-aware waiting, and presence assertion:

```python
def test_001_child_with_0(dash_duo):
    app = dash.Dash()
    app.layout = html.Div(id="nully-wrapper", children=0)
    dash_duo.start_server(app)
    dash_duo.wait_for_text_to_equal("#nully-wrapper", "0", timeout=4)
    assert dash_duo.find_element("#nully-wrapper").text == "0"
    assert dash_duo.get_logs() == [], "browser console should contain no error"
    dash_duo.percy_snapshot("test_001_child_with_0-layout")
```

### Other Browser API methods cited (verbatim, Section "Browser APIs")

- `find_elements(selector)`: *"a list of all elements matching by the CSS selector"*.
- `multiple_click(selector, clicks)`: *"find the element with the `CSS selector` and clicks it with number of `clicks`"*.
- `take_snapshot(name)`: *"hook method to take a snapshot while Selenium test fails. the snapshot is placed under `/tmp/dash_artifacts`"*.
- `percy_snapshot(name, wait_for_callbacks=False)`: *"visual test API shortcut to `percy_runner.snapshot`"*.

### Wait subsystem (verbatim)

*"all custom wait conditions are defined in `dash.testing.wait`"*, and there are two extra APIs
`until` and `until_not` *"which are similar to the explicit wait with WebDriver."* CSS selector and
XPATH are the two locator strategies; the docs *"recommend using the CSS Selector in most cases"*.

---

## Applies to canopy

juniper-canopy's L3 real-browser regression layer needs to set values on `dcc.Input(type="number")`,
which Playwright cannot do — React's controlled `onChange` never fires on a programmatic value-set,
leaving the Dash `State` null (see MEMORY: "Playwright cannot drive Dash dbc.Input(type=number)").
`dash_duo` is the official, Plotly-supported fallback for the POC #1 numeric-input proof because:

- It drives inputs through **Selenium `send_keys` on the real `<input>` handle** (real keystroke
  events), so React's controlled `onChange` fires and the Dash `State` populates — exactly the gap
  Playwright leaves.
- `dash_duo.find_element('#<id> > input')` reaches the inner native `<input>` inside the Dash
  component wrapper; `clear_input(el)` then `el.send_keys('<n>')` is the documented set-value flow.
- `wait_for_text_to_equal('#output', ...)` gives a callback-aware assertion that the numeric value
  round-tripped through the Dash callback, which is the actual proof the L3 layer needs.
- Setup is `start_server(app)` in a threaded server + ChromeDriver; `dash_duo.driver` exposes raw
  Selenium if a step needs lower-level control. Install via `pip install dash[testing]`.
- No version concern at dash 4.1.0/4.2.0: the fixture API is unchanged from the 2.x docs (only the
  unrelated callback-unit-test feature is marked "New in Dash 2.6").

**Caveat for canopy:** this is a Selenium + chromedriver dependency (heavier than Playwright);
scope it to the numeric-input proofs rather than swapping the whole L3 harness.
