# Architecture Optimization & Review

## Overview

This document analyzes the `webfetcher` architecture, specifically focusing on the fetcher fallback mechanism (`urllib` -> `CDP` -> `Selenium`), resource management, and opportunities for optimization.

## Current Architecture

### 1. Workflow (`fetch_html_with_retry`)

The main entry point is `fetch_html_with_retry` in `src/webfetcher/core.py`. It implements a sequential fallback chain:

1.  **Config-Driven Routing:** Checks `routing.yaml` via `RoutingEngine`. If a specific fetcher is mandated (e.g., `selenium` for `xiaohongshu.com`), it jumps directly to that fetcher.
2.  **Default Flow (Auto Mode):**
    *   **Step 1: `urllib` (Standard Request):**
        *   Attempts to fetch content using `urllib.request`.
        *   **Retry Logic:** Retries up to 3 times for transient errors (timeouts, network issues).
        *   **Optimization Opportunity:** The current retry logic is "retry-first". For specific errors like 403 (Forbidden/Anti-bot) or 412 (Precondition Failed), retrying `urllib` is usually futile. A "Fail-Fast" mechanism should be implemented to skip retries and immediately fallback to CDP/Selenium for these specific status codes.
    *   **Step 2: CDP Fallback:**
        *   Triggered if `urllib` fails (exhausts retries or hits fatal error).
        *   Uses `CDPFetcher` (`pychrome`) to connect to a Chrome instance on port 9222.
        *   **Mechanism:** It tries to attach to an existing tab or create a new one, waits for page load (default 3s), and retrieves the rendered DOM (`outerHTML`).
        *   **Advantage:** Significantly lighter than Selenium; reuses the browser session (cookies/login state).
    *   **Step 3: Selenium Fallback:**
        *   Triggered if CDP fails (e.g., Chrome not running, connection refused).
        *   Uses `ensure_chrome_debug.sh` to check/start Chrome.
        *   Uses Selenium Remote WebDriver to connect.
        *   **Observation:** This step is largely redundant if CDP is working correctly, as both rely on the same underlying Chrome instance. However, Selenium provides better driver management and element interaction if deep interaction is needed.
    *   **Step 4: Manual Chrome (Last Resort):**
        *   If all automation fails, it prompts the user to open the browser manually.

### 2. Resource Management

*   **CDP Connections:** `CDPFetcher` initializes a new `pychrome.Browser` connection for every single fetch request (`connect` method).
    *   **Optimization:** For batch processing (future feature), a persistent browser connection object would reduce overhead. For CLI single-url usage, the current approach is acceptable.
*   **Chrome Process:** The system relies on an external Chrome process (managed via shell scripts in `src/webfetcher/config/`). The `ensure_chrome_debug.sh` script is robust (handles PID checking, port conflicts, and timeouts).

## Proposed Optimizations

### 1. Fail-Fast Strategy for `urllib`

Currently, `fetch_html_with_retry` retries all exceptions. We should modify it to immediately trigger fallback for definitive anti-bot signals.

**Implementation Plan:**
- In `fetch_html_with_retry`, catch `urllib.error.HTTPError`.
- If status code is `403`, `412`, or `429`, skip the remaining `urllib` retries and call `_try_cdp_fallback_after_urllib_failure` immediately.

### 2. "Empty Content" Detection

A common issue with SPA (Single Page Application) sites is that `urllib` returns `200 OK` but the content is essentially empty (e.g., just `<div id="root"></div>` and `<script>` tags). The current logic considers this a "success", leading to empty Markdown files.

**Implementation Plan:**
- In `fetch_html_original` (or immediately after), inspect the retrieved HTML.
- **Heuristic:** If `len(html) < 500` bytes (configurable) OR if the ratio of script tags to text content is extremely high, treat it as a "soft failure".
- Trigger CDP fallback for these "soft failures" even if the HTTP status was 200.

### 3. Enhanced Error Reporting

The error chain can be obscure (e.g., "urllib failed... CDP failed...").

**Implementation Plan:**
- Improve the `FetchMetrics` object to store a trace of *why* each method failed (e.g., "urllib: 403 Forbidden" -> "CDP: Connection Refused" -> "Selenium: Success").
- Ensure these details are exposed in the `wf --diagnose` command and the final Markdown footer.

### 4. CDP Session Persistence (Future)

For `wf batch` command:
- Refactor `CDPFetcher` to accept an existing `browser` instance.
- In `cli.py`'s batch loop, instantiate `CDPFetcher` once and pass it to the processing function.

## Summary of Recommendations

1.  **Implement "Fail-Fast" in `fetch_html_with_retry`** for 403/412 errors.
2.  **Implement SPA Detection:** Treat "200 OK" but empty/script-only responses as failures to trigger CDP fallback.
3.  **Persist Template Name:** Ensure the parser template name is always recorded in metadata (Completed in v1.1.1).
4.  **Standardize Timeout:** Ensure `ensure_chrome_debug.sh` and Python timeouts are aligned (Completed: both now use ~15s).
