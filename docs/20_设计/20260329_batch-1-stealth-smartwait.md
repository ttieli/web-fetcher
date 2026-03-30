# Stealth + Smart Wait Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Inject anti-detection JavaScript into CDP and Selenium fetchers, and replace CDP's fixed-time wait with DOM-stability-based smart wait—boosting fetch success rate on anti-bot protected and SPA sites.

**Architecture:** A shared `STEALTH_JS` constant is injected before each navigation via CDP's `Page.addScriptToEvaluateOnNewDocument` (both fetchers support this). Smart wait polls `body.innerHTML.length` stability after `readyState === 'complete'`, exiting early for static sites and waiting longer for SPAs.

**Tech Stack:** Python 3.10+, pychrome (CDP), Selenium 4+ (`execute_cdp_cmd`), pure JavaScript injection (no new dependencies)

---

## File Structure

| File | Action | Responsibility |
|------|--------|----------------|
| `src/webfetcher/fetchers/cdp_fetcher.py` | Modify | Add stealth JS injection + smart wait |
| `src/webfetcher/fetchers/selenium.py` | Modify | Add stealth JS injection via `execute_cdp_cmd` |

---

### Task 1: Add shared stealth JS constant and inject into CDP fetcher

**Files:**
- Modify: `src/webfetcher/fetchers/cdp_fetcher.py`

- [ ] **Step 1.1: Add STEALTH_JS constant at module level**

Insert after the `CDP_AVAILABLE` check block (after line 21), before the `CDPFetchResult` class:

```python
# === STEALTH JS — Anti-bot detection bypass ===
# Injected before each navigation to mask automation fingerprints.
# Shared between CDP and Selenium fetchers.
STEALTH_JS = """
// 1. Remove webdriver flag (primary detection vector)
Object.defineProperty(navigator, 'webdriver', { get: () => undefined });

// 2. Fake chrome.runtime (Cloudflare checks this)
if (!window.chrome) {
  window.chrome = {};
}
if (!window.chrome.runtime) {
  window.chrome.runtime = {};
}

// 3. Fake plugins array (empty plugins = automation fingerprint)
Object.defineProperty(navigator, 'plugins', {
  get: () => [1, 2, 3, 4, 5],
});

// 4. Fake languages
Object.defineProperty(navigator, 'languages', {
  get: () => ['zh-CN', 'zh', 'en-US', 'en'],
});

// 5. Override permissions.query (notification permission detection)
if (navigator.permissions && navigator.permissions.query) {
  const originalQuery = navigator.permissions.query.bind(navigator.permissions);
  navigator.permissions.query = (parameters) =>
    parameters.name === 'notifications'
      ? Promise.resolve({ state: Notification.permission })
      : originalQuery(parameters);
}
"""
```

- [ ] **Step 1.2: Add `_inject_stealth` method to CDPFetcher class**

Insert after the `new_tab()` method (after line 156), before `fetch()`:

```python
    def _inject_stealth(self, tab):
        """Inject stealth JS to mask automation fingerprints.

        Uses Page.addScriptToEvaluateOnNewDocument so the script runs
        before any page JS on every navigation (including redirects).
        Falls back to Runtime.evaluate if the CDP command isn't available.
        """
        try:
            tab.call_method("Page.addScriptToEvaluateOnNewDocument", source=STEALTH_JS)
            logger.debug("Stealth JS injected via Page.addScriptToEvaluateOnNewDocument")
        except Exception:
            # Fallback: inject after navigation (less reliable but still useful)
            try:
                tab.Runtime.evaluate(expression=STEALTH_JS)
                logger.debug("Stealth JS injected via Runtime.evaluate (fallback)")
            except Exception as e:
                logger.debug(f"Stealth JS injection failed (non-fatal): {e}")
```

- [ ] **Step 1.3: Call `_inject_stealth` in `fetch()` before navigation**

In the `fetch()` method, find the block where the tab navigates AND the shared `_wait_for_ready` call (lines 184-192). Replace the entire block including the wait call:

Find:
```python
            # 选择或创建标签页
            if use_existing_tab and self.current_tab:
                tab = self.current_tab
                tab.Page.navigate(url=url)
            else:
                tab = self.new_tab(url)

            # 等待页面加载（智能轮询 readyState）
            self._wait_for_ready(tab, timeout=wait_time)
```

Replace with:
```python
            # 选择或创建标签页
            if use_existing_tab and self.current_tab:
                tab = self.current_tab
                self._inject_stealth(tab)
                tab.Page.navigate(url=url)
            else:
                tab = self.new_tab()
                self._inject_stealth(tab)
                tab.Page.navigate(url=url)

            # 等待页面加载（智能等待：readyState + DOM 稳定性检测）
            self._wait_for_ready(tab, timeout=wait_time)
```

Note: `new_tab()` is called without URL so we can inject stealth before first navigation. The shared `_wait_for_ready` call applies to both branches (no duplication).

- [ ] **Step 1.4: Verify CDP fetcher compiles**

Run:
```bash
cd "." && PYTHONPATH=src python -c "from webfetcher.fetchers.cdp_fetcher import CDPFetcher, STEALTH_JS; print(f'STEALTH_JS length: {len(STEALTH_JS)} chars'); print('OK')"
```

Expected: `STEALTH_JS length: ~700 chars` and `OK`

- [ ] **Step 1.5: Commit**

```bash
git add src/webfetcher/fetchers/cdp_fetcher.py
git commit -m "feat: add stealth JS injection to CDP fetcher

Injects anti-detection JS before each navigation via
Page.addScriptToEvaluateOnNewDocument (with Runtime.evaluate fallback).
Masks navigator.webdriver, chrome.runtime, plugins, languages,
and permissions.query fingerprints."
```

---

### Task 2: Inject stealth JS into Selenium fetcher

**Files:**
- Modify: `src/webfetcher/fetchers/selenium.py`

- [ ] **Step 2.1: Import STEALTH_JS from cdp_fetcher**

Near the top of selenium.py, find the conditional import block for requests (around line 59-63). After it, add:

```python
# Stealth JS for anti-bot bypass (shared with CDP fetcher)
try:
    from webfetcher.fetchers.cdp_fetcher import STEALTH_JS
    _STEALTH_JS_AVAILABLE = True
except ImportError:
    _STEALTH_JS_AVAILABLE = False
    STEALTH_JS = ""
```

- [ ] **Step 2.2: Inject stealth after Chrome connection succeeds**

In `connect_to_chrome()`, after the successful connection block (after line 999, right before the notification block), add stealth injection:

Find:
```python
                logging.info(f"✓ Connected to Chrome debug session on {debugger_address} in {connection_time:.2f}s")

                # Solution E: Show browser notification if enabled
```

Replace with:
```python
                logging.info(f"✓ Connected to Chrome debug session on {debugger_address} in {connection_time:.2f}s")

                # Inject stealth JS to mask automation fingerprints
                if _STEALTH_JS_AVAILABLE and STEALTH_JS:
                    try:
                        self.driver.execute_cdp_cmd(
                            'Page.addScriptToEvaluateOnNewDocument',
                            {'source': STEALTH_JS}
                        )
                        logging.info("Stealth JS injected via CDP command")
                    except Exception as e:
                        logging.debug(f"Stealth JS injection failed (non-fatal): {e}")

                # Solution E: Show browser notification if enabled
```

- [ ] **Step 2.3: Add `--disable-blink-features=AutomationControlled` to Chrome options**

In `connect_to_chrome()`, find the Chrome options block (lines 975-979). Add the anti-automation flag:

Find:
```python
                # Phase 2: Error suppression options (Selenium layer)
                # Note: --log-level and --disable-logging help reduce Chrome console noise
                options.add_argument('--log-level=3')  # Level 3 = FATAL only
                options.add_argument('--disable-logging')
                options.add_argument('--silent')
```

Replace with:
```python
                # Phase 2: Error suppression options (Selenium layer)
                # Note: --log-level and --disable-logging help reduce Chrome console noise
                options.add_argument('--log-level=3')  # Level 3 = FATAL only
                options.add_argument('--disable-logging')
                options.add_argument('--silent')
                # Anti-automation detection: disable blink automation flag at engine level
                options.add_argument('--disable-blink-features=AutomationControlled')
```

- [ ] **Step 2.4: Verify Selenium fetcher compiles**

Run:
```bash
cd "." && PYTHONPATH=src python -c "from webfetcher.fetchers.selenium import SeleniumFetcher; print('OK')"
```

Expected: `OK`

- [ ] **Step 2.5: Commit**

```bash
git add src/webfetcher/fetchers/selenium.py
git commit -m "feat: add stealth JS injection to Selenium fetcher

Imports STEALTH_JS from cdp_fetcher and injects via
execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument') after
Chrome connection. Also adds --disable-blink-features=AutomationControlled
to Chrome options for engine-level anti-automation masking."
```

---

### Task 3: Replace fixed wait with DOM-stability smart wait in CDP fetcher

**Files:**
- Modify: `src/webfetcher/fetchers/cdp_fetcher.py`

- [ ] **Step 3.1: Replace `_wait_for_ready()` with smart wait implementation**

Find the entire `_wait_for_ready` method (lines 232-251):

```python
    def _wait_for_ready(self, tab, timeout: float = 10, poll_interval: float = 0.3):
        """
        等待页面加载完成（轮询 document.readyState）

        Args:
            tab: CDP tab object
            timeout: 最大等待时间（秒）
            poll_interval: 轮询间隔（秒）
        """
        deadline = time.time() + timeout
        while time.time() < deadline:
            try:
                state = self._eval_js(tab, "document.readyState")
                if state == "complete":
                    logger.debug(f"Page ready in {timeout - (deadline - time.time()):.1f}s")
                    return
            except Exception:
                pass
            time.sleep(poll_interval)
        logger.debug(f"Page load timeout after {timeout}s, proceeding anyway")
```

Replace with:

```python
    def _wait_for_ready(self, tab, timeout: float = 15, poll_interval: float = 0.5):
        """
        Smart wait: readyState + DOM content stability detection.

        Phase 1: Wait for document.readyState === 'complete'
        Phase 2: After readyState complete, monitor body.innerHTML.length
                 until it stabilizes (2 consecutive checks with same length)

        This exits quickly for static sites (~0.5s) and waits longer
        for SPAs that render content asynchronously (~2-10s).

        Args:
            tab: CDP tab object
            timeout: Maximum total wait time in seconds (hard cap)
            poll_interval: Check interval in seconds
        """
        deadline = time.time() + timeout
        ready_state_done = False
        prev_body_len = -1
        stable_count = 0
        STABLE_THRESHOLD = 2  # consecutive checks with same length = stable

        while time.time() < deadline:
            try:
                result = self._eval_js(tab, """
                    JSON.stringify({
                        state: document.readyState,
                        bodyLen: document.body ? document.body.innerHTML.length : 0
                    })
                """)

                if result:
                    status = json.loads(result)
                    state = status.get('state', '')
                    body_len = status.get('bodyLen', 0)

                    # Phase 1: Wait for readyState complete
                    if not ready_state_done:
                        if state == 'complete':
                            ready_state_done = True
                            prev_body_len = body_len
                            logger.debug(f"readyState complete, body={body_len} chars, checking stability...")
                    else:
                        # Phase 2: Check DOM stability
                        if body_len == prev_body_len and body_len > 0:
                            stable_count += 1
                            if stable_count >= STABLE_THRESHOLD:
                                elapsed = timeout - (deadline - time.time())
                                logger.debug(f"DOM stable after {elapsed:.1f}s (body={body_len} chars)")
                                return
                        else:
                            stable_count = 0
                            prev_body_len = body_len

            except Exception:
                pass

            time.sleep(poll_interval)

        logger.debug(f"Smart wait timeout after {timeout}s, proceeding anyway")
```

- [ ] **Step 3.2: Update default wait_time in fetch() to 15s**

The `fetch()` method currently defaults to `wait_time: float = 3.0`. Smart wait exits early anyway, so we can raise the ceiling to give SPAs more room.

Find (line 158):
```python
    def fetch(self, url: str, wait_time: float = 3.0, use_existing_tab: bool = True) -> CDPFetchResult:
```

Replace with:
```python
    def fetch(self, url: str, wait_time: float = 15.0, use_existing_tab: bool = True) -> CDPFetchResult:
```

Also update `fetch_with_cdp` at line 329:

Find:
```python
def fetch_with_cdp(url: str, wait_time: float = 3.0, **kwargs) -> Tuple[str, str, dict]:
```

Replace with:
```python
def fetch_with_cdp(url: str, wait_time: float = 15.0, **kwargs) -> Tuple[str, str, dict]:
```

- [ ] **Step 3.3: Verify the smart wait compiles and basic logic works**

Run:
```bash
cd "." && PYTHONPATH=src python -c "
from webfetcher.fetchers.cdp_fetcher import CDPFetcher, fetch_with_cdp, STEALTH_JS
import inspect
# Verify _wait_for_ready has smart wait logic
source = inspect.getsource(CDPFetcher._wait_for_ready)
assert 'stable_count' in source, 'Missing stable_count'
assert 'STABLE_THRESHOLD' in source, 'Missing STABLE_THRESHOLD'
assert 'bodyLen' in source, 'Missing bodyLen check'
print('Smart wait implementation verified')

# Verify default wait_time raised
sig = inspect.signature(CDPFetcher.fetch)
assert sig.parameters['wait_time'].default == 15.0, f'Expected 15.0, got {sig.parameters[\"wait_time\"].default}'
print('Default wait_time = 15.0s verified')
print('OK')
"
```

Expected: All assertions pass, `OK`

- [ ] **Step 3.4: Commit**

```bash
git add src/webfetcher/fetchers/cdp_fetcher.py
git commit -m "feat: replace fixed wait with DOM-stability smart wait

Phase 1: poll document.readyState until 'complete'
Phase 2: monitor body.innerHTML.length stability (2 consecutive
identical checks = content settled)

Static sites exit in ~0.5s, SPAs wait until content renders (up to 15s).
Replaces fixed 3s wait_time with adaptive 15s ceiling."
```

---

### Task 4: End-to-end verification

- [ ] **Step 4.1: Verify both fetchers import cleanly**

Run:
```bash
cd "." && PYTHONPATH=src python -c "
from webfetcher.fetchers.cdp_fetcher import CDPFetcher, STEALTH_JS, fetch_with_cdp
from webfetcher.fetchers.selenium import SeleniumFetcher
from webfetcher.core import fetch_html_with_retry
print(f'STEALTH_JS: {len(STEALTH_JS)} chars')
print('All imports OK')
"
```

Expected: No import errors, STEALTH_JS ~700 chars.

- [ ] **Step 4.2: Verify stealth JS content is valid JavaScript**

Run:
```bash
cd "." && PYTHONPATH=src python -c "
from webfetcher.fetchers.cdp_fetcher import STEALTH_JS
# Check key stealth signatures are present
assert 'navigator' in STEALTH_JS and 'webdriver' in STEALTH_JS, 'Missing webdriver override'
assert 'chrome' in STEALTH_JS and 'runtime' in STEALTH_JS, 'Missing chrome.runtime'
assert 'plugins' in STEALTH_JS, 'Missing plugins override'
assert 'languages' in STEALTH_JS, 'Missing languages override'
assert 'permissions' in STEALTH_JS, 'Missing permissions override'
print('All 5 stealth signatures present')
print('OK')
"
```

- [ ] **Step 4.3: Test full wf fetch still works (regression)**

Run:
```bash
cd "." && PYTHONPATH=src python -m webfetcher.core --stdout --fetch-mode urllib "https://www.baidu.com" 2>/dev/null | head -5
```

Expected: Normal fetch output (urllib doesn't use stealth, so this is a regression check).

No commit needed for verification.

---

## Risk Mitigation Notes

1. **Stealth injection failure is non-fatal**: Both CDP and Selenium paths wrap injection in try/except. If `Page.addScriptToEvaluateOnNewDocument` isn't available, we fall back to `Runtime.evaluate`. If that also fails, we log and continue — fetch works normally, just without stealth.

2. **Smart wait backward compatibility**: The new `_wait_for_ready` still respects the `timeout` parameter. If DOM monitoring fails (e.g., JS error), the loop continues until timeout — same behavior as before, just with a higher default ceiling.

3. **No new dependencies**: Everything is pure JS strings and existing CDP/Selenium APIs. No pip install needed.

4. **`--disable-blink-features=AutomationControlled`**: This Chrome flag only affects newly started Chrome instances. Since wf connects to an existing debug session, the flag is passed via Selenium options but may be ignored if Chrome was started without it. This is a best-effort enhancement — the JS injection is the primary defense.
