# Task 000 Design Updates

## Changes Made - 2025-10-09

### Summary
Updated manual Chrome hybrid integration design based on practical macOS usage feedback. All modifications improve simplicity, reliability, and user experience for single-user macOS environment.

---

## Key Changes Applied

### 1. **Platform Support Simplification**
**What Changed**:
- Marked manual_chrome module as "macOS only"
- Removed Linux/Windows paths and complexity
- Keep only: `/Applications/Google Chrome.app/Contents/MacOS/Google Chrome`
- Added optional `chrome_path` config parameter

**Benefits**:
- Simpler implementation
- Clearer focus for development
- Easy to extend to other platforms later if needed

**Implementation Details**:
```python
# Default Chrome path for macOS
chrome_path = self.config.get('chrome', {}).get('path',
    '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome')
```

---

### 2. **Chrome Startup Check Improvement**
**What Changed**:
- Replaced `which` command with `os.path.exists()`
- Added dedicated validation method with clear error messages
- Added port availability check with helpful solutions

**Benefits**:
- More reliable Chrome detection
- Better error messages guide users to solutions
- Prevents port conflict issues upfront

**Error Message Example**:
```
Chrome not found at: /Applications/Google Chrome.app/Contents/MacOS/Google Chrome

Please install Chrome or set custom path in:
  config/manual_chrome_config.yaml

Example config:
  chrome:
    path: '/path/to/Google Chrome'
```

---

### 3. **Selenium Manager Integration**
**What Changed**:
- Use Selenium's built-in Selenium Manager for chromedriver
- Simply use `webdriver.Chrome()` without specifying driver path
- Added WebDriverException handling with diagnostic guidance

**Benefits**:
- No manual chromedriver installation needed
- Automatic driver version matching
- Reduced configuration complexity

**Requirements**:
- Selenium 4.6+ (checked in diagnostic tool)

---

### 4. **Cleanup Logic Improvement**
**What Changed**:
- ALWAYS call `self.driver.quit()` to release resources
- Only terminate Chrome process when `force=True`
- Proper exception handling in cleanup

**Benefits**:
- Prevents chromedriver from occupying port
- Better resource management
- Chrome stays open for user unless explicitly closed

**Code Pattern**:
```python
def _cleanup(self, force=False):
    # ALWAYS quit driver
    if self.driver:
        self.driver.quit()
        self.driver = None

    # Only terminate Chrome if forced
    if force and self.chrome_process:
        self.chrome_process.terminate()
```

---

### 5. **UX Simplification with Graceful Fallback**
**What Changed**:
- Keep terminal prompts as essential (always shown)
- Wrap clipboard in try/except with fallback message
- Wrap notifications in try/except (silent fail)
- Core functionality works without optional dependencies

**Benefits**:
- Works even without pyperclip installed
- No blocking on missing optional libraries
- Clear fallback messages when features unavailable

**Graceful Degradation Example**:
```python
try:
    import pyperclip
    pyperclip.copy(url)
    print("✓ URL copied to clipboard")
except ImportError:
    print("⚠️  pyperclip not available")
    print("   Please manually copy URL from above")
```

---

### 6. **Added Comprehensive Diagnostic Tool**
**New Feature**:
- `--diagnose` flag for CLI tool
- Checks all prerequisites and dependencies
- Provides actionable solutions for issues

**Diagnostic Checks**:
1. Platform verification (macOS)
2. Chrome installation and version
3. Selenium version and Manager support
4. Port availability
5. Optional dependencies status
6. Chrome startup test
7. Selenium attachment test

**Usage**:
```bash
python scripts/manual_mode_cli.py --diagnose
```

---

## Validation Checklist

### Core Functionality
- [ ] Chrome starts with default path on macOS
- [ ] Chrome starts with custom path configuration
- [ ] Error shown when Chrome not found
- [ ] Error shown when port 9222 occupied
- [ ] Selenium Manager auto-downloads chromedriver
- [ ] Driver cleanup always happens
- [ ] Chrome process only terminates when forced

### Graceful Degradation
- [ ] Works without pyperclip installed
- [ ] Works without notification support
- [ ] Clear fallback messages shown
- [ ] Core functionality unaffected by optional dependencies

### Diagnostic Tool
- [ ] --diagnose identifies Chrome installation issues
- [ ] --diagnose checks Selenium version correctly
- [ ] --diagnose detects port conflicts
- [ ] --diagnose provides actionable solutions

### User Experience
- [ ] Clear instructions always displayed
- [ ] URL shown even if clipboard fails
- [ ] Error messages guide to solutions
- [ ] Process completes in < 30 seconds

---

## Breaking Changes
**None** - This is new functionality being added to the system.

---

## Migration Notes

### For Developers
1. Ensure Selenium 4.6+ is installed for Selenium Manager support
2. Default configuration assumes macOS environment
3. Optional dependencies (pyperclip) are not required for core functionality

### For Users
1. Chrome must be installed in default location or path configured
2. Port 9222 must be available (close other Chrome debug instances)
3. Clipboard functionality requires pyperclip (optional)

---

## Configuration Template (Updated)

```yaml
# config/manual_chrome_config.yaml
manual_chrome:
  enabled: true
  platform: macos  # macOS only for now

  chrome:
    # Optional: Custom Chrome path
    # path: "/path/to/Google Chrome"
    debug_port: 9222
    user_data_dir: /tmp/web-fetcher-manual
    flags:
      - --no-first-run
      - --disable-extensions

  trigger_conditions:
    all_retries_exhausted: true
    content_size_below: 100
    status_codes: [400, 403, 412]

  ux:
    auto_copy_url: true      # Graceful fallback if unavailable
    show_notification: false # Optional macOS notifications
    wait_timeout: 300

  log_level: INFO
```

---

## Testing Requirements

### Unit Tests Added/Modified
- `test_validate_chrome_installation()` - Uses os.path.exists
- `test_check_debug_port()` - Port availability checking
- `test_selenium_manager_usage()` - No driver path specified
- `test_cleanup_logic()` - Always quit driver behavior
- `test_graceful_clipboard_fallback()` - ImportError handling

### Integration Tests Needed
- Test with Chrome in non-default location
- Test with port already in use
- Test without pyperclip installed
- Test Selenium Manager auto-download
- Test on fresh macOS installation

---

## Document Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-10-09 | Initial design document |
| 2.0 | 2025-10-09 | Applied macOS simplifications based on user feedback |

---

## Review Status

- ✅ Architecture Review: Approved
- ✅ Simplification Benefits: Confirmed
- ✅ Risk Assessment: Acceptable
- ✅ Ready for Implementation: Yes

---

*End of Update Summary*